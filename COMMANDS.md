# Essential Commands Reference

Quick reference for all essential commands to run and maintain the MikroTik Billing System.

---

## 📦 Initial Setup

### 1. Install Dependencies

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
nano .env

# Set these values:
# DATABASE_URL=postgresql://localhost:5432/mikrotik_billing
# MIKROTIK_HOST=192.168.1.7  # Your MikroTik IP
# MIKROTIK_USERNAME=api_admin
# MIKROTIK_PASSWORD=YourPassword
# MIKROTIK_PORT=8728
```

### 3. Initialize Database

```bash
cd backend
source venv/bin/activate
python -c "from database import init_db; init_db()"
```

---

## 🚀 Running the System

### Start Backend

```bash
cd backend
source venv/bin/activate
python main.py

# Backend runs on: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Start Frontend

```bash
cd frontend
npm start

# Frontend runs on: http://localhost:3000
```

### Stop Services

```bash
# Stop backend: Ctrl+C in terminal
# Or kill process:
lsof -ti:8000 | xargs kill -9

# Stop frontend: Ctrl+C in terminal
# Or kill process:
lsof -ti:3000 | xargs kill -9
```

---

## 🐳 Docker Commands

### Start All Services

```bash
docker-compose up -d
```

### Stop All Services

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Rebuild After Changes

```bash
docker-compose up -d --build
```

### Reset Everything

```bash
docker-compose down -v
docker-compose up -d --build
```

---

## 🗄️ Database Commands

### Connect to Database

```bash
# Local PostgreSQL
psql postgresql://localhost:5432/mikrotik_billing

# Docker PostgreSQL
docker-compose exec postgres psql -U admin -d mikrotik_billing
```

### Backup Database

```bash
# Local
pg_dump -h localhost -U admin mikrotik_billing > backup_$(date +%Y%m%d).sql

# Docker
docker-compose exec -T postgres pg_dump -U admin mikrotik_billing > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Local
psql postgresql://localhost:5432/mikrotik_billing < backup.sql

# Docker
cat backup.sql | docker-compose exec -T postgres psql -U admin -d mikrotik_billing
```

### View Database Tables

```bash
psql postgresql://localhost:5432/mikrotik_billing -c "\dt"
```

### Check User Count

```bash
psql postgresql://localhost:5432/mikrotik_billing -c "SELECT COUNT(*) FROM users;"
```

---

## 📡 MikroTik Commands

### Connect to MikroTik

```bash
# Via SSH
ssh api_admin@192.168.1.7

# Via Winbox
# Open Winbox → Connect to 192.168.1.7
```

### Check Hotspot Users

```bash
/ip hotspot user print
```

### Check Active Sessions

```bash
/ip hotspot active print
```

### Check IP Configuration

```bash
/ip address print
/ip dhcp-client print
```

### Set Static IP

```bash
# Remove DHCP client
/ip dhcp-client remove 0

# Add static IP
/ip address add address=192.168.1.7/24 interface=bridgeLocal network=192.168.1.0
/ip route add gateway=192.168.1.1
/ip dns set servers=8.8.8.8,1.1.1.1
```

### Check API Settings

```bash
/ip service print
# Ensure API is enabled on port 8728

# Enable API if needed
/ip service enable api
/ip service set api address=192.168.1.0/24
```

### View Logs

```bash
/log print
/log print where topics~"system"
```

### Backup MikroTik Configuration

```bash
/system backup save name=backup-$(date +%Y%m%d)
```

---

## 🧪 Testing & Debugging

### Test MikroTik Connection

```bash
cd backend
source venv/bin/activate

python -c "
from mikrotik_api import MikroTikAPI
api = MikroTikAPI()
print('Connected!' if api.connect() else 'Failed!')
"
```

### Test API Endpoints

```bash
# Get stats
curl http://localhost:8000/stats

# Get users
curl http://localhost:8000/users

# Get active connections
curl http://localhost:8000/active-connections

# Create user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123",
    "plan_type": "daily_1000"
  }'
```

### Check Backend Logs

```bash
cd backend
source venv/bin/activate
python main.py 2>&1 | tee backend.log
```

### Find MikroTik IP by MAC

```bash
arp -a | grep -i d4:01:c3:6f:3f:02
```

### Discover MikroTik Devices

```bash
cd backend
python3 discover_mikrotik.py
```

---

## 🔧 Maintenance Commands

### Update Python Dependencies

```bash
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Update Node Dependencies

```bash
cd frontend
npm update
```

### Clean Up

```bash
# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove Node cache
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Check Disk Usage

```bash
# Database size
psql postgresql://localhost:5432/mikrotik_billing -c "
SELECT pg_size_pretty(pg_database_size('mikrotik_billing'));
"

# Docker volumes
docker system df
```

---

## 📊 Monitoring Commands

### Check System Status

