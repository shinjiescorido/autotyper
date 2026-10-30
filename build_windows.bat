@echo off
rem Builds dist\AutoTyper.exe (one file, no console, no Python needed to run it)
rem and then dist\AutoTyperSetup.exe (installer: Start Menu, optional desktop icon, uninstaller).
rem Run this ON WINDOWS (double-click or from cmd). PyInstaller/Inno Setup can't cross-compile from Linux.
rem Needs Python 3 (python.org installer) and, for the installer, Inno Setup 6.3+:
rem     winget install JRSoftware.InnoSetup

setlocal
cd /d "%~dp0"

where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")

rem Separate venv from the Linux .venv, in case this folder is shared between machines.
if not exist .venv-win\Scripts\python.exe (
    echo Creating .venv-win ...
    %PY% -m venv .venv-win || goto :fail
)

echo Installing dependencies ...
.venv-win\Scripts\python -m pip install --upgrade pip >nul
.venv-win\Scripts\python -m pip install pynput PySide6 pyinstaller || goto :fail

echo Building AutoTyper.exe ...
rem pynput picks its backend at runtime, so PyInstaller can't see it: name the win32 ones.
.venv-win\Scripts\pyinstaller --noconfirm --clean --onefile --windowed ^
    --name AutoTyper ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    autotyper_gui.py || goto :fail

rem Find Inno Setup's compiler: PATH, then the all-users and per-user install folders.
rem (Kept out of ( ) blocks: the ")" in %ProgramFiles(x86)% would end the block early.)
set "ISCC="
for /f "delims=" %%i in ('where ISCC 2^>nul') do if not defined ISCC set "ISCC=%%i"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC goto :no_inno

echo Building AutoTyperSetup.exe ...
"%ISCC%" autotyper.iss || goto :fail

echo.
echo Done:
echo   %cd%\dist\AutoTyperSetup.exe   (installer: give this one out)
echo   %cd%\dist\AutoTyper.exe        (portable, runs without installing)
pause
exit /b 0

:no_inno
echo.
echo Built %cd%\dist\AutoTyper.exe, but skipped the installer: Inno Setup not found.
echo Install it (winget install JRSoftware.InnoSetup) and run this again.
pause
exit /b 0

:fail
echo.
echo Build failed, see the output above.
pause
exit /b 1
