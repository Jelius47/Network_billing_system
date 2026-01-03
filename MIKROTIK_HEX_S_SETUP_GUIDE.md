# MikroTik Hex S Configuration Guide for Hotspot Billing System

This guide will help you configure your new MikroTik Hex S router to work with your hotspot billing system.

## Table of Contents
1. [Initial Router Setup](#initial-router-setup)
2. [Network Configuration](#network-configuration)
3. [Hotspot Configuration](#hotspot-configuration)
4. [API User Setup](#api-user-setup)
5. [Testing the Setup](#testing-the-setup)
6. [Uploading Hotspot Login Page](#uploading-hotspot-login-page)

---

## Initial Router Setup

### 1. Connect to Your MikroTik Hex S

**Option A: Via WinBox (Recommended)**
1. Download WinBox from [mikrotik.com/download](https://mikrotik.com/download)
2. Connect your computer to any LAN port on the Hex S
3. Open WinBox
4. Click on "Neighbors" tab
5. Select your MikroTik device (MAC address will be shown)
6. Default credentials:
   - Username: `admin`
   - Password: (empty)

**Option B: Via Web Browser**
1. Connect to LAN port
2. Open browser and go to `http://192.168.88.1`
3. Login with default credentials

### 2. Update RouterOS (Recommended)

```
/system package update
check-for-updates
# If updates available:
download
# Wait for download, then:
/system reboot
```

### 3. Reset to Default Configuration (If needed)

```
/system reset-configuration no-defaults=yes skip-backup=yes
```

---

## Network Configuration

### 1. Configure WAN Interface (Internet Connection)

**If using DHCP from ISP:**
```
/ip dhcp-client add interface=ether1 disabled=no
```

**If using Static IP:**
```
/ip address
add address=YOUR_ISP_IP/SUBNET interface=ether1

/ip route
add gateway=YOUR_ISP_GATEWAY

/ip dns
set servers=8.8.8.8,8.8.4.4
```

### 2. Configure LAN Network

```
# Create bridge for LAN ports
/interface bridge add name=bridge-lan

# Add LAN ports to bridge
/interface bridge port
add bridge=bridge-lan interface=ether2
add bridge=bridge-lan interface=ether3
add bridge=bridge-lan interface=ether4
add bridge=bridge-lan interface=ether5

# Set LAN IP address
/ip address add address=10.10.10.1/24 interface=bridge-lan network=10.10.10.0

# Create IP pool for hotspot
/ip pool add name=hotspot-pool ranges=10.10.10.10-10.10.10.254

# Setup DHCP for your admin network (optional - separate admin VLAN)
# This is if you want to access the router from a specific admin network
```

### 3. Configure NAT (Masquerade)

```
/ip firewall nat add chain=srcnat action=masquerade out-interface=ether1 comment="Internet NAT"
```

---

## Hotspot Configuration

### 1. Quick Hotspot Setup

**Using Terminal:**
```
/ip hotspot setup
# Answer the prompts:
# hotspot interface: bridge-lan
# local address of network: 10.10.10.1/24
# address pool for hotspot network: hotspot-pool
# select certificate: none
# smtp server: 0.0.0.0
# dns servers: 8.8.8.8
# dns name: wifi.local
# name of local hotspot user: (skip - leave empty)
# password for the user: (skip - leave empty)
```

**This will automatically create:**
- Hotspot server on bridge-lan
- IP pool
- Hotspot profile
- Firewall rules

### 2. Configure Hotspot Profile

```
/ip hotspot profile set hsprof1 \
    login-by=http-chap,http-pap,https \
    use-radius=no \
    trial-uptime-limit=5m \
    trial-user-profile=default

# Important: Disable trial users if you don't want free access
set hsprof1 trial-uptime-limit=none trial-user-profile=none
```

### 3. Configure User Profiles for Time-Based Plans

```
# Daily plan profile (24 hours of usage time)
/ip hotspot user profile \
add name=daily_1000 \
    idle-timeout=5m \
    keepalive-timeout=2m \
    status-autorefresh=1m \
    shared-users=1 \
    rate-limit=3M/3M \
    transparent-proxy=no

# Monthly plan profile (30 days of usage time)
/ip hotspot user profile \
add name=monthly_1000 \
    idle-timeout=5m \
    keepalive-timeout=2m \
    status-autorefresh=1m \
    shared-users=1 \
    rate-limit=3M/3M \
    transparent-proxy=no

# Monthly 2-device plan
/ip hotspot user profile \
add name=monthly_15000 \
    idle-timeout=5m \
    keepalive-timeout=2m \
    status-autorefresh=1m \
    shared-users=2 \
    rate-limit=3M/3M \
    transparent-proxy=no
```

**Note:** The actual time limiting (24h for daily, 30 days for monthly) is handled by your backend system via the `uptime-limit` parameter when creating users through the API.

### 4. Disable Default Login Page (We'll use custom)

```
/ip hotspot walled-garden\
add dst-host=*.facebook.com\
add dst-host=*.google.com\
add dst-host=YOUR_BACKEND_SERVER_IP comment="Allow access to payment system"

# Allow access to your backend server without authentication
/ip hotspot walled-garden ip
add action=accept dst-address=YOUR_BACKEND_SERVER_IP
```

---

## API User Setup

### 1. Create API Admin User

```
/user group add name=api_admin policy=api,read,write,policy,test,!local,!telnet,!ssh,!ftp,!reboot,!password

/user add name=api_admin password=YourStrongPassword123 group=api_admin \
    comment="API user for billing system"
```

### 2. Enable API Service

```
/ip service set api address=0.0.0.0/0 disabled=no port=8728

# Optional: Restrict API access to your server IP only
set api address=YOUR_BACKEND_SERVER_IP/32
```

### 3. Configure Firewall for API Access

```
# Allow API access from your backend server
/ip firewall filter add chain=input protocol=tcp dst-port=8728 \
    src-address=164.90.233.185 \
    action=accept comment="Allow API from backend server"

# If you want to access from anywhere (development only):
add chain=input protocol=tcp dst-port=8728 action=accept comment="Allow API"
```

---

## Uploading Hotspot Login Page

### 1. Prepare Your Login Page

Your custom login page is located at:
`docs/hotspot/login.html`

**Update the API_BASE_URL in login.html:**

Open the file and find line 546:
```javascript
const API_BASE_URL = 'http://YOUR_SERVER_IP:8000/api';
```

Change it to your actual backend server address.

### 2. Upload to MikroTik

**Using WinBox:**
1. Click "Files" in the left menu
2. Drag and drop `login.html` into the Files window
3. Rename it to `hotspot/login.html`

**Using Terminal:**
```
# First, upload via FTP or WinBox, then:
/ip hotspot profile set hsprof1 html-directory=hotspot
```

**Using FTP:**
```bash
# From your computer terminal:
ftp 10.10.10.1
# Login with admin credentials
cd hotspot
put login.html
quit
```

### 3. Set Custom Login Page

```
/ip hotspot profile set hsprof1 html-directory=hotspot login-by=http-chap,http-pap
```

---

## Testing the Setup

### 1. Test Internet Connectivity from Router

```
/ping 8.8.8.8 count=5
/ping google.com count=5
```

### 2. Test Hotspot

1. Connect a device to the LAN/WiFi
2. Try to browse any website
3. You should be redirected to the login page
4. The login page should show the "Buy Access" tab with payment options

### 3. Test API Connectivity

From your backend server, test the connection:

```python
from routeros_api import RouterOsApiPool

connection = RouterOsApiPool(
    '10.10.10.1',  # Your MikroTik IP
    username='api_admin',
    password='YourStrongPassword123',
    port=8728,
    plaintext_login=True
)

api = connection.get_api()
users = api.get_resource('/ip/hotspot/user').get()
print(f"Total hotspot users: {len(users)}")

connection.disconnect()
```

### 4. Test User Creation via Your Backend

```bash
# From your backend server:
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "plan_type": "daily_1000"
  }'
```

---

## WiFi Configuration (Optional)

If your Hex S has WiFi capabilities or you're using an external access point:

### Using External Access Point:

1. Connect AP to one of the LAN ports (ether2-ether5)
2. Configure AP in bridge/AP mode (not router mode)
3. Set AP to use DHCP from MikroTik
4. The AP will automatically be part of the hotspot network

### Configure WiFi Settings on AP:

- **SSID**: Your WiFi network name (e.g., "Guest WiFi")
- **Security**: WPA2-PSK or Open
- **Password**: If using WPA2, set a password
- **Mode**: Bridge/AP mode (not router)
- **DHCP**: Disabled (MikroTik handles DHCP)

---

## Security Hardening (Production)

### 1. Disable Unnecessary Services

```
/ip service
set telnet disabled=yes
set ftp disabled=yes
set www disabled=no
set ssh disabled=no
set api disabled=no
set winbox disabled=no
set api-ssl disabled=yes
```

### 2. Change Default Admin Password

```
/user
set admin password=NewStrongPassword123!
```

### 3. Configure Basic Firewall

```
# Allow established and related connections
/ip firewall filter
add chain=input connection-state=established,related action=accept

# Allow ICMP
add chain=input protocol=icmp action=accept

# Allow access from LAN
add chain=input in-interface=bridge-lan action=accept

# Allow API from backend server
add chain=input protocol=tcp dst-port=8728 src-address=YOUR_BACKEND_SERVER_IP action=accept

# Drop everything else
add chain=input action=drop comment="Drop all other input"
```

### 4. Regular Backups

```
/system backup save name=hex-s-backup
```

Download the backup file regularly via WinBox or FTP.

---

## Troubleshooting

### Users can't connect to internet after login:

Check NAT:
```
/ip firewall nat print
```

### Can't access login page:

Check hotspot status:
```
/ip hotspot print
```

### API connection fails:

1. Check API service is running:
```
/ip service print
```

2. Check firewall rules:
```
/ip firewall filter print
```

3. Test from MikroTik terminal:
```
/ip hotspot user print
```

### Users not being created:

1. Check logs:
```
/log print
```

2. Verify API credentials match your `.env` file

---

## Next Steps

After completing this configuration:

1. Update your backend `.env` file with the MikroTik details
2. Deploy your backend server
3. Update the login.html with your backend URL
4. Test the complete payment flow
5. Monitor the dashboard for analytics

Refer to `DEPLOYMENT_GUIDE.md` for server deployment instructions.
