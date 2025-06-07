#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Run streamlit with explicit settings
streamlit run app.py \
    --server.port 8501 \
    --server.address localhost \
    --server.headless true \
    --browser.serverAddress localhost