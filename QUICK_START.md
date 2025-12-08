# Quick Start Guide

Get your MikroTik Billing System up and running in minutes.

## Prerequisites Checklist

- [ ] MikroTik RB941 router (connected and accessible)
- [ ] Computer/Server with Ubuntu/macOS/Windows
- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed
- [ ] PostgreSQL 12+ installed
- [ ] Network access to router

## 5-Minute Setup

### Step 1: Configure Router (5 min)

```bash
# Connect to router via Winbox or web interface
# Run these commands in terminal:

# Quick hotspot setup
/ip hotspot setup

# Create user profiles
/ip hotspot user profile add name=daily_1000 rate-limit=1M/1M session-timeout=1d
/ip hotspot user profile add name=monthly_1000 rate-limit=1M/1M session-timeout=30d

# Enable API
/ip service set api disabled=no

# Create API user
/user add name=api_admin password=YourStrongPassword123 group=full
```

### Step 2: Setup Database (2 min)

#### Option A: New PostgreSQL Installation (Ubuntu/Debian)

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create database
sudo -u postgres psql <<EOF
CREATE DATABASE mikrotik_billing;
CREATE USER admin WITH PASSWORD 'temp123';
GRANT ALL PRIVILEGES ON DATABASE mikrotik_billing TO admin;
\q
EOF
```

#### Option B: New PostgreSQL Installation (macOS)

```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Create database
psql postgres -c "CREATE DATABASE mikrotik_billing;"
```

#### Option C: Existing PostgreSQL Installation

If you already have PostgreSQL running:

```bash
# Find your PostgreSQL connection URL
# Common formats:
# - postgresql://localhost:5432/postgres
# - postgresql://username:password@localhost:5432/postgres

# Create the mikrotik_billing database
psql postgresql://localhost:5432/postgres -c "CREATE DATABASE mikrotik_billing;"

# Or if you need username/password
psql postgresql://yourusername:yourpassword@localhost:5432/postgres -c "CREATE DATABASE mikrotik_billing;"

# Test connection
psql postgresql://localhost:5432/mikrotik_billing -c "SELECT 'Connected!' as status;"
```

Your `.env` file should use:
```env
DATABASE_URL=postgresql://localhost:5432/mikrotik_billing
# Or with credentials:
DATABASE_URL=postgresql://yourusername:yourpassword@localhost:5432/mikrotik_billing
```

### Step 3: Setup Backend (3 min)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your router IP and credentials
```

Edit `.env`:
```env
DATABASE_URL=postgresql://admin:temp123@localhost/mikrotik_billing
MIKROTIK_HOST=192.168.88.1
MIKROTIK_USERNAME=api_admin
MIKROTIK_PASSWORD=YourStrongPassword123
MIKROTIK_PORT=8728
```

```bash
# Start backend
python main.py
```

Keep this terminal open. Backend runs on `http://localhost:8000`

### Step 4: Setup Frontend (2 min)

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Start frontend
npm start
```

Frontend opens automatically at `http://localhost:3000`

## First User Creation

1. Open dashboard: `http://localhost:3000`
2. Click "Add User"
3. Fill in:
   - Username: `test_user`
   - Password: `test123`
   - Plan: `Daily - 1000`
4. Click "Create User"
5. User is created in both database and router!

## Test the System

### Test User Login

1. Connect device to router's WiFi/LAN
2. Open browser
3. Hotspot login page appears
4. Login with: `test_user` / `test123`
5. Should get internet access

### Test Dashboard Features

1. **Home Page:** View statistics
2. **Users Page:** See all users and their status
3. **Add User:** Create new users
4. **Payments:** Record payments and extend users

## Verify Everything Works

```bash
# Check backend API
curl http://localhost:8000/stats

# Check database
psql -U admin -d mikrotik_billing -c "SELECT * FROM users;"

# Check router (via SSH)
ssh admin@192.168.88.1
/ip hotspot user print
```

## Common First-Time Issues

### "Connection refused" when starting backend
- PostgreSQL not running: `sudo systemctl start postgresql`
- Wrong database credentials in `.env`

### "Cannot connect to MikroTik"
- Check router IP: `ping 192.168.88.1`
- Verify API enabled: `/ip service print`
- Check credentials in `.env`

### Frontend shows "Network Error"
- Backend not running
- Check `frontend/src/config.js` has correct API URL

### Hotspot not redirecting
- Hotspot not enabled: `/ip hotspot print`
- DNS issues on client device
- Clear browser cache

## What's Next?

1. **Read full docs:** `docs/MIKROTIK_SETUP.md`
2. **Secure your system:** Change default passwords
3. **Backup config:** Router and database
4. **Monitor logs:** Watch for errors
5. **Test auto-disable:** Wait for user to expire

## Production Deployment

For production use:

1. Use strong passwords everywhere
2. Enable HTTPS
3. Set up proper firewall rules
4. Configure automated backups
5. Set up monitoring/alerting
6. Use systemd services for auto-start
7. Consider using Docker

See `docs/DEPLOYMENT.md` for detailed production setup.

## Support

- **Documentation:** `docs/` directory
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`
- **Emergencies:** `docs/EMERGENCY.md`
- **MikroTik Setup:** `docs/MIKROTIK_SETUP.md`

## Quick Commands Reference

```bash
# Backend
cd backend && source venv/bin/activate && python main.py

# Frontend
cd frontend && npm start

# Database
psql -U admin -d mikrotik_billing

# View users
curl http://localhost:8000/users

# View stats
curl http://localhost:8000/stats

# Router SSH
ssh admin@192.168.88.1
```

## Architecture Overview

```
┌─────────────────┐
│   Customer      │
│   Devices       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MikroTik      │◄──────┐
│   Hotspot       │       │
└─────────────────┘       │
                          │ API
┌─────────────────┐       │
│   Dashboard     │───────┤
│   (React)       │       │
└─────────────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│   Backend       │───────┘
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Database      │
│   (PostgreSQL)  │
└─────────────────┘
```

## Daily Operations Workflow

1. **Customer arrives**
2. **Collect payment** → Record in "Payments" page
3. **Create/Extend user** → System auto-updates MikroTik
4. **Give credentials** → Customer connects and logs in
5. **Monitor expiry** → System auto-disables when expired

That's it! Your billing system is now operational.
