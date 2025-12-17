"""
Diagnostic script to verify PythonAnywhere deployment setup
Run this in PythonAnywhere Bash console to check for common issues
Usage: python3 wsgi_diagnostic.py
"""
import sys
import os

def check_path(path_name, path_value):
    """Check if a path exists and is accessible"""
    exists = os.path.exists(path_value)
    readable = os.access(path_value, os.R_OK) if exists else False
    status = "✓" if exists and readable else "✗"
    print(f"{status} {path_name}: {path_value}")
    if exists:
        print(f"   Type: {'Directory' if os.path.isdir(path_value) else 'File'}")
    return exists and readable

def check_module(module_name):
    """Check if a Python module can be imported"""
    try:
        __import__(module_name)
        print(f"✓ Module '{module_name}' can be imported")
        return True
    except ImportError as e:
        print(f"✗ Module '{module_name}' cannot be imported: {e}")
        return False
    except Exception as e:
        print(f"⚠ Module '{module_name}' import error: {e}")
        return False

def main():
    print("=" * 80)
    print("PythonAnywhere Deployment Diagnostic")
    print("=" * 80)
    print()
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print()
    
    # Check project paths
    print("Checking project paths...")
    project_paths = [
        ('Project path (primary)', '/home/chusi/pcmlegacy'),
        ('Project path (alternative)', '/home/chusi/pcm'),
    ]
    
    found_path = None
    for name, path in project_paths:
        if check_path(name, path):
            found_path = path
            break
    
    if not found_path:
        print("\n⚠ Warning: No project path found!")
        print("   Update wsgi_production.py with your actual project path")
        return
    
    print(f"\nUsing project path: {found_path}")
    print()
    
    # Check critical files
    print("Checking critical files...")
    critical_files = [
        ('app.py', os.path.join(found_path, 'app.py')),
        ('wsgi_production.py', os.path.join(found_path, 'wsgi_production.py')),
        ('requirements.txt', os.path.join(found_path, 'requirements.txt')),
        ('config.py', os.path.join(found_path, 'config.py')),
    ]
    
    for name, filepath in critical_files:
        check_path(name, filepath)
    
    print()
    
    # Check portal-sdk directory
    print("Checking portal-sdk...")
    portal_sdk_path = os.path.join(found_path, 'portal-sdk')
    portal_sdk_exists = check_path('portal-sdk directory', portal_sdk_path)
    
    if portal_sdk_exists:
        portalsdk_path = os.path.join(portal_sdk_path, 'portalsdk')
        check_path('portalsdk package', portalsdk_path)
        
        api_py = os.path.join(portalsdk_path, 'api.py')
        init_py = os.path.join(portalsdk_path, '__init__.py')
        check_path('portalsdk/api.py', api_py)
        check_path('portalsdk/__init__.py', init_py)
    
    print()
    
    # Check Python path
    print("Checking Python path (sys.path)...")
    print(f"Current sys.path entries: {len(sys.path)}")
    portal_sdk_in_path = any('portal-sdk' in p for p in sys.path)
    if portal_sdk_in_path:
        print("✓ portal-sdk is in sys.path")
        for p in sys.path:
            if 'portal-sdk' in p:
                print(f"   Found: {p}")
    else:
        print("✗ portal-sdk is NOT in sys.path")
        print("   This will be added automatically by wsgi_production.py")
    
    print()
    
    # Try adding portal-sdk to path and test import
    print("Testing portalsdk import...")
    if portal_sdk_exists:
        if portal_sdk_path not in sys.path:
            sys.path.insert(0, portal_sdk_path)
            print(f"✓ Added {portal_sdk_path} to sys.path for testing")
        
        # Test import
        portalsdk_ok = check_module('portalsdk')
        if portalsdk_ok:
            try:
                from portalsdk import APIContext, APIMethodType, APIRequest
                print("✓ portalsdk classes can be imported")
            except Exception as e:
                print(f"✗ Error importing portalsdk classes: {e}")
    else:
        print("✗ Cannot test portalsdk import - portal-sdk directory not found")
    
    print()
    
    # Check dependencies
    print("Checking dependencies...")
    dependencies = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_mail',
        'flask_wtf',
        'requests',  # Required by portalsdk
        'Crypto',    # From pycryptodome, required by portalsdk
        'dotenv',
    ]
    
    for dep in dependencies:
        check_module(dep)
    
    print()
    
    # Check environment variables
    print("Checking environment variables...")
    secret_key = os.environ.get('SECRET_KEY')
    flask_env = os.environ.get('FLASK_ENV')
    
    if secret_key:
        print(f"✓ SECRET_KEY is set (length: {len(secret_key)})")
    else:
        print("✗ SECRET_KEY is NOT set")
        print("   Set it in PythonAnywhere Web tab → Environment variables")
    
    if flask_env:
        print(f"✓ FLASK_ENV is set to: {flask_env}")
    else:
        print("⚠ FLASK_ENV is not set (will default to development)")
    
    print()
    
    # Summary
    print("=" * 80)
    print("Diagnostic Summary")
    print("=" * 80)
    print("\nIf you see any ✗ marks above, those issues need to be fixed.")
    print("Refer to PYTHONANYWHERE_DEPLOY.md for detailed instructions.")
    print()

if __name__ == '__main__':
    main()
