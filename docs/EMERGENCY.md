# Emergency Recovery Procedures

Quick reference for emergency situations when the billing system fails.

## Emergency Contact Info

**Keep this information accessible:**
- Router IP: `192.168.88.1`
- Router Admin User: `admin`
- Database Server: `localhost`
- Backend Port: `8000`
- Frontend Port: `3000`

## Quick Diagnostic Commands

```bash
# Check if services are running
sudo systemctl status postgresql
ps aux | grep python
ps aux | grep node

# Check network connectivity
ping 192.168.88.1
curl http://localhost:8000/
curl http://localhost:3000/

# Check database
psql -U admin -d mikrotik_billing -c "SELECT COUNT(*) FROM users;"

# Check router API
telnet 192.168.88.1 8728
```

## Critical Failure Scenarios

### 1. Complete System Failure

**Situation:** Everything is down, customers have no internet

**Immediate Actions:**

1. **Bypass billing system temporarily:**
   ```
   # On MikroTik router via Winbox
   /ip hotspot disable [find]

   # Enable direct internet access
   # (NAT should still work from initial config)
   ```

2. **Keep track of who was online:**
   ```
   /ip dhcp-server lease print
   ```

3. **Fix system and restore hotspot:**
   ```
   /ip hotspot enable [find]
   ```

### 2. Backend Server Crash

**Situation:** Dashboard not accessible, but router is working

**Manual User Management via Winbox:**

1. **Create User:**
   ```
   /ip hotspot user add name=username password=password123 profile=daily_1000
   ```

2. **Disable User:**
   ```
   /ip hotspot user set [find name=username] disabled=yes
   ```

3. **Enable User:**
   ```
   /ip hotspot user set [find name=username] disabled=no
   ```

4. **Extend User (change profile):**
   ```
   /ip hotspot user set [find name=username] profile=monthly_1000
   ```

5. **View Active Users:**
   ```
   /ip hotspot active print
   ```

**Track Payments Manually:**
- Keep notebook/spreadsheet
- Record: Username, Amount, Date, Plan
- Update database when system recovers

### 3. Database Corruption

**Situation:** Backend running but no user data

**Recovery Steps:**

1. **Stop backend:**
   ```bash
   pkill -f "python main.py"
   ```

2. **Backup current database:**
   ```bash
   pg_dump -U admin mikrotik_billing > corrupted_backup.sql
   ```

3. **Restore from last good backup:**
   ```bash
   dropdb -U admin mikrotik_billing
   createdb -U admin mikrotik_billing
   psql -U admin -d mikrotik_billing < backup.sql
   ```

4. **If no backup, export from router:**
   ```
   # On router
   /ip hotspot user export file=users_backup

   # Download file via WinBox
   # Manually recreate database entries
   ```

5. **Restart backend:**
   ```bash
   cd backend
   python main.py
   ```

### 4. Router Becomes Inaccessible

**Situation:** Cannot connect to router via IP or Winbox

**Recovery Options:**

**Option A: MAC Connection**
1. Open Winbox
2. Click "Neighbors" tab
3. Connect using MAC address
4. Check IP configuration

**Option B: Hard Reset**
1. Locate reset button on router
2. Power on router
3. Hold reset button for 10 seconds
4. Router resets to defaults
5. **IMPORTANT:** Reconfigure from scratch using backup or docs

**Option C: Serial Console**
1. Connect via serial cable
2. Use PuTTY/screen: `115200 8N1`
3. Login and diagnose

### 5. Cannot Disable Expired Users

**Situation:** Expired users still have access

**Quick Fix:**

1. **List all users in router:**
   ```
   /ip hotspot user print
   ```

2. **Bulk disable all users:**
   ```
   /ip hotspot user set [find] disabled=yes
   ```

3. **Re-enable only active users from database:**
   ```bash
   # Export active users from database
   psql -U admin -d mikrotik_billing -c "
   SELECT username FROM users
   WHERE expiry > NOW() AND is_active = true;
   " -t -A > active_users.txt

   # Create MikroTik script to enable them
   cat active_users.txt | while read user; do
     echo "/ip hotspot user set [find name=$user] disabled=no"
   done > enable_users.rsc

   # Import script to router via Winbox
   ```

## Emergency User Creation Script

Save this as `emergency_user.sh`:

```bash
#!/bin/bash
# Emergency user creation script
# Usage: ./emergency_user.sh username password plan_type

USERNAME=$1
PASSWORD=$2
PLAN=${3:-daily_1000}

# Add to router via SSH
ssh admin@192.168.88.1 "/ip hotspot user add name=$USERNAME password=$PASSWORD profile=$PLAN"

# Add to database
psql -U admin -d mikrotik_billing <<EOF
INSERT INTO users (username, password, plan_type, expiry, is_active, created_at)
VALUES (
  '$USERNAME',
  '$PASSWORD',
  '$PLAN',
  NOW() + INTERVAL '1 day',
  true,
  NOW()
);
EOF

echo "User $USERNAME created successfully"
```

## Data Export/Import

### Export Current Users

```bash
# From database to CSV
psql -U admin -d mikrotik_billing -c "
COPY (SELECT username, password, plan_type, expiry, is_active
      FROM users
      ORDER BY created_at DESC)
TO '/tmp/users_export.csv'
CSV HEADER;
"

# From router to text
ssh admin@192.168.88.1 "/ip hotspot user export file=users"
```

### Bulk Import Users

```bash
# From CSV to database
psql -U admin -d mikrotik_billing -c "
COPY users(username, password, plan_type, expiry, is_active)
FROM '/tmp/users_import.csv'
CSV HEADER;
"

# From script to router (via Winbox File menu)
```

## System Restore Checklist

- [ ] Database backup restored
- [ ] Router configuration restored
- [ ] Backend service running
- [ ] Frontend accessible
- [ ] Test user creation
- [ ] Test user login
- [ ] Test auto-disable function
- [ ] Verify active users count
- [ ] Check payment records
- [ ] Review system logs

## Prevent Future Emergencies

### Daily Tasks
- [ ] Check system status dashboard
- [ ] Verify auto-disable is working
- [ ] Monitor active connections

### Weekly Tasks
- [ ] Backup database
- [ ] Backup router config
- [ ] Review error logs
- [ ] Test recovery procedures

### Monthly Tasks
- [ ] Update system dependencies
- [ ] Security audit
- [ ] Performance review
- [ ] Documentation update

## Emergency Contacts

```
System Administrator: _______________
Network Engineer: _______________
Database Admin: _______________
ISP Support: _______________
```

## Keep These Files Accessible

1. Router backup (.backup file)
2. Router config export (.rsc file)
3. Database backup (.sql file)
4. User list export (.csv file)
5. This emergency guide (printed copy)
6. Router admin credentials (secure location)

## Recovery Time Objectives

- **Minor issue:** 15 minutes
- **Backend crash:** 30 minutes
- **Database corruption:** 1 hour
- **Complete system failure:** 2-4 hours

## Post-Emergency Actions

1. Document what went wrong
2. Document what fixed it
3. Update emergency procedures
4. Implement preventive measures
5. Test backup/recovery procedures
6. Update monitoring/alerting
7. Train additional staff

## Testing Emergency Procedures

Regularly test these procedures in non-emergency situations:

```bash
# Test backup restore (on test database)
createdb test_restore
psql -U admin -d test_restore < backup.sql

# Test router config restore (on test router)
/system backup load name=test-backup

# Test manual user creation
# Practice the emergency_user.sh script
```

Remember: **Stay calm, follow procedures, document everything!**
