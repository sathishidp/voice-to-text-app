@echo off
REM ============ CLEAN BUILD ============
rd /s /q dist
rd /s /q build
del main.spec

REM ============ BUILD APP ONLY ============
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --icon=icon.ico ^
  main.py

echo.
echo ✅ Build complete! Copy ffmpeg.exe manually next to dist\main.exe
pause
