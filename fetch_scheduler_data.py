#!/usr/bin/env python3
"""
Script to fetch scheduler data from the API and save to JSON files.
Extracts data from the API response and filters by current day's start timestamp.
"""

import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path


def get_current_day_start_timestamp():
    """
    Get the current day's start timestamp (00:00:00) in WIB timezone (UTC+7) in milliseconds.
    Returns the timestamp as a string to match the format in the data.
    """
    # WIB timezone is UTC+7
    wib_timezone = timezone(timedelta(hours=7))
    now = datetime.now(wib_timezone)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    timestamp_ms = int(start_of_day.timestamp() * 1000)
    return str(timestamp_ms)


def fetch_scheduler_data(curl_file_path):
    """
    Fetch scheduler data from the API by executing the curl command directly.
    Returns the JSON response.
    """
    print(f"Executing curl command from: {curl_file_path}")
    
    # Read the curl command file
    with open(curl_file_path, 'r') as f:
        curl_command = f.read().strip()
    
    # Execute the curl command using bash
    result = subprocess.run(
        ['bash', '-c', curl_command],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Parse the JSON response
    response_data = json.loads(result.stdout)
    return response_data


def main():
    """Main function to fetch and process scheduler data."""
    script_dir = Path(__file__).parent
    
    # File paths
    curl_file = script_dir / "curl-command.txt"
    past_data_file = script_dir / "past-data.json"
    today_data_file = script_dir / "today-data.json"
    
    # Fetch data from API
    try:
        response_data = fetch_scheduler_data(curl_file)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return 1
    
    # Extract the 'data' array
    if 'data' not in response_data:
        print("Error: 'data' key not found in response")
        return 1
    
    data_list = response_data['data']
    print(f"Found {len(data_list)} records in response")
    
    # Save all data to past-data.json
    with open(past_data_file, 'w') as f:
        json.dump(data_list, f, indent=4)
    print(f"Saved {len(data_list)} records to {past_data_file}")
    
    # Get current day's start timestamp
    current_day_start = get_current_day_start_timestamp()
    print(f"Filtering for analyticDate: {current_day_start} (current day start)")
    
    # Filter data for current day
    today_data = [
        record for record in data_list
        if record.get('analyticDate') == current_day_start
    ]
    
    print(f"Found {len(today_data)} records for today")
    
    # Save today's data to today-data.json
    with open(today_data_file, 'w') as f:
        json.dump(today_data, f, indent=4)
    print(f"Saved {len(today_data)} records to {today_data_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())

