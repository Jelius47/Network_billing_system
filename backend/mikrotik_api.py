import routeros_api
import os
import subprocess
import re
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class MikroTikAPI:
    def __init__(self):
        self.host = os.getenv("MIKROTIK_HOST", "192.168.88.1")
        self.username = os.getenv("MIKROTIK_USERNAME", "admin")
        self.password = os.getenv("MIKROTIK_PASSWORD", "")
        self.port = int(os.getenv("MIKROTIK_PORT", "8728"))
        self.connection = None

        # If host is MAC address, try to find IP
        if self._is_mac_address(self.host):
            print(f"MAC address detected: {self.host}")
            ip = self._find_ip_from_mac(self.host)
            if ip:
                print(f"Found IP for MAC {self.host}: {ip}")
                self.host = ip
            else:
                print(f"Warning: Could not find IP for MAC {self.host}, trying anyway...")

    def _is_mac_address(self, address):
        """Check if the address is a MAC address"""
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        return bool(mac_pattern.match(address))

    def _find_ip_from_mac(self, mac_address):
        """Find IP address from MAC address using ARP"""
        try:
            # Run arp -a command
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)

            # Parse ARP table
            mac_normalized = mac_address.lower().replace('-', ':')
            for line in result.stdout.split('\n'):
                if mac_normalized in line.lower():
                    # Extract IP address
                    ip_match = re.search(r'\(([0-9.]+)\)', line)
                    if ip_match:
                        return ip_match.group(1)

            # Try pinging common router IPs to populate ARP cache (with shorter timeout)
            common_ips = ['192.168.1.159', '192.168.88.1', '192.168.1.1']
            for ip in common_ips:
                try:
                    subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                 capture_output=True, timeout=1)
                except subprocess.TimeoutExpired:
                    continue

            # Try ARP again
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if mac_normalized in line.lower():
                    ip_match = re.search(r'\(([0-9.]+)\)', line)
                    if ip_match:
                        return ip_match.group(1)

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

                print(f"Connecting to MikroTik at {self.host}:{self.port} (attempt {attempt + 1}/{max_retries})...")

                # Set socket timeout
                import socket
                socket.setdefaulttimeout(10)

                self.connection = routeros_api.RouterOsApiPool(
                    self.host,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    plaintext_login=True
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

                # Determine profile based on plan type
                profile = plan_type  # 'daily_1000' or 'monthly_1000'

                print(f"Getting hotspot user resource...")
                # Create hotspot user
                user_resource = api.get_resource('/ip/hotspot/user')

                print(f"Adding user {username} with profile {profile}...")
                user_resource.add(
                    name=username,
                    password=password,
                    profile=profile
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
                user_resource = api.get_resource('/ip/hotspot/user')

                # Find the user
                users = user_resource.get(name=username)
                if users:
                    user_id = users[0]['id']
                    user_resource.set(id=user_id, disabled='yes')
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
                user_resource = api.get_resource('/ip/hotspot/user')

                # Find the user
                users = user_resource.get(name=username)
                if users:
                    user_id = users[0]['id']
                    user_resource.set(id=user_id, disabled='no')
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
            active_resource = api.get_resource('/ip/hotspot/active')

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
            user_resource = api.get_resource('/ip/hotspot/user')

            users = user_resource.get()
            # Return list of usernames
            return [user.get('name') for user in users if user.get('name')]
        except Exception as e:
            print(f"Failed to get all users: {e}")
            return []

    def delete_user(self, username):
        """Delete a hotspot user from MikroTik"""
        try:
            if not self.connection:
                self.connect()

            api = self.connection.get_api()
            user_resource = api.get_resource('/ip/hotspot/user')

            # Find and delete the user
            users = user_resource.get(name=username)
            if users:
                user_id = users[0]['id']
                user_resource.remove(id=user_id)
                print(f"User {username} deleted successfully")
                return True
            else:
                print(f"User {username} not found")
                return False
        except Exception as e:
            print(f"Failed to delete user {username}: {e}")
            return False

# Global instance
mikrotik = MikroTikAPI()
