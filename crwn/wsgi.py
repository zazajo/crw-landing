"""
WSGI config for crwn project.
"""

import os
import sys
import time
import traceback

print("=" * 60)
print("WSGI.PY STARTING - STEP 1")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print(f"Environment variables:")
for key in ['DJANGO_SETTINGS_MODULE', 'PORT', 'SECRET_KEY', 'DATABASE_URL']:
    print(f"  {key}: {'[SET]' if os.environ.get(key) else '[MISSING]'}")
print("=" * 60)

try:
    print("STEP 2: Setting Django settings module...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crwn.settings')
    
    print("STEP 3: Importing Django...")
    import django
    print(f"Django version: {django.get_version()}")
    
    print("STEP 4: Setting up Django...")
    django.setup()
    print("✓ Django setup complete")
    
    print("STEP 5: Importing get_wsgi_application...")
    from django.core.wsgi import get_wsgi_application
    
    print("STEP 6: Creating WSGI application...")
    application = get_wsgi_application()
    print("✓ WSGI application created successfully!")
    
    print("STEP 7: Testing database connection...")
    from django.db import connections
    from django.db.utils import OperationalError
    
    db_conn = connections['default']
    try:
        c = db_conn.cursor()
        c.execute("SELECT 1")
        c.fetchone()
        print("✓ Database connection successful")
    except OperationalError as e:
        print(f"⚠️ Database connection failed: {e}")
        print("This might be normal if migrations haven't run yet")
    
    print("=" * 60)
    print("WSGI.PY COMPLETED SUCCESSFULLY")
    print("=" * 60)
    
except Exception as e:
    print("=" * 60)
    print("ERROR IN WSGI.PY:")
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc(file=sys.stdout)
    print("=" * 60)
    raise