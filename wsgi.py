"""
WSGI Configuration for PythonAnywhere
This file is used by PythonAnywhere to serve your Flask application.
"""
import sys
import os
path = '/home/yourusername/pcmlegacy'
if path not in sys.path:
    sys.path.insert(0, path)
os.chdir(path)
from app import app as application
try:
    with application.app_context():
        from app import init_db
        init_db()
except Exception as e:
    print(f"Database initialization error: {e}")
