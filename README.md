# Employee Time Clock Analysis System

A comprehensive Python-based analysis tool for employee time clock data that identifies patterns, anomalies, and attendance issues through detailed visualizations and management reports.

## Features

### 📊 Detailed Punch-by-Punch Heat Map
- **Visual Analysis**: Color-coded grid showing each employee's daily punch times
- **Professional Styling**: Large, clear cells with excellent readability
- **Color Coding**: 
  - 🟢 Green: On time (±5 minutes)
  - 🟡 Yellow: Minor delay (5-7 minutes)
  - 🔴 Red: Significant delay (>7 minutes)
  - ⚪ Gray: Missing punch data

### 📈 Anomaly Detection
- **Late Arrivals**: Identifies employees arriving >7 minutes late
- **Irregular Lunch Times**: Tracks lunch departure and return timing
- **Missed Days**: Detects complete absences
- **Extra Breaks**: Flags additional punch pairs indicating extra breaks
- **Scoring System**: Weighted anomaly scores (High=10pts, Medium=5pts, Low=2pts)

### 📋 Management Reports
- **Executive Summary**: Key statistics and high-priority employees
- **Period Analysis**: 2-week interval breakdowns
- **Anomaly Breakdown**: Categorized violation counts
- **Systematic Offenders**: Employees requiring immediate attention

### 🎯 Expected Schedule
- **Morning Arrival**: 8:00 AM
- **Lunch Departure**: 12:00 PM  
- **Lunch Return**: 12:30 PM
- **End of Day**: 4:00 PM or 4:30 PM
- **Buffer Window**: ±7 minutes tolerance

## Installation

### Prerequisites
- Python 3.7+
- Required packages: pandas, numpy, matplotlib, seaborn

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd timeclockchecker

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install pandas numpy matplotlib seaborn

# Run the analysis
python main.py
```

## Usage

### Input Data Format
Place your time clock data in `timeclock.csv` with the following columns:
- `DisplayAs`: Employee name (format: "LastName, FirstName")
- `InDate`: Punch-in date (MM/DD/YY)
- `OutDate`: Punch-out date (MM/DD/YY)
- `InTime`: Punch-in time (HH:MMa/p format, e.g., "07:54a")
- `OutTime`: Punch-out time (HH:MMa/p format, e.g., "04:31p")
- `InDow`: Day of week for punch-in
- `OutDow`: Day of week for punch-out

### Running Analysis
```bash
python main.py
```

### Generated Outputs
- `timeclock_detailed_heatmap.png` - High-resolution heat map visualization
- `timeclock_detailed_heatmap.pdf` - Vector format for presentations
- `timeclock_analysis_report.txt` - Detailed management report

## Data Structure Understanding

### Daily Punch Pattern
Each employee generates **2 rows per work day**:
1. **Morning Shift**: Arrival to lunch departure
2. **Afternoon Shift**: Lunch return to end of day

### Analysis Periods
- Data is automatically divided into **2-week intervals**
- Each period analyzed independently
- Results aggregated for trend analysis

## Anomaly Types

| Type | Severity | Description |
|------|----------|-------------|
| Missed Day | High (10pts) | Complete absence from work |
| Late Arrival | Medium (5pts) | >7 minutes late for morning shift |
| Late Lunch Return | Medium (5pts) | >7 minutes late returning from lunch |
| Incomplete Day | Medium (5pts) | Only one punch pair when two expected |
| Date Mismatch | Medium (5pts) | InDate ≠ OutDate |
| Irregular Lunch Departure | Low (2pts) | Lunch timing outside ±7min window |
| Irregular End Time | Low (2pts) | End time outside acceptable windows |
| Extra Punches | Low (2pts) | Additional breaks beyond standard pattern |

## Sample Output

### Heat Map Features
- **Large Format**: 20x24+ inches for clear visibility
- **Professional Colors**: Bootstrap-inspired color scheme
- **Smart Contrast**: Text color automatically adjusts for readability
- **Employee Grouping**: Clear separation between different employees
- **Comprehensive Legend**: Color coding explanation included

### Report Sample
```
EMPLOYEES REQUIRING IMMEDIATE ATTENTION
--------------------------------------------------
• Santos, Clayton
  Average Score: 90.0
  High-Score Periods: 1/1
  Total Anomalies: 10

• Felice, Aldo
  Average Score: 36.0
  High-Score Periods: 1/1
  Total Anomalies: 9
```

## Configuration

### Customizable Parameters
Edit the `TimeClockAnalyzer` class to adjust:
- Expected arrival/departure times
- Buffer window tolerance (default: 7 minutes)
- Scoring weights for different anomaly types
- Color scheme and visualization settings

### Time Parameters
```python
EXPECTED_MORNING_ARRIVAL = 8 * 60    # 8:00 AM
EXPECTED_LUNCH_DEPARTURE = 12 * 60   # 12:00 PM
EXPECTED_LUNCH_RETURN = 12 * 60 + 30 # 12:30 PM
EXPECTED_END_TIME_1 = 16 * 60        # 4:00 PM
EXPECTED_END_TIME_2 = 16 * 60 + 30   # 4:30 PM
BUFFER_MINUTES = 7                   # ±7 minute tolerance
```

## Technical Details

### Dependencies
- **pandas**: Data processing and CSV handling
- **numpy**: Numerical computations and statistics
- **matplotlib**: Core plotting and visualization
- **seaborn**: Enhanced statistical visualizations

### Performance
- Handles datasets with hundreds of employees
- Processes thousands of punch records efficiently
- Optimized memory usage for large time periods
- High-resolution output suitable for presentations

## License

This project is provided as-is for time clock analysis and management reporting purposes.

## Support

For issues or questions:
1. Check that your CSV data matches the expected format
2. Ensure all required Python packages are installed
3. Verify that date/time formats are consistent in your data

---

**Generated with Claude Code** - An AI-powered employee time analysis solution.