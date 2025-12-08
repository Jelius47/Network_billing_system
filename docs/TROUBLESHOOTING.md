# Troubleshooting Guide

Common issues and their solutions for the MikroTik Billing System.

## Backend Issues

### Database Connection Fails

**Symptoms:**
- `FATAL: password authentication failed for user "admin"`
- `column users.username does not exist`
- Backend crashes on startup

**Solutions:**

#### For New Installations:
1. Check PostgreSQL is running:
   ```bash
   # Ubuntu/Debian
   sudo systemctl status postgresql

   # macOS
   brew services list | grep postgresql
   ```

2. Verify database exists:
   ```bash
   sudo -u postgres psql -l
   ```

3. Test connection:
   ```bash
   psql -U admin -d mikrotik_billing -h localhost
   ```

4. Reset password if needed:
   ```bash
   sudo -u postgres psql
   ALTER USER admin WITH PASSWORD 'temp123';
   ```

#### For Existing PostgreSQL Installations:

**Symptoms:**
- You already have PostgreSQL running at `postgresql://localhost:5432/postgres`
- Error: `column users.username does not exist`

**Solution:**
1. Create the mikrotik_billing database:
   ```bash
   psql postgresql://localhost:5432/postgres -c "CREATE DATABASE mikrotik_billing;"
   ```

2. Update your `.env` file:
   ```env
   DATABASE_URL=postgresql://localhost:5432/mikrotik_billing
   ```

3. Test connection:
   ```bash
   psql postgresql://localhost:5432/mikrotik_billing -c "SELECT 'Connected!' as status;"
   ```

4. Start the backend - it will create tables automatically:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```

5. Verify tables were created:
   ```bash
   psql postgresql://localhost:5432/mikrotik_billing -c "\dt"
   ```

   You should see: users, payments, logs

**If you need authentication:**
```env
DATABASE_URL=postgresql://yourusername:yourpassword@localhost:5432/mikrotik_billing
```

### MikroTik API Connection Fails

**Symptoms:**
- `Connection failed: [Errno 111] Connection refused`
- Users not created in router

**Solutions:**
1. Verify API is enabled on router:
   ```
   /ip service print
   ```

2. Check API port (default 8728):
   ```
   /ip service set api port=8728
   ```

3. Test connection from backend server:
   ```bash
   telnet 192.168.88.1 8728
   ```

4. Verify credentials in `.env` file

5. Check firewall rules on router

### Users Not Auto-Disabling

**Symptoms:**
- Expired users still have access
- Background task not running

**Solutions:**
1. Check backend logs for errors

2. Verify scheduler is running:
   ```python
   # In main.py, ensure scheduler.start() is called
   ```

3. Manually trigger check:
   ```bash
   curl http://localhost:8000/expired
   ```

4. Check user expiry dates are correct

## Frontend Issues

### Cannot Connect to Backend

**Symptoms:**
- `Network Error`
- API calls failing

**Solutions:**
1. Verify backend is running:
   ```bash
   curl http://localhost:8000/
   ```

2. Check API_BASE_URL in `frontend/src/config.js`

3. Verify CORS is enabled in backend

4. Check firewall on backend server

### Users Not Showing in Dashboard

**Symptoms:**
- Empty user list
- Dashboard shows 0 users

**Solutions:**
1. Check browser console for errors (F12)

2. Verify API endpoint:
   ```bash
   curl http://localhost:8000/users
   ```

3. Check database has users:
   ```bash
   psql -U admin -d mikrotik_billing -c "SELECT * FROM users;"
   ```

4. Clear browser cache

## MikroTik Router Issues

### Hotspot Not Redirecting

**Symptoms:**
- Users get internet without login
- No login page appears

**Solutions:**
1. Check hotspot is active:
   ```
   /ip hotspot print
   ```

2. Verify hotspot interface:
   ```
   /ip hotspot print detail
   ```

3. Check DNS configuration:
   ```
   /ip dns print
   /ip hotspot profile print
   ```

4. Clear DNS cache on client device

### Users Cannot Login

**Symptoms:**
- "Invalid username or password"
- Login page appears but credentials rejected

**Solutions:**
1. Verify user exists in router:
   ```
   /ip hotspot user print where name=username
   ```

2. Check user is not disabled:
   ```
   /ip hotspot user print where name=username
   ```

3. Verify profile exists:
   ```
   /ip hotspot user profile print
   ```

4. Check user limits not exceeded:
   ```
   /ip hotspot active print
   ```

### API Commands Fail

**Symptoms:**
- Users created in database but not in router
- Disable/enable operations fail

**Solutions:**
1. Test API manually via Winbox

2. Check API user has correct permissions:
   ```
   /user print
   ```

3. Verify API service is running:
   ```
   /ip service print where name=api
   ```

4. Check router logs:
   ```
   /log print where topics~"api"
   ```

## Performance Issues

### Slow Dashboard

**Solutions:**
1. Reduce auto-refresh interval in components

2. Add pagination to user list

3. Optimize database queries

4. Use caching for stats

### Router CPU High

**Solutions:**
1. Check active connections:
   ```
   /ip hotspot active print
   ```

2. Reduce session timeout

3. Implement connection limits

4. Monitor system resources:
   ```
   /system resource print
   ```

## Emergency Recovery

### System Completely Broken

1. **Backend down:**
   - Create users manually in Winbox
   - Use RouterOS terminal commands

2. **Database corrupted:**
   - Restore from backup
   - Export users from router:
     ```
     /ip hotspot user print
     ```
   - Manually recreate database

3. **Router inaccessible:**
   - Hard reset button (hold 10 seconds)
   - Restore from backup
   - Reconfigure from scratch

### Quick Recovery Commands

```bash
# Export database to CSV
psql -U admin -d mikrotik_billing -c "COPY users TO '/tmp/users.csv' CSV HEADER;"

# Import users to router via script
# Create script file: import_users.rsc
/ip hotspot user add name=user1 password=pass1 profile=daily_1000
/ip hotspot user add name=user2 password=pass2 profile=monthly_1000

# Import via Winbox: File > Open > import_users.rsc
```

## Common Error Messages

### `routeros_api.exceptions.RouterOsApiConnectionError`
- Router not reachable
- Check network connectivity
- Verify IP address and port

### `psycopg2.OperationalError: FATAL: database does not exist`
- Database not created
- Run database setup commands

### `CORS policy: No 'Access-Control-Allow-Origin' header`
- CORS not configured in backend
- Add CORS middleware

### `HTTPException: 400 Username already exists`
- Duplicate username
- Choose different username
- Check if user was partially created

## Debug Mode

### Enable Verbose Logging

**Backend:**
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**MikroTik:**
```
/system logging add topics=api,!debug action=memory
/log print
```

### Monitor API Calls

```bash
# Watch backend logs
tail -f /var/log/mikrotik-billing.log

# Monitor API requests
curl -X GET http://localhost:8000/logs
```

## Getting Help

If issues persist:

1. Check backend logs
2. Check router logs: `/log print`
3. Verify all configuration files
4. Test each component individually
5. Review documentation for specific features

## Preventive Measures

1. **Regular backups:**
   ```bash
   # Database backup
   pg_dump -U admin mikrotik_billing > backup.sql

   # Router backup
   /system backup save name=daily-backup
   ```

2. **Monitor system health:**
   - Check disk space
   - Monitor CPU/memory usage
   - Review logs regularly

3. **Test recovery procedures:**
   - Practice restoring from backup
   - Document recovery steps
   - Keep offline copies of critical configs

4. **Update regularly:**
   - Keep dependencies updated
   - Update RouterOS to stable versions
   - Review security patches
