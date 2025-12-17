"""
Production WSGI Configuration for PythonAnywhere
This file is optimized for PythonAnywhere hosting with SQLite database.

Copy this content to your PythonAnywhere WSGI file:
/var/www/yourusername_pythonanywhere_com_wsgi.py
"""
import sys
import os

# Set the path to your PythonAnywhere project directory
# This should match your "Source code" and "Working directory" settings
path = '/home/chusi/pcmlegacy'

# Add the path to Python path if not already there
if path not in sys.path:
    sys.path.insert(0, path)

# Load .env file BEFORE checking SECRET_KEY
# This allows SECRET_KEY to be loaded from .env file in the project directory
try:
    from dotenv import load_dotenv
    # Load .env file from the project directory
    env_path = os.path.join(path, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded .env file from: {env_path}")
    else:
        print(f"⚠ .env file not found at: {env_path}")
        # Try alternative path
        alt_env_path = os.path.join('/home/chusi/pcm', '.env')
        if os.path.exists(alt_env_path):
            load_dotenv(alt_env_path)
            print(f"✓ Loaded .env file from alternative path: {alt_env_path}")
except ImportError:
    print("⚠ python-dotenv not installed - .env file will not be loaded")
    print("  Install it with: pip install python-dotenv")

# SECURITY NOTE: Do NOT hardcode SECRET_KEY here!
# SECRET_KEY can be set via:
# 1. PythonAnywhere Web tab → Environment variables (recommended for production)
# 2. .env file in the project directory (convenient for development)
# Hardcoding SECRET_KEY in version control is a security vulnerability.
# The config.py module will raise ValueError if SECRET_KEY is missing in production.

# IMPORTANT: Check SECRET_KEY AFTER loading .env file but BEFORE setting FLASK_ENV to production
# This prevents config.py from raising an error during import
SECRET_KEY_SET = bool(os.environ.get('SECRET_KEY'))

if SECRET_KEY_SET:
    # Only set production environment if SECRET_KEY is set
    os.environ['FLASK_ENV'] = 'production'
    print("✓ SECRET_KEY found - setting FLASK_ENV to production")
else:
    # Don't set FLASK_ENV to production - this prevents config.py validation error
    # We'll create an error app instead that explains the issue
    print("⚠ SECRET_KEY not set - creating error app instead of importing main app")

# Change to the application directory
try:
    os.chdir(path)
    print(f"✓ Changed to directory: {path}")
except OSError as e:
    print(f"⚠ Warning: Could not change to {path}: {e}")
    # Try alternative path
    alt_path = '/home/chusi/pcm'
    if os.path.exists(alt_path):
        try:
            path = alt_path
            if path not in sys.path:
                sys.path.insert(0, path)
            os.chdir(path)
            print(f"✓ Changed to alternative directory: {path}")
        except OSError as e2:
            print(f"✗ Error: Could not change to alternative directory {alt_path}: {e2}")
            print("⚠ Continuing with original path, but app may not work correctly")
    else:
        print(f"⚠ Warning: Alternative path {alt_path} does not exist")

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

# Add portal-sdk directory to Python path (required for portalsdk module)
portal_sdk_path = os.path.join(path, 'portal-sdk')
portal_sdk_available = False

# Try primary path first
if os.path.exists(portal_sdk_path) and portal_sdk_path not in sys.path:
    sys.path.insert(0, portal_sdk_path)
    print(f"✓ Added portal-sdk directory to Python path: {portal_sdk_path}")
    portal_sdk_available = True
elif portal_sdk_path in sys.path:
    portal_sdk_available = True  # Already in path
else:
    # Try alternative path
    alt_portal_sdk_path = os.path.join('/home/chusi/pcm', 'portal-sdk')
    if os.path.exists(alt_portal_sdk_path) and alt_portal_sdk_path not in sys.path:
        sys.path.insert(0, alt_portal_sdk_path)
        print(f"✓ Added portal-sdk directory from alternative path: {alt_portal_sdk_path}")
        portal_sdk_available = True
    elif alt_portal_sdk_path in sys.path:
        portal_sdk_available = True  # Already in path

# Only warn if portalsdk is not available via any path
if not portal_sdk_available:
    alt_portal_sdk_path = os.path.join('/home/chusi/pcm', 'portal-sdk')
    if not os.path.exists(portal_sdk_path) and not os.path.exists(alt_portal_sdk_path):
        print(f"⚠ Warning: portal-sdk directory not found at: {portal_sdk_path}")
        print(f"  Also checked alternative path: {alt_portal_sdk_path}")
        print(f"  The portalsdk module may not be importable. Check that portal-sdk directory exists.")

# Check if SECRET_KEY is set before importing app
# This check happens after path setup so Flask can be imported if needed
if not SECRET_KEY_SET:
    error_msg = """
    SECRET_KEY is not set!
    
    SECRET_KEY can be set in two ways:
    
    Option 1: Using .env file (recommended if you have one)
    - Make sure .env file exists in: /home/chusi/pcmlegacy/.env
    - Add line: SECRET_KEY=your-strong-secret-key-here
    
    Option 2: Using PythonAnywhere Environment Variables
    1. Go to PythonAnywhere → Web tab
    2. Click on your web app
    3. Scroll to "Environment variables" section
    4. Add: SECRET_KEY=your-strong-secret-key-here
    5. Click "Reload" button
    
    Generate a strong secret key using:
    python3 -c "import secrets; print(secrets.token_hex(32))"
    """
    print("=" * 80)
    print(error_msg)
    print("=" * 80)
    
    # Create a minimal error app
    try:
        from flask import Flask
        application = Flask(__name__)
        @application.route('/')
        def error():
            return """
            <h1>Configuration Error</h1>
            <p><strong>SECRET_KEY is not set!</strong></p>
            <h2>How to Fix:</h2>
            <p>SECRET_KEY can be set in two ways:</p>
            <h3>Option 1: Using .env file (if you have one)</h3>
            <ol>
                <li>Make sure <code>.env</code> file exists in: <code>/home/chusi/pcmlegacy/.env</code></li>
                <li>Add line: <code>SECRET_KEY=your-strong-secret-key-here</code></li>
                <li>Make sure <code>python-dotenv</code> is installed</li>
            </ol>
            <h3>Option 2: Using PythonAnywhere Environment Variables</h3>
            <ol>
                <li>Go to PythonAnywhere → <strong>Web</strong> tab</li>
                <li>Click on your web app</li>
                <li>Scroll to <strong>"Environment variables"</strong> section</li>
                <li>Add: <code>SECRET_KEY=your-strong-secret-key-here</code></li>
                <li>Click <strong>"Reload"</strong> button</li>
            </ol>
            <h2>Generate a Strong Secret Key:</h2>
            <p>Run this command in PythonAnywhere Bash console:</p>
            <pre>python3 -c "import secrets; print(secrets.token_hex(32))"</pre>
            <p>Copy the output and use it as your SECRET_KEY value.</p>
            """, 500
    except ImportError:
        # If Flask is not available, create a simple WSGI app
        def application(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'text/html')]
            body = """
            <h1>Configuration Error</h1>
            <p><strong>SECRET_KEY is not set!</strong></p>
            <p>Please set SECRET_KEY either in:</p>
            <ul>
                <li>.env file at /home/chusi/pcmlegacy/.env, or</li>
                <li>PythonAnywhere Web tab → Environment variables</li>
            </ul>
            """
            start_response(status, headers)
            return [body.encode()]

