#!/usr/bin/env python3
"""
Script to fetch today's scheduler data from the API and update today-data.json.
Constructs a curl command dynamically with today's start timestamp in WIB timezone.
"""

import json
import subprocess
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import time


def get_sso_token_from_file():
    """Get SSO token from .sso_token file."""
    script_dir = Path(__file__).parent
    token_file = script_dir / '.sso_token'
    if token_file.exists():
        try:
            return token_file.read_text().strip()
        except:
            pass
    return None


def get_current_day_start_timestamp():
    """
    Get the current day's start timestamp (00:00:00) in WIB timezone (UTC+7) in milliseconds.
    Returns the timestamp as an integer.
    """
    # WIB timezone is UTC+7
    wib_timezone = timezone(timedelta(hours=7))
    now = datetime.now(wib_timezone)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    timestamp_ms = int(start_of_day.timestamp() * 1000)
    return timestamp_ms


def build_curl_command(today_timestamp, sso_token=None):
    """
    Build the curl command for fetching today's data.
    Constructs the command dynamically with today's start timestamp.
    
    Args:
        today_timestamp: Today's start timestamp in epoch milliseconds (WIB timezone)
        sso_token: Optional SSO token. If not provided, uses default token.
    
    Returns:
        Complete curl command as a string
    """
    # Base URL and headers
    url = "https://database-explorer.gdn-app.com/backend/data-explorer/api/v1/databases/exec/163"
    
    # Use provided token or default
    default_token = 'aKqjbQJLZUP4VvLhHdW9'
    token = sso_token if sso_token else default_token
    
    # Headers
    headers = {
        'accept': 'application/json',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'infra-sso-token': token,
        'origin': 'https://database-explorer.gdn-app.com',
        'priority': 'u=1, i',
        'referer': 'https://database-explorer.gdn-app.com/db/mongo/163',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
    }
    
    # Cookie string - update token in cookie as well
    cookie_base = '_vwo_uuid=D177B6EF6C914DACA5DC2405ADC253862; _vwo_ssm=1; _vis_opt_exp_82_combi=1; _vis_opt_s=4%7C; _vis_opt_test_cookie=1; _vwo_uuid_v2=D94AE4557E15DE7349AC497F04E7CB7F5|3dc24c7459862dc6bb3f62870701583c; _gcl_au=1.1.712251690.1762516136; moe_c_s=1; moe_h_a_s=0; _fbp=fb.1.1762516137254.816794765661547553; _tt_enable_cookie=1; _ttp=01KA87EQM2SC0CNM3H72DYQZPZ_.tt.1; _vwo_ds=3%3Aa_0%2Ct_0%3A0%241746703211%3A98.69085096%3A%3A%3A%3A0%3A1763360332%3A1762520776%3A3; _cfuvid=YtZLDfiWOUHued7cRRjOi44h4rwi94LAYawRBEdlgMk-1763360345918-0.0.1.1-604800000; _vis_opt_exp_82_goal_1=48; moe_i_m=q1Yqjc9UsgJSmSlKVkqmBoYmBoaW5pZKtbUA; moe_u_d=TYxNCsMgFAbv8q0VNP7leRl5-hQKgS7SdBO8e5usshoGhjnByCeOl1z4IiMY642lRFA4Cn-QbYpuNT6axTo_p8Je3tu_H7ztXUEKi_Sn3zdQ4tipVR0akfbGDU3inaawJK6j2bVWzB8; moe_s_n=RYo7DsIwDIbv4jmR3Np_cHMVhKw0yYAQMKQb4u4QFsbv8aLhN8pUWltNZIm7FURFqXHrQOxJsaem1SpT-M7DD8rLKYmxKgRI095_1pgDVb_6MfF8maX__82wslmghz99UJb3Bw; _ga_M865CMWYXJ=GS2.1.s1763804450$o5$g1$t1763808052$j60$l0$h0; forterToken=13aad943c08a44e68068049e4c6cb089_1763812130347_870_UDF43-m4_25ck; _ga_GRV0RQ2EZR=GS2.1.s1763874648$o6$g1$t1763874742$j40$l0$h0; _ga_F56DM94W5T=GS2.1.s1764163070$o31$g1$t1764163085$j45$l0$h0; _ga=GA1.2.542273956.1762515882; ttcsid=1764163069920::CT7GjRAcQryJiwfu-4sp.26.1764163086067.0; ttcsid_D3S8VSJC77UACP4037BG=1764163069919::VblhbiNSmSrOyZH37j4D.26.1764163086067.0; moe_uuid=90ce80e3-eece-4135-b97a-478ca2497c40'
    cookie = f'{cookie_base}; infra-sso-token={token}'
    
    # Build the JSON payload with dynamic analyticDate
    payload = {
        "query": f"db.scheduler.find({{\n  analyticDate: {today_timestamp}\n}})",
        "limit": 500,
        "offset": 0
    }
    
    # Build curl command
    curl_parts = [f"curl '{url}'"]
    
    # Add cookie header
    curl_parts.append(f"  -b '{cookie}'")
    
    # Add all headers
    for key, value in headers.items():
        curl_parts.append(f"  -H '{key}: {value}'")
    
    # Add data-raw with JSON payload
    # The payload needs to be properly escaped for shell execution
    payload_json = json.dumps(payload)
    curl_parts.append(f"  --data-raw '{payload_json}'")
    
    return ' \\\n'.join(curl_parts)


