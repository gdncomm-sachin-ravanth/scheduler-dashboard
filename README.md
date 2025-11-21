# SAI Scheduler Dashboard

## Overview

A web-based monitoring and analytics tool for managing and tracking Rundeck scheduler jobs. Provides real-time insights into job execution status, performance metrics, and historical patterns through interactive visualizations, heatmaps, and detailed tables.

**Key Features:**
- Real-time job status monitoring and metrics
- Interactive heatmaps and execution analytics
- Pattern analysis for success rates and retry behavior
- Quick access to curl commands for manual execution
- Support for Canary and Non-Canary environments

## Pages

### 🚀 All Jobs (Rundeck Jobs)

View and manage all Rundeck scheduler jobs. Includes metrics dashboard, job schedule heatmap, interactive job table with filtering, and curl command access.

### 📊 Today's Summary (Today's Report)

Real-time snapshot of today's scheduler execution results. Monitor success rates, identify failures, track data processing metrics, and view detailed execution table.

### 📈 Overview (Reports Overview)

Historical overview of scheduler performance with daily breakdown charts and activity heatmaps showing trends and patterns over time.

### 🔍 Pattern Analysis

Deep dive into execution patterns, success rates, and performance metrics. Includes duration distribution charts and attempt analysis to understand scheduler behavior.

### 📋 All Data (All Scheduler Data)

Comprehensive table view of all historical scheduler executions with detailed information for analysis and troubleshooting. Includes advanced filtering and sorting capabilities.

## Prerequisites

### Python 3 (Recommended)

**Verify Installation:**
```bash
python3 --version
```

**Install Python 3:**

- **macOS:** `brew install python3` or download from [python.org](https://www.python.org/downloads/)
- **Linux (Ubuntu/Debian):** `sudo apt install python3 python3-pip`
- **Linux (CentOS/RHEL):** `sudo yum install python3`
- **Windows:** Download from [python.org](https://www.python.org/downloads/) (check "Add Python to PATH")

**Alternative Options:** Node.js (`npx http-server -p 8000`) or PHP (`php -S localhost:8000`)

## Running the Dashboard

1. Ensure all three JSON data files are in the same directory as `scheduler-dashboard.html`:
   - `jobs-data.json` - Rundeck job configurations
   - `today-data.json` - Today's execution results
   - `past-data.json` - Historical execution data

2. Start a local web server:
   ```bash
   python3 -m http.server 8000
   ```

3. Open `http://localhost:8000/scheduler-dashboard.html` in your browser

## Notes

- Requires a modern browser with JavaScript enabled
- All data is loaded from JSON files - no backend server required
- Curl commands can be copied directly from the modal for manual execution
