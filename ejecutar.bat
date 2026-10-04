@echo off
rem Abre la aplicacion en el navegador (doble clic sobre este archivo).
cd /d "%~dp0"
python -m streamlit run app.py
pause
