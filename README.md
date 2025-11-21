# Scheduler Dashboard

## Overview

Scheduler Dashboard is a comprehensive web-based monitoring and analytics tool for managing and tracking Rundeck scheduler jobs. It provides real-time insights into job execution status, performance metrics, and historical patterns through interactive visualizations, heatmaps, and detailed tables. The dashboard helps you quickly identify issues, understand execution patterns, and access curl commands for manual job execution.

**Key Features:**
- Real-time job status monitoring and metrics
- Interactive heatmaps showing job distribution and activity patterns
- Detailed execution history and analytics
- Pattern analysis for success rates and retry behavior
- Quick access to curl commands for manual job execution
- Support for both Canary and Non-Canary environments
- Comprehensive filtering and search capabilities

## Pages

### 🚀 All Jobs (Rundeck Jobs)

**Description:** View and manage all Rundeck scheduler jobs in one place. This page provides a complete overview of your job inventory with detailed metrics and filtering options.

**Features:**
- **Metrics Dashboard:** Total jobs count, enabled/disabled status, Canary vs Non-Canary distribution, and frequency breakdown (Daily, Weekly, Monthly)
- **Job Schedule Heatmap:** Visual representation of job distribution across 24 hours, showing enabled vs disabled jobs by frequency type
- **Interactive Job Table:** Sortable table with job names, schedule times, frequency, day info, status, environment, and quick access to curl commands
- **Advanced Filtering:** Search by job name, filter by frequency (Daily/Weekly/Monthly), status (Enabled/Disabled), and environment (Canary/Non-Canary)
- **Curl Command Modal:** Click the eye icon to view and copy curl commands with options to toggle between Canary/Non-Canary environments and force execution

**Use Cases:**
- Quickly find a specific job and its schedule
- Identify peak hours when most jobs are scheduled
- View curl commands for manual job execution
- Filter jobs by environment or frequency

---

### 📊 Today's Summary (Today's Report)

**Description:** Get a real-time snapshot of today's scheduler execution results. Monitor success rates, identify failures, and track data processing metrics.

**Features:**
- **Key Metrics:** Succeeded jobs, failed jobs, total jobs executed, total rows processed, and largest job size
- **Failed Schedulers Section:** Detailed breakdown of failed jobs with:
  - Retry status indicators showing which attempt failed
  - Scheduled time slots vs actual execution times
  - Severity badges (First attempt failed, Retry failed, Final failure)
  - Rundeck schedule information and remaining retry slots
- **Execution Table:** Complete list of today's executions with:
  - Analytic name, execution status, and time slots
  - Start/end times and duration
  - BigQuery data fetch vs saved data comparison
  - Highlighted successful time slots
  - Data mismatch warnings (when BQ data ≠ saved data)
- **Search Functionality:** Filter executions by analytic name

**Use Cases:**
- Monitor daily execution health at a glance
- Quickly identify and investigate failed jobs
- Track data processing volumes
- Identify retry patterns and final failures

---

### 📈 Overview (Reports Overview)

**Description:** Historical overview of scheduler performance with visual analytics showing trends and activity patterns over time.

**Features:**
- **Daily Breakdown Chart:** Bar chart showing success vs failed executions per day, helping identify trends and problematic periods
- **Scheduler Activity Heatmap:** Interactive heatmap displaying execution activity by hour of day, filtered by frequency (All/Daily/Weekly/Monthly)
  - Color-coded by execution status (Success/Retry/Failed)
  - Shows activity intensity across schedulers and time slots
  - Helps identify peak activity hours and problem patterns

**Use Cases:**
- Identify trends in success/failure rates over time
- Understand when schedulers are most active
- Spot recurring issues at specific times
- Analyze execution patterns by frequency type

---

### 🔍 Pattern Analysis

**Description:** Deep dive into execution patterns, success rates, and performance metrics to understand scheduler behavior and identify optimization opportunities.

**Features:**
- **Summary Statistics:**
  - Total unique schedulers
  - Overall success rate percentage
  - Peak activity hour
