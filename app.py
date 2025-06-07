#!/usr/bin/env python3
"""
Streamlit Frontend for Employee Time Clock Analysis System
"""

import streamlit as st
import pandas as pd
import tempfile
import os
import time
from pathlib import Path
import base64
from main import TimeClockAnalyzer

# Page configuration
st.set_page_config(
    page_title="Time Clock Analyzer",
    page_icon="⏰",
    layout="wide"
)

# Custom CSS for console-style output
st.markdown("""
<style>
.console-output {
    background-color: #1e1e1e;
    color: #228B22;
    font-family: 'Courier New', monospace;
    padding: 20px;
    border-radius: 5px;
    height: 500px;
    overflow-y: scroll;
    white-space: pre-wrap;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

def get_binary_file_downloader_html(file_path, file_label='File'):
    """Generate download link for binary files"""
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}" class="btn btn-primary">📥 Download {file_label}</a>'

def main():
    # Header
    st.title("🕐 Employee Time Clock Analysis System")
    st.markdown("---")
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("ℹ️ About")
        st.info("""
        This tool analyzes employee time clock data to identify:
        - Attendance patterns
        - Anomalies requiring attention
        - Multiple punch patterns
        - Late arrivals and departures
        
        The analysis uses color coding:
        - 🟢 Green: Acceptable (±5 min)
        - 🟡 Yellow: Minor Delay (5-7 min)
        - 🟠 Orange: Major Delay (7-11 min)
        - 🔴 Red: Significant Delay (>11 min)
        - 🟣 Purple: Missed Out Punch
        - 🩷 Pink: Multiple Punches Detected
        """)
        
        st.header("📋 Instructions")
        st.markdown("""
        1. **Upload CSV**: Drag and drop your timeclock CSV file
        2. **Process**: Click 'Analyze' to process the data
        3. **View Results**: See the analysis report
        4. **Download**: Get the PDF visualization
        
        **CSV Format Requirements:**
        The CSV must be the two week export from the time clock.
        """)
    
    # Main content area
    st.header("📁 Upload Time Clock Data")
    
    # File uploader with drag and drop
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Drag and drop your timeclock CSV file here"
    )
    
    if uploaded_file is not None:
        # Display file info
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size:,} bytes",
            "File type": uploaded_file.type
        }
        st.json(file_details)
        
        # Preview data
        if st.checkbox("Preview data (first 10 rows)"):
            try:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df.head(10))
                uploaded_file.seek(0)  # Reset file pointer
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
        
        # Analyze button
        if st.button("🔍 Analyze Time Clock Data", type="primary"):
            with st.spinner("Processing..."):
                # Create progress container
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # Update progress
                    progress_bar.progress(10)
                    status_text.text("Loading data...")
                    
                    # Initialize analyzer
                    analyzer = TimeClockAnalyzer(tmp_file_path)
                    
                    # Load data
                    progress_bar.progress(20)
                    status_text.text("Parsing CSV data...")
                    if not analyzer.load_data():
                        st.error("Failed to load data")
                        return
                    
                    # Process data
                    progress_bar.progress(30)
                    status_text.text("Processing time records...")
                    if not analyzer.process_data():
                        st.error("Failed to process data")
                        return
                    
                    # Create periods
                    progress_bar.progress(40)
                    status_text.text("Creating analysis periods...")
                    analyzer.create_two_week_periods()
                    
                    # Run analysis
                    progress_bar.progress(50)
                    status_text.text("Analyzing employee patterns...")
                    
                    # Analyze each employee
                    employees = sorted(analyzer.processed_data['employee'].unique())
                    total_employees = len(employees)
                    
                    for idx, employee in enumerate(employees):
                        analyzer.analysis_results[employee] = {}
                        for period in analyzer.two_week_periods:
                            result = analyzer.analyze_employee_period(employee, period)
                            analyzer.analysis_results[employee][period['label']] = result
                        
                        # Update progress
                        progress = 50 + int((idx + 1) / total_employees * 30)
                        progress_bar.progress(progress)
                        status_text.text(f"Analyzing employees... ({idx + 1}/{total_employees})")
                    
                    # Generate visualizations
                    progress_bar.progress(85)
                    status_text.text("Generating heat maps...")
                    
                    # Generate files in temp directory
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Change to temp directory
                        original_dir = os.getcwd()
                        os.chdir(temp_dir)
                        
                        # Generate files
                        analyzer.generate_heat_map()
                        report_text = analyzer.generate_report()
                        
                        # Update progress
                        progress_bar.progress(100)
                        status_text.text("Analysis complete!")
                        time.sleep(0.5)  # Brief pause to show completion
                        
                        # Clear progress indicators
                        progress_container.empty()
                        
                        # Success message
                        st.success("✅ Analysis completed successfully!")
                        
                        # Display results in two columns
                        result_col1, result_col2 = st.columns([3, 1])
                        
                        with result_col1:
                            st.header("📊 Analysis Report")
                            # Display report in console style
                            st.markdown(
                                f'<div class="console-output">{report_text}</div>',
                                unsafe_allow_html=True
                            )
                        
                        with result_col2:
                            st.header("📥 Download Results")
                            
                            # Check if files exist
                            pdf_path = os.path.join(temp_dir, 'timeclock_detailed_heatmap.pdf')
                            txt_path = os.path.join(temp_dir, 'timeclock_analysis_report.txt')
                            
                            if os.path.exists(pdf_path):
                                st.markdown(get_binary_file_downloader_html(
                                    pdf_path, 
                                    'Heat Map (PDF)'
                                ), unsafe_allow_html=True)
                                st.markdown("<br>", unsafe_allow_html=True)
                            
                            if os.path.exists(txt_path):
                                st.markdown(get_binary_file_downloader_html(
                                    txt_path, 
                                    'Analysis Report (TXT)'
                                ), unsafe_allow_html=True)
                        
                        # Change back to original directory
                        os.chdir(original_dir)
                    
                    # Clean up temp CSV
                    os.unlink(tmp_file_path)
                    
                except Exception as e:
                    progress_container.empty()
                    st.error(f"❌ Error during analysis: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

if __name__ == "__main__":
    main()