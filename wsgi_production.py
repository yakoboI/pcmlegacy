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

# Set the path to your PythonAnywhere project directory
# This should match your "Source code" and "Working directory" settings
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

# Import the Flask application
app_import_successful = False
try:
    from app import app as application
    app_import_successful = True
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
