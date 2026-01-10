# MikroTik Billing System

A complete billing system for MikroTik RB941 routers with API integration, user management, and automatic subscription handling.

## Features

- User Management (Create, Enable/Disable, Extend)
- Automatic expiry checking and user disabling
- Payment tracking
- Real-time dashboard with statistics
- MikroTik API integration
- Daily and Monthly subscription plans
- Auto-refresh user list

## Architecture

### System Overview

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   React     │◄─────►│   FastAPI   │◄─────►│  MikroTik   │
│  Dashboard  │       │   Backend   │       │   Router    │
└─────────────┘       └─────────────┘       └─────────────┘
                              │
                              ▼
                      ┌─────────────┐
                      │ PostgreSQL  │
                      │  Database   │
                      └─────────────┘
```

### Login Page Architecture (Hotspot Portal)

**Important:** The hotspot login page (`login.html`) is served from MikroTik but communicates with the backend API via AJAX.

```
┌──────────────────┐          ┌──────────────────┐          ┌─────────────────┐
│   MikroTik       │          │   Backend API    │          │   PostgreSQL    │
│   Router         │          │  (FastAPI)       │          │   Database      │
│  (Hotspot)       │          │  Your Server IP  │          │                 │
└────────┬─────────┘          └────────┬─────────┘          └────────┬────────┘
         │                             │                             │
         │ 1. Serves login.html        │ 3. API Calls               │
         │    (Static HTML)            │    (CORS enabled)          │
         │                             │                             │
         │    2. User Browser ────────►│ 4. Create User ───────────►│
         │       (AJAX/Fetch)          │    Send WhatsApp           │
         │                             │                             │
         └────────5. Authenticate──────┘                             │
              (MikroTik direct)                                      │
```

**How It Works:**
1. User connects to WiFi → MikroTik serves `login.html` from hotspot
2. User buys access → JavaScript makes API call to backend server
3. Backend creates user + sends credentials via WhatsApp
4. User logs in → MikroTik authenticates (no backend needed)

**Configuration Required:**
- `login.html` line 546: Set `API_BASE_URL` to your backend server IP/domain
- Backend CORS must allow all origins (already configured)
- MikroTik hotspot must be configured to serve the login page

## Quick Start

### 🐳 Docker Deployment (Recommended)

**Easiest way to deploy anywhere:**

```bash
# Clone repository
git clone <your-repo> mikrotik-billing
cd mikrotik-billing

# Configure
cp .env.docker .env
nano .env  # Update with your MikroTik details

# Deploy
docker-compose up -d

# Access dashboard
open http://localhost
```

**Complete Docker guide:** See `DOCKER_DEPLOY.md`

---

### 💻 Manual Installation

**Platform-Specific Guides:**
- **macOS Users:** See `docs/MACOS_SETUP.md` for detailed macOS setup
- **Ubuntu/Debian Users:** Follow instructions below
- **Existing PostgreSQL:** See `QUICK_START.md` Option C

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- MikroTik RB941 Router
- Network access to the router

### 1. Database Setup

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE mikrotik_billing;"
sudo -u postgres psql -c "CREATE USER admin WITH PASSWORD 'temp123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mikrotik_billing TO admin;"
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MikroTik details

# Run the backend
python main.py
```

Backend will be available at `http://localhost:8000`

### 3. Database Migrations (Alembic)

**Important:** Use Alembic for managing database schema changes. Never hardcode credentials in `alembic.ini`.

```bash
cd backend
source venv/bin/activate  # Activate virtual environment

# Install Alembic (if not already installed)
pip install alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations to database
alembic upgrade head

# Check current migration status
alembic current

# View migration history
alembic history
```

**Configuration Notes:**
- Database URL is loaded from `.env` file automatically
- Never hardcode credentials in `alembic.ini`
- All migrations are stored in `backend/alembic/versions/`
- The `alembic/env.py` is configured to use your database models from `database.py`

**Common Alembic Commands:**
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Dashboard will be available at `http://localhost:3000`

## Configuration

### Backend (.env file)

```env
# Database Configuration (use postgresql+psycopg2:// for proper driver support)
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/mikrotik_billing

# MikroTik Router Configuration
MIKROTIK_HOST=192.168.88.1
MIKROTIK_USERNAME=api_admin
MIKROTIK_PASSWORD=your_password
MIKROTIK_PORT=8728

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# ZenoPay Configuration (for payment integration)
ZENOPAY_API_KEY=your_zenopay_api_key_here
ZENOPAY_PIN=0000
ZENOPAY_WEBHOOK_URL=http://your-domain.com/api/payments/webhook

# Payment Plan Pricing (in TZS)
DAILY_1_DEVICE_PRICE=1000
DAILY_2_DEVICES_PRICE=1500
MONTHLY_1_DEVICE_PRICE=10000
MONTHLY_2_DEVICES_PRICE=15000

# WhatsApp Business API Configuration (for sending credentials)
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_BUSINESS_ID=your_business_account_id_here
WHATSAPP_API_VERSION=v21.0
```

