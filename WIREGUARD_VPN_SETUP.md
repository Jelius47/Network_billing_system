# WireGuard VPN Setup - Connect Cloud Server to MikroTik

This guide sets up a WireGuard VPN tunnel between your cloud server and MikroTik router so they can communicate securely.

## Overview

```
[Cloud Server]  <----- WireGuard Tunnel -----> [MikroTik Router]
164.90.233.185                                  Your Public IP
      |                                               |
   10.99.99.1  <------- VPN Network -------->  10.99.99.2
      |                                               |
      +---------- Can access MikroTik API -----------+
                         10.10.10.1
```

**After setup:**
- Cloud server IP in VPN: `10.99.99.1`
- MikroTik IP in VPN: `10.99.99.2`
- Cloud server can access MikroTik at: `10.10.10.1` or `10.99.99.2`
- Secure, fast, encrypted connection

---

## Step 1: Configure MikroTik WireGuard Server

### 1.1: Generate WireGuard Keys on MikroTik

Connect to MikroTik via WinBox or Terminal:

```
# Generate MikroTik private key
/interface/wireguard add name=wireguard1 listen-port=13231

# View the public key (you'll need this for the cloud server)
/interface/wireguard print
```

**Save this public key!** It will look like:
```
public-key: AbCdEfGh1234567890aBcDeFgH1234567890AbCd=
```

### 1.2: Add VPN IP Address to WireGuard Interface

```
/ip/address add address=10.99.99.2/24 interface=wireguard1 network=10.99.99.0
```

### 1.3: Configure Firewall to Allow WireGuard

```
# Allow WireGuard traffic (UDP port 13231)
/ip/firewall/filter add chain=input action=accept protocol=udp dst-port=13231 \
    comment="Allow WireGuard VPN"

# Allow traffic from VPN network to MikroTik API
/ip/firewall/filter add chain=input action=accept src-address=10.99.99.0/24 \
    protocol=tcp dst-port=8728 \
    comment="Allow API from WireGuard VPN"

# Allow all traffic from VPN
/ip/firewall/filter add chain=input action=accept in-interface=wireguard1 \
    comment="Allow WireGuard Interface"
```

### 1.4: Create Peer for Cloud Server

**First, you need the cloud server's public key. We'll generate it in Step 2, then come back to add it here.**

