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

### 3. Frontend Setup

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
DATABASE_URL=postgresql://admin:temp123@localhost/mikrotik_billing
MIKROTIK_HOST=192.168.88.1
MIKROTIK_USERNAME=api_admin
MIKROTIK_PASSWORD=your_password
MIKROTIK_PORT=8728
API_HOST=0.0.0.0
API_PORT=8000
```

### MikroTik Router Configuration

See `docs/MIKROTIK_SETUP.md` for detailed router configuration instructions.

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