**Important:** Never commit your `.env` file to version control. Keep your credentials secure.

### MikroTik Router Configuration

See `docs/MIKROTIK_SETUP.md` for detailed router configuration instructions.

### MikroTik Backup & Restore

**IMPORTANT:** Always backup your working MikroTik configuration to avoid losing settings!

#### Creating Backups

Run these commands on your MikroTik router:

```bash
# Create binary backup (includes passwords)
/system backup save name=hotspot-working-config

# Create export script (human-readable)
/export file=hotspot-working-export

# Verify backups were created
/file print
```

You should see two files:
- `hotspot-working-config.backup` - Complete system backup
- `hotspot-working-export.rsc` - Text-based configuration script

#### Downloading Backups

**Method 1: Via WinBox**
1. Open WinBox → Connect to router
2. Click **Files** in the left menu
3. Find `hotspot-working-config.backup` and `hotspot-working-export.rsc`
4. **Drag and drop** files to your computer

**Method 2: Via WebFig**
1. Go to `http://192.168.88.1/webfig`
2. Click **Files**
3. Download both backup files

**Method 3: Via SCP (if SSH enabled)**
```bash
scp admin@192.168.88.1:hotspot-working-config.backup ~/Desktop/
scp admin@192.168.88.1:hotspot-working-export.rsc ~/Desktop/
```

#### Restoring from Backup

**CRITICAL:** Keep these files safe! Store them in:
- Your computer's backup folder
- Cloud storage (Google Drive, Dropbox, etc.)
- USB drive

**To restore your configuration:**

1. **Upload backup file to MikroTik:**
   - Via WinBox: Files → Drag `.backup` file into MikroTik
   - Via WebFig: Files → Upload → Select `.backup` file

2. **Restore the backup:**
   ```bash
   /system backup load name=hotspot-working-config
   ```

3. **Router will reboot automatically**

**Alternative: Restore from Export Script:**
```bash
/import file=hotspot-working-export.rsc
```

#### What's Included in Backup

Your backup includes:
✅ All firewall rules (NAT, filter)
✅ Hotspot configuration
✅ IP addresses and pools
✅ Walled garden settings (Mac/Apple captive portal fix)
✅ User profiles and bandwidth limits
✅ Bridge and interface configuration
✅ All custom settings

#### Backup Best Practices

1. **Create backups after major changes:**
   - After initial hotspot setup
   - After firewall rule modifications
   - Before firmware updates
   - Monthly routine backups

2. **Name backups descriptively:**
   ```bash
   /system backup save name=hotspot-2026-01-10-working
   /export file=hotspot-2026-01-10-export
   ```

3. **Test your backups:**
   - Keep multiple versions
   - Test restore on a separate device if possible

4. **Document your changes:**
   - Keep notes of what you changed
   - Store notes with backup files

### Hotspot Login Page Configuration

The login page (`docs/hotspot/login.html`) needs to be configured with your backend API URL:

1. **Edit login.html line 546:**
   ```javascript
   const API_BASE_URL = 'http://YOUR_SERVER_IP:8000/api';
   ```
   Replace `YOUR_SERVER_IP` with your backend server's public IP or domain name.

2. **Upload to MikroTik:**
   - Access MikroTik WebFig/Winbox
   - Go to Files → Upload `login.html`
   - Configure Hotspot to use this custom login page

3. **CORS is pre-configured:**
   - The backend already allows cross-origin requests
   - No additional configuration needed

**Example Configuration:**
```javascript
// For local development/testing
const API_BASE_URL = 'http://localhost:8000/api';

// For production (replace with your actual server)
const API_BASE_URL = 'http://YOUR_SERVER_IP:8000/api';
// Or use a domain name:
// const API_BASE_URL = 'https://api.yourdomain.com/api';
```

## Project Structure

```
networking_mikrotik/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database models
│   ├── mikrotik_api.py      # MikroTik API integration
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Configuration
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── App.js           # Main app component
│   │   └── config.js        # API configuration
│   └── package.json         # Node dependencies
└── docs/
    ├── MIKROTIK_SETUP.md    # Router setup guide
    ├── TROUBLESHOOTING.md   # Common issues
    └── EMERGENCY.md         # Recovery procedures
```

## API Endpoints

### Users
- `POST /users` - Create new user
- `GET /users` - List all users
- `GET /users/{id}` - Get specific user
- `POST /users/{id}/extend` - Extend subscription
- `POST /users/{id}/toggle` - Enable/disable user

### Payments
- `POST /payments` - Record payment
- `GET /payments` - List all payments

### Statistics
- `GET /stats` - Get system statistics
- `GET /expired` - List expired users
- `GET /active-connections` - Get active connections from MikroTik

## Development

### Running in Development Mode

1. Backend: `cd backend && python main.py`
2. Frontend: `cd frontend && npm start`

### Production Deployment

See `docs/DEPLOYMENT.md` for production deployment instructions.

## Support

For issues, questions, or contributions, please refer to the documentation in the `docs/` directory.

## License

MIT License - feel free to use and modify for your needs.
