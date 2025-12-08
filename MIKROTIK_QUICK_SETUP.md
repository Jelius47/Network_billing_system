# MikroTik Quick Setup - Step by Step

## Prerequisites
- MikroTik RB941 connected to power
- Computer connected to MikroTik (via LAN cable or WiFi)
- MikroTik has internet connection on ether1 (WAN port)

## Access Your Router

### Method 1: Web Browser
1. Open browser
2. Go to: `http://192.168.88.1`
3. Login: Username `admin`, Password: (leave blank)
4. Click on "Terminal" in the left menu

### Method 2: Winbox (Recommended)
1. Download: https://mikrotik.com/download
2. Run Winbox.exe (Windows) or Winbox.app (Mac)
3. In the "Connect To" field, enter: `192.168.88.1`
4. Username: `admin`
5. Password: (leave blank)
6. Click "Connect"
7. Click "New Terminal" button (top menu)

### Method 3: SSH from Mac Terminal
```bash
ssh admin@192.168.88.1
# Password: (press Enter - blank)
```

---

## Commands to Run

### Step 1: Check if Hotspot Already Exists

```
/ip hotspot print
```

**If you see a hotspot already configured:**
- Skip to Step 2

**If no hotspot exists:**
```
/ip hotspot setup
```
Follow the wizard:
- Just press Enter for all prompts (accept defaults)
- When asked for DNS: type `8.8.8.8`
- When asked for password: type a password you'll remember

---

### Step 2: Create User Profiles

Copy and paste this (one line at a time):

```
/ip hotspot user profile add name=daily_1000 rate-limit=1M/1M session-timeout=1d

/ip hotspot user profile add name=monthly_1000 rate-limit=1M/1M session-timeout=30d
```

**Verify it worked:**
```
/ip hotspot user profile print
```

You should see `daily_1000` and `monthly_1000` in the list.

---

### Step 3: Enable API

```
/ip service set api disabled=no
```

**Verify it worked:**
```
/ip service print where name=api
```

You should see:
```
name="api" port=8728 disabled=no
```

---

### Step 4: Create API Admin User

**⚠️ IMPORTANT:** Replace `YourStrongPassword123` with your own password!

```
/user add name=api_admin password=YourStrongPassword123 group=full
```

**Verify it worked:**
```
/user print
```

You should see `api_admin` in the list.

---

### Step 5: Test Creating a User

```
/ip hotspot user add name=testuser password=test123 profile=daily_1000
```

**Verify it worked:**
```
/ip hotspot user print
```

You should see `testuser` in the list.

**Remove the test user:**
```
/ip hotspot user remove [find name=testuser]
```

---

### Step 6: Backup Configuration

```
/system backup save name=billing-backup

/export file=billing-config
```

**Download backups via Winbox:**
1. Click "Files" in left menu
2. Right-click on `billing-backup.backup` → Download
3. Right-click on `billing-config.rsc` → Download
4. Save to a safe location

---

## What You Should Have Now

✅ Hotspot service running
✅ Two user profiles: `daily_1000` and `monthly_1000`
✅ API enabled on port 8728
✅ User `api_admin` created
✅ Configuration backed up

---

## Common Issues

### "failure: already have interface with such name"
- Hotspot already exists, skip the setup wizard
- Go directly to Step 2

### "no such item"
- Check spelling carefully
- Make sure you press Enter after each command

### "invalid value for argument"
- You might have a typo in the command
- Copy-paste the command exactly as shown

---

## Next: Configure Your Mac

Now that your router is ready, configure your Mac:

1. **Edit backend configuration:**
```bash
cd ~/Documents/personal_pro/networking_mikrotik/backend
nano .env
```

2. **Add your router details:**
```env
MIKROTIK_HOST=192.168.88.1
MIKROTIK_USERNAME=api_admin
MIKROTIK_PASSWORD=YourStrongPassword123  # Use the password you set!
MIKROTIK_PORT=8728
```

3. **Save and exit:** Press `Ctrl+X`, then `Y`, then Enter

---

## Summary of Credentials

**Router Web/Winbox:**
- URL: http://192.168.88.1
- Username: admin
- Password: (your hotspot admin password)

**API Access (for backend):**
- Host: 192.168.88.1
- Port: 8728
- Username: api_admin
- Password: (the password you set in Step 4)

**Write these down and keep them safe!**

---

## Test Your Setup

From your Mac terminal:
```bash
telnet 192.168.88.1 8728
```

You should see: "Connected to router.lan."

Press `Ctrl+]` then type `quit` to exit.

---

You're done with the MikroTik configuration! 🎉

Next step: Set up the backend on your Mac (follow QUICK_START.md)
