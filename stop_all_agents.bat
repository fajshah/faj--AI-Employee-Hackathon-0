@echo off
REM =====================================================
REM Gold Tier Autonomous AI Employee - Stop All Agents
REM =====================================================
REM This script gracefully stops all running components
REM =====================================================

echo =====================================================
echo   GOLD TIER AI EMPLOYEE - STOPPING ALL AGENTS
echo =====================================================
echo.

cd /d "%~dp0"

echo Stopping all running agents...
echo.

echo [1/6] Stopping Orchestrator...
taskkill /FI "WindowTitle eq Orchestrator*" /F 2>nul

echo [2/6] Stopping Ralph Wiggum Loop...
taskkill /FI "WindowTitle eq Ralph_Loop*" /F 2>nul

echo [3/6] Stopping Monitoring Agent...
taskkill /FI "WindowTitle eq Monitoring_Agent*" /F 2>nul

echo [4/6] Stopping MCP Finance Server...
taskkill /FI "WindowTitle eq MCP_Finance*" /F 2>nul

echo [5/6] Stopping MCP Social Server...
taskkill /FI "WindowTitle eq MCP_Social*" /F 2>nul

echo [6/6] Stopping MCP Comms Server...
taskkill /FI "WindowTitle eq MCP_Comms*" /F 2>nul

echo.
echo Waiting for processes to terminate...
timeout /t 3 /nobreak >nul

REM Force kill any remaining Python processes
echo Force cleaning up...
taskkill /FI "ImageName eq python.exe" /FI "WindowTitle eq MCP_*" /F 2>nul
taskkill /FI "ImageName eq python.exe" /FI "WindowTitle eq *Agent*" /F 2>nul
taskkill /FI "ImageName eq python.exe" /FI "WindowTitle eq *Loop*" /F 2>nul
taskkill /FI "ImageName eq python.exe" /FI "WindowTitle eq *Orchestrator*" /F 2>nul

echo.
echo =====================================================
echo   ALL AGENTS STOPPED
echo =====================================================
echo.
echo Creating stop marker file...
echo %date% %time% - All agents stopped > Logs\last_stop.txt

echo.
echo Summary:
echo   - All MCP Servers stopped
echo   - All Agents stopped
echo   - Ralph Wiggum Loop stopped
echo   - Orchestrator stopped
echo.
echo To start all agents again, run: start_all_agents.bat
echo =====================================================
echo.

pause
