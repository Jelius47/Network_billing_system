# Fix WiFi Login Persistence Issue

## Problem
Users complain that when they disconnect WiFi and reconnect, the system keeps asking for login credentials.

## Solution
Configure MikroTik Hotspot to use MAC cookies for persistent authentication.

## Commands to Run on MikroTik

Connect to your MikroTik via WinBox or SSH and run these commands:

### 1. Enable MAC Cookie Authentication

This allows MikroTik to remember authenticated devices by their MAC address:

```bash
/ip hotspot profile
set [find name=hsprof1] login-by=mac-cookie,http-chap
set [find name=hsprof1] mac-cookie-timeout=3d
```

**Explanation:**
- `login-by=mac-cookie,http-chap` - Enables MAC cookie authentication along with HTTP CHAP
- `mac-cookie-timeout=3d` - Remembers devices for 3 days after authentication

### 2. Increase Session Timeout

Prevent sessions from expiring too quickly:

```bash
/ip hotspot profile
set [find name=hsprof1] session-timeout=1d
set [find name=hsprof1] idle-timeout=none
set [find name=hsprof1] keepalive-timeout=2m
```

**Explanation:**
- `session-timeout=1d` - Session lasts 1 day
- `idle-timeout=none` - No timeout for idle connections
- `keepalive-timeout=2m` - Check if user is still online every 2 minutes

### 3. For Daily and Monthly Profiles

If you're using custom profiles (daily_1000, monthly_1000), apply the same settings:

```bash
# For daily_1000 profile
/ip hotspot profile
set [find name=daily_1000] login-by=mac-cookie,http-chap
set [find name=daily_1000] mac-cookie-timeout=1d
set [find name=daily_1000] session-timeout=1d
set [find name=daily_1000] idle-timeout=none
set [find name=daily_1000] keepalive-timeout=2m

# For monthly_1000 profile
/ip hotspot profile
set [find name=monthly_1000] login-by=mac-cookie,http-chap
set [find name=monthly_1000] mac-cookie-timeout=30d
set [find name=monthly_1000] session-timeout=30d
set [find name=monthly_1000] idle-timeout=none
set [find name=monthly_1000] keepalive-timeout=2m
```

### 4. Verify Settings

Check that the settings were applied:

```bash
/ip hotspot profile print detail
```

## What This Does

1. **MAC Cookie** - MikroTik stores a cookie on the device tied to its MAC address
2. **When user reconnects** - MikroTik recognizes the MAC and automatically logs them in
3. **No repeated login** - Users only need to log in once within the cookie timeout period
4. **Still enforces limits** - Uptime limits and expiry dates still apply

## Testing

1. Connect a device to WiFi and log in
2. Disconnect WiFi
3. Reconnect WiFi
4. Device should connect without asking for credentials (if within cookie timeout)

## Notes

- Users will need to log in again after the cookie timeout expires
- Clearing browser cookies or changing devices requires new login
- MAC cookie works across WiFi disconnections and device reboots
