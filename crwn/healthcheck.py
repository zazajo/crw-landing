from django.http import HttpResponse
from django.db import connections
from django.db.utils import OperationalError
import os

def healthcheck(request):
    """Simple healthcheck endpoint for Railway"""
    # Check database connection
    db_conn = connections['default']
    try:
        c = db_conn.cursor()
        c.execute("SELECT 1")
        c.fetchone()
        db_status = "healthy"
    except OperationalError:
        db_status = "unhealthy"
    
    # Check environment
    status = {
        "status": "healthy",
        "database": db_status,
        "debug": os.getenv('DEBUG', 'False'),
    }
    
    if db_status == "unhealthy":
        return HttpResponse("Database unhealthy", status=500)
    
    return HttpResponse("OK", status=200)