"""
Django initialization helper
Call this before using Django models in standalone scripts
"""
import os
import django

def setup_django():
    """Initialize Django for standalone use"""
    # Add parent directory to path if needed
    import sys
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
    
    # Setup Django
    django.setup()


