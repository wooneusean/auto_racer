@echo off
python -m venv .\venv
call .\venv\Scripts\activate
pip install -r requirements.txt
echo "Done installation, run with start.bat"
@pause