For now, prepare the command (we'll run it after generating cloud server keys):

```
# YOU'LL RUN THIS AFTER STEP 2
/interface/wireguard/peers
add interface=wireguard1 \
    public-key="CLOUD_SERVER_PUBLIC_KEY_HERE" \
    allowed-address=10.99.99.1/32 \
    comment="Cloud Server"
```

---

## Step 2: Install and Configure WireGuard on Cloud Server

### 2.1: Install WireGuard

```bash
# Update packages
sudo apt update

# Install WireGuard
sudo apt install wireguard -y
```

### 2.2: Generate Keys for Cloud Server

```bash
# Generate private key
wg genkey | sudo tee /etc/wireguard/privatekey
sudo chmod 600 /etc/wireguard/privatekey

# Generate public key from private key
sudo cat /etc/wireguard/privatekey | wg pubkey | sudo tee /etc/wireguard/publickey

# View your public key (you'll add this to MikroTik)
sudo cat /etc/wireguard/publickey
```

**Copy this public key!** You'll add it to MikroTik in the next step.

### 2.3: Get MikroTik Public IP

You need your MikroTik's public IP address. Find it:

**From MikroTik terminal:**
```
/ip address print where interface=ether1
```

Or check: https://whatismyipaddress.com from a device on your network.

**If you have dynamic IP**, you'll need to use MikroTik Cloud DDNS (explained later).

### 2.4: Create WireGuard Configuration File

```bash
sudo nano /etc/wireguard/wg0.conf
```

Add the following (replace the placeholders):

```ini
[Interface]
PrivateKey = YOUR_CLOUD_SERVER_PRIVATE_KEY_FROM_STEP_2.2
Address = 10.99.99.1/24
ListenPort = 51820

# Optional: Add routes to MikroTik's local network
PostUp = ip route add 10.10.10.0/24 dev wg0
PostDown = ip route del 10.10.10.0/24 dev wg0

[Peer]
# MikroTik Router
PublicKey = YOUR_MIKROTIK_PUBLIC_KEY_FROM_STEP_1.1
Endpoint = YOUR_MIKROTIK_PUBLIC_IP:13231
AllowedIPs = 10.99.99.2/32, 10.10.10.0/24
PersistentKeepalive = 25
```

**Example (filled in):**
```ini
[Interface]
PrivateKey = yAnz5TF+lXXJte14tji3zlMNq+hd2rYUIgJBgB3fBmk=
Address = 10.99.99.1/24
ListenPort = 51820
PostUp = ip route add 10.10.10.0/24 dev wg0
PostDown = ip route del 10.10.10.0/24 dev wg0

[Peer]
PublicKey = AbCdEfGh1234567890aBcDeFgH1234567890AbCd=
Endpoint = 41.93.123.456:13231
AllowedIPs = 10.99.99.2/32, 10.10.10.0/24
PersistentKeepalive = 25
```

Save the file (Ctrl+X, Y, Enter).

### 2.5: Set Correct Permissions

```bash
sudo chmod 600 /etc/wireguard/wg0.conf
```

---

## Step 3: Add Cloud Server Peer to MikroTik

Now go back to MikroTik and add the cloud server as a peer:

```
/interface/wireguard/peers add interface=wireguard1 \
    public-key="YOUR_CLOUD_SERVER_PUBLIC_KEY_FROM_STEP_2.2" \
    allowed-address=10.99.99.1/32 \
    comment="Cloud Backend Server"
```

**Example:**
```
/interface/wireguard/peers
add interface=wireguard1 \
    public-key="sOmEpUbLiCkEy1234567890aBcDeFgHiJkLmNoPqRsT=" \
    allowed-address=10.99.99.1/32 \
    comment="Cloud Backend Server"
```

---

## Step 4: Start WireGuard VPN

### 4.1: Enable and Start WireGuard on Cloud Server

```bash
# Enable IP forwarding (if needed)
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf

# Start WireGuard
sudo systemctl start wg-quick@wg0

# Enable on boot
sudo systemctl enable wg-quick@wg0

# Check status
sudo systemctl status wg-quick@wg0
```

### 4.2: Verify WireGuard Connection

```bash
# Check WireGuard interface
sudo wg show

# You should see output like:
# interface: wg0
#   public key: sOmEpUbLiCkEy...
#   private key: (hidden)
#   listening port: 51820
#
# peer: AbCdEfGh1234...
#   endpoint: 41.93.123.456:13231
#   allowed ips: 10.99.99.2/32, 10.10.10.0/24
#   latest handshake: 1 minute, 23 seconds ago
#   transfer: 4.56 KiB received, 2.34 KiB sent
```

**Important:** "latest handshake" should show a recent time. If it says "never", the connection isn't working.

### 4.3: Test VPN Connection

```bash
# Ping MikroTik VPN IP
ping 10.99.99.2 -c 4

# Ping MikroTik LAN IP
ping 10.10.10.1 -c 4
```

If you get replies, the VPN is working!

---

## Step 5: Update Backend Configuration

### 5.1: Update .env File

```bash
sudo nano /var/www/mikrotik-billing/backend/.env
```

Update MikroTik host:

```ini
# MikroTik Configuration - Access via VPN
MIKROTIK_HOST=10.10.10.1
MIKROTIK_USERNAME=api_admin
MIKROTIK_PASSWORD=YourStrongPassword123
MIKROTIK_PORT=8728
```

### 5.2: Restart Backend Service

```bash
sudo systemctl restart mikrotik-backend
```

### 5.3: Check Backend Logs

```bash
sudo journalctl -u mikrotik-backend -f
```

Look for successful connections instead of "Connection refused".

---

## Step 6: Test Backend Connection to MikroTik

```bash
cd /var/www/mikrotik-billing/backend
source venv/bin/activate

python3 << 'EOF'
from mikrotik_api import MikroTikAPI

print("Testing MikroTik API connection via WireGuard VPN...")

api = MikroTikAPI()
try:
    connection = api.connect()
    if connection:
        print("✓ SUCCESS! Connected to MikroTik via WireGuard VPN")

        # Get hotspot users
        resource = connection.get_resource('/ip/hotspot/user')
        users = resource.get()
        print(f"✓ Total hotspot users: {len(users)}")

        # Get WireGuard status
        wg_resource = connection.get_resource('/interface/wireguard')
        wg = wg_resource.get()
        print(f"✓ WireGuard interfaces: {len(wg)}")

        print("\n✓ Everything is working perfectly!")
    else:
        print("✗ Failed to connect to MikroTik")
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check VPN is running: sudo wg show")
    print("2. Test ping: ping 10.10.10.1")
    print("3. Check MikroTik API: /ip service print")
EOF
```

---

## Troubleshooting

### VPN Connection Issues

#### 1. No Handshake on Cloud Server

```bash
# Check WireGuard status
sudo wg show

# If "latest handshake" shows "never":
```

**Possible causes:**
- MikroTik public IP is wrong
- MikroTik firewall blocking UDP 13231
- MikroTik WireGuard peer not configured correctly

**Solutions:**

```bash
# Verify MikroTik IP
ping YOUR_MIKROTIK_PUBLIC_IP

# Check if port is open
nc -vzu YOUR_MIKROTIK_PUBLIC_IP 13231

# Check WireGuard logs
sudo journalctl -u wg-quick@wg0 -f
```

On MikroTik:
```
# Check firewall rules
/ip/firewall/filter print where chain=input

# Check WireGuard peers
/interface/wireguard/peers print

# Check WireGuard interface
/interface/wireguard print
```

#### 2. Can't Ping MikroTik

```bash
# Check routing
ip route show

# Should show route to 10.10.10.0/24 via wg0
```

**If route is missing:**
```bash
# Add manually
sudo ip route add 10.10.10.0/24 dev wg0

# Or restart WireGuard
sudo systemctl restart wg-quick@wg0
```

#### 3. API Connection Still Fails

**Check MikroTik firewall allows VPN:**
```
/ip/firewall/filter print where chain=input

# Should have rule allowing src-address=10.99.99.0/24 to port 8728
```

**Test API access manually:**
```bash
# From cloud server
telnet 10.10.10.1 8728

# If connection refused, check firewall
# If no route to host, check VPN routing
```

### Dynamic IP Solution

If your MikroTik has a dynamic public IP:

#### Enable MikroTik Cloud DDNS:

```
/ip/cloud set ddns-enabled=yes

# Get your domain
/ip/cloud print
```

You'll get something like: `xxxxxxxxxxxx.sn.mynetname.net`

#### Update WireGuard config on cloud server:

```bash
sudo nano /etc/wireguard/wg0.conf
```

Change:
```ini
[Peer]
Endpoint = xxxxxxxxxxxx.sn.mynetname.net:13231
```

Restart WireGuard:
```bash
sudo systemctl restart wg-quick@wg0
```

### Firewall Issues

**Check cloud server firewall:**
```bash
# Check if UFW is blocking
sudo ufw status

# Allow WireGuard
sudo ufw allow 51820/udp
```

**Check MikroTik firewall:**
```
# View input chain rules
/ip/firewall/filter print where chain=input

# Add rule if missing
add chain=input action=accept protocol=udp dst-port=13231 place-before=0
```

---

## Monitoring and Maintenance

### Check VPN Status Regularly

**On Cloud Server:**
```bash
# Check connection
sudo wg show

# Check if handshake is recent (should be < 2 minutes)
sudo wg show wg0 latest-handshakes
```

**On MikroTik:**
```
# Check WireGuard peers
/interface/wireguard/peers print

# Check traffic
/interface/wireguard/peers print stats
```

### Restart VPN if Needed

**Cloud Server:**
```bash
sudo systemctl restart wg-quick@wg0
```

**MikroTik:**
```
/interface/wireguard disable wireguard1
/interface/wireguard enable wireguard1
```

### Monitor Backend Logs

```bash
# Check for API connection errors
sudo journalctl -u mikrotik-backend -f | grep -i "mikrotik\|connection"
```

---

## Security Best Practices

1. ✅ Keep WireGuard keys secure (600 permissions)
2. ✅ Use strong MikroTik API password
3. ✅ Restrict API access to VPN network only
4. ✅ Keep WireGuard updated: `sudo apt update && sudo apt upgrade`
5. ✅ Monitor VPN logs regularly
6. ✅ Use firewall rules to restrict unnecessary access
7. ✅ Change default MikroTik passwords
8. ✅ Backup MikroTik configuration regularly

---

## Quick Command Reference

### Cloud Server Commands

```bash
# Start/Stop VPN
sudo systemctl start wg-quick@wg0
sudo systemctl stop wg-quick@wg0
sudo systemctl restart wg-quick@wg0

# Check status
sudo systemctl status wg-quick@wg0
sudo wg show

# Test connectivity
ping 10.99.99.2  # MikroTik VPN IP
ping 10.10.10.1  # MikroTik LAN IP

# View logs
sudo journalctl -u wg-quick@wg0 -f

# Test API
telnet 10.10.10.1 8728
```

### MikroTik Commands

```
# Check WireGuard
/interface/wireguard print
/interface/wireguard/peers print

# Check firewall
/ip/firewall/filter print where chain=input

# View logs
/log print where topics~"wireguard"

# Test from MikroTik
/ping 10.99.99.1
```

---

## Summary

After completing this setup:

✅ WireGuard VPN tunnel established between cloud server and MikroTik
✅ Cloud server can access MikroTik API securely
✅ Backend can manage hotspot users without issues
✅ No more "Connection refused" errors
✅ Encrypted, fast, modern VPN solution

Your system is now ready for production use!
