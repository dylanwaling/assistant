@echo off
REM Change to the project directory
cd /d "D:\Documents D\assistant"

REM Launch main.py in watch mode in a new terminal window
start "AI Chief Watcher" cmd /k "python main.py watch"

REM Open a second prompt in the project directory
start "AI Chief Command Prompt" cmd /k "cd /d D:\Documents D\assistant"