# Import the Flask application
# Skip import if SECRET_KEY is not set (error app already created above)
app_import_successful = False
import_error_message = None

if SECRET_KEY_SET:
    try:
        from app import app as application
        app_import_successful = True
        print("✓ Flask app imported successfully")
    except Exception as e:
        import_error_message = str(e)
        print(f"✗ Error importing Flask app: {e}")
        import traceback
        traceback.print_exc()
        # Create a minimal app to show error instead of "Hello from Flask!"
        try:
            from flask import Flask
            application = Flask(__name__)
            @application.route('/')
            def error():
                error_msg = import_error_message or "Unknown error"
                return f"""
                <h1>Configuration Error</h1>
                <p>Could not import Flask application from app.py</p>
                <p><strong>Error:</strong> {error_msg}</p>
                <h2>Please check:</h2>
                <ul>
                    <li>The path in wsgi_production.py matches your PythonAnywhere directory</li>
                    <li>All dependencies are installed in your virtualenv (run: pip install -r requirements.txt)</li>
                    <li>The portal-sdk directory exists in your project root</li>
                    <li>app.py exists in the correct location</li>
                    <li>SECRET_KEY environment variable is set in PythonAnywhere Web tab</li>
                    <li>If error mentions 'portalsdk', ensure portal-sdk directory is present and contains portalsdk package</li>
                </ul>
                <p>Check the error log in PythonAnywhere for more details.</p>
                """, 500
        except ImportError:
            # Fallback if Flask is not available
            def application(environ, start_response):
                status = '500 Internal Server Error'
                headers = [('Content-Type', 'text/html')]
                error_msg = import_error_message or "Unknown error"
                body = f"""
                <h1>Configuration Error</h1>
                <p>Could not import Flask application from app.py</p>
                <p><strong>Error:</strong> {error_msg}</p>
                <p>Please check the error log in PythonAnywhere for more details.</p>
                """
                start_response(status, headers)
                return [body.encode()]
else:
    print("⚠ Skipping app import - SECRET_KEY not set (error app created)")

# Initialize database (safe migration that preserves data)
# Only attempt if app import was successful
if app_import_successful:
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
else:
    print("⚠ Skipping database initialization - app module not imported successfully")