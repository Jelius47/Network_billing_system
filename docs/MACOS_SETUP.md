# macOS Setup Guide

Complete setup guide specifically for macOS users.

## Prerequisites

- macOS 11.0 (Big Sur) or later
- Homebrew installed
- MikroTik RB941 router on your network

## Step 1: Install Homebrew (if needed)

```bash
# Check if Homebrew is installed
which brew

# If not installed, install it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Step 2: Install Python 3.11

```bash
# Install Python 3.11
brew install python@3.11

# Verify installation
python3.11 --version
```

## Step 3: Install Node.js

```bash
# Install Node.js
brew install node

# Verify installation
node --version
npm --version
```

## Step 4: Install PostgreSQL

### Option A: New PostgreSQL Installation

```bash
# Install PostgreSQL 14
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Verify it's running
brew services list | grep postgresql

# Create database
psql postgres -c "CREATE DATABASE mikrotik_billing;"

# Test connection
psql postgres -c "\l"
```

### Option B: Using Existing PostgreSQL

If you already have PostgreSQL running:

```bash
# Check your PostgreSQL connection
psql postgres -c "SELECT version();"

# Create the billing database
psql postgres -c "CREATE DATABASE mikrotik_billing;"

# Or if you have a different connection URL
psql postgresql://localhost:5432/postgres -c "CREATE DATABASE mikrotik_billing;"
```

## Step 5: Clone or Navigate to Project

```bash
cd ~/Documents/personal_pro/networking_mikrotik
```

## Step 6: Setup Backend

```bash
cd backend

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## Step 7: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit configuration
nano .env
```

Update these values in `.env`:

### For New PostgreSQL Installation:
```env
DATABASE_URL=postgresql://localhost:5432/mikrotik_billing
```

### For Existing PostgreSQL with Credentials:
```env
DATABASE_URL=postgresql://yourusername:yourpassword@localhost:5432/mikrotik_billing
```

### MikroTik Configuration:
```env
MIKROTIK_HOST=192.168.88.1
MIKROTIK_USERNAME=api_admin
MIKROTIK_PASSWORD=YourStrongPassword123
MIKROTIK_PORT=8728
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then Enter

## Step 8: Test Database Connection

```bash
# Test connection
psql postgresql://localhost:5432/mikrotik_billing -c "SELECT 'Connected!' as status;"

# Should return: Connected!
```

## Step 9: Start Backend

```bash
# Make sure venv is activated
source venv/bin/activate

# Start backend
python main.py
```

Expected output:
```
INFO:     Started server process
Database initialized and MikroTik connected
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

## Step 10: Setup Frontend (New Terminal)

Open a new terminal window:

```bash
cd ~/Documents/personal_pro/networking_mikrotik/frontend

# Install dependencies
npm install

# Start development server
npm start
```

Browser should automatically open to `http://localhost:3000`

## Step 11: Verify Everything Works

### Check Backend API:
```bash
curl http://localhost:8000/
```

Should return:
```json
{"status":"online","message":"MikroTik Billing System API"}
```

### Check Database Tables:
```bash
psql postgresql://localhost:5432/mikrotik_billing -c "\dt"
```

Should show:
- users
- payments
- logs

### Check Dashboard:
Open browser to `http://localhost:3000`

## Common macOS-Specific Issues

### Issue: "Command not found: psql"

**Solution:**
```bash
# Add PostgreSQL to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)

# Or use different port in .env
API_PORT=8001
```

### Issue: "Port 3000 already in use"

**Solution:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or change port
PORT=3001 npm start
```

### Issue: Python version conflicts

**Solution:**
```bash
# Use specific Python version
python3.11 -m venv venv

# Or use pyenv for version management
brew install pyenv
pyenv install 3.11.7
pyenv local 3.11.7
```

### Issue: "Permission denied" when installing packages

**Solution:**
```bash
# Don't use sudo with pip in venv
# Make sure venv is activated
source venv/bin/activate

# Then install
pip install -r requirements.txt
```

### Issue: Can't connect to router

**Solution:**
```bash
# Check network connection
ping 192.168.88.1

# Test API port
telnet 192.168.88.1 8728

# Check if on same network
ifconfig | grep "inet "
```

## Useful macOS Commands

```bash
# Check running services
brew services list

# Restart PostgreSQL
brew services restart postgresql@14

# View PostgreSQL logs
tail -f /opt/homebrew/var/log/postgresql@14.log

# Check Python version in venv
source venv/bin/activate
python --version

# Check installed packages
pip list

# Find processes on ports
lsof -i :8000
lsof -i :3000
lsof -i :5432
```

## Startup Scripts for macOS

Create convenience scripts:

### Start Backend (`start_backend.sh`):
```bash
#!/bin/bash
cd ~/Documents/personal_pro/networking_mikrotik/backend
source venv/bin/activate
python main.py
```

### Start Frontend (`start_frontend.sh`):
```bash
#!/bin/bash
cd ~/Documents/personal_pro/networking_mikrotik/frontend
npm start
```

Make them executable:
```bash
chmod +x start_backend.sh start_frontend.sh
```

## Auto-Start on Login (Optional)

### Create Launch Agents:

**Backend Launch Agent:**
```bash
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.mikrotik.billing.backend.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mikrotik.billing.backend</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ~/Documents/personal_pro/networking_mikrotik/backend && source venv/bin/activate && python main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load the agent
launchctl load ~/Library/LaunchAgents/com.mikrotik.billing.backend.plist
```

## System Requirements

- **macOS:** 11.0+ (Big Sur or later)
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 500MB for software + space for database
- **Network:** Ethernet or WiFi connection to MikroTik router

## Performance Tips for macOS

1. **Use Ethernet connection** to router for best API performance
2. **Keep PostgreSQL data on SSD** (default location is fine)
3. **Don't use VPN** when connecting to router
4. **Allow firewall exceptions** for ports 8000, 3000, 8728
5. **Keep macOS updated** for best Python compatibility

## Next Steps

1. Configure your MikroTik router (see `MIKROTIK_SETUP.md`)
2. Create your first user in the dashboard
3. Test hotspot login
4. Set up automated backups

## Troubleshooting

For more detailed troubleshooting, see `TROUBLESHOOTING.md`

## Uninstall

To remove everything:

```bash
# Stop services
brew services stop postgresql@14

# Remove project
rm -rf ~/Documents/personal_pro/networking_mikrotik

# Remove PostgreSQL (optional)
brew uninstall postgresql@14
rm -rf /opt/homebrew/var/postgresql@14

# Remove launch agents (if created)
launchctl unload ~/Library/LaunchAgents/com.mikrotik.billing.backend.plist
rm ~/Library/LaunchAgents/com.mikrotik.billing.backend.plist
```

## Support

For issues specific to macOS setup, check:
- `docs/TROUBLESHOOTING.md` - General troubleshooting
- `QUICK_START.md` - Quick setup guide
- Homebrew documentation: https://brew.sh/