- **Duration Distribution Chart:** Visual breakdown of average execution duration per scheduler, sorted by performance
- **Attempt Analysis Chart:** Statistics on first-try success, first-try failures, retry successes, and retry failures
  - Shows percentage distribution of execution attempts
  - Helps understand retry effectiveness

**Use Cases:**
- Analyze which schedulers take longest to execute
- Understand retry patterns and success rates
- Identify schedulers that frequently require retries
- Optimize scheduling based on performance data

---

### 📋 All Data (All Scheduler Data)

**Description:** Comprehensive table view of all historical scheduler executions with detailed information for in-depth analysis and troubleshooting.

**Features:**
- **Detailed Execution Table:** Complete execution history with:
  - Scheduler name and execution date
  - Scheduled time slots (from Rundeck configuration)
  - Success time slot (which scheduled slot succeeded)
  - Execution status
  - Duration and data rows processed
- **Advanced Filtering:**
  - Search by scheduler name
  - Filter by specific date
  - Sort by any column (name, date, time slot, status, duration, data)
- **Slot Analysis:** Shows which scheduled time slot succeeded, helping identify retry patterns

**Use Cases:**
- Investigate specific scheduler execution history
- Analyze retry patterns for problematic schedulers
- Compare execution times across different dates
- Export or analyze execution data for reporting

---

## Data Files

The dashboard requires three JSON data files in the same directory:

- **`jobs-data.json`** - Rundeck job configurations and schedules
- **`today-data.json`** - Today's execution results
- **`past-data.json`** - Historical execution data

## Prerequisites

### Python (Recommended)

Python 3 is the recommended way to run the dashboard. Follow these steps to verify and install Python:

#### Verify Python Installation

1. **Check if Python 3 is installed:**
   ```bash
   python3 --version
   ```
   
   You should see output like: `Python 3.x.x`
   
   **Note:** If you see `Python 3.x.x` or higher, you're all set! Skip to the "Running the Dashboard" section.

2. **Check if Python (without version) is installed:**
   ```bash
   python --version
   ```
   
   If this shows Python 3.x.x, you can use `python` instead of `python3` in the commands below.

#### Install Python 3

If Python 3 is not installed, follow these steps based on your operating system:

**macOS:**
1. **Using Homebrew (Recommended):**
   ```bash
   # Install Homebrew if not already installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install Python 3
   brew install python3
   ```

2. **Using Official Installer:**
   - Visit [python.org/downloads](https://www.python.org/downloads/)
   - Download Python 3.x for macOS
   - Run the installer and follow the instructions
   - Make sure to check "Add Python to PATH" during installation

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install python3
```

**Windows:**
1. Visit [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.x for Windows
3. Run the installer
4. **Important:** Check "Add Python to PATH" during installation
5. After installation, verify in Command Prompt or PowerShell:
   ```cmd
   python --version
   ```

#### Verify Installation

After installation, verify Python 3 is working correctly:

```bash
python3 --version
# Should output: Python 3.x.x

python3 -m http.server --help
# Should show http.server help text
```

**Troubleshooting:**

- **Command not found:** Make sure Python is added to your system PATH
- **Permission denied:** On Linux/macOS, you may need to use `sudo` for installation
- **Multiple Python versions:** Use `python3` explicitly to ensure you're using Python 3

### Alternative Options

If you prefer not to use Python, you can also use:

- **Node.js:** Requires Node.js and npm installed
- **PHP:** Requires PHP installed

## Running the Dashboard

1. Ensure all three JSON data files are in the same directory as `scheduler-dashboard.html`
2. Start a local web server (required due to browser CORS restrictions):
   ```bash
   # Option 1: Python 3
   python3 -m http.server 8000
   
   # Option 2: Node.js
   npx http-server -p 8000
   
   # Option 3: PHP
   php -S localhost:8000
   ```
3. Open `http://localhost:8000/scheduler-dashboard.html` in your browser

## Notes

- The dashboard uses client-side JavaScript and requires a modern browser
- All data is loaded from JSON files - no backend server required
- Curl commands can be copied directly from the modal for manual execution
- Canary mode requires appropriate cookies for authentication
