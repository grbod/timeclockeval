# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Employee Time Clock Analysis System that processes CSV timeclock data to identify attendance patterns, anomalies, and generate management reports. The system creates detailed visualizations and produces comprehensive analysis reports for HR and management review.

## Core Architecture

### Single Module Design
- `main.py`: Contains the complete `TimeClockAnalyzer` class with all analysis logic
- Self-contained monolithic design with data processing, analysis, and visualization in one file
- No separate modules or packages - all functionality is within the main class

### Key Components
- **Data Processing**: CSV parsing and time format conversion (12-hour to minutes from midnight)
- **Period Analysis**: Automatic division of data into 2-week intervals for systematic review
- **Anomaly Detection**: Rule-based scoring system for attendance violations
- **Visualization**: Professional heat maps with color-coded timing analysis
- **Reporting**: Text-based management reports with employee rankings

### Data Flow
1. Load CSV with columns: `DisplayAs`, `InDate`, `OutDate`, `InTime`, `OutTime`, `InDow`, `OutDow`
2. Process into 2-week periods starting from Mondays
3. Analyze each employee per period using expected schedule rules
4. Generate dual heat maps (detailed punch times + anomaly scores)
5. Create comprehensive text reports for management

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Analysis
```bash
# Execute complete analysis (requires timeclock.csv in root directory)
python main.py
```

### Dependencies
Core packages defined in `requirements.txt`:
- pandas: CSV data processing
- numpy: Numerical computations and statistics
- matplotlib: Primary visualization library
- seaborn: Enhanced statistical plots

## Expected Schedule Configuration

The system analyzes against these hardcoded schedule expectations (in `TimeClockAnalyzer.__init__`):
- Morning arrival: 8:00 AM (480 minutes)
- Lunch departure: 12:00 PM (720 minutes)
- Lunch return: 12:30 PM (750 minutes)
- End times: 4:00 PM or 4:30 PM (960/990 minutes)
- Buffer tolerance: ±7 minutes for all times

## Anomaly Scoring System

Weighted scoring for attendance violations:
- **High (10 points)**: Missed entire days
- **Medium (5 points)**: Late arrivals, late lunch returns, incomplete days, date mismatches
- **Low (2 points)**: Irregular lunch timing, irregular end times, extra breaks

## Output Files

The system generates three files automatically:
- `timeclock_detailed_heatmap.png`: High-resolution detailed punch visualization
- `timeclock_detailed_heatmap.pdf`: Vector format for presentations
- `timeclock_analysis_report.txt`: Management summary with employee rankings

## Data Format Requirements

Input CSV must contain exact column names and formats:
- Employee names in "LastName, FirstName" format
- Dates in MM/DD/YY format
- Times in "HH:MMa/p" format (e.g., "07:54a", "04:31p")
- Each work day generates 2 rows: morning shift and afternoon shift punches