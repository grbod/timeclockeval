#!/usr/bin/env python3
"""
Employee Time Clock Analysis System

Analyzes employee time clock data over 2-week intervals to identify
extraordinary patterns and anomalies requiring management attention.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for lower memory
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from collections import defaultdict
import gc
import os
from PyPDF2 import PdfMerger
import warnings
warnings.filterwarnings('ignore')

class TimeClockAnalyzer:
    def __init__(self, csv_file_path):
        """Initialize the analyzer with time clock data."""
        self.csv_file_path = csv_file_path
        self.data = None
        self.processed_data = None
        self.two_week_periods = []
        self.analysis_results = {}
        
        # Standard schedule parameters (in minutes from midnight)
        self.EXPECTED_MORNING_ARRIVAL = 8 * 60  # 8:00 AM
        self.EXPECTED_LUNCH_DEPARTURE = 12 * 60  # 12:00 PM
        self.EXPECTED_LUNCH_RETURN = 12 * 60 + 30  # 12:30 PM
        self.EXPECTED_END_TIME_1 = 16 * 60  # 4:00 PM
        self.EXPECTED_END_TIME_2 = 16 * 60 + 30  # 4:30 PM
        
        # Buffer windows (in minutes)
        self.BUFFER_MINUTES = 7
        
    def load_data(self):
        """Load and parse the CSV time clock data."""
        try:
            self.data = pd.read_csv(self.csv_file_path)
            print(f"Loaded {len(self.data)} punch records")
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def time_to_minutes(self, time_str):
        """Convert time string (e.g., '07:54a') to minutes from midnight."""
        try:
            time_str = time_str.strip().lower()
            if time_str.endswith('a') or time_str.endswith('p'):
                am_pm = time_str[-1]
                time_part = time_str[:-1]
            else:
                return None
                
            hours, minutes = map(int, time_part.split(':'))
            
            if am_pm == 'p' and hours != 12:
                hours += 12
            elif am_pm == 'a' and hours == 12:
                hours = 0
                
            return hours * 60 + minutes
        except:
            return None
    
    def minutes_to_time(self, minutes):
        """Convert minutes from midnight to readable time string."""
        hours = minutes // 60
        mins = minutes % 60
        am_pm = 'AM' if hours < 12 else 'PM'
        
        if hours == 0:
            hours = 12
        elif hours > 12:
            hours -= 12
            
        return f"{hours}:{mins:02d} {am_pm}"
    
    def process_data(self):
        """Process raw data into structured format for analysis."""
        if self.data is None:
            return False
            
        processed_records = []
        
        for _, row in self.data.iterrows():
            try:
                # Parse date
                date_obj = datetime.strptime(row['InDate'], '%m/%d/%y').date()
                
                record = {
                    'employee': row['DisplayAs'],
                    'date': date_obj,
                    'day_of_week': row['InDow'],
                    'in_time_str': row['InTime'],
                    'out_time_str': row['OutTime'],
                    'in_time_minutes': self.time_to_minutes(row['InTime']),
                    'out_time_minutes': self.time_to_minutes(row['OutTime']),
                    'in_date': row['InDate'],
                    'out_date': row['OutDate']
                }
                
                if record['in_time_minutes'] is not None and record['out_time_minutes'] is not None:
                    processed_records.append(record)
                    
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
        self.processed_data = pd.DataFrame(processed_records)
        print(f"Processed {len(self.processed_data)} valid records")
        return True
    
    def create_two_week_periods(self):
        """Divide data into 2-week periods for analysis."""
        if self.processed_data is None or len(self.processed_data) == 0:
            return
            
        # Get date range
        min_date = self.processed_data['date'].min()
        max_date = self.processed_data['date'].max()
        
        # Create 2-week periods starting from Monday
        current_date = min_date
        while current_date.weekday() != 0:  # Move to Monday
            current_date -= timedelta(days=1)
            
        periods = []
        while current_date <= max_date:
            period_end = current_date + timedelta(days=13)  # 2 weeks
            periods.append({
                'start': current_date,
                'end': period_end,
                'label': f"{current_date.strftime('%m/%d')} - {period_end.strftime('%m/%d')}"
            })
            current_date += timedelta(days=14)
            
        self.two_week_periods = periods
        print(f"Created {len(periods)} two-week periods")
    
    def analyze_employee_period(self, employee, period):
        """Analyze a specific employee for a specific 2-week period."""
        period_data = self.processed_data[
            (self.processed_data['employee'] == employee) &
            (self.processed_data['date'] >= period['start']) &
            (self.processed_data['date'] <= period['end'])
        ].copy()
        
        if len(period_data) == 0:
            return {
                'employee': employee,
                'period': period['label'],
                'anomalies': [],
                'score': 0,
                'total_days': 0,
                'worked_days': 0,
                'missed_days': 0
            }
        
        # Group by date to analyze daily patterns
        daily_groups = period_data.groupby('date')
        anomalies = []
        
        # Calculate expected work days (Monday-Friday) in period
        expected_days = []
        current_date = period['start']
        while current_date <= period['end']:
            if current_date.weekday() < 5:  # Monday=0, Friday=4
                expected_days.append(current_date)
            current_date += timedelta(days=1)
        
        worked_days = len(daily_groups)
        missed_days = len(expected_days) - worked_days
        
        # Check for missed days
        worked_dates = set(daily_groups.groups.keys())
        for expected_date in expected_days:
            if expected_date not in worked_dates:
                anomalies.append({
                    'type': 'missed_day',
                    'date': expected_date,
                    'severity': 'high',
                    'description': f"Missed entire work day on {expected_date.strftime('%m/%d/%y')}"
                })
        
        # Analyze each worked day
        for date, day_data in daily_groups:
            day_data = day_data.sort_values('in_time_minutes')
            day_records = day_data.to_dict('records')
            
            # Check for date mismatches
            for record in day_records:
                if record['in_date'] != record['out_date']:
                    anomalies.append({
                        'type': 'date_mismatch',
                        'date': date,
                        'severity': 'medium',
                        'description': f"Punch dates don't match: {record['in_date']} vs {record['out_date']}"
                    })
            
            # Analyze daily punch patterns
            if len(day_records) == 1:
                # Only one punch pair - incomplete day
                anomalies.append({
                    'type': 'incomplete_day',
                    'date': date,
                    'severity': 'medium',
                    'description': f"Only one punch pair on {date.strftime('%m/%d/%y')}"
                })
            elif len(day_records) == 2:
                # Standard two punch pairs - check timing
                morning_record = day_records[0]
                afternoon_record = day_records[1]
                
                # Check morning arrival
                if morning_record['in_time_minutes'] > self.EXPECTED_MORNING_ARRIVAL + self.BUFFER_MINUTES:
                    late_minutes = morning_record['in_time_minutes'] - self.EXPECTED_MORNING_ARRIVAL
                    anomalies.append({
                        'type': 'late_arrival',
                        'date': date,
                        'severity': 'medium',
                        'description': f"Late arrival: {morning_record['in_time_str']} ({late_minutes} min late)",
                        'minutes_late': late_minutes
                    })
                
                # Check lunch departure timing
                lunch_out_time = morning_record['out_time_minutes']
                if abs(lunch_out_time - self.EXPECTED_LUNCH_DEPARTURE) > self.BUFFER_MINUTES:
                    anomalies.append({
                        'type': 'irregular_lunch_departure',
                        'date': date,
                        'severity': 'low',
                        'description': f"Irregular lunch departure: {morning_record['out_time_str']}"
                    })
                
                # Check lunch return timing
                lunch_return_time = afternoon_record['in_time_minutes']
                if lunch_return_time > self.EXPECTED_LUNCH_RETURN + self.BUFFER_MINUTES:
                    late_minutes = lunch_return_time - self.EXPECTED_LUNCH_RETURN
                    anomalies.append({
                        'type': 'late_lunch_return',
                        'date': date,
                        'severity': 'medium',
                        'description': f"Late lunch return: {afternoon_record['in_time_str']} ({late_minutes} min late)",
                        'minutes_late': late_minutes
                    })
                
                # Check end time
                end_time = afternoon_record['out_time_minutes']
                end_time_valid = (
                    abs(end_time - self.EXPECTED_END_TIME_1) <= self.BUFFER_MINUTES or
                    abs(end_time - self.EXPECTED_END_TIME_2) <= self.BUFFER_MINUTES
                )
                
                if not end_time_valid:
                    anomalies.append({
                        'type': 'irregular_end_time',
                        'date': date,
                        'severity': 'low',
                        'description': f"Irregular end time: {afternoon_record['out_time_str']}"
                    })
            
            elif len(day_records) > 2:
                # Extra punch pairs - additional breaks
                extra_punches = len(day_records) - 2
                anomalies.append({
                    'type': 'extra_punches',
                    'date': date,
                    'severity': 'low',
                    'description': f"Extra punch pairs ({extra_punches}) indicating additional breaks"
                })
        
        # Calculate anomaly score
        score = 0
        for anomaly in anomalies:
            if anomaly['severity'] == 'high':
                score += 10
            elif anomaly['severity'] == 'medium':
                score += 5
            else:  # low
                score += 2
        
        return {
            'employee': employee,
            'period': period['label'],
            'anomalies': anomalies,
            'score': score,
            'total_days': len(expected_days),
            'worked_days': worked_days,
            'missed_days': missed_days
        }
    
    def run_analysis(self):
        """Run complete analysis for all employees across all periods."""
        if not self.load_data():
            return False
            
        if not self.process_data():
            return False
            
        self.create_two_week_periods()
        
        # Get unique employees
        employees = sorted(self.processed_data['employee'].unique())
        
        # Analyze each employee for each period
        for employee in employees:
            self.analysis_results[employee] = {}
            for period in self.two_week_periods:
                result = self.analyze_employee_period(employee, period)
                self.analysis_results[employee][period['label']] = result
        
        print(f"Analysis complete for {len(employees)} employees across {len(self.two_week_periods)} periods")
        return True
    
    def generate_detailed_punch_heatmap(self):
        """Generate paginated heat maps with memory optimization."""
        if self.processed_data is None or len(self.processed_data) == 0:
            print("No processed data to visualize")
            return
        
        # Get employees and create day-by-day data structure
        employees = sorted(self.processed_data['employee'].unique())
        
        # CHANGE REQUEST #4: Create master list of ALL dates worked by ANY employee
        all_dates = sorted(self.processed_data['date'].unique())
        
        # Create data structure for punch details
        punch_data = {}
        color_data = {}
        total_hours_data = {}
        
        # Process all data first (this is relatively memory efficient)
        for employee in employees:
            punch_data[employee] = {}
            color_data[employee] = {}
            total_hours_data[employee] = {}
            
            # Get employee's data
            emp_data = self.processed_data[self.processed_data['employee'] == employee]
            employee_dates = set(emp_data['date'].unique())
            
            # Process ALL dates for this employee
            for date in all_dates:
                day_name = date.strftime('%a')  # Mon, Tue, Wed, Thu, Fri
                day_key = f"{date.strftime('%m/%d')} ({day_name})"
                
                # Check if employee worked on this date
                if date in employee_dates:
                    # Employee worked on this date - process normally
                    day_data = emp_data[emp_data['date'] == date].sort_values('in_time_minutes')
                    
                    # Check for multiple punch detection (>2 punch pairs per day)
                    daily_punch_count = len(day_data)
                    flagged_for_multiple_punches = daily_punch_count > 2
                    
                    punch_data[employee][day_key] = {
                        'morn_in': '',
                        'morn_out': '',
                        'aft_in': '',
                        'aft_out': ''
                    }
                    # Initialize with default colors (may be overridden for flagged days)
                    default_color = '#FFB6C1' if flagged_for_multiple_punches else '#F8F8F8'
                    color_data[employee][day_key] = {
                        'morn_in': default_color,
                        'morn_out': default_color,
                        'aft_in': default_color,
                        'aft_out': default_color
                    }
                    
                    # Process punch pairs for this day
                    records = day_data.to_dict('records')
                else:
                    # Employee was absent - show N/A with gray background
                    flagged_for_multiple_punches = False  # No flagging for absent days
                    
                    punch_data[employee][day_key] = {
                        'morn_in': 'N/A',
                        'morn_out': 'N/A',
                        'aft_in': 'N/A',
                        'aft_out': 'N/A'
                    }
                    color_data[employee][day_key] = {
                        'morn_in': '#D3D3D3',  # Gray background for absent days
                        'morn_out': '#D3D3D3',
                        'aft_in': '#D3D3D3',
                        'aft_out': '#D3D3D3'
                    }
                    records = []  # No records to process for absent days
                
                # Process records (same logic as before)
                if len(records) >= 1:
                    # First punch pair - determine if morning or afternoon based on start time
                    first_rec = records[0]
                    first_punch_time = first_rec['in_time_minutes']
                    
                    # Check if first punch is before 11:00 AM (660 minutes from midnight)
                    if first_punch_time < 660:  # Before 11:00 AM
                        # Place in morning columns
                        punch_data[employee][day_key]['morn_in'] = first_rec['in_time_str']
                        punch_data[employee][day_key]['morn_out'] = first_rec['out_time_str']
                        morning_rec = first_rec
                    else:  # 11:00 AM or later
                        # Place in afternoon columns
                        punch_data[employee][day_key]['aft_in'] = first_rec['in_time_str']
                        punch_data[employee][day_key]['aft_out'] = first_rec['out_time_str']
                        afternoon_rec = first_rec
                    
                    # Skip color analysis for flagged multiple punch days - keep pink background
                    if not flagged_for_multiple_punches:
                        # Apply color analysis based on where the first punch was placed
                        if first_punch_time < 660:  # First punch was placed in morning columns
                            # Enhanced severity color classification for morning in
                            morn_in_diff = abs(morning_rec['in_time_minutes'] - self.EXPECTED_MORNING_ARRIVAL)
                            if morn_in_diff <= 5:
                                color_data[employee][day_key]['morn_in'] = '#228B22'  # Green: Acceptable
                            elif morn_in_diff <= 7:
                                color_data[employee][day_key]['morn_in'] = '#DAA520'  # Yellow: Minor Delay
                            elif morn_in_diff <= 11:
                                color_data[employee][day_key]['morn_in'] = '#FF6600'  # Orange: Major Delay
                            else:
                                color_data[employee][day_key]['morn_in'] = '#DC143C'  # Red: Significant Delay
                            
                            # Enhanced severity color classification for lunch departure
                            morn_out_diff = abs(morning_rec['out_time_minutes'] - self.EXPECTED_LUNCH_DEPARTURE)
                            if morn_out_diff <= 5:
                                color_data[employee][day_key]['morn_out'] = '#228B22'  # Green: Acceptable
                            elif morn_out_diff <= 7:
                                color_data[employee][day_key]['morn_out'] = '#DAA520'  # Yellow: Minor Delay
                            elif morn_out_diff <= 11:
                                color_data[employee][day_key]['morn_out'] = '#FF6600'  # Orange: Major Delay
                            else:
                                color_data[employee][day_key]['morn_out'] = '#DC143C'  # Red: Significant Delay
                            
                            # Check for missed out punch (InDate != OutDate)
                            if morning_rec['in_date'] != morning_rec['out_date']:
                                color_data[employee][day_key]['morn_out'] = '#9932CC'  # Purple: Missed Out Punch
                        else:  # First punch was placed in afternoon columns
                            # For afternoon starters, compare against lunch return like normal
                            aft_in_diff = abs(afternoon_rec['in_time_minutes'] - self.EXPECTED_LUNCH_RETURN)
                            if aft_in_diff <= 5:
                                color_data[employee][day_key]['aft_in'] = '#228B22'  # Green: Acceptable
                            elif aft_in_diff <= 7:
                                color_data[employee][day_key]['aft_in'] = '#DAA520'  # Yellow: Minor Delay
                            elif aft_in_diff <= 11:
                                color_data[employee][day_key]['aft_in'] = '#FF6600'  # Orange: Major Delay
                            else:
                                color_data[employee][day_key]['aft_in'] = '#DC143C'  # Red: Significant Delay
                            
                            # Color end time
                            aft_out_time = afternoon_rec['out_time_minutes']
                            end_time_diff_1 = abs(aft_out_time - self.EXPECTED_END_TIME_1)
                            end_time_diff_2 = abs(aft_out_time - self.EXPECTED_END_TIME_2)
                            min_end_diff = min(end_time_diff_1, end_time_diff_2)
                            
                            if min_end_diff <= 5:
                                color_data[employee][day_key]['aft_out'] = '#228B22'  # Green: Acceptable
                            elif min_end_diff <= 7:
                                color_data[employee][day_key]['aft_out'] = '#DAA520'  # Yellow: Minor Delay
                            elif min_end_diff <= 11:
                                color_data[employee][day_key]['aft_out'] = '#FF6600'  # Orange: Major Delay
                            else:
                                color_data[employee][day_key]['aft_out'] = '#DC143C'  # Red: Significant Delay
                            
                            # Check for missed out punch (InDate != OutDate)
                            if afternoon_rec['in_date'] != afternoon_rec['out_date']:
                                color_data[employee][day_key]['aft_out'] = '#9932CC'  # Purple: Missed Out Punch
                
                if len(records) >= 2:
                    # Handle second punch pair - only if first punch was in morning
                    if first_punch_time < 660:  # First punch was in morning, so this is afternoon
                        afternoon_rec = records[1]
                        punch_data[employee][day_key]['aft_in'] = afternoon_rec['in_time_str']
                        punch_data[employee][day_key]['aft_out'] = afternoon_rec['out_time_str']
                        
                        # Skip color analysis for flagged multiple punch days - keep pink background
                        if not flagged_for_multiple_punches:
                            # Enhanced severity color classification for lunch return
                            aft_in_diff = abs(afternoon_rec['in_time_minutes'] - self.EXPECTED_LUNCH_RETURN)
                            if aft_in_diff <= 5:
                                color_data[employee][day_key]['aft_in'] = '#228B22'  # Green: Acceptable
                            elif aft_in_diff <= 7:
                                color_data[employee][day_key]['aft_in'] = '#DAA520'  # Yellow: Minor Delay
                            elif aft_in_diff <= 11:
                                color_data[employee][day_key]['aft_in'] = '#FF6600'  # Orange: Major Delay
                            else:
                                color_data[employee][day_key]['aft_in'] = '#DC143C'  # Red: Significant Delay
                            
                            # Enhanced severity color classification for end of day
                            aft_out_time = afternoon_rec['out_time_minutes']
                            end_time_diff_1 = abs(aft_out_time - self.EXPECTED_END_TIME_1)
                            end_time_diff_2 = abs(aft_out_time - self.EXPECTED_END_TIME_2)
                            min_end_diff = min(end_time_diff_1, end_time_diff_2)
                            
                            if min_end_diff <= 5:
                                color_data[employee][day_key]['aft_out'] = '#228B22'  # Green: Acceptable
                            elif min_end_diff <= 7:
                                color_data[employee][day_key]['aft_out'] = '#DAA520'  # Yellow: Minor Delay
                            elif min_end_diff <= 11:
                                color_data[employee][day_key]['aft_out'] = '#FF6600'  # Orange: Major Delay
                            else:
                                color_data[employee][day_key]['aft_out'] = '#DC143C'  # Red: Significant Delay
                            
                            # Check for missed out punch (InDate != OutDate)
                            if afternoon_rec['in_date'] != afternoon_rec['out_date']:
                                color_data[employee][day_key]['aft_out'] = '#9932CC'  # Purple: Missed Out Punch
                
                # Calculate total hours for this day
                # Get ALL records for this employee on this date to handle irregular days
                date_str = date.strftime('%m/%d/%y') if date in employee_dates else None
                if date_str:
                    # Get all punch pairs for this specific date
                    all_day_records = day_data if date in employee_dates else []
                    total_minutes = 0
                    
                    # Sum up all punch pairs
                    for record in records:
                        if record['in_time_minutes'] is not None and record['out_time_minutes'] is not None:
                            # Calculate time worked for this punch pair
                            minutes_worked = record['out_time_minutes'] - record['in_time_minutes']
                            # Handle case where out punch is past midnight
                            if minutes_worked < 0:
                                minutes_worked += 1440  # Add 24 hours
                            total_minutes += minutes_worked
                    
                    # Convert to hours:minutes format
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    total_hours_data[employee][day_key] = f"{hours}:{minutes:02d}"
                else:
                    # Absent day
                    total_hours_data[employee][day_key] = "0:00"
        
        # Now generate pages
        employees_per_page = 2
        total_pages = (len(employees) + employees_per_page - 1) // employees_per_page
        
        # List to store PDF files
        temp_pdf_files = []
        
        print(f"Generating {total_pages} pages for {len(employees)} employees...")
        
        for page_num in range(total_pages):
            start_idx = page_num * employees_per_page
            end_idx = min(start_idx + employees_per_page, len(employees))
            employees_subset = employees[start_idx:end_idx]
            
            print(f"  Processing page {page_num + 1}/{total_pages}: {', '.join(employees_subset)}")
            
            # Generate page and save as temporary PDF
            temp_filename = f'temp_page_{page_num + 1}.pdf'
            self.generate_detailed_punch_heatmap_page(
                employees_subset, page_num + 1, total_pages,
                punch_data, color_data, total_hours_data, temp_filename
            )
            temp_pdf_files.append(temp_filename)
            
            # Clear memory
            plt.close('all')
            gc.collect()
        
        # Combine all PDFs into one
        print("Combining pages into single PDF...")
        merger = PdfMerger()
        
        for pdf_file in temp_pdf_files:
            if os.path.exists(pdf_file):
                merger.append(pdf_file)
        
        # Save final combined PDF
        merger.write('timeclock_detailed_heatmap.pdf')
        merger.close()
        
        # Clean up temporary files
        for pdf_file in temp_pdf_files:
            if os.path.exists(pdf_file):
                os.remove(pdf_file)
        
        print("Enhanced heat map saved:")
        print("  - timeclock_detailed_heatmap.pdf (Multi-page PDF)")
    
    def generate_detailed_punch_heatmap_page(self, employees_subset, page_num, total_pages, punch_data, color_data, total_hours_data, output_filename):
        """Generate a single page of the heat map for a subset of employees."""
        # Enhanced column headers
        columns = ['Morning\nArrival', 'Lunch\nDeparture', 'Lunch\nReturn', 'End of\nDay', 'Total\nHours']
        column_positions = [0.5, 1.5, 2.5, 3.5, 4.25]  # Total hours column is narrower
        
        # Prepare data for this page only
        all_employees_expanded = []
        punch_times_grid = []
        colors_grid = []
        employee_separators = []
        
        # Calculate figure size for just these employees
        total_rows = sum(len(punch_data[emp]) for emp in employees_subset if emp in punch_data)
        # Add spacing rows
        if len(employees_subset) > 1:
            total_rows += len(employees_subset) - 1
        
        cell_height = 0.7  # Height per cell (optimized for 2 employees)
        cell_width = 2.0   # Width per cell (reduced for letter size)
        
        # Standard letter size: 8.5 x 11 inches
        fig_width = 8.5
        fig_height = 11  # Keep consistent height regardless of employee count
        
        # Create figure with only one subplot (no secondary heat map for memory efficiency)
        fig, ax1 = plt.subplots(1, 1, figsize=(fig_width, fig_height))
        
        # Set professional styling
        plt.style.use('default')
        fig.patch.set_facecolor('white')
        
        # Title removed per request
        
        # Build grid data for subset of employees
        row_index = 0
        for emp_idx, employee in enumerate(employees_subset):
            if employee not in punch_data:
                continue
                
            employee_days = sorted([day for day in punch_data[employee].keys()])
            employee_start_row = row_index
            
            for day in employee_days:
                all_employees_expanded.append(f"{employee}\n{day}")
                
                # Get punch times and colors for this employee-day
                day_punches = [
                    punch_data[employee][day]['morn_in'],
                    punch_data[employee][day]['morn_out'],
                    punch_data[employee][day]['aft_in'],
                    punch_data[employee][day]['aft_out'],
                    total_hours_data[employee][day]  # Add total hours
                ]
                
                # Determine color for total hours based on value
                total_hours_str = total_hours_data[employee][day]
                if total_hours_str == "0:00":
                    # Absent day
                    hours_color = '#D3D3D3'  # Gray for absent
                else:
                    # Parse hours and minutes
                    hours_parts = total_hours_str.split(':')
                    total_hours_float = float(hours_parts[0]) + float(hours_parts[1])/60
                    
                    if total_hours_float < 7.5:
                        hours_color = '#9247d5'  # Purple for under-hours
                    elif total_hours_float > 8.5:
                        hours_color = '#2c67dc'  # Blue background for overtime
                    else:
                        hours_color = '#FFFFFF'  # White background for normal hours
                
                day_colors = [
                    color_data[employee][day]['morn_in'],
                    color_data[employee][day]['morn_out'],
                    color_data[employee][day]['aft_in'],
                    color_data[employee][day]['aft_out'],
                    hours_color  # Add color for total hours
                ]
                
                punch_times_grid.append(day_punches)
                colors_grid.append(day_colors)
                row_index += 1
            
            # Add visual spacing between employees (except after last employee)
            if emp_idx < len(employees_subset) - 1:
                # Add spacing row - empty with white background
                all_employees_expanded.append("")  # Empty label for spacing row
                punch_times_grid.append(["", "", "", "", ""])  # Empty punch data with 5 columns
                colors_grid.append(["white", "white", "white", "white", "white"])  # White background for 5 columns
                row_index += 1
            
            # Mark employee separator
            employee_separators.append(employee_start_row + len(employee_days))
        
        # Create the enhanced heatmap with larger cells and better spacing
        for i, (row_punches, row_colors) in enumerate(zip(punch_times_grid, colors_grid)):
            for j, (punch_time, color) in enumerate(zip(row_punches, row_colors)):
                # Handle spacing rows without borders for clean separation
                if color == 'white':
                    # Spacing row - no border, clean white space
                    if j == 4:  # Narrower column for total hours
                        rect = plt.Rectangle((j + 0.02, len(punch_times_grid) - 1 - i + 0.02), 
                                           0.48, 0.96,  # Half width for spacing in total hours column
                                           facecolor=color,
                                           edgecolor='white', linewidth=0,
                                           alpha=1.0)
                    else:
                        rect = plt.Rectangle((j + 0.02, len(punch_times_grid) - 1 - i + 0.02), 
                                           0.96, 0.96,
                                           facecolor=color,
                                           edgecolor='white', linewidth=0,
                                           alpha=1.0)
                else:
                    # Check if this is the total hours column
                    if j == 4:  # Total hours column
                        # Special formatting for total hours with reduced width
                        rect = plt.Rectangle((j + 0.02, len(punch_times_grid) - 1 - i + 0.02), 
                                           0.48, 0.96,  # Half width (0.48 instead of 0.96)
                                           facecolor=color,
                                           edgecolor='#34495E', linewidth=2.0,  # Bold dark gray border
                                           alpha=1.0)
                    else:
                        # Regular data cell
                        rect = plt.Rectangle((j + 0.02, len(punch_times_grid) - 1 - i + 0.02), 
                                           0.96, 0.96,  # Slightly smaller than 1 to create padding
                                           facecolor=color,
                                           edgecolor='#34495E', linewidth=1.5,
                                           alpha=0.9)
                ax1.add_patch(rect)
                
                # Add punch time text with enhanced readability
                if punch_time:
                    # Skip text rendering for spacing rows (white background)
                    if color == 'white':
                        continue  # Don't render any text for spacing rows
                    
                    # Handle flagged multiple punch notation
                    if color == '#FFB6C1' and j == 3:  # Pink background on last column (End of Day)
                        # Add flagged notation in italic dark gray
                        ax1.text(j + 0.5, len(punch_times_grid) - 1 - i + 0.5, 
                               'Flagged: Additional\nPunches Detected',
                               ha='center', va='center', fontsize=8, 
                               style='italic', color='#495057', fontweight='normal')
                        continue  # Skip normal punch time rendering for this cell
                    
                    # Check if this is the total hours column
                    if j == 4:  # Total hours column
                        # Special handling for hours column
                        if color == '#2c67dc':  # Blue background (overtime)
                            text_color = 'white'
                        elif color == '#9247d5':  # Purple background (under-hours)
                            text_color = 'white'
                        elif color == '#D3D3D3':  # Gray background (absent)
                            text_color = '#6C757D'
                        else:  # White background (normal hours)
                            text_color = '#2C3E50'  # Dark text
                        
                        # Render with bold monospace font, adjusted for narrower column
                        ax1.text(j + 0.25, len(punch_times_grid) - 1 - i + 0.5, punch_time,
                               ha='center', va='center', fontsize=11, fontweight='bold',
                               color=text_color, family='monospace')
                    else:
                        # Determine text color based on new color scheme
                        if color == '#228B22':  # Green: Acceptable
                            text_color = '#2C3E50'  # Dark text for readability
                        elif color == '#DAA520':  # Yellow: Minor Delay
                            text_color = '#2C3E50'  # Dark text for readability
                        elif color == '#FF6600':  # Orange: Major Delay
                            text_color = 'white'  # White text for contrast
                        elif color == '#DC143C':  # Red: Significant Delay
                            text_color = 'white'  # White text for contrast
                        elif color == '#9932CC':  # Purple: Missed Out Punch
                            text_color = 'white'  # White text for contrast
                        elif color == '#FFB6C1':  # Pink: Multiple punches flagged
                            text_color = '#495057'  # Dark gray for readability
                        elif color == '#D3D3D3':  # Gray: Absent days
                            text_color = '#6C757D'  # Medium gray for N/A text
                        else:  # Light gray (missing data)
                            text_color = '#6C757D'  # Medium gray
                        
                        ax1.text(j + 0.5, len(punch_times_grid) - 1 - i + 0.5, punch_time,
                               ha='center', va='center', fontsize=10, fontweight='bold',
                               color=text_color, family='monospace')
                elif color != 'white':  # Don't show N/A for spacing rows
                    # Show "N/A" for missing punches (but not for spacing rows)
                    if color == '#D3D3D3':  # Absent day styling
                        text_color = '#6C757D'  # Medium gray for absent days
                    else:
                        text_color = '#6C757D'  # Medium gray for missing punches
                    
                    ax1.text(j + 0.5, len(punch_times_grid) - 1 - i + 0.5, 'N/A',
                           ha='center', va='center', fontsize=9, fontweight='normal',
                           color=text_color, style='italic')
        
        # Enhanced axes setup
        ax1.set_xlim(-0.1, 4.7)  # Adjusted for narrower total hours column
        ax1.set_ylim(-0.1, len(punch_times_grid) + 1.5)  # Extra space for column headers at top
        
        # Move column headers to top
        ax1.set_xticks(column_positions)
        ax1.set_xticklabels([])  # Remove bottom labels
        
        # Add column headers at the top
        for i, (pos, col) in enumerate(zip(column_positions, columns)):
            ax1.text(pos, len(punch_times_grid) + 0.5, col, 
                    ha='center', va='bottom', fontsize=11, fontweight='bold', 
                    color='#2C3E50')
        
        # Enhanced row labels (employee names and days)
        ax1.set_yticks([i + 0.5 for i in range(len(all_employees_expanded))])
        ax1.set_yticklabels(reversed(all_employees_expanded), fontsize=8, color='#2C3E50')
        
        # Enhanced axis labels
        ax1.set_ylabel('EMPLOYEES & WORK DAYS', fontsize=11, fontweight='bold', color='#2C3E50', labelpad=10)
        
        # Add professional employee separator lines
        for sep_row in employee_separators:
            if sep_row < len(punch_times_grid) - 1:  # Don't draw after last employee
                ax1.axhline(y=len(punch_times_grid) - sep_row - 0.5, color='#34495E', linewidth=1.5, alpha=0.3)
        
        # Grid styling
        ax1.set_axisbelow(True)
        ax1.grid(False)
        
        # Clean up plot borders
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_color('#34495E')
        ax1.spines['left'].set_color('#34495E')
        ax1.tick_params(colors='#34495E', which='both')
        
        # Create horizontal color legend at the top
        legend_elements = [
            plt.Rectangle((0, 0), 1, 1, facecolor='#228B22', label='Acceptable (±5 min)'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#DAA520', label='Minor (5-7 min)'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#FF6600', label='Major (7-11 min)'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#DC143C', label='Significant (>11 min)'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#9932CC', label='Missed Out Punch'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#FFB6C1', edgecolor='#34495E', label='Multiple Punches'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#F8F8F8', edgecolor='#34495E', label='Missing Data'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#D3D3D3', edgecolor='#34495E', label='Absent Day')
        ]
        
        # Add the legend at the top (no title now)
        fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.92),
                  ncol=4, fontsize=9, frameon=True, fancybox=True, shadow=True)
        
        # Enhanced layout and save
        plt.tight_layout()
        plt.subplots_adjust(top=0.86)  # Make room for legend only
        
        # Add page number in lower right corner
        ax1.text(0.95, 0.02, f'{page_num} of {total_pages}', 
                transform=ax1.transAxes, ha='right', va='bottom',
                fontsize=10, color='#2C3E50', style='italic')
        
        # Save with 300 DPI (reduced from 400)
        plt.savefig(output_filename, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', format='pdf')
        
        # Don't show plot - just save
        plt.close(fig)
    
    
    def generate_heat_map(self):
        """Generate both detailed punch heat map and overall anomaly score heat map."""
        self.generate_detailed_punch_heatmap()
    
    def generate_report(self):
        """Generate detailed text report for management review."""
        if not self.analysis_results:
            print("No analysis results to report")
            return
        
        report = []
        report.append("=" * 80)
        report.append("EMPLOYEE TIME CLOCK ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Data Source: {self.csv_file_path}")
        report.append("")
        
        # Summary statistics
        total_employees = len(self.analysis_results)
        total_periods = len(self.two_week_periods)
        
        report.append("SUMMARY STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Employees Analyzed: {total_employees}")
        report.append(f"Analysis Periods: {total_periods}")
        report.append(f"Period Range: {self.two_week_periods[0]['label']} to {self.two_week_periods[-1]['label']}")
        report.append("")
        
        # Identify systematic offenders
        systematic_offenders = []
        for employee, periods in self.analysis_results.items():
            high_score_periods = sum(1 for result in periods.values() if result['score'] >= 20)
            total_anomalies = sum(len(result['anomalies']) for result in periods.values())
            avg_score = np.mean([result['score'] for result in periods.values()])
            
            if high_score_periods >= 2 or avg_score >= 15:
                systematic_offenders.append({
                    'employee': employee,
                    'avg_score': avg_score,
                    'high_score_periods': high_score_periods,
                    'total_anomalies': total_anomalies
                })
        
        systematic_offenders.sort(key=lambda x: x['avg_score'], reverse=True)
        
        report.append("EMPLOYEES REQUIRING IMMEDIATE ATTENTION")
        report.append("-" * 50)
        if systematic_offenders:
            for offender in systematic_offenders[:5]:  # Top 5
                report.append(f"• {offender['employee']}")
                report.append(f"  Average Score: {offender['avg_score']:.1f}")
                report.append(f"  High-Score Periods: {offender['high_score_periods']}/{total_periods}")
                report.append(f"  Total Anomalies: {offender['total_anomalies']}")
                report.append("")
        else:
            report.append("No employees require immediate attention.")
            report.append("")
        
        # Period-by-period analysis
        report.append("DETAILED PERIOD ANALYSIS")
        report.append("-" * 40)
        
        for period in self.two_week_periods:
            period_label = period['label']
            report.append(f"\nPeriod: {period_label}")
            report.append("-" * 30)
            
            # Collect all results for this period
            period_results = []
            for employee, periods in self.analysis_results.items():
                if period_label in periods:
                    period_results.append(periods[period_label])
            
            if not period_results:
                report.append("No data for this period")
                continue
            
            # Period statistics
            total_missed_days = sum(r['missed_days'] for r in period_results)
            high_score_employees = [r for r in period_results if r['score'] >= 20]
            avg_period_score = np.mean([r['score'] for r in period_results])
            
            report.append(f"Period Summary:")
            report.append(f"  Average Anomaly Score: {avg_period_score:.1f}")
            report.append(f"  Total Missed Days: {total_missed_days}")
            report.append(f"  High-Risk Employees: {len(high_score_employees)}")
            
            if high_score_employees:
                report.append("  Employees with High Scores:")
                for emp_result in sorted(high_score_employees, key=lambda x: x['score'], reverse=True):
                    report.append(f"    • {emp_result['employee']}: {emp_result['score']} points")
            
            report.append("")
        
        # Anomaly breakdown
        report.append("ANOMALY TYPE BREAKDOWN")
        report.append("-" * 40)
        
        anomaly_counts = defaultdict(int)
        for employee_results in self.analysis_results.values():
            for period_result in employee_results.values():
                for anomaly in period_result['anomalies']:
                    anomaly_counts[anomaly['type']] += 1
        
        for anomaly_type, count in sorted(anomaly_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"{anomaly_type.replace('_', ' ').title()}: {count}")
        
        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        # Save report to file
        report_text = "\n".join(report)
        with open('timeclock_analysis_report.txt', 'w') as f:
            f.write(report_text)
        
        print("Detailed report saved as 'timeclock_analysis_report.txt'")
        print("\nReport Preview:")
        print("\n".join(report[:50]))  # Show first 50 lines
        
        return report_text

def main():
    """Main function to run the complete analysis."""
    print("Employee Time Clock Analysis System")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = TimeClockAnalyzer('timeclock.csv')
    
    # Run analysis
    if analyzer.run_analysis():
        print("\nGenerating visualizations and reports...")
        
        # Generate heat map
        analyzer.generate_heat_map()
        
        # Generate detailed report
        analyzer.generate_report()
        
        print("\nAnalysis complete!")
        print("Files generated:")
        print("  - timeclock_detailed_heatmap.png (Detailed punch-by-punch + overall heat maps)")
        print("  - timeclock_analysis_report.txt (Detailed report)")
    else:
        print("Analysis failed. Please check your data file.")

if __name__ == "__main__":
    main()