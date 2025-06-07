# Streamlit Time Clock Analyzer

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at http://localhost:8501

## Features

- **Drag & Drop CSV Upload**: Simply drag your timeclock CSV file into the upload area
- **Real-time Progress Bar**: Watch the analysis progress with detailed status updates
- **Console-style Report Display**: View the analysis report in a terminal-like interface
- **Download Options**: 
  - PDF heat map visualization
  - PNG heat map image
  - TXT analysis report
- **Data Preview**: Option to preview your CSV data before processing

## Usage

1. Open the app in your browser
2. Drag and drop your timeclock CSV file
3. Optionally preview the data
4. Click "Analyze Time Clock Data"
5. Watch the progress bar as the analysis runs
6. View the report in the console window
7. Download the PDF visualization and/or text report

## Notes

- The CSV file must follow the format specified in the sidebar
- Large files may take a few minutes to process
- All generated files are temporary and not saved to disk