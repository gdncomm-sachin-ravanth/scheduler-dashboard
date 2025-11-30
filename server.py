#!/usr/bin/env python3
"""
Simple HTTP server to serve the dashboard and provide API endpoint to refresh data.
"""

import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import os


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard server."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # API endpoint to refresh data
        if path == '/api/refresh':
            self.handle_refresh()
            return
        
        # Serve static files
        if path == '/' or path == '/scheduler-dashboard.html':
            path = '/scheduler-dashboard.html'
        
        # Remove leading slash for file path
        file_path = Path(__file__).parent / path.lstrip('/')
        
        # Security: prevent directory traversal
        try:
            file_path.resolve().relative_to(Path(__file__).parent.resolve())
        except ValueError:
            self.send_error(403, "Forbidden")
            return
        
        if not file_path.exists():
            self.send_error(404, "File not found")
            return
        
        # Determine content type
        content_type = 'text/html'
        if file_path.suffix == '.json':
            content_type = 'application/json'
        elif file_path.suffix == '.css':
            content_type = 'text/css'
        elif file_path.suffix == '.js':
            content_type = 'application/javascript'
        
        # Read and send file
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/refresh-today':
            self.handle_refresh_today()
            return
        else:
            self.send_error(404, "Not found")
            return
    
    def handle_refresh_today(self):
        """Handle the refresh today API endpoint."""
        try:
            # Execute the fetch today script
            script_path = Path(__file__).parent / 'fetch_today_data.py'
            result = subprocess.run(
                ['python3', str(script_path)],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                # Read the output to get record count
                output_lines = result.stdout.strip().split('\n')
                today_count = 0
                
                for line in output_lines:
                    if 'Saved' in line and 'today-data.json' in line:
                        # Extract number from "Saved X records to today-data.json"
                        try:
                            today_count = int(line.split()[1])
                        except:
                            pass
                
                response = {
                    'success': True,
                    'message': 'Today\'s data refreshed successfully',
                    'today_records': today_count,
                    'output': result.stdout
                }
            else:
                response = {
                    'success': False,
                    'message': 'Failed to refresh today\'s data',
                    'error': result.stderr,
                    'output': result.stdout
                }
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except subprocess.TimeoutExpired:
            response = {
                'success': False,
                'message': 'Request timed out'
            }
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            response = {
                'success': False,
                'message': f'Error: {str(e)}'
            }
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to customize log format."""
        print(f"[{self.address_string()}] {format % args}")


def main():
    """Start the HTTP server."""
    port = int(os.environ.get('PORT', 8000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    print(f"🚀 Dashboard server running on http://localhost:{port}")
    print(f"📊 Open http://localhost:{port}/scheduler-dashboard.html in your browser")
    print(f"🔄 Use the refresh button in the dashboard to update data")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        httpd.shutdown()


if __name__ == '__main__':
    main()

