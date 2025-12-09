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
        elif path == '/api/update-sso-token':
            self.handle_update_sso_token()
            return
        elif path == '/api/validate-sales-funnel':
            self.handle_validate_sales_funnel()
            return
        elif path == '/api/execute-curl':
            self.handle_execute_curl()
            return
        else:
            self.send_error(404, "Not found")
            return
    
    def get_sso_token(self):
        """Get the stored SSO token from file."""
        token_file = Path(__file__).parent / '.sso_token'
        if token_file.exists():
            try:
                return token_file.read_text().strip()
            except:
                pass
        return None
    
    def save_sso_token(self, token):
        """Save the SSO token to file."""
        token_file = Path(__file__).parent / '.sso_token'
        try:
            token_file.write_text(token)
            return True
        except Exception as e:
            print(f"Error saving SSO token: {e}")
            return False
    
    def handle_update_sso_token(self):
        """Handle the update SSO token API endpoint."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            token = data.get('token', '').strip()
            if not token:
                response = {
                    'success': False,
                    'message': 'Token is required'
                }
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Save token
            if self.save_sso_token(token):
                response = {
                    'success': True,
                    'message': 'SSO token updated successfully'
                }
                self.send_response(200)
            else:
                response = {
                    'success': False,
                    'message': 'Failed to save SSO token'
                }
                self.send_response(500)
            
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError:
            response = {
                'success': False,
                'message': 'Invalid JSON in request body'
            }
            self.send_response(400)
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
    
    def handle_refresh_today(self):
        """Handle the refresh today API endpoint."""
        try:
            # Get SSO token if available
            sso_token = self.get_sso_token()
            
            # Execute the fetch today script
            script_path = Path(__file__).parent / 'fetch_today_data.py'
            cmd = ['python3', str(script_path)]
            if sso_token:
                cmd.extend(['--token', sso_token])
            
            result = subprocess.run(
                cmd,
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
    
    def handle_validate_sales_funnel(self):
        """Handle the validate sales funnel API endpoint."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b'{}'
            request_data = json.loads(body.decode('utf-8'))
            scheduler_name = request_data.get('scheduler_name')
            force_refresh = request_data.get('force_refresh', False)  # Allow forcing refresh
            
            # Get SSO token if available
            sso_token = self.get_sso_token()
            
            # Import the validation function
            import sys
            script_dir = Path(__file__).parent
            sys.path.insert(0, str(script_dir))
            from fetch_today_data import validate_single_sales_funnel_report
            
            # Run validation (silent mode for API calls, use cache unless force_refresh)
            result = validate_single_sales_funnel_report(
                scheduler_name, 
                sso_token=sso_token, 
                silent=True,
                use_cache=True,
                force_refresh=force_refresh
            )
            
            if 'error' in result:
                # Return 200 even for errors - empty results are not server errors
                response = {
                    'success': False,
                    'message': 'Failed to validate sales funnel report',
                    'error': result.get('error'),
                    'empty_result': result.get('empty_result', False),
                    'found_reports': result.get('found_reports', 0),
                    'found_schedulers': result.get('found_schedulers', []),
                    'today_date': result.get('today_date')
                }
                self.send_response(200)
            else:
                # Include cache metadata if available
                response = {
                    'success': True,
                    'message': 'Sales funnel validation completed',
                    'validation': result.get('validation', {}),
                    'report': result.get('report'),
                    'scheduler_report_details': result.get('scheduler_report_details', {}),
                    'scheduler_record': result.get('scheduler_record'),
                    'from_cache': result.get('from_cache', False),
                    'fetched_at': result.get('fetched_at')
                }
                self.send_response(200)
            
            # Send JSON response
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            response = {
                'success': False,
                'message': f'Error: {str(e)}',
                'error': str(e),
                'traceback': error_traceback
            }
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            # Also print to console for debugging
            print(f"Error in handle_validate_sales_funnel: {error_traceback}")
    
    def handle_execute_curl(self):
        """Handle the execute curl command API endpoint."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b'{}'
            request_data = json.loads(body.decode('utf-8'))
            curl_command = request_data.get('curl_command')
            
            if not curl_command:
                response = {
                    'success': False,
                    'error': 'No curl command provided'
                }
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Execute curl command using bash
            import subprocess
            try:
                result = subprocess.run(
                    ['bash', '-c', curl_command],
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
                
                response = {
                    'success': True,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'exit_code': result.returncode
                }
                self.send_response(200)
            except subprocess.TimeoutExpired:
                response = {
                    'success': False,
                    'error': 'Command execution timed out (30 seconds)'
                }
                self.send_response(200)
            except Exception as e:
                response = {
                    'success': False,
                    'error': f'Error executing command: {str(e)}'
                }
                self.send_response(200)
            
            # Send JSON response
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            response = {
                'success': False,
                'error': f'Server Error: {str(e)}'
            }
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            print(f"Error in handle_execute_curl: {error_traceback}")
    
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

