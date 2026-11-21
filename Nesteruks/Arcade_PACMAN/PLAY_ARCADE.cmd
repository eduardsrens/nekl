@echo off
setlocal
title Maze Arcade
where python3.14 >nul 2>nul
if not errorlevel 1 (
    python3.14 -B "%~dp0PLAY_ARCADE.py" %*
    goto finished
)
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -B "%~dp0PLAY_ARCADE.py" %*
    goto finished
)
python -B "%~dp0PLAY_ARCADE.py" %*
:finished
if errorlevel 1 (
    echo.
    echo The game could not start. Read the error above, then press any key.
    pause >nul
)
endlocal
