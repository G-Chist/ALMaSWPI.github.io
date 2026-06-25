"""WSGI entry point for PythonAnywhere.
Point your web app's "Code → WSGI configuration file" at this file.
Set OPENCODE_API_KEY via the "Environment variables" section on PythonAnywhere.
"""

import os, sys

# Add this directory to the path so api.py can import
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from api import app as application
