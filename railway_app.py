#!/usr/bin/env python
"""
Single-file solution for Railway - runs both healthcheck server and Django
"""
import os
import sys
import subprocess
import time
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
HEALTH_PORT = int(os.environ.get('HEALTH_PORT', 8081))
DJANGO_PORT = int(os.environ.get('PORT', 8080))

print("=" * 50)
print(f"🚀 Starting CrownieVerse on Railway")
print(f"📊 Healthcheck port: {HEALTH_PORT}")
print(f"🌐 Django port: {DJANGO_PORT}")
print("=" * 50)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silence logs
    
    def do_GET(self):
        print(f"✅ Healthcheck received at {self.path}")
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_server():
    """Run healthcheck server"""
    try:
        server = HTTPServer(('0.0.0.0', HEALTH_PORT), HealthCheckHandler)
        print(f"✅ Healthcheck server running on port {HEALTH_PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Healthcheck server failed: {e}")

def test_health_server():
    """Test if healthcheck server is responding"""
    time.sleep(2)  # Give it time to start
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', HEALTH_PORT))
        sock.close()
        if result == 0:
            print(f"✅ Healthcheck server is accepting connections on port {HEALTH_PORT}")
            return True
        else:
            print(f"❌ Healthcheck server is NOT accepting connections on port {HEALTH_PORT}")
            return False
    except Exception as e:
        print(f"❌ Failed to test healthcheck server: {e}")
        return False

def run_migrations():
    """Run Django migrations"""
    print("🗄️ Running migrations...")
    result = subprocess.run(['python', 'manage.py', 'migrate', '--noinput'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Migrations complete")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ Migrations failed")
        print(result.stderr)
        sys.exit(1)

def collect_static():
    """Collect static files"""
    print("📦 Collecting static files...")
    result = subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Static files collected")
    else:
        print("❌ Static collection failed")
        print(result.stderr)
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
    os.execvp('gunicorn', cmd)

if __name__ == '__main__':
    try:
        # Start healthcheck server in background thread
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        # Test if healthcheck server is working
        if not test_health_server():
            print("⚠️ Healthcheck server not responding, but continuing...")
        
        # Run migrations and collectstatic
        run_migrations()
        collect_static()
        
        # Start Django
        run_django()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)