```bash
# Backend status
curl http://localhost:8000/stats

# Database connections
psql postgresql://localhost:5432/mikrotik_billing -c "
SELECT count(*) FROM pg_stat_activity WHERE datname='mikrotik_billing';
"
```

### View Active Users on MikroTik

```bash
# All active
/ip hotspot active print

# Count
/ip hotspot active print count-only

# By user
/ip hotspot active print where user="testuser"
```

### Check Network Connectivity

```bash
# Ping MikroTik
ping -c 4 192.168.1.7

# Check API port
nc -zv 192.168.1.7 8728

# Check backend
curl -I http://localhost:8000

# Check frontend
curl -I http://localhost:3000
```

---

## 🚨 Emergency Commands

### Kill All Processes

```bash
# Kill backend
lsof -ti:8000 | xargs kill -9

# Kill frontend
lsof -ti:3000 | xargs kill -9

# Kill all Python processes
pkill -f "python main.py"
```

### Reset Database

```bash
# Drop and recreate
psql postgresql://localhost:5432/postgres -c "DROP DATABASE mikrotik_billing;"
psql postgresql://localhost:5432/postgres -c "CREATE DATABASE mikrotik_billing;"

# Reinitialize
cd backend
source venv/bin/activate
python -c "from database import init_db; init_db()"
```

### Restart MikroTik Router

```bash
# Via SSH
ssh api_admin@192.168.1.7
/system reboot
```

### Emergency User Creation (Manual)

```bash
# On MikroTik
/ip hotspot user add name=emergency password=temp123 profile=daily_1000
```

---

## 📝 Daily Operations

### Morning Startup

```bash
# 1. Start backend
cd backend && source venv/bin/activate && python main.py &

# 2. Start frontend
cd frontend && npm start &

# 3. Check status
curl http://localhost:8000/stats
```

### Create New User

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "pass123",
    "plan_type": "monthly_1000"
  }'
```

### Extend User Subscription

```bash
# Extend by 30 days
curl -X POST http://localhost:8000/users/1/extend \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

### Record Payment

```bash
curl -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "amount": 1000,
    "payment_method": "cash"
  }'
```

### Delete User

```bash
curl -X DELETE http://localhost:8000/users/1
```

### Sync Database with MikroTik

```bash
curl -X POST http://localhost:8000/sync-users
```

---

## 🔍 Troubleshooting

### Connection Issues

```bash
# Test MikroTik API
telnet 192.168.1.7 8728

# Check firewall
# On MikroTik:
/ip firewall filter print

# Check if API is accessible
/ip service print
```

### Database Issues

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql

# Check connections
psql postgresql://localhost:5432/postgres -c "SELECT version();"
```

### Frontend Issues

```bash
# Clear cache and rebuild
cd frontend
rm -rf node_modules build
npm install
npm start
```

### Backend Issues

```bash
# Reinstall dependencies
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📦 Deployment Commands

### Deploy to Production

```bash
# Pull latest code
git pull

# Backup database
./scripts/backup.sh

# Update dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Rebuild and restart
docker-compose up -d --build
```

### Production Backup

```bash
# Run backup script
/opt/scripts/backup.sh

# Manual backup
docker-compose exec -T postgres pg_dump -U admin mikrotik_billing | gzip > backup_$(date +%Y%m%d).sql.gz
```

---

## 🔑 Quick Reference

| Task | Command |
|------|---------|
| Start Backend | `cd backend && source venv/bin/activate && python main.py` |
| Start Frontend | `cd frontend && npm start` |
| Start Docker | `docker-compose up -d` |
| View Logs | `docker-compose logs -f` |
| Backup DB | `pg_dump mikrotik_billing > backup.sql` |
| Connect MikroTik | `ssh api_admin@192.168.1.7` |
| Test API | `curl http://localhost:8000/stats` |
| Find Router IP | `arp -a \| grep -i d4:01:c3:6f:3f:02` |
| Kill Backend | `lsof -ti:8000 \| xargs kill -9` |
| Reset Docker | `docker-compose down -v && docker-compose up -d` |

---

## 📚 Documentation Links

- **Setup Guide**: `README.md`
- **Docker Guide**: `DOCKER_DEPLOY.md`
- **Production Guide**: `PRODUCTION_DEPLOY.md`
- **MikroTik Setup**: `docs/MIKROTIK_SETUP.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **Emergency**: `docs/EMERGENCY.md`

---

## 💡 Pro Tips

1. **Always backup before updates**: Run `./scripts/backup.sh` first
2. **Use Docker in production**: More reliable and easier to manage
3. **Set static IP on MikroTik**: Prevents connection issues
4. **Monitor logs**: `docker-compose logs -f` helps catch issues early
5. **Keep credentials safe**: Never commit `.env` to git
6. **Test locally first**: Verify changes work before deploying

---

**Last Updated**: 2025-12-08
**Version**: 1.0
