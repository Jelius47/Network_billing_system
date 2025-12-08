# Production Deployment Guide

Complete guide for deploying the MikroTik Billing System in production environments.

## Table of Contents

1. [DigitalOcean Deployment](#digitalocean-deployment)
2. [AWS Deployment](#aws-deployment)
3. [VPS Deployment (Generic)](#vps-deployment)
4. [Security Hardening](#security-hardening)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup Strategy](#backup-strategy)
7. [High Availability](#high-availability)

---

## DigitalOcean Deployment

### 1. Create Droplet

**Recommended Configuration:**
- **Image:** Docker on Ubuntu 22.04
- **Plan:** Basic - $12/month (2GB RAM, 1 vCPU, 50GB SSD)
- **Datacenter:** Choose region closest to your users
- **Networking:** Enable IPv6, Private networking
- **Add-ons:** Backups ($2.40/month)

### 2. Initial Setup

```bash
# SSH to droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Create deployment user
adduser deploy
usermod -aG sudo,docker deploy

# Setup firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Switch to deploy user
su - deploy
```

### 3. Deploy Application

```bash
# Clone repository
cd /opt
sudo mkdir mikrotik-billing
sudo chown deploy:deploy mikrotik-billing
git clone <your-repo-url> mikrotik-billing
cd mikrotik-billing

# Configure environment
cp .env.docker .env
nano .env
```

**Example `.env` for production:**
```env
# Strong database password
DB_PASSWORD=$(openssl rand -base64 32)

# MikroTik connection (via tunnel or VPN)
MIKROTIK_HOST=localhost  # If using SSH tunnel
MIKROTIK_USERNAME=api_admin
MIKROTIK_PASSWORD=your_secure_password
MIKROTIK_PORT=8728
```

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

### 4. Setup Reverse Proxy with SSL

```bash
# Install nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# Create nginx config
sudo nano /etc/nginx/sites-available/mikrotik
```

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (will be added by certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Docker container
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://localhost:80/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/mikrotik /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 5. Setup MikroTik Connection

**Option A: SSH Tunnel from MikroTik Location**

On device at MikroTik network:
```bash
# Install autossh
sudo apt install autossh

# Create systemd service
sudo nano /etc/systemd/system/mikrotik-tunnel.service
```

```ini
[Unit]
Description=MikroTik API SSH Tunnel
After=network.target

[Service]
Type=simple
User=deploy
ExecStart=/usr/bin/autossh -M 0 -N -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -R 8728:192.168.1.159:8728 deploy@your-droplet-ip
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mikrotik-tunnel
sudo systemctl start mikrotik-tunnel
```

**Option B: WireGuard VPN**

See `DOCKER_DEPLOY.md` for WireGuard configuration.

### 6. Setup Monitoring

```bash
# Install DigitalOcean agent
curl -sSL https://repos.insights.digitalocean.com/install.sh | sudo bash

# Setup log rotation
sudo nano /etc/logrotate.d/mikrotik-billing
```

```
/var/log/mikrotik-billing/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### 7. Automated Backups

```bash
# Create backup script
sudo mkdir -p /opt/scripts
sudo nano /opt/scripts/backup.sh
```

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f /opt/mikrotik-billing/docker-compose.yml exec -T postgres \
    pg_dump -U admin mikrotik_billing | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup .env
cp /opt/mikrotik-billing/.env $BACKUP_DIR/env_$DATE

# Optional: Upload to DigitalOcean Spaces
# s3cmd put $BACKUP_DIR/db_$DATE.sql.gz s3://your-space/backups/

# Clean old backups
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "env_*" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
```

```bash
sudo chmod +x /opt/scripts/backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

---

## Security Hardening

### 1. SSH Security

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
```

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

```bash
sudo systemctl restart sshd
```

### 2. Fail2ban

```bash
sudo apt install fail2ban -y

sudo nano /etc/fail2ban/jail.local
```

```ini
[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Docker Security

```bash
# Run Docker daemon with user namespace remapping
sudo nano /etc/docker/daemon.json
```

```json
{
  "userns-remap": "default",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
sudo systemctl restart docker
```

### 4. Environment Secrets

Use Docker secrets for sensitive data:

```yaml
# docker-compose.prod.yml
version: '3.8'

secrets:
  db_password:
    file: ./secrets/db_password.txt
  mikrotik_password:
    file: ./secrets/mikrotik_password.txt

services:
  backend:
    secrets:
      - db_password
      - mikrotik_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
      MIKROTIK_PASSWORD_FILE: /run/secrets/mikrotik_password
```

---

## Monitoring & Logging

### 1. Application Metrics

Install Prometheus and Grafana:

```bash
# Create monitoring stack
nano docker-compose.monitoring.yml
```

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"

volumes:
  prometheus_data:
  grafana_data:
```

### 2. Log Aggregation

Use Docker's logging driver:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. Alerting

Setup alerts for:
- Service downtime
- High CPU/memory usage
- Database connection issues
- Failed MikroTik API connections

---

## Backup Strategy

### Automated Backups

1. **Database:** Daily at 2 AM
2. **Environment files:** Daily
3. **Docker volumes:** Weekly
4. **System snapshot:** Weekly (DigitalOcean Droplet backup)

### Backup Retention

- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months

### Disaster Recovery

Test restore procedure monthly:

```bash
# Stop services
docker-compose down

# Restore database
docker-compose up -d postgres
gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U admin mikrotik_billing

# Restart all services
docker-compose up -d
```

---

## High Availability

### Multi-Region Deployment

Deploy in multiple regions with separate MikroTik routers:

```
Region 1 (US East)          Region 2 (EU)
┌────────────┐              ┌────────────┐
│   Droplet  │              │   Droplet  │
│  + Docker  │              │  + Docker  │
└─────┬──────┘              └─────┬──────┘
      │                            │
      ▼                            ▼
 MikroTik 1                   MikroTik 2
```

### Load Balancing

Use DigitalOcean Load Balancer or Cloudflare for traffic distribution.

### Database Replication

Setup PostgreSQL replication for high availability:

```yaml
services:
  postgres-primary:
    # Primary database
  postgres-replica:
    # Read replica
```

---

## Maintenance

### Update Procedure

```bash
cd /opt/mikrotik-billing

# Pull latest changes
git pull

# Backup before update
/opt/scripts/backup.sh

# Rebuild and restart
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

### Health Checks

Create health check script:

```bash
#!/bin/bash
# /opt/scripts/health-check.sh

# Check if services are running
docker-compose ps | grep -q "Up" || exit 1

# Check database connection
docker-compose exec -T postgres pg_isready || exit 1

# Check backend API
curl -f http://localhost:8000/ || exit 1

# Check frontend
curl -f http://localhost/ || exit 1

echo "All checks passed"
```

Add to cron for monitoring:
```bash
*/5 * * * * /opt/scripts/health-check.sh || mail -s "Alert: Service Down" admin@example.com
```

---

## Cost Optimization

### DigitalOcean

- **Droplet:** $12/month (2GB)
- **Backups:** $2.40/month
- **Spaces (optional):** $5/month
- **Total:** ~$20/month

### AWS Alternative

- **t3.micro EC2:** ~$8/month
- **RDS db.t3.micro:** ~$15/month
- **Total:** ~$25/month

### Scaling Strategy

Start small, scale based on load:
1. **< 100 users:** 1GB Droplet ($6/month)
2. **100-500 users:** 2GB Droplet ($12/month)
3. **500-2000 users:** 4GB Droplet ($24/month)
4. **2000+ users:** Load balanced setup

---

## Support & Troubleshooting

- **Logs:** `docker-compose logs -f`
- **Status:** `docker-compose ps`
- **Restart:** `docker-compose restart`
- **Emergency:** See `docs/EMERGENCY.md`

**Production is now ready! 🚀**
