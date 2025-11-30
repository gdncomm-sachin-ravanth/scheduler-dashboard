#!/usr/bin/env python3
"""
Script to fetch today's scheduler data from the API and update today-data.json.
Constructs a curl command dynamically with today's start timestamp in WIB timezone.
"""

import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path


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


def build_curl_command(today_timestamp):
    """
    Build the curl command for fetching today's data.
    Constructs the command dynamically with today's start timestamp.
    
    Args:
        today_timestamp: Today's start timestamp in epoch milliseconds (WIB timezone)
    
    Returns:
        Complete curl command as a string
    """
    # Base URL and headers
    url = "https://database-explorer.gdn-app.com/backend/data-explorer/api/v1/databases/exec/163"
    
    # Headers
    headers = {
        'accept': 'application/json',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'infra-sso-token': 'aKqjbQJLZUP4VvLhHdW9',
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
    
    # Cookie string
    cookie = '_vwo_uuid=D177B6EF6C914DACA5DC2405ADC253862; _vwo_ssm=1; _vis_opt_exp_82_combi=1; _vis_opt_s=4%7C; _vis_opt_test_cookie=1; _vwo_uuid_v2=D94AE4557E15DE7349AC497F04E7CB7F5|3dc24c7459862dc6bb3f62870701583c; _gcl_au=1.1.712251690.1762516136; moe_c_s=1; moe_h_a_s=0; _fbp=fb.1.1762516137254.816794765661547553; _tt_enable_cookie=1; _ttp=01KA87EQM2SC0CNM3H72DYQZPZ_.tt.1; _vwo_ds=3%3Aa_0%2Ct_0%3A0%241746703211%3A98.69085096%3A%3A%3A%3A0%3A1763360332%3A1762520776%3A3; _cfuvid=YtZLDfiWOUHued7cRRjOi44h4rwi94LAYawRBEdlgMk-1763360345918-0.0.1.1-604800000; _vis_opt_exp_82_goal_1=48; moe_i_m=q1Yqjc9UsgJSmSlKVkqmBoYmBoaW5pZKtbUA; moe_u_d=TYxNCsMgFAbv8q0VNP7leRl5-hQKgS7SdBO8e5usshoGhjnByCeOl1z4IiMY642lRFA4Cn-QbYpuNT6axTo_p8Je3tu_H7ztXUEKi_Sn3zdQ4tipVR0akfbGDU3inaawJK6j2bVWzB8; moe_s_n=RYo7DsIwDIbv4jmR3Np_cHMVhKw0yYAQMKQb4u4QFsbv8aLhN8pUWltNZIm7FURFqXHrQOxJsaem1SpT-M7DD8rLKYmxKgRI095_1pgDVb_6MfF8maX__82wslmghz99UJb3Bw; _ga_M865CMWYXJ=GS2.1.s1763804450$o5$g1$t1763808052$j60$l0$h0; forterToken=13aad943c08a44e68068049e4c6cb089_1763812130347_870_UDF43-m4_25ck; _ga_GRV0RQ2EZR=GS2.1.s1763874648$o6$g1$t1763874742$j40$l0$h0; _ga_F56DM94W5T=GS2.1.s1764163070$o31$g1$t1764163085$j45$l0$h0; _ga=GA1.2.542273956.1762515882; ttcsid=1764163069920::CT7GjRAcQryJiwfu-4sp.26.1764163086067.0; ttcsid_D3S8VSJC77UACP4037BG=1764163069919::VblhbiNSmSrOyZH37j4D.26.1764163086067.0; moe_uuid=90ce80e3-eece-4135-b97a-478ca2497c40; infra-sso-token=aKqjbQJLZUP4VvLhHdW9'
    
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


def fetch_today_data(today_timestamp):
    """
    Fetch today's scheduler data from the API using a dynamically constructed curl command.
    
    Args:
        today_timestamp: Today's start timestamp in epoch milliseconds (WIB timezone)
    
    Returns:
        JSON response data
    """
    print(f"Fetching data for today (analyticDate: {today_timestamp})")
    
    # Build curl command
    curl_command = build_curl_command(today_timestamp)
    
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


def main():
    """Main function to fetch and save today's scheduler data."""
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
        response_data = fetch_today_data(today_timestamp)
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