def fetch_today_data(today_timestamp, sso_token=None):
    """
    Fetch today's scheduler data from the API using a dynamically constructed curl command.
    
    Args:
        today_timestamp: Today's start timestamp in epoch milliseconds (WIB timezone)
        sso_token: Optional SSO token. If not provided, uses default token.
    
    Returns:
        JSON response data
    """
    print(f"Fetching data for today (analyticDate: {today_timestamp})")
    
    # Build curl command
    curl_command = build_curl_command(today_timestamp, sso_token)
    
    print("Executing curl command...")
    
    # Execute the curl command using bash
    result = subprocess.run(
        ['bash', '-c', curl_command],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Debug: Print response (first 500 chars)
    if result.stdout:
        print(f"Response preview: {result.stdout[:500]}...")
    
    # Parse the JSON response
    try:
        response_data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response:")
        print(f"  Response: {result.stdout}")
        print(f"  Error: {e}")
        raise
    
    return response_data


def build_sales_funnel_curl_command(today_timestamp, sso_token=None):
    """
    Build the curl command for fetching sales funnel scheduler reports.
    Based on CURL_sales_funnel_report.yaml structure.
    
    Args:
        today_timestamp: Today's start timestamp in epoch milliseconds (WIB timezone)
        sso_token: Optional SSO token. If not provided, reads from .sso_token file or uses default.
    
    Returns:
        Complete curl command as a string
    """
    # Base URL and headers
    url = "https://database-explorer.gdn-app.com/backend/data-explorer/api/v1/databases/exec/163"
    
    # Get token from file if not provided
    if not sso_token:
        sso_token = get_sso_token_from_file()
    
    # Use provided token or default
    default_token = 'UwpivB3HAqlRUrQ5TYTp'
    token = sso_token if sso_token else default_token
    
    # Headers (matching CURL_sales_funnel_report.yaml)
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
    
    # Cookie string - update token in cookie as well
    cookie_base = '_vwo_uuid=D177B6EF6C914DACA5DC2405ADC253862; _vwo_ssm=1; _vis_opt_exp_82_combi=1; _vis_opt_s=4%7C; _vis_opt_test_cookie=1; _vwo_uuid_v2=D94AE4557E15DE7349AC497F04E7CB7F5|3dc24c7459862dc6bb3f62870701583c; moe_c_s=1; moe_h_a_s=0; _fbp=fb.1.1762516137254.816794765661547553; _tt_enable_cookie=1; _ttp=01KA87EQM2SC0CNM3H72DYQZPZ_.tt.1; _vwo_ds=3%3Aa_0%2Ct_0%3A0%241746703211%3A98.69085096%3A%3A%3A%3A0%3A1763360332%3A1762520776%3A3; _vis_opt_exp_82_goal_1=48; moe_i_m=q1Yqjc9UsgJSmSlKVkqmBoYmBoaW5pZKtbUA; moe_u_d=TYxNCsMgFAbv8q0VNP7leRl5-hQKgS7SdBO8e5usshoGhjnByCeOl1z4IiMY642lRFA4Cn-QbYpuNT6axTo_p8Je3tu_H7ztXUEKi_Sn3zdQ4tipVR0akfbGDU3inaawJK6j2bVWzB8; moe_s_n=RYo7DsIwDIbv4jmR3Np_cHMVhKw0yYAQMKQb4u4QFsbv8aLhN8pUWltNZIm7FURFqXHrQOxJsaem1SpT-M7DD8rLKYmxKgRI095_1pgDVb_6MfF8maX__82wslmghz99UJb3Bw; _ga_M865CMWYXJ=GS2.1.s1763804450$o5$g1$t1763808052$j60$l0$h0; forterToken=13aad943c08a44e68068049e4c6cb089_1763812130347_870_UDF43-m4_25ck; _gcl_au=1.1.712251690.1762516136.1203570952.1764924591.1764924594; _ga_GRV0RQ2EZR=GS2.1.s1764924582$o7$g1$t1764924786$j17$l0$h0; moe_uuid=62a6e511-6e56-4e76-bc0f-5264eebbcd8f; _gid=GA1.2.403427694.1765159020; infra-sso-token=UwpivB3HAqlRUrQ5TYTp; _cfuvid=FbhSoJoMIa2XbLttyZUeACWFXMv_bj_dPrFBf19f46o-1765175685846-0.0.1.1-604800000; _ga=GA1.2.542273956.1762515882; ttcsid=1765175682981::i9HqBkD-xHMLrERJ9lXA.32.1765175695826.0; ttcsid_D3S8VSJC77UACP4037BG=1765175682981::t7wXURLjETEDibrG9QMP.32.1765175695827.1; _ga_F56DM94W5T=GS2.1.s1765175682$o37$g1$t1765176436$j60$l0$h0'
    cookie = cookie_base.replace('infra-sso-token=UwpivB3HAqlRUrQ5TYTp', f'infra-sso-token={token}')
    
    # Build the JSON payload - filter for the three schedulers with today's date
    scheduler_names = ['SALES_FUNNEL_YESTERDAY', 'SALES_FUNNEL_LAST_THIRTY_DAYS', 'SALES_FUNNEL_PREVIOUS_MONTH']
    scheduler_names_str = ', '.join([f'"{name}"' for name in scheduler_names])
    # Filter by schedulerName and today's date (start of day in WIB timezone)
    if today_timestamp:
        query_str = f'db.salesFunnelSchedulerReport.find({{"date": {today_timestamp}, "schedulerName": {{"$in": [{scheduler_names_str}]}}}})'
    else:
        # Fallback: if no timestamp provided, get latest records
        query_str = f'db.salesFunnelSchedulerReport.find({{"schedulerName": {{"$in": [{scheduler_names_str}]}}}}).sort({{"date": -1}})'
    payload = {
        "query": query_str,
        "limit": 10,
        "offset": 0
    }
    
    # Build curl command
    curl_parts = [f"curl '{url}'"]
    
    # Add cookie header
    curl_parts.append(f"  -b '{cookie}'")
    
    # Add all headers
    for key, value in headers.items():
        curl_parts.append(f"  -H '{key}: {value}'")
    
    # Add data-raw with JSON payload
    payload_json = json.dumps(payload)
    curl_parts.append(f"  --data-raw '{payload_json}'")
    
    return ' \\\n'.join(curl_parts)


def fetch_sales_funnel_reports(today_timestamp=None, sso_token=None, silent=False):
    """
    Fetch sales funnel scheduler reports from the API.
    
    Args:
        today_timestamp: Optional timestamp in epoch milliseconds (WIB timezone). If None, fetches latest records.
        sso_token: Optional SSO token. If not provided, reads from .sso_token file.
        silent: If True, suppress print statements (useful for API calls).
    
    Returns:
        JSON response data (list of scheduler reports)
    """
    if not silent:
        if today_timestamp:
            print(f"Fetching sales funnel reports for date: {today_timestamp}")
        else:
            print("Fetching latest sales funnel reports")
    
    # Build curl command
    curl_command = build_sales_funnel_curl_command(today_timestamp, sso_token)
    
    if not silent:
        print("Executing curl command...")
    
    # Execute the curl command using bash
    result = subprocess.run(
        ['bash', '-c', curl_command],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Debug: Print response (first 500 chars)
    if not silent and result.stdout:
        print(f"Response preview: {result.stdout[:500]}...")
    
    # Parse the JSON response
    try:
        response_data = json.loads(result.stdout)
        # The response might be wrapped in a 'data' key or be a direct array
        if isinstance(response_data, dict):
            if 'data' in response_data:
                response_data = response_data['data']
            elif 'result' in response_data:
                response_data = response_data['result']
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response:")
        print(f"  Response: {result.stdout}")
        print(f"  Error: {e}")
        raise
    
    # Ensure we have a list
    if not isinstance(response_data, list):
        print(f"Warning: Expected list but got {type(response_data)}")
        response_data = []
    
    return response_data


def calculate_rows_inserted(reports):
    """
    Calculate total rows inserted for each scheduler by summing rowsInserted from all pods.
    
    Args:
        reports: List of scheduler report objects
    
    Returns:
        Dictionary mapping scheduler name to total rows inserted
    """
    scheduler_totals = {}
    
    for report in reports:
        scheduler_name = report.get('schedulerName')
        scheduler_report = report.get('schedulerReport', {})
        
        if not scheduler_name:
            continue
        
        total_rows = 0
        pod_count = 0
        
        # Sum rowsInserted from all pods
        for pod_key, pod_data in scheduler_report.items():
            if isinstance(pod_data, dict):
                rows_inserted = pod_data.get('rowsInserted', 0)
                if rows_inserted is not None:
                    total_rows += rows_inserted
                    pod_count += 1
        
        scheduler_totals[scheduler_name] = {
            'total_rows_inserted': total_rows,
            'pod_count': pod_count,
            'execution_success': any(
                pod_data.get('executionSuccess', False) 
                for pod_data in scheduler_report.values() 
                if isinstance(pod_data, dict)
            ) if scheduler_report else False
        }
    
    return scheduler_totals


def validate_sales_funnel_reports(today_data_file=None, sso_token=None, silent=False):
    """
    Fetch sales funnel reports and validate against today's data.
    
    Args:
        today_data_file: Path to today-data.json file. If None, uses default location.
        sso_token: Optional SSO token. If not provided, reads from .sso_token file.
        silent: If True, suppress print statements (useful for API calls).
    
    Returns:
        Dictionary with validation results
    """
    script_dir = Path(__file__).parent
    
    if today_data_file is None:
        today_data_file = script_dir / "today-data.json"
    
    # Get today's start timestamp in WIB timezone
    today_timestamp = get_current_day_start_timestamp()
    
    # Format timestamp for display
    wib_timezone = timezone(timedelta(hours=7))
    today_date = datetime.fromtimestamp(today_timestamp / 1000, tz=wib_timezone)
    if not silent:
        print(f"Today's date (WIB): {today_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Today's timestamp (epoch ms): {today_timestamp}")
        print()
    
    # Fetch sales funnel reports
    try:
        reports = fetch_sales_funnel_reports(today_timestamp, sso_token, silent=silent)
    except subprocess.CalledProcessError as e:
        if not silent:
            print(f"Error executing curl command:")
            print(f"  Return code: {e.returncode}")
            print(f"  Error output: {e.stderr}")
        return {'error': str(e)}
    except Exception as e:
        if not silent:
            print(f"Error fetching sales funnel reports: {e}")
        return {'error': str(e)}
    
    if not silent:
        print(f"Found {len(reports)} sales funnel scheduler reports")
        print()
    
    # Calculate rows inserted for each scheduler
    scheduler_totals = calculate_rows_inserted(reports)
    
    # Load today's data for comparison
    try:
        with open(today_data_file, 'r') as f:
            today_data = json.load(f)
    except FileNotFoundError:
        if not silent:
            print(f"Warning: {today_data_file} not found. Cannot compare with today's data.")
        return {
            'reports': reports,
            'scheduler_totals': scheduler_totals,
            'validation': 'today_data_file_not_found'
        }
    
    # Extract expected values from today's data
    expected_values = {}
    for record in today_data:
        analytic_name = record.get('analyticName')
        if analytic_name in ['SALES_FUNNEL_YESTERDAY', 'SALES_FUNNEL_LAST_THIRTY_DAYS', 'SALES_FUNNEL_PREVIOUS_MONTH']:
            expected_values[analytic_name] = record.get('analyticTotalData', 0)
    
    # Compare and validate
    validation_results = {}
    if not silent:
        print("=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
    
    target_schedulers = ['SALES_FUNNEL_YESTERDAY', 'SALES_FUNNEL_LAST_THIRTY_DAYS', 'SALES_FUNNEL_PREVIOUS_MONTH']
    
    for scheduler_name in target_schedulers:
        if not silent:
            print(f"\n{scheduler_name}:")
            print("-" * 80)
        
        report_total = scheduler_totals.get(scheduler_name, {})
        rows_inserted = report_total.get('total_rows_inserted', 0)
        pod_count = report_total.get('pod_count', 0)
        execution_success = report_total.get('execution_success', False)
        expected_total = expected_values.get(scheduler_name, 0)
        
        match = rows_inserted == expected_total
        
        if not silent:
            print(f"  Pods: {pod_count}")
            print(f"  Rows Inserted (from schedulerReport): {rows_inserted:,}")
            print(f"  Expected (SAVED DATA from today-data.json): {expected_total:,}")
            print(f"  Match: {'✓ YES' if match else '✗ NO'}")
            print(f"  Execution Success: {'✓ YES' if execution_success else '✗ NO'}")
            
            if not match:
                diff = rows_inserted - expected_total
                print(f"  Difference: {diff:+,}")
        
        validation_results[scheduler_name] = {
            'rows_inserted': rows_inserted,
            'expected_total': expected_total,
            'match': match,
            'pod_count': pod_count,
            'execution_success': execution_success
        }
    
    if not silent:
        print("\n" + "=" * 80)
    
    return {
        'reports': reports,
        'scheduler_totals': scheduler_totals,
        'validation': validation_results
    }


def get_sales_funnel_cache_file():
    """Get the consolidated cache file path for sales funnel validation results."""
    script_dir = Path(__file__).parent
    cache_dir = script_dir / ".validation_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "sales_funnel_cache.json"


def migrate_old_cache_files():
    """Migrate old separate cache files to consolidated file."""
    script_dir = Path(__file__).parent
    cache_dir = script_dir / ".validation_cache"
    cache_file = get_sales_funnel_cache_file()
    
    # Load existing consolidated cache
    cache_list = []
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    cache_list = existing_data
        except Exception:
            cache_list = []
    
    # Check for old separate files and migrate them
    scheduler_names = ['SALES_FUNNEL_YESTERDAY', 'SALES_FUNNEL_LAST_THIRTY_DAYS', 'SALES_FUNNEL_PREVIOUS_MONTH']
    migrated_count = 0
    
    for scheduler_name in scheduler_names:
        safe_name = scheduler_name.replace('/', '_').replace('\\', '_')
        old_cache_file = cache_dir / f"{safe_name}.json"
        
        if old_cache_file.exists():
            try:
                with open(old_cache_file, 'r') as f:
                    old_cache_data = json.load(f)
                
                # Check if already in consolidated cache
                exists = any(item.get('scheduler_name') == scheduler_name for item in cache_list)
                if not exists:
                    cache_list.append({
                        'scheduler_name': scheduler_name,
                        'fetched_at': old_cache_data.get('fetched_at', int(time.time() * 1000)),
                        'result': old_cache_data.get('result', {})
                    })
                    migrated_count += 1
                
                # Delete old file after migration
                old_cache_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to migrate {old_cache_file.name}: {e}")
    
    # Save consolidated cache if migrations occurred
    if migrated_count > 0:
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_list, f, indent=2)
            print(f"Migrated {migrated_count} sales funnel cache files to consolidated file")
        except Exception as e:
            print(f"Warning: Failed to save consolidated cache: {e}")


def save_validation_cache(scheduler_name, result, silent=False):
    """Save validation result to consolidated cache file."""
    try:
        cache_file = get_sales_funnel_cache_file()
        
        # Migrate old files if they exist
        migrate_old_cache_files()
        
        # Load existing cache
        cache_list = []
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        cache_list = existing_data
                    elif isinstance(existing_data, dict):
                        # Handle old single-file format (shouldn't happen, but handle gracefully)
                        if existing_data.get('scheduler_name') == scheduler_name:
                            cache_list = [existing_data]
                        else:
                            cache_list = []
            except Exception:
                cache_list = []
        
        # Find and update existing entry or add new one
        found = False
        for item in cache_list:
            if item.get('scheduler_name') == scheduler_name:
                item['fetched_at'] = int(time.time() * 1000)
                item['result'] = result
                found = True
                break
        
        if not found:
            # Add new entry
            cache_list.append({
                'scheduler_name': scheduler_name,
                'fetched_at': int(time.time() * 1000),  # Timestamp in milliseconds
                'result': result
            })
        
        # Save updated cache
        with open(cache_file, 'w') as f:
            json.dump(cache_list, f, indent=2)
        
        if not silent:
            print(f"Validation result cached for {scheduler_name}")
    except Exception as e:
        if not silent:
            print(f"Warning: Failed to save cache: {e}")


def load_validation_cache(scheduler_name, silent=False):
    """Load validation result from consolidated cache file if available and valid."""
    try:
        cache_file = get_sales_funnel_cache_file()
        if not cache_file.exists():
            # Try migrating old files
            migrate_old_cache_files()
            if not cache_file.exists():
                return None
        
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # Handle both list format (new) and dict format (old single entry)
        cache_list = []
        if isinstance(cache_data, list):
            cache_list = cache_data
        elif isinstance(cache_data, dict):
            # Old format - single entry
            cache_list = [cache_data]
        
        # Find entry for the requested scheduler
        entry = None
        for item in cache_list:
            if item.get('scheduler_name') == scheduler_name:
                entry = item
                break
        
        if not entry:
            return None
        
        # Check if cache is from today (same day)
        fetched_at = entry.get('fetched_at', 0)
        cache_date = datetime.fromtimestamp(fetched_at / 1000, tz=timezone(timedelta(hours=7)))
        today_timestamp = get_current_day_start_timestamp()
        today_date = datetime.fromtimestamp(today_timestamp / 1000, tz=timezone(timedelta(hours=7)))
        
        # Check if cache is from today
        if cache_date.date() != today_date.date():
            if not silent:
                print(f"Cache expired: from {cache_date.date()}, today is {today_date.date()}")
            # Remove expired entry from cache
            cache_list = [item for item in cache_list if item.get('scheduler_name') != scheduler_name]
            if cache_list:
                with open(cache_file, 'w') as f:
                    json.dump(cache_list, f, indent=2)
            else:
                cache_file.unlink()
            return None
        
        # Check if result is valid (successful and matched)
        result = entry.get('result', {})
        validation = result.get('validation', {})
        
        # Migrate old cache format: if scheduler_report_details exists, remove it
        # and ensure report has schedulerReport
        if 'scheduler_report_details' in result:
            # Old format detected - migrate it
            if 'report' in result and isinstance(result['report'], dict):
                # If report doesn't have schedulerReport but scheduler_report_details exists,
                # reconstruct it (shouldn't happen in practice, but handle gracefully)
                if 'schedulerReport' not in result['report'] and result.get('scheduler_report_details'):
                    result['report']['schedulerReport'] = result['scheduler_report_details']
            # Remove redundant scheduler_report_details
            result.pop('scheduler_report_details', None)
        
        # Migrate old validation format: remove scheduler_name if present
        if 'scheduler_name' in validation:
            validation.pop('scheduler_name')
        
        # Migrate old report format: if full MongoDB document, extract only needed fields
        if 'report' in result and isinstance(result['report'], dict):
            report = result['report']
            # Check if it's a full MongoDB document (has _id, _class, etc.)
            if '_id' in report or '_class' in report:
                # Extract only needed fields
                result['report'] = {
                    'schedulerReport': report.get('schedulerReport', {}),
                    'date': report.get('date'),
                    'schedulerName': report.get('schedulerName')
                }
                # Save migrated cache back
                entry['result'] = result
                cache_list = [item for item in cache_list if item.get('scheduler_name') != scheduler_name]
                cache_list.append(entry)
                with open(cache_file, 'w') as f:
                    json.dump(cache_list, f, indent=2)
        
        if validation.get('execution_success') and validation.get('match'):
            if not silent:
                print(f"Using cached validation result for {scheduler_name} (fetched at {cache_date.strftime('%Y-%m-%d %H:%M:%S')})")
            return {
                'result': result,
                'fetched_at': fetched_at,
                'from_cache': True
            }
        else:
            if not silent:
                print(f"Cache invalid: execution_success={validation.get('execution_success')}, match={validation.get('match')}")
            return None
            
    except Exception as e:
        if not silent:
            print(f"Warning: Failed to load cache: {e}")
        return None


def validate_single_sales_funnel_report(scheduler_name, today_data_file=None, sso_token=None, silent=False, use_cache=True, force_refresh=False):
    """
    Fetch and validate a single sales funnel scheduler report.
    
    Args:
        scheduler_name: Name of the scheduler to validate (e.g., 'SALES_FUNNEL_YESTERDAY')
        today_data_file: Path to today-data.json file. If None, uses default location.
        sso_token: Optional SSO token. If not provided, reads from .sso_token file.
        silent: If True, suppress print statements (useful for API calls).
        use_cache: If True, check cache before fetching from database.
        force_refresh: If True, bypass cache and fetch fresh data.
    
    Returns:
        Dictionary with validation results and detailed scheduler report
    """
    script_dir = Path(__file__).parent
    
    if today_data_file is None:
        today_data_file = script_dir / "today-data.json"
    
    # Validate scheduler name
    valid_schedulers = ['SALES_FUNNEL_YESTERDAY', 'SALES_FUNNEL_LAST_THIRTY_DAYS', 'SALES_FUNNEL_PREVIOUS_MONTH']
    if scheduler_name not in valid_schedulers:
        return {'error': f'Invalid scheduler name. Must be one of: {", ".join(valid_schedulers)}'}
    
    # Check cache first (unless force refresh is requested)
    if use_cache and not force_refresh:
        cache_result = load_validation_cache(scheduler_name, silent=silent)
        if cache_result:
            # Add cache metadata to result
            result = cache_result['result'].copy()
            result['from_cache'] = True
            result['fetched_at'] = cache_result['fetched_at']
            return result
    
    # Fetch sales funnel reports for today's start of day
    today_timestamp = get_current_day_start_timestamp()
    try:
        reports = fetch_sales_funnel_reports(today_timestamp, sso_token, silent=silent)
    except subprocess.CalledProcessError as e:
        error_msg = f"Error executing curl command (return code: {e.returncode}): {e.stderr}"
        if not silent:
            print(error_msg)
        return {'error': error_msg}
    except Exception as e:
        error_msg = f"Error fetching sales funnel reports: {str(e)}"
        if not silent:
            print(error_msg)
        return {'error': error_msg}
    
    # Debug: Log what we found
    if not silent:
        print(f"Found {len(reports)} reports")
        for r in reports:
            print(f"  - {r.get('schedulerName')} (date: {r.get('date')})")
    
    # Find the specific scheduler report (get the latest one if multiple exist)
    target_report = None
    matching_reports = [r for r in reports if r.get('schedulerName') == scheduler_name]
    
    if matching_reports:
        # Sort by date descending and get the latest one
        matching_reports.sort(key=lambda x: x.get('date', 0), reverse=True)
        target_report = matching_reports[0]
    
    if not target_report:
        found_names = [r.get('schedulerName') for r in reports]
        wib_timezone = timezone(timedelta(hours=7))
        today_date = datetime.fromtimestamp(today_timestamp / 1000, tz=wib_timezone)
        date_str = today_date.strftime('%Y-%m-%d')
        error_msg = f'No report found for scheduler "{scheduler_name}" for today\'s date ({date_str}).'
        if len(reports) == 0:
            error_msg += ' No reports found in the database for today.'
        else:
            error_msg += f' Found {len(reports)} reports for other schedulers: {", ".join(found_names) if found_names else "none"}.'
        if not silent:
            print(error_msg)
        return {
            'error': error_msg,
            'found_reports': len(reports),
            'found_schedulers': found_names,
            'empty_result': len(reports) == 0,
            'today_date': date_str
        }
    
    # Extract scheduler report and calculate total rows inserted
    scheduler_report = target_report.get('schedulerReport', {})
    total_rows_inserted = 0
    
    for pod_key, pod_data in scheduler_report.items():
        if isinstance(pod_data, dict):
            rows_inserted = pod_data.get('rowsInserted', 0)
            if rows_inserted is not None:
                total_rows_inserted += rows_inserted
    
    # Load today's data for comparison
    try:
        with open(today_data_file, 'r') as f:
            today_data = json.load(f)
    except FileNotFoundError:
        optimized_report = {
            'schedulerReport': target_report.get('schedulerReport', {}),
            'date': target_report.get('date'),
            'schedulerName': target_report.get('schedulerName')
        }
        return {
            'error': f'{today_data_file} not found. Cannot compare with today\'s data.',
            'report': optimized_report
        }
    
    # Extract scheduler record and expected value from today's data
    scheduler_record = None
    expected_total = 0
    for record in today_data:
        record_name = record.get('analyticName', '')
        if record_name == scheduler_name:
            scheduler_record = record
            expected_total = record.get('analyticTotalData', 0)
            break
    
    # Debug: Log if scheduler_record was found
    if not scheduler_record and not silent:
        found_names = [r.get('analyticName', '') for r in today_data if 'SALES_FUNNEL' in r.get('analyticName', '')]
        print(f"Warning: Scheduler record not found for {scheduler_name}. Found sales funnel schedulers: {found_names}")
    
    # Calculate validation result
    match = total_rows_inserted == expected_total
    pod_count = len(scheduler_report)
    execution_success = any(
        pod.get('executionSuccess', False) 
        for pod in scheduler_report.values() if isinstance(pod, dict)
    )
    
    validation_result = {
        'rows_inserted': total_rows_inserted,
        'expected_total': expected_total,
        'match': match,
        'pod_count': pod_count,
        'execution_success': execution_success,
        'difference': total_rows_inserted - expected_total
    }
    
    # Store only necessary fields from report (schedulerReport and date)
    # Remove redundant scheduler_report_details - use report.schedulerReport directly
    optimized_report = {
        'schedulerReport': target_report.get('schedulerReport', {}),
        'date': target_report.get('date'),
        'schedulerName': target_report.get('schedulerName')
    }
    
    result = {
        'validation': validation_result,
        'report': optimized_report,
        'scheduler_record': scheduler_record  # Include the full scheduler record from today-data.json
    }
    
    # Save to cache if validation is successful and data matches
    if execution_success and match:
        save_validation_cache(scheduler_name, result, silent=silent)
    
    return result


def main():
    # Migrate old cache files to consolidated format on startup
    migrate_old_cache_files()
    """Main function to fetch and save today's scheduler data."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch today\'s scheduler data')
    parser.add_argument('--token', type=str, help='SSO token to use for authentication')
    parser.add_argument('--validate-sales-funnel', action='store_true', 
                       help='Validate sales funnel reports against today\'s data')
    args = parser.parse_args()
    
    # If validate flag is set, run validation instead
    if args.validate_sales_funnel:
        result = validate_sales_funnel_reports(sso_token=args.token)
        return 0 if 'error' not in result else 1
    
    script_dir = Path(__file__).parent
    
    # File path
    today_data_file = script_dir / "today-data.json"
    
    # Get today's start timestamp in WIB timezone
    today_timestamp = get_current_day_start_timestamp()
    
    # Format timestamp for display
    wib_timezone = timezone(timedelta(hours=7))
    today_date = datetime.fromtimestamp(today_timestamp / 1000, tz=wib_timezone)
    print(f"Today's date (WIB): {today_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Today's timestamp (epoch ms): {today_timestamp}")
    print()
    
    # Fetch data from API
    try:
        response_data = fetch_today_data(today_timestamp, args.token)
    except subprocess.CalledProcessError as e:
        print(f"Error executing curl command:")
        print(f"  Return code: {e.returncode}")
        print(f"  Error output: {e.stderr}")
        return 1
    except Exception as e:
        print(f"Error fetching data: {e}")
        return 1
    
    # Extract the 'data' array
    if 'data' not in response_data:
        print("Error: 'data' key not found in response")
        print(f"Response keys: {list(response_data.keys())}")
        print(f"Full response: {json.dumps(response_data, indent=2)}")
        return 1
    
    data_list = response_data['data']
    print(f"Found {len(data_list)} records for today")
    
    # Verify all records have the correct analyticDate
    correct_date_count = sum(1 for record in data_list if str(record.get('analyticDate')) == str(today_timestamp))
    if correct_date_count != len(data_list):
        print(f"Warning: Only {correct_date_count} out of {len(data_list)} records have analyticDate matching today")
    
    # Save today's data to today-data.json
    with open(today_data_file, 'w') as f:
        json.dump(data_list, f, indent=4)
    print(f"Saved {len(data_list)} records to {today_data_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())

