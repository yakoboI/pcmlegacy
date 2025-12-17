# Deploy from GitHub to PythonAnywhere

Quick guide to deploy your code from GitHub to PythonAnywhere.

## Method 1: Clone Fresh (Recommended for first time)

### Step 1: Open PythonAnywhere Bash Console
1. Log in to [PythonAnywhere](https://www.pythonanywhere.com)
2. Go to **Consoles** tab
3. Click **Bash** to open a new console

### Step 2: Navigate to Home Directory
```bash
cd /home/chusi
```

### Step 3: Remove Old Directory (if exists)
```bash
# Backup your database first!
cp -r pcmlegacy/instance pcmlegacy_instance_backup 2>/dev/null || true

# Remove old directory
rm -rf pcmlegacy
```

### Step 4: Clone from GitHub
```bash
git clone https://github.com/yakoboI/pcmlegacy.git pcmlegacy
```

### Step 5: Restore Database (if you backed it up)
```bash
# If you backed up the instance directory
cp -r pcmlegacy_instance_backup/* pcmlegacy/instance/ 2>/dev/null || true
```

### Step 6: Install Dependencies
```bash
cd pcmlegacy

# Check your Python version (from Web tab)
# Then install dependencies (replace 3.10 with your version)
pip3.10 install --user -r requirements.txt
```

### Step 7: Configure WSGI File
1. Go to **Web** tab in PythonAnywhere
2. Click on your web app
3. Click **WSGI configuration file** link
4. Copy content from `wsgi_production.py` and paste it
5. Update path if needed: `/home/chusi/pcmlegacy`

### Step 8: Reload Web App
- Click the green **Reload** button in Web tab

---

## Method 2: Pull Updates (If already cloned)

### Step 1: Open Bash Console
Go to **Consoles** → **Bash**

### Step 2: Navigate to Project
```bash
cd /home/chusi/pcmlegacy
```

### Step 3: Backup Database (Important!)
```bash
# Create backup of your database
cp instance/pcm_store.db instance/pcm_store_backup_$(date +%Y%m%d_%H%M%S).db
```

### Step 4: Pull Latest Changes
```bash
git pull origin main
```

### Step 5: Install New Dependencies (if any)
```bash
pip3.10 install --user -r requirements.txt
```

### Step 6: Reload Web App
- Go to **Web** tab → Click **Reload**

---

## Method 3: Using Git in Existing Directory

If your directory is already set up but not a git repo:

### Step 1: Initialize Git
```bash
cd /home/chusi/pcmlegacy
git init
git remote add origin https://github.com/yakoboI/pcmlegacy.git
git fetch origin
git checkout -b main origin/main
```

### Step 2: Install Dependencies
```bash
pip3.10 install --user -r requirements.txt
```

### Step 3: Reload Web App

---

## Important Notes

### Database Protection
- **Always backup your database** before pulling/cloning
- Your database is in `instance/pcm_store.db`
- Backups are in `instance/backups/` (if created via admin panel)

### Environment Variables
After deploying, make sure to set environment variables in **Web** tab:
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key`
- Email and M-Pesa credentials

### Static Files
Make sure static files are configured in **Web** tab:
- URL: `/static/`
- Directory: `/home/chusi/pcmlegacy/static/`

### Virtualenv (Optional)
If using a virtualenv:
```bash
cd /home/chusi/pcmlegacy
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then set virtualenv path in **Web** tab:
- `/home/chusi/pcmlegacy/venv`

---

## Troubleshooting

### "Permission denied"
```bash
chmod 755 /home/chusi/pcmlegacy
chmod 755 /home/chusi/pcmlegacy/instance
```

### "Module not found"
```bash
# Make sure you're using the correct Python version
python3.10 -c "import flask; print('OK')"

# Install missing packages
pip3.10 install --user <package-name>
```

### "Database locked"
- Make sure web app is reloaded
- Check no other process is using the database

---

## Quick Deploy Script

Save this as `deploy.sh` in your project:

```bash
#!/bin/bash
cd /home/chusi/pcmlegacy

# Backup database
cp instance/pcm_store.db instance/pcm_store_backup_$(date +%Y%m%d_%H%M%S).db

# Pull updates
git pull origin main

# Install dependencies
pip3.10 install --user -r requirements.txt

echo "Deployment complete! Reload your web app in the Web tab."
```

Make it executable:
```bash
chmod +x deploy.sh
```

Run it:
```bash
./deploy.sh
```

