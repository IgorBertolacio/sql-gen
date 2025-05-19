@echo off
set "PROJECT_DIR=C:\RAG\workspace\STEVIA"
set "PYTHONPATH=%PROJECT_DIR%\SQL-GENERATE\src"
set "PYTHON_EXEC=%PROJECT_DIR%\SQL-GENERATE\.venv\Scripts\python.exe"

echo Iniciando backend com ambiente virtual correto...
cd /d %PROJECT_DIR%\sql-generate-interface
start cmd /k "%PYTHON_EXEC% -m interfaces.api.run_api"
