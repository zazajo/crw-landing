"""
WSGI config for crwn project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys
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
    print("STEP 2: Importing Django...")
    from django.core.wsgi import get_wsgi_application
    print("✓ Django imported successfully")
    
    print("STEP 3: Setting settings module...")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crwn.settings')
    print(f"✓ Settings module set to: {os.environ['DJANGO_SETTINGS_MODULE']}")
    
    print("STEP 4: Creating WSGI application...")
    application = get_wsgi_application()
    print("✓ WSGI application created successfully!")
    
    print("STEP 5: Checking if application is callable...")
    if callable(application):
        print("✓ Application is callable")
    else:
        print("✗ Application is NOT callable")
    
except Exception as e:
    print("=" * 60)
    print("ERROR IN WSGI.PY:")
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc(file=sys.stdout)
    print("=" * 60)
    raise

print("=" * 60)
print("WSGI.PY COMPLETED SUCCESSFULLY")
print("=" * 60)