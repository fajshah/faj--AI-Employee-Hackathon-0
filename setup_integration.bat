@echo off
REM Quick Start Script for Odoo-AI Employee Integration
REM Run this to set up the integration

echo ============================================
echo Odoo-AI Employee Integration Setup
echo ============================================
echo.

REM Check if running in correct directory
if not exist "odoo_integration" (
    echo Error: Please run this script from D:\hackthone-0
    exit /b 1
)

echo Step 1: Setting up environment files...
if not exist "odoo\.env" (
    copy "odoo\.env.example" "odoo\.env"
    echo Created odoo\.env from template
) else (
    echo odoo\.env already exists
)

echo.
echo Step 2: Creating necessary directories...
if not exist "odoo\logs" mkdir "odoo\logs"
if not exist "odoo\drafts" mkdir "odoo\drafts"
if not exist "odoo\tokens" mkdir "odoo\tokens"
if not exist "odoo_integration\logs" mkdir "odoo_integration\logs"
if not exist "odoo_integration\drafts" mkdir "odoo_integration\drafts"
if not exist "odoo_integration\tokens" mkdir "odoo_integration\tokens"

echo.
echo Step 3: Installing Python dependencies...
cd odoo_integration
pip install -r requirements.txt
cd ..

echo.
echo Step 4: Starting Docker services...
cd odoo
docker-compose up -d
cd ..

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next Steps:
echo 1. Edit odoo\.env with your credentials
echo 2. Open Odoo at http://localhost:8069
echo 3. Install "AI Employee Connector" module
echo 4. Configure webhook settings in Odoo
echo 5. Test the connection
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
echo.
