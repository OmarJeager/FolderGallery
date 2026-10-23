@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo Could not install build dependencies.
  pause
  exit /b 1
)
py -3 -m PyInstaller --noconfirm --clean --windowed --name FolderGallery --collect-all PySide6 main.py
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)
echo.
echo Done. Your portable app is in dist\FolderGallery\FolderGallery.exe
echo Copy the entire dist\FolderGallery folder to another Windows PC.
pause
