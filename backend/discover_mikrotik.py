#!/usr/bin/env python3
"""
MikroTik Device Discovery using MNDP (MikroTik Neighbor Discovery Protocol)
Works just like Winbox - discovers all MikroTik devices on the network
"""

import socket
import struct
import time
from typing import List, Dict

class MikroTikDiscovery:
    """Discover MikroTik devices using MNDP protocol"""

    MNDP_PORT = 5678
    BROADCAST_ADDR = '<broadcast>'

    def __init__(self):
        self.devices = {}

    def discover(self, timeout: int = 3) -> List[Dict]:
        """
        Discover MikroTik devices on the local network

        Args:
            timeout: How long to listen for responses (seconds)

        Returns:
            List of discovered devices with their details
        """
        print(f"Scanning for MikroTik devices (timeout: {timeout}s)...")

        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(timeout)

            # Bind to MNDP port
            sock.bind(('', self.MNDP_PORT))

            print(f"Listening on UDP port {self.MNDP_PORT}...")

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(1500)
                    device_info = self._parse_mndp_packet(data, addr)
                    if device_info:
                        device_id = device_info.get('mac', addr[0])
                        self.devices[device_id] = device_info
                        self._print_device(device_info)
                except socket.timeout:
                    break
                except Exception as e:
                    print(f"Error receiving packet: {e}")
                    continue

            sock.close()

            print(f"\n✓ Found {len(self.devices)} MikroTik device(s)")
            return list(self.devices.values())

        except PermissionError:
            print("✗ Permission denied. Try running with sudo:")
            print("  sudo python3 discover_mikrotik.py")
            return []
        except Exception as e:
            print(f"✗ Discovery error: {e}")
            return []

    def _parse_mndp_packet(self, data: bytes, addr: tuple) -> Dict:
        """Parse MNDP packet and extract device information"""
        try:
            device = {
                'source_ip': addr[0],
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # MNDP packets contain TLV (Type-Length-Value) fields
            offset = 0
            while offset < len(data) - 4:
                try:
                    # Read TLV header
                    tlv_type = struct.unpack_from('!H', data, offset)[0]
                    tlv_length = struct.unpack_from('!H', data, offset + 2)[0]
                    offset += 4

                    if offset + tlv_length > len(data):
                        break

                    tlv_value = data[offset:offset + tlv_length]
                    offset += tlv_length

                    # Parse known TLV types
                    if tlv_type == 1:  # MAC address
                        device['mac'] = ':'.join(f'{b:02x}' for b in tlv_value)
                    elif tlv_type == 5:  # Identity/hostname
                        device['identity'] = tlv_value.decode('utf-8', errors='ignore')
                    elif tlv_type == 7:  # Version
                        device['version'] = tlv_value.decode('utf-8', errors='ignore')
                    elif tlv_type == 8:  # Platform
                        device['platform'] = tlv_value.decode('utf-8', errors='ignore')
                    elif tlv_type == 10:  # Uptime
                        if len(tlv_value) >= 4:
                            uptime_sec = struct.unpack('!I', tlv_value[:4])[0]
                            device['uptime'] = self._format_uptime(uptime_sec)
                    elif tlv_type == 11:  # Software ID
                        device['software_id'] = tlv_value.decode('utf-8', errors='ignore')
                    elif tlv_type == 12:  # Board name
                        device['board'] = tlv_value.decode('utf-8', errors='ignore')
                    elif tlv_type == 14:  # IPv6 address
                        device['ipv6'] = tlv_value.decode('utf-8', errors='ignore')
                    elif tlv_type == 15:  # Interface name
                        device['interface'] = tlv_value.decode('utf-8', errors='ignore')

                except Exception as e:
                    # Skip malformed TLV
                    break

            return device if 'mac' in device else None

        except Exception as e:
            return None

    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in human-readable format"""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def _print_device(self, device: Dict):
        """Pretty print device information"""
        print("\n" + "="*60)
        print(f"MAC Address:  {device.get('mac', 'Unknown')}")
        print(f"IP Address:   {device.get('source_ip', 'Unknown')}")
        print(f"Identity:     {device.get('identity', 'Unknown')}")
        print(f"Version:      {device.get('version', 'Unknown')}")
        print(f"Platform:     {device.get('platform', 'Unknown')}")
        print(f"Board:        {device.get('board', 'Unknown')}")
        print(f"Uptime:       {device.get('uptime', 'Unknown')}")
        print("="*60)

    def get_device_by_mac(self, mac_address: str) -> Dict:
        """Get device info by MAC address"""
        mac_normalized = mac_address.lower().replace('-', ':')
        for device in self.devices.values():
            if device.get('mac', '').lower() == mac_normalized:
                return device
        return None


def main():
    """Main function - run discovery"""
    print("MikroTik Device Discovery Tool")
    print("=" * 60)

    discovery = MikroTikDiscovery()
    devices = discovery.discover(timeout=5)

    if not devices:
        print("\n⚠️  No devices found. Make sure:")
        print("  1. You're on the same network as MikroTik devices")
        print("  2. MikroTik Neighbor Discovery is enabled")
        print("  3. Your firewall isn't blocking UDP port 5678")
        print("  4. Try running with sudo for better results")
        print("\nTo enable neighbor discovery on MikroTik:")
        print("  /ip neighbor discovery set discover=yes")
    else:
        print(f"\n✓ Discovery complete!")
        print(f"\nTo use a device, add its MAC to your .env file:")
        for device in devices:
            print(f"  MIKROTIK_HOST={device.get('mac')}")


if __name__ == "__main__":
    main()
