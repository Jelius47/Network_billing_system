# Deployment Guide - MikroTik Hotspot Billing System

This guide covers deploying your backend server and frontend dashboard to manage your MikroTik Hex S hotspot.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Database Setup (Neon)](#database-setup-neon)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Configuration](#configuration)
6. [Running the System](#running-the-system)
7. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Services

1. **Server/VPS**: Ubuntu 20.04+ or similar Linux distribution (or any hosting platform)
2. **Neon Database**: PostgreSQL database (already using)
3. **Python**: Version 3.8 or higher
4. **Node.js**: Version 14 or higher (for frontend)
5. **Domain** (optional but recommended): For HTTPS and proper URLs

### Required API Keys

1. **ZenoPay Account**: Sign up at [zenopay.co.tz](https://zenopay.co.tz)
   - API Key
   - PIN

2. **WhatsApp Business API**: Set up at [developers.facebook.com](https://developers.facebook.com/apps/)
   - Access Token
   - Phone Number ID
   - Business Account ID

3. **Sentry** (optional): For error tracking at [sentry.io](https://sentry.io)

4. **Neon Database**: Your PostgreSQL connection string from [neon.tech](https://neon.tech)

---

## Database Setup (Neon)

### 1. Get Your Neon Connection String

1. Login to your Neon dashboard at [console.neon.tech](https://console.neon.tech)
2. Select your project (or create a new one)
3. Go to the "Connection Details" section
4. Copy the connection string that looks like:
   ```
   postgresql://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

### 2. Update Connection String for SQLAlchemy

Your `.env` file needs to use the `psycopg2` driver. Convert your Neon connection string:

```ini
# Original Neon format:
postgresql://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# Convert to (add +psycopg2 after postgresql):
postgresql+psycopg2://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### 3. No Local PostgreSQL Installation Needed

Since you're using Neon, you don't need to install PostgreSQL locally. Your database is hosted in the cloud and accessible from anywhere.

---

## Backend Deployment

### 1. Setup Project Directory

```bash
cd /var/www  # or your preferred directory
# If cloning from git:
# git clone <your-repo-url> mikrotik-billing
cd mikrotik-billing/backend
```

### 2. Install Python Dependencies

```bash
# Install Python 3 and pip if not already installed
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your actual values
nano .env
```

**Fill in the following values:**

```ini
# Database Configuration - NEON DATABASE
DATABASE_URL=postgresql+psycopg2://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# MikroTik Router Configuration
MIKROTIK_HOST=10.10.10.1  # Your MikroTik Hex S IP address
MIKROTIK_USERNAME=api_admin
MIKROTIK_PASSWORD=YourStrongPassword123  # From router setup
MIKROTIK_PORT=8728

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# ZenoPay Configuration
ZENOPAY_API_KEY=zp_live_xxxxxxxxxxxxxxxxxx
ZENOPAY_PIN=0000  # Your ZenoPay PIN
ZENOPAY_WEBHOOK_URL=http://YOUR_SERVER_IP:8000/api/payments/webhook

# Payment Pricing (Tanzanian Shillings)
DAILY_1_DEVICE_PRICE=1000
DAILY_2_DEVICES_PRICE=1500
MONTHLY_1_DEVICE_PRICE=10000
MONTHLY_2_DEVICES_PRICE=15000

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=EAXXXXXXXXXXXXXXXXXXXXXXXX
WHATSAPP_PHONE_NUMBER_ID=1234567890123456
WHATSAPP_BUSINESS_ID=1234567890123456
WHATSAPP_API_VERSION=v21.0

# Optional: Sentry for error tracking
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

### 4. Run Database Migrations

```bash
# Make sure you're in the backend directory with venv activated
cd /var/www/mikrotik-billing/backend
source venv/bin/activate

# Run migrations to create tables in Neon database
alembic upgrade head
```

### 5. Verify Database Connection

```bash
# Test connection to Neon
python3 -c "
from database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✓ Neon database connection successful!')
"
```

---

## Frontend Deployment

### 1. Install Node.js

```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Build Frontend

```bash
cd /var/www/mikrotik-billing/frontend

# Install dependencies
npm install

# Update API URL in src/App.js
nano src/App.js
# Find: axios.defaults.baseURL
# Change to: axios.defaults.baseURL = 'http://YOUR_SERVER_IP:8000/api';
# Or for production: 'https://YOUR_DOMAIN.com/api'

# Build for production
npm run build
```

### 3. Serve Frontend with Nginx

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/mikrotik-dashboard
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # Frontend
    location / {
        root /var/www/mikrotik-billing/frontend/build;
        try_files $uri /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/mikrotik-dashboard /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## Running the System

### 1. Start Backend (Development)

```bash
cd /var/www/mikrotik-billing/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Start Backend with Auto-reload (Development)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Production Deployment

### 1. Create Systemd Service for Backend

```bash
sudo nano /etc/systemd/system/mikrotik-backend.service
```

Add the following:

```ini
[Unit]
Description=MikroTik Hotspot Billing Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/mikrotik-billing/backend
Environment="PATH=/var/www/mikrotik-billing/backend/venv/bin"
ExecStart=/var/www/mikrotik-billing/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Set proper permissions
sudo chown -R www-data:www-data /var/www/mikrotik-billing

# Reload systemd
sudo systemctl daemon-reload

# Start and enable service
sudo systemctl start mikrotik-backend
sudo systemctl enable mikrotik-backend

# Check status
sudo systemctl status mikrotik-backend
```

### 2. Configure Firewall

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

### 3. Setup HTTPS with Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate (replace YOUR_DOMAIN.com with your actual domain)
sudo certbot --nginx -d YOUR_DOMAIN.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

### 4. Update Hotspot Login Page

After deployment, update the hotspot login page with your server URL:

```bash
nano /var/www/mikrotik-billing/docs/hotspot/login.html
```

Find line 546 and update:
```javascript
const API_BASE_URL = 'https://YOUR_DOMAIN.com/api';  // or http://YOUR_IP:8000/api
```

Then upload the updated `login.html` to your MikroTik Hex S (see MIKROTIK_HEX_S_SETUP_GUIDE.md).

### 5. Configure ZenoPay Webhook

Login to your ZenoPay dashboard and set the webhook URL to:
```
https://YOUR_DOMAIN.com/api/payments/webhook
```

or for non-HTTPS:

```
http://YOUR_SERVER_IP:8000/api/payments/webhook
```

---

## Monitoring and Maintenance

### 1. View Backend Logs

```bash
# Real-time logs
sudo journalctl -u mikrotik-backend -f

# Last 100 lines
sudo journalctl -u mikrotik-backend -n 100

# Filter by date
sudo journalctl -u mikrotik-backend --since today
```

### 2. Restart Services

```bash
# Restart backend
sudo systemctl restart mikrotik-backend

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status mikrotik-backend
sudo systemctl status nginx
```

### 3. Database Backup (Neon)

Neon provides automatic backups, but you can also export manually:

**Option 1: Using Neon Console**
1. Go to your Neon dashboard
2. Select your project
3. Click "Backups" tab
4. Create a manual backup

**Option 2: Using pg_dump**
```bash
# Install PostgreSQL client tools
sudo apt install postgresql-client -y

# Create backup script
nano ~/backup-neon-db.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/mikrotik"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Export your Neon connection string
export NEON_URL="postgresql://username:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require"

pg_dump "$NEON_URL" | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

```bash
# Make executable
chmod +x ~/backup-neon-db.sh

# Test it
~/backup-neon-db.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/YOUR_USER/backup-neon-db.sh
```

### 4. Monitor System Resources

```bash
# Install htop
sudo apt install htop -y

# Monitor
htop
```

### 5. Check Auto-Expiry Scheduler

The backend automatically runs a scheduler every 10 minutes to disable expired users. Check if it's working:

```bash
# Check logs for scheduler activity
sudo journalctl -u mikrotik-backend | grep "Checking for expired users"

# Or watch in real-time
sudo journalctl -u mikrotik-backend -f | grep "expired"
```

---

## Testing the Complete System

### 1. Test Backend API

```bash
# Test health check
curl http://YOUR_SERVER_IP:8000/api/stats
```

Should return JSON with statistics like:
```json
{
  "total_users": 0,
  "active_users": 0,
  "expired_users": 0,
  "total_payments": 0
}
```

### 2. Test Neon Database Connection

```bash
cd /var/www/mikrotik-billing/backend
source venv/bin/activate

python3 << EOF
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
print(f"✓ Connected to Neon! Total users: {result}")
db.close()
EOF
```

### 3. Test Frontend

Open browser and go to:
```
http://YOUR_SERVER_IP  # or https://YOUR_DOMAIN.com
```

You should see the dashboard with statistics.

### 4. Test Payment Flow (Complete End-to-End)

1. **From Customer Side:**
   - Connect to your MikroTik hotspot WiFi
   - Open browser (should redirect to login page)
   - Click "Buy Access" tab
   - Fill in phone number (Tanzanian format: +255...)
   - Enter name
   - Select a plan (Daily 1000 TSH, Monthly 10000 TSH, or Monthly 15000 TSH for 2 devices)
   - Click "Proceed to Payment"
   - Complete payment via ZenoPay mobile money

2. **What Should Happen:**
   - Payment link sent via WhatsApp
   - After payment completion, credentials sent via WhatsApp
   - User created in Neon database
   - User created in MikroTik router
   - User can login with credentials

3. **Verify in Dashboard:**
   - Login to dashboard: `http://YOUR_SERVER_IP`
   - Check "Users" tab - new user should appear
   - Check "Active Users" tab after customer logs in
   - Check "Payments" tab - payment should be recorded

### 5. Test MikroTik API Connection from Server

```bash
cd /var/www/mikrotik-billing/backend
source venv/bin/activate

python3 << EOF
from mikrotik_api import MikroTikAPI

api = MikroTikAPI()
connection = api.connect()

if connection:
    resource = connection.get_resource('/ip/hotspot/user')
    users = resource.get()
    print(f"✓ Connected to MikroTik! Total hotspot users: {len(users)}")
else:
    print("✗ Failed to connect to MikroTik")
EOF
```

---

## Troubleshooting

### Backend won't start:

1. **Check logs:**
```bash
sudo journalctl -u mikrotik-backend -n 50 --no-pager
```

2. **Check if port 8000 is in use:**
```bash
sudo netstat -tulpn | grep 8000
```

3. **Test .env configuration:**
```bash
cat /var/www/mikrotik-billing/backend/.env | grep -v PASSWORD
```

4. **Test manually:**
```bash
cd /var/www/mikrotik-billing/backend
source venv/bin/activate
python3 main.py
```

### Neon database connection errors:

1. **Check connection string format:**
   - Must use `postgresql+psycopg2://` (not just `postgresql://`)
   - Must include `?sslmode=require` at the end
   - Must have correct username, password, and host

2. **Test connection directly:**
```bash
cd /var/www/mikrotik-billing/backend
source venv/bin/activate
python3 -c "from database import engine; engine.connect(); print('✓ Connected!')"
```

3. **Check Neon dashboard:**
   - Ensure project is active (not suspended)
   - Check if there are connection limits reached
   - Verify IP allowlist settings (if configured)

### MikroTik API connection fails:

1. **Test from server:**
```bash
cd /var/www/mikrotik-billing/backend
source venv/bin/activate
python3 -c "
from mikrotik_api import MikroTikAPI
api = MikroTikAPI()
api.connect()
print('✓ Connection successful!')
"
```

2. **Check MikroTik API service:**
```
# From MikroTik terminal via WinBox or SSH:
/ip service print
```

Ensure API service is enabled and accessible.

3. **Check firewall rules on MikroTik:**
```
/ip firewall filter print
```

Ensure your server IP is allowed to access port 8728.

4. **Test network connectivity:**
```bash
ping 10.10.10.1  # Your MikroTik IP
telnet 10.10.10.1 8728
```

### Payment webhook not receiving calls:

1. **Check ZenoPay dashboard:**
   - Verify webhook URL is correct
   - Check webhook logs in ZenoPay dashboard

2. **Ensure webhook URL is publicly accessible:**
```bash
# Test from external service like webhook.site or from another machine
curl -X POST http://YOUR_SERVER_IP:8000/api/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{"status": "COMPLETED", "tx_ref": "test123"}'
```

3. **Check backend logs for webhook calls:**
```bash
sudo journalctl -u mikrotik-backend -f | grep webhook
```

4. **Firewall issues:**
   - Ensure port 8000 (or 80/443 if behind Nginx) is open
   - Check if firewall is blocking ZenoPay's IP

### WhatsApp messages not sending:

1. **Verify credentials in `.env`:**
   - WHATSAPP_ACCESS_TOKEN
   - WHATSAPP_PHONE_NUMBER_ID
   - WHATSAPP_BUSINESS_ID

2. **Check phone number format:**
   - Must be in E.164 format: +255XXXXXXXXX (Tanzania)
   - No spaces or dashes

3. **Test WhatsApp API:**
```bash
cd /var/www/mikrotik-billing/backend
source venv/bin/activate

python3 << EOF
from whatsapp_service import WhatsAppService
service = WhatsAppService()
result = service.send_credentials("+255712345678", "testuser", "testpass")
print(result)
EOF
```

4. **Check Facebook Developer Console:**
   - Verify phone number is verified
   - Check if WhatsApp Business account is active
   - Review API usage limits

### Auto-expiry not working:

1. **Check if scheduler is running:**
```bash
sudo journalctl -u mikrotik-backend -f | grep "Checking for expired users"
```

2. **Manually trigger expiry check:**
```bash
cd /var/www/mikrotik-billing/backend
source venv/bin/activate

python3 << EOF
from main import check_expired_users
import asyncio
asyncio.run(check_expired_users())
EOF
```

---

## Security Checklist

- [ ] Use strong passwords for all services
- [ ] Secure your Neon database credentials in `.env`
- [ ] Enable UFW firewall on server
- [ ] Setup HTTPS with SSL certificate (Let's Encrypt)
- [ ] Configure ZenoPay webhook with HTTPS
- [ ] Restrict MikroTik API access to server IP only
- [ ] Keep system updated: `sudo apt update && sudo apt upgrade`
- [ ] Setup automated Neon database backups
- [ ] Monitor logs regularly for suspicious activity
- [ ] Use environment variables (never hardcode secrets)
- [ ] Enable fail2ban for SSH protection (optional)
- [ ] Configure proper CORS settings for production
- [ ] Secure WhatsApp API credentials

---

## Performance Optimization

### For Backend:

1. **Increase Uvicorn workers:**
```ini
# In /etc/systemd/system/mikrotik-backend.service
ExecStart=... --workers 4  # Adjust based on CPU cores
```

2. **Enable connection pooling for Neon:**

Already configured in `database.py`, but you can adjust:
```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # Adjust as needed
    max_overflow=10
)
```

3. **Monitor Neon connection limits:**
   - Check your Neon plan's connection limits
   - Upgrade plan if needed for more concurrent connections

### For Frontend:

1. **Enable Nginx caching:**
```nginx
# In /etc/nginx/sites-available/mikrotik-dashboard
location /static {
    root /var/www/mikrotik-billing/frontend/build;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

2. **Enable gzip compression:**
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;
```

---

## Updating the System

```bash
cd /var/www/mikrotik-billing

# Pull latest changes (if using git)
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Run any new migrations
alembic upgrade head

# Restart backend
sudo systemctl restart mikrotik-backend

# Update frontend
cd ../frontend
npm install
npm run build

# Restart Nginx (to clear cache)
sudo systemctl restart nginx
```

---

## Quick Command Reference

```bash
# Service Management
sudo systemctl start mikrotik-backend
sudo systemctl stop mikrotik-backend
sudo systemctl restart mikrotik-backend
sudo systemctl status mikrotik-backend

# Logs
sudo journalctl -u mikrotik-backend -f
sudo journalctl -u mikrotik-backend -n 100
sudo journalctl -u mikrotik-backend --since "1 hour ago"

# Database
# View Neon connection in .env
grep DATABASE_URL /var/www/mikrotik-billing/backend/.env

# Test API
curl http://localhost:8000/api/stats

# Monitor Resources
htop
df -h  # Disk space
free -h  # Memory

# Nginx
sudo nginx -t  # Test config
sudo systemctl restart nginx
```

---

## Next Steps

After completing this deployment:

1. ✓ Configure your MikroTik Hex S (see `MIKROTIK_HEX_S_SETUP_GUIDE.md`)
2. ✓ Test the complete payment flow
3. ✓ Monitor the dashboard for real-time analytics
4. ✓ Set up automated Neon backups
5. ✓ Configure HTTPS for production
6. ✓ Test auto-expiry functionality
7. ✓ Train staff on using the dashboard

Your MikroTik Hotspot Billing System with Neon database is now deployed and ready to use!
