# Docker Deployment Guide

Deploy the MikroTik Billing System anywhere using Docker.

## Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- MikroTik router accessible from deployment location

## Quick Start (Local Development)

```bash
# Clone the repository
cd networking_mikrotik

# Copy environment file
cp .env.docker .env

# Edit with your MikroTik details
nano .env

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access dashboard
open http://localhost
```

## Environment Configuration

Edit `.env` file:

```env
# Database password
DB_PASSWORD=your_secure_password_here

# MikroTik Router
MIKROTIK_HOST=192.168.1.159      # Your router IP
MIKROTIK_USERNAME=api_admin       # API user
MIKROTIK_PASSWORD=YourPassword   # API password
MIKROTIK_PORT=8728               # API port
```

## Deployment Scenarios

### 1. Local Network (Same network as MikroTik)

```bash
# Use default .env configuration
docker-compose up -d
```

Access: `http://localhost` or `http://your-machine-ip`

### 2. Remote VPS (DigitalOcean, AWS, etc.)

#### Option A: SSH Tunnel

**On a device at MikroTik location:**
```bash
# Create persistent tunnel to VPS
autossh -M 0 -N -R 8728:192.168.1.159:8728 user@vps-ip
```

**On VPS `.env`:**
```env
MIKROTIK_HOST=localhost
MIKROTIK_PORT=8728
```

#### Option B: WireGuard VPN

1. Setup WireGuard on VPS (see MIKROTIK_SETUP.md)
2. Connect MikroTik to VPS via WireGuard
3. Update `.env`:
```env
MIKROTIK_HOST=10.0.0.2  # MikroTik WireGuard IP
```

### 3. Multi-Location Deployment

Deploy one instance per location or use multi-router support (coming soon).

## Docker Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
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

### Restart Services
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
```

### Rebuild After Changes
```bash
# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend
```

### Execute Commands in Containers
```bash
# Backend Python shell
docker-compose exec backend python

# Database access
docker-compose exec postgres psql -U admin -d mikrotik_billing

# Backend bash
docker-compose exec backend bash
```

## Production Deployment

### 1. Deploy to DigitalOcean

```bash
# SSH to droplet
ssh root@your-droplet-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Clone project
git clone <your-repo> /opt/mikrotik-billing
cd /opt/mikrotik-billing

# Configure
cp .env.docker .env
nano .env  # Update with your values

# Start services
docker-compose up -d

# Setup reverse proxy (nginx)
sudo apt install nginx
```

#### Nginx Configuration for Docker

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

### 3. Auto-Start on Boot

Docker Compose services restart automatically with `restart: unless-stopped` policy.

To ensure Docker starts on boot:
```bash
sudo systemctl enable docker
```

## Data Persistence

Volumes are automatically created:
- `postgres_data`: Database data

### Backup Database

```bash
# Create backup
docker-compose exec postgres pg_dump -U admin mikrotik_billing > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U admin mikrotik_billing < backup.sql
```

### Automated Backups

Create `/opt/scripts/docker-backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U admin mikrotik_billing \
  > $BACKUP_DIR/db_$DATE.sql

# Keep last 7 days
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/scripts/docker-backup.sh
```

## Monitoring

### View Resource Usage

```bash
docker stats
```

### Health Checks

All services have health checks built-in:

```bash
# Check service health
docker-compose ps
```

### Logs

```bash
# Real-time logs
docker-compose logs -f --tail=100

# Save logs to file
docker-compose logs > logs.txt
```

## Troubleshooting

### Backend Can't Connect to MikroTik

```bash
# Test connectivity from backend container
docker-compose exec backend ping 192.168.1.159

# Check if API port is accessible
docker-compose exec backend nc -zv 192.168.1.159 8728
```

### Database Connection Issues

```bash
# Check if postgres is running
docker-compose ps postgres

# View postgres logs
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U admin -d mikrotik_billing -c "SELECT version();"
```

### Frontend Not Loading

```bash
# Check nginx logs
docker-compose exec frontend cat /var/log/nginx/error.log

# Verify frontend is running
docker-compose ps frontend

# Test frontend locally
curl http://localhost
```

### Reset Everything

```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose up -d --build
```

## Updating

### Pull Latest Changes

```bash
cd /opt/mikrotik-billing
git pull
docker-compose up -d --build
```

### Update Single Service

```bash
# Update only backend
docker-compose up -d --build backend

# Update only frontend
docker-compose up -d --build frontend
```

## Custom Configurations

### Use External Database

Update `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      DATABASE_URL: postgresql://user:pass@external-db-host:5432/dbname
```

### Custom Ports

Update `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # Access on port 8080
```

### Development Mode

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  backend:
    volumes:
      - ./backend:/app
    command: python -m uvicorn main:app --reload --host 0.0.0.0

  frontend:
    volumes:
      - ./frontend/src:/app/src
    command: npm start
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Security Best Practices

1. **Change default passwords** in `.env`
2. **Use SSL/HTTPS** in production
3. **Restrict database port** (remove port mapping if not needed)
4. **Regular backups** of database
5. **Keep Docker images updated**
6. **Use secrets management** for production

## Performance Tuning

### Increase Resources

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### Database Optimization

```yaml
services:
  postgres:
    command: postgres -c shared_buffers=256MB -c max_connections=200
```

## Support

- Check logs: `docker-compose logs -f`
- View documentation: `docs/` directory
- Emergency procedures: `docs/EMERGENCY.md`
