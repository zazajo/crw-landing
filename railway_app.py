#!/usr/bin/env python
"""
Single-file solution for Railway - runs both healthcheck server and Django
"""
import os
import sys
import subprocess
import time
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
HEALTH_PORT = int(os.environ.get('HEALTH_PORT', 8081))
DJANGO_PORT = int(os.environ.get('PORT', 8080))

class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silence logs
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
        print(f"✅ Healthcheck OK at {time.strftime('%H:%M:%S')}")
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_server():
    """Run healthcheck server in a separate process"""
    server = HTTPServer(('0.0.0.0', HEALTH_PORT), HealthCheckHandler)
    print(f"✅ Healthcheck server running on port {HEALTH_PORT}")
    server.serve_forever()

def run_migrations():
    """Run Django migrations"""
    print("🗄️ Running migrations...")
    result = subprocess.run(['python', 'manage.py', 'migrate', '--noinput'])
    if result.returncode == 0:
        print("✅ Migrations complete")
    else:
        print("❌ Migrations failed")
        sys.exit(1)

def collect_static():
    """Collect static files"""
    print("📦 Collecting static files...")
    result = subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'])
    if result.returncode == 0:
        print("✅ Static files collected")
    else:
        print("❌ Static collection failed")
        sys.exit(1)

def run_django():
    """Run Django with gunicorn"""
    print(f"🚀 Starting Django on port {DJANGO_PORT}")
    cmd = [
        'gunicorn', 'crwn.wsgi:application',
        '--bind', f'0.0.0.0:{DJANGO_PORT}',
        '--workers', '1',
        '--threads', '1',
        '--timeout', '120',
        '--log-level', 'debug',
        '--access-logfile', '-',
        '--error-logfile', '-'
    ]
    os.execvp('gunicorn', cmd)  # Replace process with gunicorn

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting CrownieVerse on Railway")
    print("=" * 50)
    
    # Start healthcheck server in background thread
    import threading
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Give healthcheck server time to start
    time.sleep(2)
    
    # Run migrations and collectstatic
    run_migrations()
    collect_static()
    
    # Start Django
    run_django()