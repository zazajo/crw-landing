#!/usr/bin/env python
"""
Simple HTTP server for Railway healthcheck
This runs on a different port and ALWAYS returns 200 OK
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import sys
import socket

PORT = int(os.environ.get('HEALTH_PORT', 8081))  # Different port from main app

class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence logs
        pass
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
        print(f"✅ Healthcheck received at {self.path}")
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    print(f"🚀 Starting healthcheck server on port {PORT}")
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down healthcheck server")
        server.shutdown()