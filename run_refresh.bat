@echo off

cd /d C:\Users\HP\Downloads\polluxa_part2_starter\polluxa_part2

call .venv\Scripts\activate

python refresh_pipeline.py >> logs\scheduled_refresh.log 2>&1