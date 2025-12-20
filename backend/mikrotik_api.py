import os
import re
import subprocess
from datetime import datetime

import routeros_api
from dotenv import load_dotenv

load_dotenv()


class MikroTikAPI:
    def __init__(self):
        self.original_host = os.getenv(
            "MIKROTIK_HOST", "192.168.88.1"
        )  # Store original (MAC or IP)
        self.host = self.original_host
        self.username = os.getenv("MIKROTIK_USERNAME", "admin")
        self.password = os.getenv("MIKROTIK_PASSWORD", "")
        self.port = int(os.getenv("MIKROTIK_PORT", "8728"))
        self.connection = None
        self.cached_ip = None  # Cache resolved IP
        self.last_scan_time = 0  # Track last scan (avoid frequent rescans)

        # If host is MAC address, try to find IP
        if self._is_mac_address(self.original_host):
            print(f"MAC address detected: {self.original_host}")
            ip = self._find_ip_from_mac(self.original_host)
            if ip:
                print(f"✓ Resolved to: {ip}")
                self.host = ip
                self.cached_ip = ip
                import time

                self.last_scan_time = time.time()
            else:
                print(f"✗ Could not resolve MAC to IP")

    def refresh_config(self):
        """Reload configuration from .env and clear caches"""
        from dotenv import load_dotenv

        load_dotenv(override=True)  # Force reload .env

        # Clear connection and caches
        if self.connection:
            try:
                self.connection.disconnect()
            except:
                pass
        self.connection = None
        self.cached_ip = None
        self.last_scan_time = 0

        # Reload config
        self.original_host = os.getenv("MIKROTIK_HOST", "192.168.88.1")
        self.host = self.original_host
        self.username = os.getenv("MIKROTIK_USERNAME", "admin")
        self.password = os.getenv("MIKROTIK_PASSWORD", "")
        self.port = int(os.getenv("MIKROTIK_PORT", "8728"))

        print(f"✓ Configuration refreshed - MikroTik host: {self.host}")

    def _is_mac_address(self, address):
        """Check if the address is a MAC address"""
        mac_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
        return bool(mac_pattern.match(address))

    def _get_local_network(self):
        """Get local network subnet"""
        try:
            import socket

            import netifaces

            # Try using netifaces (more reliable)
            try:
                gateways = netifaces.gateways()
                default_interface = gateways["default"][netifaces.AF_INET][1]
                addrs = netifaces.ifaddresses(default_interface)
                ip = addrs[netifaces.AF_INET][0]["addr"]
                # Extract subnet (e.g., 192.168.1.x from 192.168.1.100)
                subnet = ".".join(ip.split(".")[0:3])
                return subnet
            except:
                pass

            # Fallback: use socket to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            subnet = ".".join(local_ip.split(".")[0:3])
            return subnet
        except:
            return "192.168.1"  # Default fallback

    def _find_ip_from_mac(self, mac_address):
        """Find IP address from MAC address using ARP - FAST VERSION"""
        try:
            mac_normalized = mac_address.lower().replace("-", ":")

            # STEP 1: Quick ARP cache check (instant)
            result = subprocess.run(
                ["arp", "-a"], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split("\n"):
                if mac_normalized in line.lower():
                    ip_match = re.search(r"\(([0-9.]+)\)", line)
                    if ip_match:
                        found_ip = ip_match.group(1)
                        print(f"✓ Found in ARP cache: {found_ip}")
                        return found_ip

            # STEP 2: Quick targeted ping (2-3 seconds max)
            print(f"Scanning for MAC {mac_address}...")
            subnet = self._get_local_network()

            # Only check most likely IPs (gateway, MikroTik default, and .159)
            quick_scan = [f"{subnet}.1", f"{subnet}.159", "192.168.88.1"]

            # Ping all at once using threading for speed
            import threading

            def quick_ping(ip):
                try:
                    subprocess.run(
                        ["ping", "-c", "1", "-W", "1", ip],
                        capture_output=True,
                        timeout=2,
                    )
                except:
                    pass

            threads = []
            for ip in quick_scan:
                t = threading.Thread(target=quick_ping, args=(ip,))
                t.start()
                threads.append(t)

            # Wait for all pings (max 2 seconds)
            for t in threads:
                t.join(timeout=2)

            # Quick ARP check
            result = subprocess.run(
                ["arp", "-a"], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split("\n"):
                if mac_normalized in line.lower():
                    ip_match = re.search(r"\(([0-9.]+)\)", line)
                    if ip_match:
                        found_ip = ip_match.group(1)
                        print(f"✓ Found after quick scan: {found_ip}")
                        return found_ip

            print(f"✗ Could not find MAC {mac_address} quickly")
            print(f"TIP: Make sure you're on the same network as the router")

        except Exception as e:
            print(f"Error finding IP from MAC: {e}")

        return None

    def connect(self, retry=True):
        """Establish connection to MikroTik router"""
        import time

        max_retries = 3 if retry else 1

        for attempt in range(max_retries):
            try:
                # Disconnect existing connection if any
                if self.connection:
                    try:
                        self.connection.disconnect()
                    except:
                        pass
                    self.connection = None

                # Re-resolve MAC to IP only if needed (smart caching)
                if self._is_mac_address(self.original_host):
                    current_time = time.time()
                    cache_age = current_time - self.last_scan_time

                    # Use cached IP if it's less than 5 minutes old, otherwise re-scan
                    if self.cached_ip and cache_age < 300:  # 5 minutes
                        self.host = self.cached_ip
                        if attempt == 0:  # Only print on first attempt
                            print(f"Using cached IP: {self.cached_ip}")
                    else:
                        print(f"Refreshing IP for MAC {self.original_host}...")
                        ip = self._find_ip_from_mac(self.original_host)
                        if ip:
                            self.host = ip
                            self.cached_ip = ip
                            self.last_scan_time = current_time
                        else:
                            print(f"✗ Could not resolve MAC to IP")
                            if attempt < max_retries - 1:
                                time.sleep(2)
                                continue
                            return False

                print(
                    f"Connecting to MikroTik at {self.host}:{self.port} (attempt {attempt + 1}/{max_retries})..."
                )

                # Set socket timeout (increased for network latency)
                import socket

                socket.setdefaulttimeout(240)

                self.connection = routeros_api.RouterOsApiPool(
                    self.host,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    plaintext_login=True,
                )
                print(f"✅ Connected to MikroTik successfully")
                return True
            except Exception as e:
                print(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                return False

        return False

    def disconnect(self):
        """Close connection to MikroTik router"""
        if self.connection:
            self.connection.disconnect()

    def create_user(self, username, password, plan_type):
        """Create a new hotspot user in MikroTik"""
        for attempt in range(2):  # Try twice
            try:
                # Always reconnect for each operation to avoid stale connections
                if not self.connect():
                    raise Exception("Failed to connect to MikroTik")

                # Get fresh API instance
                api = self.connection.get_api()

                # Determine profile and uptime limit based on plan type
                profile = plan_type  # 'daily_1000' or 'monthly_1000'

                # Set uptime limit (actual usage time, not calendar time)
                if plan_type == "daily_1000":
                    uptime_limit = "1d"  # 24 hours of actual usage
                elif plan_type == "monthly_1000":
                    uptime_limit = "30d"  # 30 days of actual usage
                else:
                    uptime_limit = "1d"  # Default to 1 day

                print(f"Getting hotspot user resource...")
                # Create hotspot user
                user_resource = api.get_resource("/ip/hotspot/user")

                print(f"Adding user {username} with profile {profile} and uptime limit {uptime_limit}...")
                user_resource.add(
                    name=username,
                    password=password,
                    profile=profile,
                    **{"limit-uptime": uptime_limit}
                )

                print(f"User {username} created successfully in MikroTik")
                return True
            except Exception as e:
                print(f"Failed to create user {username} (attempt {attempt + 1}): {e}")
                if attempt == 0:  # First attempt failed, clear connection and retry
                    self.connection = None
                    continue
                return False
        return False

    def disable_user(self, username):
        """Disable a hotspot user in MikroTik"""
        for attempt in range(2):  # Try twice
            try:
                # Always reconnect for each operation
                if not self.connect():
                    raise Exception("Failed to connect to MikroTik")

                api = self.connection.get_api()
                user_resource = api.get_resource("/ip/hotspot/user")

                # Find the user
                users = user_resource.get(name=username)
                if users:
                    user_id = users[0]["id"]
                    user_resource.set(id=user_id, disabled="yes")
                    print(f"User {username} disabled successfully")
                    return True
                else:
                    print(f"User {username} not found")
                    return False
            except Exception as e:
                print(f"Failed to disable user {username} (attempt {attempt + 1}): {e}")
                if attempt == 0:
                    self.connection = None
                    continue
                return False
        return False

    def enable_user(self, username):
        """Enable a hotspot user in MikroTik"""
        for attempt in range(2):  # Try twice
            try:
                # Always reconnect for each operation
                if not self.connect():
                    raise Exception("Failed to connect to MikroTik")

                api = self.connection.get_api()
                user_resource = api.get_resource("/ip/hotspot/user")

                # Find the user
                users = user_resource.get(name=username)
                if users:
                    user_id = users[0]["id"]
                    user_resource.set(id=user_id, disabled="no")
                    print(f"User {username} enabled successfully")
                    return True
                else:
                    print(f"User {username} not found")
                    return False
            except Exception as e:
                print(f"Failed to enable user {username} (attempt {attempt + 1}): {e}")
                if attempt == 0:
                    self.connection = None
                    continue
                return False
        return False

    def get_active_users(self):
        """Get list of all active hotspot users"""
        try:
            if not self.connection:
                self.connect()

            api = self.connection.get_api()
            active_resource = api.get_resource("/ip/hotspot/active")

            active_users = active_resource.get()
            return active_users
        except Exception as e:
            print(f"Failed to get active users: {e}")
            return []

    def get_all_users(self):
        """Get list of all configured hotspot users from MikroTik"""
        try:
            # Always reconnect for each operation to avoid stale connections
            if not self.connect():
                raise Exception("Failed to connect to MikroTik")

            api = self.connection.get_api()
            user_resource = api.get_resource("/ip/hotspot/user")

            users = user_resource.get()
            # Return list of usernames
            return [user.get("name") for user in users if user.get("name")]
        except Exception as e:
            print(f"Failed to get all users: {e}")
            return []

    def delete_user(self, username):
        """Delete a hotspot user from MikroTik with retry logic"""
        for attempt in range(3):  # Try 3 times
            try:
                # Always reconnect for each operation to avoid stale connections
                if not self.connect():
                    print(f"Failed to connect to MikroTik (attempt {attempt + 1}/3)")
                    if attempt < 2:
                        self.connection = None
                        continue
                    return False

                api = self.connection.get_api()
                user_resource = api.get_resource("/ip/hotspot/user")

                # Find and delete the user
                users = user_resource.get(name=username)
                if users:
                    user_id = users[0]["id"]
                    user_resource.remove(id=user_id)
                    print(f"User {username} deleted successfully from MikroTik")
                    return True
                else:
                    print(f"User {username} not found in MikroTik")
                    return True  # Return True if user doesn't exist (already deleted)
            except Exception as e:
                print(
                    f"Failed to delete user {username} (attempt {attempt + 1}/3): {e}"
                )
                if attempt < 2:
                    self.connection = None
                    continue
                return False
        return False


# Global instance
mikrotik = MikroTikAPI()
