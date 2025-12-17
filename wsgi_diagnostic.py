"""
Diagnostic WSGI file - Use this temporarily to check your Python environment
Copy this to /var/www/chusi_pythonanywhere_com_wsgi.py temporarily
"""
import sys
import os

path = '/home/chusi/pcmlegacy'
if path not in sys.path:
    sys.path.insert(0, path)
os.chdir(path)

# Diagnostic information
from flask import Flask
application = Flask(__name__)

@application.route('/')
def diagnostic():
    info = []
    info.append(f"<h1>Python Environment Diagnostic</h1>")
    info.append(f"<h2>Python Path:</h2>")
    info.append(f"<pre>{sys.executable}</pre>")
    info.append(f"<h2>Python Version:</h2>")
    info.append(f"<pre>{sys.version}</pre>")
    info.append(f"<h2>sys.path:</h2>")
    info.append(f"<pre>{chr(10).join(sys.path)}</pre>")
    info.append(f"<h2>Working Directory:</h2>")
    info.append(f"<pre>{os.getcwd()}</pre>")
    info.append(f"<h2>Virtualenv:</h2>")
    venv_path = os.environ.get('VIRTUAL_ENV', 'Not set')
    info.append(f"<pre>{venv_path}</pre>")
    
    info.append(f"<h2>Package Check:</h2>")
    packages_to_check = ['flask', 'flask_mail', 'flask_login', 'flask_sqlalchemy']
    for pkg in packages_to_check:
        try:
            mod = __import__(pkg)
            version = getattr(mod, '__version__', 'installed')
            info.append(f"<p>✓ {pkg}: {version}</p>")
        except ImportError:
            info.append(f"<p>✗ {pkg}: NOT INSTALLED</p>")
    
    return "<br>".join(info)

