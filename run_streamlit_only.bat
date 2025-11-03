@echo off
REM Lancer Streamlit depuis le venv (pour debug)
cd /d "%~dp0"
call venv\Scripts\activate.bat
streamlit run frontend/app.py
