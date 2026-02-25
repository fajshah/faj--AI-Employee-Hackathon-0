#!/bin/bash
# Silver Tier Scheduler Cron Setup
# Add these lines to your crontab using 'crontab -e'

# Daily LinkedIn posting at 9 AM
0 9 * * * cd /path/to/hackthone-0 && python LinkedIn_Poster.py

# System health check every 30 minutes during business hours (9AM-5PM)
*/30 9-17 * * * cd /path/to/hackthone-0 && python ai_employee_system.py

# Weekly report generation every Monday at 9 AM
0 9 * * 1 cd /path/to/hackthone-0 && python ai_employee_system.py

# Gmail check every 10 minutes
*/10 * * * * cd /path/to/hackthone-0 && python Gmail_Watcher.py

# WhatsApp check every 15 minutes
*/15 * * * * cd /path/to/hackthone-0 && python WhatsApp_Watcher.py
