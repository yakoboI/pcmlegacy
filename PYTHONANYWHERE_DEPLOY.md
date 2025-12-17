# PythonAnywhere Deployment Guide

## Quick Fix for "No module named 'portalsdk'" Error

This guide addresses the common error: **"Could not import Flask application from app.py - Error: No module named 'portalsdk'"**

## Root Cause

The `portalsdk` module is a **local package** located in the `portal-sdk/` directory. Python cannot find it because:
1. The `portal-sdk` directory is not added to Python's module search path (`sys.path`)
2. Missing dependencies required by `portalsdk` (specifically `requests`)

## Solution Steps

### Step 1: Verify Project Structure

Ensure your PythonAnywhere project has this structure:
```
/home/chusi/pcmlegacy/  (or /home/chusi/pcm/)
├── app.py
├── wsgi_production.py
├── requirements.txt
├── portal-sdk/
│   ├── portalsdk/
│   │   ├── __init__.py
│   │   └── api.py
│   └── setup.py
└── ... (other files)
```

### Step 2: Update WSGI File

The `wsgi_production.py` file has been updated to automatically add the `portal-sdk` directory to Python's path. 

**Copy the updated `wsgi_production.py` content to your PythonAnywhere WSGI file:**
- Location: `/var/www/yourusername_pythonanywhere_com_wsgi.py`
- Or edit via: PythonAnywhere Dashboard → Web tab → WSGI configuration file

### Step 3: Install Dependencies

In PythonAnywhere Bash console, run:

```bash
# Navigate to your project directory
cd /home/chusi/pcmlegacy  # or /home/chusi/pcm

# Activate virtualenv (if using one)
source venv/bin/activate  # or your venv path

# Install all dependencies including requests (required by portalsdk)
pip install --user -r requirements.txt

# Verify portalsdk dependencies are installed
pip show requests pycryptodome
```

### Step 4: Verify Portal-SDK Directory

Ensure the `portal-sdk` directory exists and contains the `portalsdk` package:

```bash
# Check if portal-sdk exists
ls -la /home/chusi/pcmlegacy/portal-sdk/

# Should show:
# portalsdk/
# setup.py
# requirements.txt
```

### Step 5: Set Environment Variables

In PythonAnywhere Dashboard:
1. Go to **Web** tab
2. Click on your web app
3. Scroll to **"Environment variables"** section
4. Add: `SECRET_KEY=your-strong-secret-key-here`
5. Click **"Reload"** button

**Generate a strong secret key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 6: Reload Web App

After making changes:
1. Go to PythonAnywhere Dashboard → **Web** tab
2. Click the **"Reload"** button for your web app
3. Check the error log if issues persist

## Troubleshooting

### Error: "No module named 'portalsdk'"

**Check:**
1. ✅ `portal-sdk` directory exists in project root
2. ✅ `wsgi_production.py` includes code to add `portal-sdk` to `sys.path`
3. ✅ All dependencies installed: `pip install -r requirements.txt`
4. ✅ Web app reloaded after changes

**Debug in PythonAnywhere Bash:**
```bash
cd /home/chusi/pcmlegacy
python3 -c "import sys; sys.path.insert(0, 'portal-sdk'); from portalsdk import APIContext; print('✓ portalsdk imports successfully')"
```

### Error: "No module named 'requests'"

**Fix:**
```bash
pip install --user requests>=2.18.4
```

### Error: "No module named 'Crypto'"

**Fix:**
```bash
pip install --user pycryptodome>=3.23.0
```

### Check Error Logs

View detailed error logs:
1. PythonAnywhere Dashboard → **Web** tab
2. Click **"Error log"** link
3. Look for import errors and traceback details

## Manual Path Addition (Alternative)

If the automatic path addition in `wsgi_production.py` doesn't work, you can manually add it at the top of your WSGI file:

```python
import sys
import os

# Add portal-sdk to Python path
project_path = '/home/chusi/pcmlegacy'  # Update with your actual path
portal_sdk_path = os.path.join(project_path, 'portal-sdk')
if portal_sdk_path not in sys.path:
    sys.path.insert(0, portal_sdk_path)
```

## Alternative: Install Portal-SDK as Package

If you prefer to install `portalsdk` as a package:

```bash
cd /home/chusi/pcmlegacy/portal-sdk
pip install --user -e .
```

This installs it in "editable" mode, so changes are reflected immediately.

## Verification Checklist

Before deploying, verify:

- [ ] `portal-sdk/portalsdk/__init__.py` exists
- [ ] `portal-sdk/portalsdk/api.py` exists
- [ ] `requirements.txt` includes `requests>=2.18.4`
- [ ] `requirements.txt` includes `pycryptodome>=3.23.0`
- [ ] `wsgi_production.py` adds `portal-sdk` to `sys.path`
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] `SECRET_KEY` environment variable set in PythonAnywhere
- [ ] Web app reloaded after changes
- [ ] Error log checked for any remaining issues

## Additional Resources

- [PythonAnywhere WSGI Documentation](https://help.pythonanywhere.com/pages/Flask/)
- [Python Module Search Path](https://docs.python.org/3/tutorial/modules.html#the-module-search-path)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/latest/deploying/)

## Support

If issues persist after following this guide:
1. Check PythonAnywhere error logs for detailed error messages
2. Verify Python version compatibility (Python 3.9+ recommended)
3. Ensure virtualenv is properly activated
4. Check file permissions on `portal-sdk` directory

