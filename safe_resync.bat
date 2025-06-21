@echo off
REM Close all Assistant Watcher and Assistant Command Prompt windows
for /f "tokens=2 delims==," %%i in ('tasklist /v /fo csv ^| findstr /i "Assistant Watcher"') do (
    taskkill /f /pid %%i >nul 2>&1
)
for /f "tokens=2 delims==," %%i in ('tasklist /v /fo csv ^| findstr /i "Assistant Command Prompt"') do (
    taskkill /f /pid %%i >nul 2>&1
)

REM Wait a moment to ensure all are closed
timeout /t 2 >nul

REM Run the resync command (this will rebuild ChromaDB)
python main.py resyncdb

REM Wait a moment to ensure resync is done
timeout /t 2 >nul

REM Reopen the watcher and assistant terminals
start "Assistant Watcher" cmd /k "title Assistant Watcher && python main.py watch"
start "Assistant Command Prompt" cmd /k "title Assistant Command Prompt && cmd"
exit