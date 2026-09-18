"""
AutoRecon Agentic™ — Main Streamlit Entrypoint.
Root streamlit_app.py for standard Streamlit deployments.
"""

import sys
from pathlib import Path

# Ensure root is on sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Execute the core Streamlit application
from src import app
