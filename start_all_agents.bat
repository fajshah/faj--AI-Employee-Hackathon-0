@echo off
REM =====================================================
REM Gold Tier Autonomous AI Employee - Start All Agents
REM =====================================================
REM This script starts all components of the AI Employee system
REM in the correct order with proper error handling.
REM =====================================================

echo =====================================================
echo   GOLD TIER AI EMPLOYEE - STARTING ALL AGENTS
echo =====================================================
echo.

REM 1. Set project root directory
cd /d "%~dp0"

REM 2. Create Logs directory if it doesn't exist
if not exist "Logs" mkdir "Logs"

REM 3. Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo [1/6] Starting MCP Comms Server (Port 5001)...
start "MCP_Comms" cmd /k "python MCP_Servers\MCP_Comms_Server.py"
timeout /t 2 /nobreak >nul

echo [2/6] Starting MCP Social Server (Port 5002)...
start "MCP_Social" cmd /k "python MCP_Servers\MCP_Social_Server.py"
timeout /t 2 /nobreak >nul

echo [3/6] Starting MCP Finance Server (Port 5003)...
start "MCP_Finance" cmd /k "python MCP_Servers\MCP_Finance_Server.py"
timeout /t 2 /nobreak >nul

echo [4/6] Starting Monitoring Agent...
start "Monitoring_Agent" cmd /k "python Agents\Monitoring_Agent.py"
timeout /t 1 /nobreak >nul

echo [5/6] Starting Ralph Wiggum Loop...
start "Ralph_Loop" cmd /k "python .claude\plugins\ralph_wiggum_loop.py"
timeout /t 1 /nobreak >nul

echo [6/6] Starting Orchestrator...
start "Orchestrator" cmd /k "python Orchestrator_Gold.py"

echo.
echo =====================================================
echo   ALL AGENTS STARTED SUCCESSFULLY
echo =====================================================
echo.
echo Running Components:
echo   - MCP Comms Server    : http://localhost:5001
echo   - MCP Social Server   : http://localhost:5002
echo   - MCP Finance Server  : http://localhost:5003
echo   - Monitoring Agent    : Active
echo   - Ralph Wiggum Loop   : Active
echo   - Orchestrator        : Active
echo.
echo To stop all agents, run: stop_all_agents.bat
echo To view logs, check the Logs\ directory
echo =====================================================
echo.

REM Wait and verify services are running
timeout /t 3 /nobreak >nul

echo Verifying services...
python -c "import requests; r=requests.get('http://localhost:5001/health', timeout=3); print('  [OK] MCP Comms Server' if r.status_code==200 else '  [FAIL] MCP Comms Server')" 2>nul || echo   [WAITING] MCP Comms Server
python -c "import requests; r=requests.get('http://localhost:5002/health', timeout=3); print('  [OK] MCP Social Server' if r.status_code==200 else '  [WAITING] MCP Social Server')" 2>nul || echo   [WAITING] MCP Social Server
python -c "import requests; r=requests.get('http://localhost:5003/health', timeout=3); print('  [OK] MCP Finance Server' if r.status_code==200 else '  [WAITING] MCP Finance Server')" 2>nul || echo   [WAITING] MCP Finance Server

echo.
echo =====================================================
echo   System is running!
echo =====================================================
echo.
echo Servers started successfully. Check system tray for running processes.
echo.
echo To stop: Run stop_all_agents.bat or close the server windows
echo To view logs: Check Logs\ folder
echo.
