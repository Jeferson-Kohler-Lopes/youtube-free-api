@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  YouTube Strategy Lab - versao sem API
echo ============================================

where py >nul 2>nul
if errorlevel 1 (
  echo Python nao foi encontrado. Instale o Python 3.11 ou superior.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  py -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

set /p CHANNEL=Coloque a URL ou @handle do canal: 
if "%CHANNEL%"=="" (
  echo Nenhum canal informado.
  pause
  exit /b 1
)

python -m collector.collect "%CHANNEL%" --max-videos 200 --max-competitors 3 --output reports/latest.json
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo Relatorio criado em reports\latest.json
echo Execute abrir-painel.bat para visualizar.
pause
