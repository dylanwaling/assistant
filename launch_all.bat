@echo off
:: Change to the project directory
cd /d "D:\Documents D\assistant"

:: Launch watcher in its own terminal window
start "AI Chief Watcher" cmd /k "python cli.py watch"

:: Launch second terminal window for user input
start "AI Chief Command Prompt" cmd /k "cd /d D:\Documents D\assistant"