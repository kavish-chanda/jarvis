@echo off
rem Builds Jarvis.exe from jarvis_app.pyw
rem Keep this file in the same folder as jarvis_app.pyw, jarvis_logo.png and jarvis_logo.ico
cd /d "%~dp0"

echo Installing PyInstaller...
py -3.12 -m pip install --upgrade pyinstaller

echo.
echo Building Jarvis.exe (this takes a few minutes)...
py -3.12 -m PyInstaller --noconfirm --clean --onefile --noconsole --name Jarvis ^
  --icon jarvis_logo.ico ^
  --add-data "jarvis_logo.png;." ^
  --add-data "jarvis_logo.ico;." ^
  --hidden-import pyaudio ^
  --hidden-import pythoncom ^
  --hidden-import pywintypes ^
  --hidden-import pyttsx3.drivers ^
  --hidden-import pyttsx3.drivers.sapi5 ^
  --collect-submodules comtypes ^
  --collect-all speech_recognition ^
  jarvis_app.pyw

echo.
if exist "dist\Jarvis.exe" (
  echo Done! Your app is here: %~dp0dist\Jarvis.exe
) else (
  echo Build failed. Scroll up to see the error.
)
pause
