# Quick Fix: "No module named 'portalsdk'" Error

## What Was Fixed

✅ **Updated `wsgi_production.py`** - Automatically adds `portal-sdk` directory to Python's module search path  
✅ **Updated `requirements.txt`** - Added missing `requests` dependency (required by portalsdk)  
✅ **Enhanced error messages** - Better guidance when portalsdk import fails  
✅ **Created diagnostic script** - `wsgi_diagnostic.py` to verify setup  

## Immediate Action Required

### 1. Copy Updated WSGI File to PythonAnywhere

Copy the updated `wsgi_production.py` content to your PythonAnywhere WSGI file:
- **Location**: `/var/www/yourusername_pythonanywhere_com_wsgi.py`
- **Or edit via**: PythonAnywhere Dashboard → Web tab → WSGI configuration file

### 2. Install Missing Dependency

In PythonAnywhere Bash console:

```bash
cd /home/chusi/pcmlegacy  # or your project path
pip install --user requests>=2.18.4
```

Or install all dependencies:
```bash
pip install --user -r requirements.txt
```

### 3. Verify Portal-SDK Directory Exists

```bash
ls -la /home/chusi/pcmlegacy/portal-sdk/
```

Should show:
```
portalsdk/
setup.py
requirements.txt
```

### 4. Reload Web App

1. Go to PythonAnywhere Dashboard → **Web** tab
2. Click **"Reload"** button
3. Check error log if issues persist

## Quick Test

Run the diagnostic script in PythonAnywhere Bash:

```bash
cd /home/chusi/pcmlegacy
python3 wsgi_diagnostic.py
```

This will check:
- ✅ Project paths
- ✅ Critical files
- ✅ Portal-sdk directory
- ✅ Python module imports
- ✅ Dependencies
- ✅ Environment variables

## What Changed in Code

### wsgi_production.py (Lines 91-104)
Added automatic path addition for `portal-sdk`:
```python
# Add portal-sdk directory to Python path (required for portalsdk module)
portal_sdk_path = os.path.join(path, 'portal-sdk')
if os.path.exists(portal_sdk_path) and portal_sdk_path not in sys.path:
    sys.path.insert(0, portal_sdk_path)
    print(f"✓ Added portal-sdk directory to Python path: {portal_sdk_path}")
```

### requirements.txt
Added missing dependency:
```
requests>=2.18.4
```

## Still Having Issues?

1. **Check error logs**: PythonAnywhere Dashboard → Web tab → Error log
2. **Run diagnostic**: `python3 wsgi_diagnostic.py`
3. **Verify paths**: Ensure `portal-sdk` directory exists in project root
4. **Check dependencies**: `pip list | grep -E "requests|pycryptodome"`

## Full Documentation

See `PYTHONANYWHERE_DEPLOY.md` for comprehensive deployment guide.

