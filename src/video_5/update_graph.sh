#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run the Python scripts
python merge_historical_sales_properties.py
python merge_copurchaser_edges.py
python merge_recommendation_edges.py
