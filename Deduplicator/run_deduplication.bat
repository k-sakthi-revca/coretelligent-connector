@echo off
REM ITGlue to ServiceNow Deduplication Tool Runner
REM This batch file helps run the deduplication process with sample data

echo === ITGlue to ServiceNow Deduplication Tool ===
echo.

REM Step 1: Generate sample data
echo Step 1: Generating sample data...
py -3 example.py
echo.

REM Step 2: Run deduplication process with sample data
echo Step 2: Running deduplication process...
py -3 deduplicator.py --organization "Acme Corporation" ^
                      --itglue-data sample_data/itglue_sample.json ^
                      --servicenow-data sample_data/servicenow_sample.json ^
                      --output sample_data/output
echo.

echo Deduplication process completed!
echo Check the sample_data/output directory for results.
echo.

pause
