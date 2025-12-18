#!/usr/bin/env python3
"""
Simple HTTP server to serve the dashboard and provide API endpoint to refresh data.
"""

import json
import subprocess
import time
from datetime import datetime, timezone, timedelta
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
        
        # Handle API endpoints
        if path == '/api/get-last-updated':
            self.handle_get_last_updated()
            return
        
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
        # SSO token is now stored in browser localStorage, no server endpoint needed
        elif path == '/api/validate-sales-funnel':
            self.handle_validate_sales_funnel()
            return
        elif path == '/api/execute-curl':
            self.handle_execute_curl()
            return
        elif path == '/api/fetch-past-data':
            self.handle_fetch_past_data()
            return
        elif path == '/api/set-last-updated':
            self.handle_set_last_updated()
            return
        else:
            self.send_error(404, "Not found")
            return
    
    # SSO token is now stored in browser localStorage, not in server files
    # Token is passed from client to server in API request bodies
    
    # SSO token update endpoint removed - token is now stored in browser localStorage
    # Token is passed from client to server in API request bodies
    
    def handle_refresh_today(self):
        """Handle the refresh today API endpoint."""
        try:
            # Read request body to get SSO token
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b'{}'
            request_data = json.loads(body.decode('utf-8'))
            sso_token = request_data.get('sso_token')
            
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
            
            # Get SSO token from request body (browser localStorage)
            sso_token = request_data.get('sso_token')
            
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
    
    def handle_fetch_past_data(self):
        """Handle the fetch past data API endpoint."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b'{}'
            request_data = json.loads(body.decode('utf-8'))
            date_range = request_data.get('date_range', 'LAST_7_DAYS')
            
            # Get SSO token from request body (browser localStorage)
            sso_token = request_data.get('sso_token')
            default_token = 'DEHijcfTDiMhsQXwTj1d'
            token = sso_token if sso_token else default_token
            
            # Calculate date range
            now_ms = int(time.time() * 1000)
            
            if date_range == 'YESTERDAY':
                # Yesterday: from yesterday 00:00:00 to yesterday 23:59:59
                wib_timezone = timezone(timedelta(hours=7))
                yesterday = datetime.now(wib_timezone) - timedelta(days=1)
                start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                start_ms = int(start_of_yesterday.timestamp() * 1000)
                end_ms = int(end_of_yesterday.timestamp() * 1000)
            elif date_range == 'LAST_7_DAYS':
                # Last 7 days: from 7 days ago to now
                start_ms = now_ms - (7 * 24 * 60 * 60 * 1000)
                end_ms = now_ms
            elif date_range == 'LAST_14_DAYS':
                # Last 14 days: from 14 days ago to now
                start_ms = now_ms - (14 * 24 * 60 * 60 * 1000)
                end_ms = now_ms
            elif date_range == 'LAST_14_DAYS_EXCLUDING_TODAY':
                # Last 14 days excluding today: from 14 days ago to end of yesterday
                wib_timezone = timezone(timedelta(hours=7))
                now_wib = datetime.now(wib_timezone)
                yesterday_end = (now_wib - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
                fourteen_days_ago_start = (now_wib - timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0)
                start_ms = int(fourteen_days_ago_start.timestamp() * 1000)
                end_ms = int(yesterday_end.timestamp() * 1000)
            else:
                response = {
                    'success': False,
                    'error': f'Invalid date_range: {date_range}'
                }
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Build curl command
            url = "https://database-explorer.gdn-app.com/backend/data-explorer/api/v1/databases/exec/163"
            
            # Headers
            headers = {
                'accept': 'application/json',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'content-type': 'application/json',
                'infra-sso-token': token,
                'origin': 'https://database-explorer.gdn-app.com',
                'priority': 'u=1, i',
                'referer': 'https://database-explorer.gdn-app.com/db/mongo/163',
                'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
            }
            
            # Cookie string
            cookie_base = '_vwo_uuid=D177B6EF6C914DACA5DC2405ADC253862; _vwo_ssm=1; _vis_opt_exp_82_combi=1; _vis_opt_s=4%7C; _vis_opt_test_cookie=1; _vwo_uuid_v2=D94AE4557E15DE7349AC497F04E7CB7F5|3dc24c7459862dc6bb3f62870701583c; moe_c_s=1; moe_h_a_s=0; _fbp=fb.1.1762516137254.816794765661547553; _tt_enable_cookie=1; _ttp=01KA87EQM2SC0CNM3H72DYQZPZ_.tt.1; _vwo_ds=3%3Aa_0%2Ct_0%3A0%241746703211%3A98.69085096%3A%3A%3A%3A0%3A1763360332%3A1762520776%3A3; _vis_opt_exp_82_goal_1=48; moe_i_m=q1Yqjc9UsgJSmSlKVkqmBoYmBoaW5pZKtbUA; moe_u_d=TYxNCsMgFAbv8q0VNP7leRl5-hQKgS7SdBO8e5usshoGhjnByCeOl1z4IiMY642lRFA4Cn-QbYpuNT6axTo_p8Je3tu_H7ztXUEKi_Sn3zdQ4tipVR0akfbGDU3inaawJK6j2bVWzB8; moe_s_n=RYo7DsIwDIbv4jmR3Np_cHMVhKw0yYAQMKQb4u4QFsbv8aLhN8pUWltNZIm7FURFqXHrQOxJsaem1SpT-M7DD8rLKYmxKgRI095_1pgDVb_6MfF8maX__82wslmghz99UJb3Bw; _ga_M865CMWYXJ=GS2.1.s1763804450$o5$g1$t1763808052$j60$l0$h0; forterToken=13aad943c08a44e68068049e4c6cb089_1763812130347_870_UDF43-m4_25ck; _gcl_au=1.1.712251690.1762516136.1203570952.1764924591.1764924594; _ga_GRV0RQ2EZR=GS2.1.s1764924582$o7$g1$t1764924786$j17$l0$h0; moe_uuid=62a6e511-6e56-4e76-bc0f-5264eebbcd8f; _gid=GA1.2.403427694.1765159020; _cfuvid=FbhSoJoMIa2XbLttyZUeACWFXMv_bj_dPrFBf19f46o-1765175685846-0.0.1.1-604800000; _ga=GA1.2.542273956.1762515882; ttcsid_D3S8VSJC77UACP4037BG=1765257793064::yDuGVpCrWzeHSumno7Z4.33.1765257802898.1; ttcsid=1765257793065::Oyd4ArYSF0oh46XO3YTm.33.1765257802898.0; _ga_F56DM94W5T=GS2.1.s1765257792$o38$g1$t1765257811$j41$l0$h0'
            cookie = f'{cookie_base}; infra-sso-token={token}'
            
            # Build the JSON payload with date range
            query_str = f'db.scheduler.find({{\n    analyticDate: {{\n      $gte: {start_ms},\n      $lte: {end_ms}\n  }}\n}})'
            payload = {
                "query": query_str,
                "limit": 500,
                "offset": 0
            }
            
            # Build curl command
            curl_parts = [f"curl '{url}'"]
            curl_parts.append(f"  -b '{cookie}'")
            for key, value in headers.items():
                curl_parts.append(f"  -H '{key}: {value}'")
            
            payload_json = json.dumps(payload)
            curl_parts.append(f"  --data-raw '{payload_json}'")
            curl_command = ' \\\n'.join(curl_parts)
            
            # Execute curl command
            result = subprocess.run(
                ['bash', '-c', curl_command],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0:
                # Parse response
                try:
                    response_data = json.loads(result.stdout)
                    data_list = response_data.get('data', [])
                    
                    # Save to past-data.json
                    past_data_file = Path(__file__).parent / 'past-data.json'
                    with open(past_data_file, 'w') as f:
                        json.dump(data_list, f, indent=4)
                    
                    response = {
                        'success': True,
                        'message': f'Fetched {len(data_list)} records for {date_range}',
                        'record_count': len(data_list),
                        'date_range': date_range
                    }
                    self.send_response(200)
                except json.JSONDecodeError as e:
                    response = {
                        'success': False,
                        'error': f'Failed to parse response: {str(e)}',
                        'stdout': result.stdout[:500]
                    }
                    self.send_response(200)
            else:
                response = {
                    'success': False,
                    'error': f'Curl command failed with exit code {result.returncode}',
                    'stderr': result.stderr
                }
                self.send_response(200)
            
            # Send JSON response
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except subprocess.TimeoutExpired:
            response = {
                'success': False,
                'error': 'Request timed out (60 seconds)'
            }
            self.send_response(200)
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
            print(f"Error in handle_fetch_past_data: {error_traceback}")
    
    def get_last_updated_cache_file(self):
        """Get the cache file path for last updated timestamps."""
        script_dir = Path(__file__).parent
        cache_dir = script_dir / ".validation_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / "last_updated.json"
    
    def load_last_updated_cache(self, cache_type):
        """Load last updated timestamp from cache file with expiry check (1 day)."""
        try:
            cache_file = self.get_last_updated_cache_file()
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r') as f:
                cache_list = json.load(f)
            
            # Ensure cache_list is a list
            if not isinstance(cache_list, list):
                return None
            
            # Find entry for the requested cache_type
            entry = None
            for item in cache_list:
                if item.get('type') == cache_type:
                    entry = item
                    break
            
            if not entry:
                return None
            
            fetched_at = entry.get('fetched_at', 0)
            if not fetched_at:
                return None
            
            # Check if cache is expired (older than 1 day = 86400000 milliseconds)
            current_time = int(time.time() * 1000)
            age_ms = current_time - fetched_at
            one_day_ms = 24 * 60 * 60 * 1000  # 86400000 milliseconds
            
            if age_ms > one_day_ms:
                # Cache expired, remove entry from list
                cache_list = [item for item in cache_list if item.get('type') != cache_type]
                # Save updated cache (remove expired entry)
                if cache_list:
                    with open(cache_file, 'w') as f:
                        json.dump(cache_list, f, indent=2)
                else:
                    # If no entries left, delete file
                    cache_file.unlink()
                return None
            
            return {
                'fetched_at': fetched_at,
                'timestamp': entry.get('timestamp')
            }
        except Exception as e:
            print(f"Warning: Failed to load last updated cache for {cache_type}: {e}")
            return None
    
    def save_last_updated_cache(self, cache_type, timestamp):
        """Save last updated timestamp to cache file."""
        try:
            cache_file = self.get_last_updated_cache_file()
            
            # Load existing cache
            cache_list = []
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        existing_data = json.load(f)
                        if isinstance(existing_data, list):
                            cache_list = existing_data
                        elif isinstance(existing_data, dict):
                            # Migrate from old dict format to list format
                            cache_list = [{'type': k, **v} for k, v in existing_data.items()]
                except Exception:
                    cache_list = []
            
            # Find and update existing entry or add new one
            found = False
            for item in cache_list:
                if item.get('type') == cache_type:
                    item['fetched_at'] = int(time.time() * 1000)
                    item['timestamp'] = timestamp
                    found = True
                    break
            
            if not found:
                # Add new entry
                cache_list.append({
                    'type': cache_type,
                    'fetched_at': int(time.time() * 1000),  # Timestamp in milliseconds
                    'timestamp': timestamp  # ISO string timestamp
                })
            
            # Save updated cache
            with open(cache_file, 'w') as f:
                json.dump(cache_list, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save last updated cache for {cache_type}: {e}")
    
    def handle_get_last_updated(self):
        """Handle GET request for last updated timestamp."""
        try:
            # Get cache_type from query string
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            cache_type = query_params.get('type', ['pastData'])[0]  # Default to 'pastData'
            
            if cache_type not in ['pastData', 'todayData']:
                response = {
                    'success': False,
                    'error': 'Invalid cache type. Must be "pastData" or "todayData"'
                }
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            cache_result = self.load_last_updated_cache(cache_type)
            
            if cache_result:
                response = {
                    'success': True,
                    'fetched_at': cache_result['fetched_at'],
                    'timestamp': cache_result['timestamp']
                }
            else:
                response = {
                    'success': True,
                    'fetched_at': None,
                    'timestamp': None
                }
            
            self.send_response(200)
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
            print(f"Error in handle_get_last_updated: {error_traceback}")
    
    def handle_set_last_updated(self):
        """Handle POST request to set last updated timestamp."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b'{}'
            request_data = json.loads(body.decode('utf-8'))
            cache_type = request_data.get('type', 'pastData')
            timestamp = request_data.get('timestamp')
            
            if cache_type not in ['pastData', 'todayData']:
                response = {
                    'success': False,
                    'error': 'Invalid cache type. Must be "pastData" or "todayData"'
                }
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            if not timestamp:
                response = {
                    'success': False,
                    'error': 'Timestamp is required'
                }
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Save to cache
            self.save_last_updated_cache(cache_type, timestamp)
            
            response = {
                'success': True,
                'message': f'Last updated timestamp saved for {cache_type}'
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError as e:
            response = {
                'success': False,
                'error': f'Invalid JSON: {str(e)}'
            }
            self.send_response(400)
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
            print(f"Error in handle_set_last_updated: {error_traceback}")
    
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

