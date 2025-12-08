# MikroTik Router Setup Guide

Complete guide for configuring your MikroTik RB941 router for the billing system.

## Step 1: Initial Router Configuration

### Reset to Defaults (Optional)

```
/system reset-configuration no-defaults=yes
```

### Configure WAN Interface

```
# Configure ether1 as WAN (connected to your ISP)
/ip dhcp-client add interface=ether1 disabled=no

# Or configure static IP if needed
/ip address add address=<your-wan-ip>/24 interface=ether1
/ip route add gateway=<your-gateway>
```

### Configure LAN Network

```
# Create bridge for LAN
/interface bridge add name=bridge-lan

# Add interfaces to bridge
/interface bridge port add bridge=bridge-lan interface=ether2
/interface bridge port add bridge=bridge-lan interface=ether3
/interface bridge port add bridge=bridge-lan interface=ether4
/interface bridge port add bridge=bridge-lan interface=wlan1

# Configure LAN IP address
/ip address add address=192.168.88.1/24 interface=bridge-lan

# Enable DHCP server on LAN
/ip pool add name=dhcp-pool ranges=192.168.88.10-192.168.88.254
/ip dhcp-server add name=dhcp-lan interface=bridge-lan address-pool=dhcp-pool disabled=no
/ip dhcp-server network add address=192.168.88.0/24 gateway=192.168.88.1 dns-server=8.8.8.8,1.1.1.1
```

### Configure NAT

```
/ip firewall nat add chain=srcnat action=masquerade out-interface=ether1
```

## Step 2: Hotspot Setup

### Quick Hotspot Setup

```
/ip hotspot setup
```

Answer the prompts:
- Hotspot interface: `bridge-lan`
- Local address: `192.168.88.1/24`
- Address pool: `192.168.88.100-192.168.88.200`
- SSL certificate: `none` (use HTTP for speed)
- SMTP server: (leave blank)
- DNS servers: `8.8.8.8,1.1.1.1`
- DNS name: `hotspot.local`
- Administrator password: `<your-password>`

### Create Hotspot User Profiles

```
# Daily plan (24 hours, 1000 limit)
/ip hotspot user profile add name=daily_1000 rate-limit=1M/1M session-timeout=1d

# Monthly plan (30 days, 1000 limit)
/ip hotspot user profile add name=monthly_1000 rate-limit=1M/1M session-timeout=30d
```

You can adjust the `rate-limit` values:
- `1M/1M` = 1 Mbps upload/download
- `2M/2M` = 2 Mbps upload/download
- `5M/5M` = 5 Mbps upload/download

## Step 3: API Configuration

### Enable API

```
# Enable API on default port
/ip service set api disabled=no

# Optional: Change API port (default is 8728)
/ip service set api port=8728

# Optional: Restrict API access to specific IP
/ip service set api address=192.168.88.0/24
```

### Create API Admin User

```
# Create dedicated user for API access
/user add name=api_admin password=<strong-password> group=full
```

**Important:** Use a strong password for the API user!

### Test API Connection

From your backend server, test the connection:

```bash
# Install routeros-api
pip install routeros-api

# Test connection
python3 -c "
import routeros_api
connection = routeros_api.RouterOsApiPool('192.168.88.1', username='api_admin', password='your-password', plaintext_login=True)
api = connection.get_api()
print('Connection successful!')
connection.disconnect()
"
```

## Step 4: Firewall Configuration

### Allow API Access

```
# Allow API access from your server
/ip firewall filter add chain=input protocol=tcp dst-port=8728 src-address=<your-server-ip> action=accept comment="API Access"

# Optional: Allow web access from your server
/ip firewall filter add chain=input protocol=tcp dst-port=80 src-address=<your-server-ip> action=accept comment="Web Access"
```

### Secure the Router

```
# Disable unnecessary services
/ip service set telnet disabled=yes
/ip service set ftp disabled=yes
/ip service set www disabled=yes
/ip service set ssh disabled=no
/ip service set api-ssl disabled=yes

# Add basic firewall rules
/ip firewall filter add chain=input connection-state=established,related action=accept
/ip firewall filter add chain=input connection-state=invalid action=drop
/ip firewall filter add chain=input protocol=icmp action=accept
/ip firewall filter add chain=input src-address=192.168.88.0/24 action=accept
/ip firewall filter add chain=input action=drop comment="Drop all other input"
```

## Step 5: Walled Garden (Optional)

Allow access to payment portal without login:

```
# Allow access to your billing dashboard
/ip hotspot walled-garden add dst-host=<your-dashboard-ip> action=accept
/ip hotspot walled-garden ip add action=accept dst-address=<your-dashboard-ip>
```

## Step 6: Backup Configuration

```
# Create backup
/system backup save name=billing-system-backup

# Export configuration as text
/export file=billing-system-config
```

## Testing Hotspot

1. Connect a device to the LAN network
2. Open a web browser
3. You should be redirected to the hotspot login page
4. Create a test user through the dashboard
5. Login with the test credentials
6. Verify internet access

## Troubleshooting

### Cannot access router
- Check physical connections
- Reset router to defaults
- Access via MAC address: `0.0.0.0` in Winbox

### API connection fails
- Verify API is enabled: `/ip service print`
- Check firewall rules
- Verify credentials
- Test with Winbox first

### Hotspot not redirecting
- Check hotspot status: `/ip hotspot print`
- Verify DNS configuration
- Check hotspot interface
- Clear browser cache

### Users can't login
- Verify user exists: `/ip hotspot user print`
- Check user profile
- Verify password is correct
- Check hotspot active users: `/ip hotspot active print`

## Quick Commands Reference

```bash
# View hotspot users
/ip hotspot user print

# View active users
/ip hotspot active print

# Disable a user
/ip hotspot user set [find name=username] disabled=yes

# Enable a user
/ip hotspot user set [find name=username] disabled=no

# Remove a user
/ip hotspot user remove [find name=username]

# View system resources
/system resource print

# View logs
/log print
```

## Security Best Practices

1. Change default admin password
2. Use strong passwords for API user
3. Disable unnecessary services
4. Implement firewall rules
5. Regular backups
6. Update RouterOS to latest stable version
7. Monitor logs regularly
8. Restrict API access to specific IPs

## Next Steps

After completing this setup:
1. Configure the backend `.env` file with your router details
2. Test the API connection
3. Create your first user through the dashboard
4. Monitor the system logs
5. Set up automated backups
