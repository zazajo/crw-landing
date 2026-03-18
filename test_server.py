import http.server
import socketserver
import os

PORT = int(os.environ.get('PORT', 8000))

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

Handler.extensions_map.update({
    '.html': 'text/html',
    '.txt': 'text/plain',
})

print(f"Starting test server on port {PORT}")
print(f" serving directory: {os.getcwd()}")
print("Test server is ready!")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server running at http://0.0.0.0:{PORT}/")
    httpd.serve_forever()