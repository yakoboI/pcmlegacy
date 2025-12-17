# PythonAnywhere Deployment - Method 3

## Step-by-Step Commands

Run these commands **one by one** in PythonAnywhere's Bash console:

### Step 1: Navigate to Your Project Directory
```bash
cd /home/chusi/pcmlegacy
```

### Step 2: Initialize Git Repository
```bash
git init
```

### Step 3: Rename Branch to Main (if Git created 'master')
```bash
git branch -m main
```

### Step 4: Add GitHub Remote
```bash
git remote add origin https://github.com/yakoboI/pcmlegacy.git
```

### Step 5: Fetch from GitHub
```bash
git fetch origin
```

### Step 6: Set Upstream and Pull
```bash
git branch --set-upstream-to=origin/main main
git pull origin main
```

**OR** if you prefer to checkout:
```bash
git checkout -b main origin/main
```

### Step 7: Install Dependencies
```bash
# Replace 3.10 with your Python version (check in Web tab)
pip3.10 install --user -r requirements.txt
```

### Step 8: Verify Installation
```bash
python3.10 -c "import flask; print('✓ Flask installed')"
python3.10 -c "import flask_mail; print('✓ Flask-Mail installed')"
python3.10 -c "import flask_login; print('✓ Flask-Login installed')"
```

### Step 9: Update WSGI File

1. Go to **Web** tab in PythonAnywhere
2. Click on your web app
3. Click **WSGI configuration file** link (`/var/www/chusi_pythonanywhere_com_wsgi.py`)
4. Replace entire content with this:

```python
"""
Production WSGI Configuration for PythonAnywhere
This file is optimized for PythonAnywhere hosting with SQLite database.

Copy this content to your PythonAnywhere WSGI file:
/var/www/yourusername_pythonanywhere_com_wsgi.py
"""
import sys
import os

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Update this path to match your actual PythonAnywhere directory
# Common paths: /home/chusi/pcm or /home/chusi/pcmlegacy
path = '/home/chusi/pcmlegacy'

# Add the path to Python path if not already there
if path not in sys.path:
    sys.path.insert(0, path)

# Change to the application directory
try:
    os.chdir(path)
    print(f"✓ Changed to directory: {path}")
except OSError as e:
    print(f"⚠ Warning: Could not change to {path}: {e}")
    # Try alternative path
    alt_path = '/home/chusi/pcm'
    if os.path.exists(alt_path):
        path = alt_path
        if path not in sys.path:
            sys.path.insert(0, path)
        os.chdir(path)
        print(f"✓ Changed to alternative directory: {path}")

# Add virtualenv site-packages to path if virtualenv exists
venv_path = os.path.join(path, 'venv')
if os.path.exists(venv_path):
    # Try common Python versions
    for python_version in ['python3.12', 'python3.11', 'python3.10', 'python3.9']:
        site_packages = os.path.join(venv_path, 'lib', python_version, 'site-packages')
        if os.path.exists(site_packages) and site_packages not in sys.path:
            sys.path.insert(0, site_packages)
            print(f"✓ Added virtualenv site-packages: {site_packages}")
            break

# Import the Flask application
try:
    from app import app as application
    print("✓ Flask app imported successfully")
except ImportError as e:
    print(f"✗ Error importing Flask app: {e}")
    import traceback
    traceback.print_exc()
    # Create a minimal app to show error instead of "Hello from Flask!"
    from flask import Flask
    application = Flask(__name__)
    @application.route('/')
    def error():
        return f"""
        <h1>Configuration Error</h1>
        <p>Could not import Flask application from app.py</p>
        <p>Error: {str(e)}</p>
        <p>Please check:</p>
        <ul>
            <li>The path in wsgi_production.py matches your PythonAnywhere directory</li>
            <li>All dependencies are installed in your virtualenv</li>
            <li>app.py exists in the correct location</li>
        </ul>
        <p>Check the error log in PythonAnywhere for more details.</p>
        """, 500

# Initialize database (safe migration that preserves data)
try:
    with application.app_context():
        # Ensure instance directory exists for SQLite database
        instance_path = os.path.join(path, 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
            print(f"✓ Created instance directory: {instance_path}")
        
        from app import init_db
        init_db()
        print("✓ Database initialized safely - all data preserved")
except Exception as e:
    print(f"⚠ Database initialization warning: {e}")
    # Don't fail if database init has issues - app should still work
    import traceback
    traceback.print_exc()
```

5. Click **Save**

### Step 10: Configure Static Files

In **Web** tab, under **Static files**:
- **URL:** `/static/`
- **Directory:** `/home/chusi/pcmlegacy/static/`

Click **Add a new static files mapping** if needed.

### Step 11: Set Environment Variables

In **Web** tab, under **Environment variables**, add:
```
FLASK_ENV=production
SECRET_KEY=your-strong-secret-key-here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MPESA_API_KEY=your-mpesa-api-key
MPESA_PUBLIC_KEY=your-mpesa-public-key
MPESA_SERVICE_PROVIDER_CODE=your-service-provider-code
MPESA_COUNTRY=TZN
MPESA_CURRENCY=TZS
MPESA_ENV=sandbox
```

### Step 12: Reload Web App

1. Go to **Web** tab
2. Click the green **Reload** button
3. Wait a few seconds
4. Click **Error log** to check for any errors

### Step 13: Test Your Website

Visit your website URL (e.g., `https://chusi.pythonanywhere.com`) and verify:
- ✅ Homepage loads
- ✅ Can navigate pages
- ✅ Login works (if applicable)
- ✅ Static files load (CSS, images)

---

## Troubleshooting

### If you get "fatal: not a git repository"
You're not in the right directory. Run:
```bash
cd /home/chusi/pcmlegacy
pwd  # Should show /home/chusi/pcmlegacy
```

### If you get "remote origin already exists"
Remove it first:
```bash
git remote remove origin
git remote add origin https://github.com/yakoboI/pcmlegacy.git
```

### If Git created 'master' branch instead of 'main'
After `git init`, rename it:
```bash
git branch -m main
```

### If packages don't install
Check your Python version in Web tab, then use the correct pip:
```bash
# For Python 3.10
pip3.10 install --user -r requirements.txt

# For Python 3.11
pip3.11 install --user -r requirements.txt
```

### If you see import errors
Check error log in Web tab and install missing packages:
```bash
pip3.10 install --user <package-name>
```

---

## Future Updates

To pull latest changes from GitHub:

```bash
cd /home/chusi/pcmlegacy

# Backup database first!
cp instance/pcm_store.db instance/pcm_store_backup_$(date +%Y%m%d_%H%M%S).db

# Pull updates
git pull origin main

# Install new dependencies (if any)
pip3.10 install --user -r requirements.txt

# Reload web app in Web tab
```

---

## Quick Reference

**Project Directory:** `/home/chusi/pcmlegacy`  
**Database Location:** `/home/chusi/pcmlegacy/instance/pcm_store.db`  
**WSGI File:** `/var/www/chusi_pythonanywhere_com_wsgi.py`  
**GitHub Repo:** `https://github.com/yakoboI/pcmlegacy.git`
