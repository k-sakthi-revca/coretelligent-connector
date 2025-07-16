#!/bin/bash
# ITGlue to ServiceNow Deduplication Tool Runner
# This shell script helps run the deduplication process with sample data

echo "=== ITGlue to ServiceNow Deduplication Tool ==="
echo

# Step 1: Generate sample data
echo "Step 1: Generating sample data..."
python3 example.py
echo

# Step 2: Run deduplication process with sample data
echo "Step 2: Running deduplication process..."
python3 deduplicator.py --organization "Acme Corporation" \
                      --itglue-data sample_data/itglue_sample.json \
                      --servicenow-data sample_data/servicenow_sample.json \
                      --output sample_data/output
echo

echo "Deduplication process completed!"
echo "Check the sample_data/output directory for results."
echo

read -p "Press Enter to continue..."
