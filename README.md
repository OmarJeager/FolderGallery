# Folder Gallery

A desktop image browser for Windows. It works locally: images are read from folders on your PC and are never uploaded.

## Features
- Add both main folders (and more, if needed).
- Scans nested subfolders recursively.
- Filter by main folder and by nested folder.
- Search image names such as `d54544548` or `g44874`.
- Sort by filename or modified date.
- Preview cards; double-click a card to open the full image in your default image viewer.
- Dark modern interface, responsive grid, hover styling and a subtle fade-in.
- Supports JPG/JPEG, PNG, BMP, GIF, WEBP, TIF/TIFF.

## Run from source
1. Install Python 3.10 or newer from https://www.python.org/downloads/ (enable **Add Python to PATH**).
2. Extract this ZIP.
3. Double-click `run.bat`, or open a terminal in this folder and run:
   ```powershell
   py -3 -m pip install -r requirements.txt
   py -3 main.py
   ```
4. Click **Add main folder** and select your first parent folder. Repeat for your second parent folder.
5. Use the two dropdowns to choose a main folder and a nested folder, or type a filename in Search.

## Build a Windows app
1. On a Windows PC with Python installed, double-click `build_exe.bat`.
2. Wait for the build to finish.
3. The app will be created in `dist\\FolderGallery\\FolderGallery.exe`.
4. Copy the **entire** `dist\\FolderGallery` folder to another Windows PC. The target PC does not need Python installed. Do not copy only the EXE.

The first run needs internet access to install Python packages. After building, the packaged app can run offline. Windows may show a SmartScreen warning because this is an unsigned personal app.

## Notes
- The app does not copy, move, rename, or edit your images.
- Very large folders may take a little time to scan.
- A folder that Windows denies access to may be skipped.
"# FolderGallery" 
