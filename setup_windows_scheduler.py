"""
Windows Task Scheduler Setup Script

Creates scheduled tasks for the Gold Tier AI Employee system.

Tasks Created:
1. CEO Briefing Generator - Daily at 9:00 AM
2. Monitoring Agent - Every 5 minutes
3. Ralph Wiggum Loop - Every 1 minute
4. Daily Summary - Daily at 6:00 PM

Usage:
    python setup_windows_scheduler.py [--uninstall]
    
    --uninstall: Remove all scheduled tasks
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/scheduler_setup.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
PYTHON_EXECUTABLE = sys.executable

# Task names
TASK_PREFIX = "AI_Employee_"
TASKS = {
    "ceo_briefing": {
        "name": f"{TASK_PREFIX}CEO_Briefing",
        "description": "Generate daily CEO briefing report",
        "script": "ceo_briefing_generator.py",
        "schedule": "09:00",
        "frequency": "DAILY"
    },
    "monitoring": {
        "name": f"{TASK_PREFIX}Monitoring_Agent",
        "description": "Run monitoring agent every 5 minutes",
        "script": "Agents/Monitoring_Agent.py",
        "schedule": "*/*/5",  # Every 5 minutes
        "frequency": "MINUTE",
        "interval": 5
    },
    "ralph_loop": {
        "name": f"{TASK_PREFIX}Ralph_Loop",
        "description": "Run Ralph Wiggum autonomous loop",
        "script": ".claude/plugins/ralph_wiggum_loop.py",
        "schedule": "*/*/1",  # Every 1 minute
        "frequency": "MINUTE",
        "interval": 1
    },
    "daily_summary": {
        "name": f"{TASK_PREFIX}Daily_Summary",
        "description": "Generate daily summary report",
        "script": "system_status.py",
        "schedule": "18:00",
        "frequency": "DAILY"
    }
}


def run_command(command: str, description: str) -> bool:
    """
    Run a shell command and log the result.
    
    Args:
        command: Command to execute
        description: Description for logging
        
    Returns:
        True if successful
    """
    logger.info(f"Executing: {description}")
    logger.debug(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {description} - Success")
            return True
        else:
            logger.error(f"❌ {description} - Failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} - Timeout")
        return False
    except Exception as e:
        logger.error(f"❌ {description} - Error: {str(e)}")
        return False


def create_task(task_config: dict) -> bool:
    """
    Create a Windows scheduled task.
    
    Args:
        task_config: Task configuration dictionary
        
    Returns:
        True if task created successfully
    """
    name = task_config["name"]
    description = task_config["description"]
    script = task_config["script"]
    frequency = task_config["frequency"]
    
    # Build the command to run
    script_path = SCRIPT_DIR / script
    command = f'"{PYTHON_EXECUTABLE}" "{script_path}"'
    
    # Build schtasks command based on frequency
    if frequency == "DAILY":
        time_str = task_config["schedule"]
        schtasks_cmd = (
            f'schtasks /Create /F /TN "{name}" '
            f'/TR "{command}" '
            f'/SC DAILY /ST {time_str} '
            f'/RL HIGHEST /RU SYSTEM '
            f'/F'
        )
    elif frequency == "MINUTE":
        interval = task_config.get("interval", 5)
        schtasks_cmd = (
            f'schtasks /Create /F /TN "{name}" '
            f'/TR "{command}" '
            f'/SC MINUTE /MO {interval} '
            f'/RL HIGHEST /RU SYSTEM '
            f'/F'
        )
    else:
        logger.error(f"Unknown frequency: {frequency}")
        return False
    
    return run_command(schtasks_cmd, f"Create task: {name}")


def delete_task(task_name: str) -> bool:
    """
    Delete a Windows scheduled task.
    
    Args:
        task_name: Name of the task to delete
        
    Returns:
        True if task deleted successfully
    """
    cmd = f'schtasks /Delete /F /TN "{task_name}"'
    return run_command(cmd, f"Delete task: {task_name}")


def task_exists(task_name: str) -> bool:
    """
    Check if a task exists.
    
    Args:
        task_name: Name of the task
        
    Returns:
        True if task exists
    """
    cmd = f'schtasks /Query /TN "{task_name}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0


def list_ai_tasks():
    """List all AI Employee scheduled tasks"""
    print("\n" + "="*60)
    print("AI EMPLOYEE SCHEDULED TASKS")
    print("="*60)
    
    for task_key, task_config in TASKS.items():
        name = task_config["name"]
        exists = task_exists(name)
        status = "✅ Exists" if exists else "❌ Not found"
        print(f"  {status} - {name}")
        print(f"           {task_config['description']}")
        print(f"           Schedule: {task_config['schedule']} ({task_config['frequency']})")
        print()
    
    print("="*60)


def install_all_tasks() -> bool:
    """
    Install all scheduled tasks.
    
    Returns:
        True if all tasks installed successfully
    """
    logger.info("="*60)
    logger.info("INSTALLING AI EMPLOYEE SCHEDULED TASKS")
    logger.info("="*60)
    
    print("\n" + "="*60)
    print("INSTALLING AI EMPLOYEE SCHEDULED TASKS")
    print("="*60)
    
    success_count = 0
    
    for task_key, task_config in TASKS.items():
        if create_task(task_config):
            success_count += 1
        else:
            print(f"  ⚠️  Failed to create: {task_config['name']}")
    
    print("\n" + "="*60)
    print(f"INSTALLATION COMPLETE: {success_count}/{len(TASKS)} tasks created")
    print("="*60)
    
    # List all tasks
    list_ai_tasks()
    
    return success_count == len(TASKS)


def uninstall_all_tasks() -> bool:
    """
    Uninstall all scheduled tasks.
    
    Returns:
        True if all tasks uninstalled successfully
    """
    logger.info("="*60)
    logger.info("UNINSTALLING AI EMPLOYEE SCHEDULED TASKS")
    logger.info("="*60)
    
    print("\n" + "="*60)
    print("UNINSTALLING AI EMPLOYEE SCHEDULED TASKS")
    print("="*60)
    
    success_count = 0
    
    for task_key, task_config in TASKS.items():
        if delete_task(task_config["name"]):
            success_count += 1
        else:
            # Task might not exist, which is also success
            if not task_exists(task_config["name"]):
                success_count += 1
                print(f"  ℹ️  Task not found (already removed): {task_config['name']}")
            else:
                print(f"  ⚠️  Failed to delete: {task_config['name']}")
    
    print("\n" + "="*60)
    print(f"UNINSTALLATION COMPLETE: {success_count}/{len(TASKS)} tasks processed")
    print("="*60)
    
    return success_count == len(TASKS)


def verify_installation() -> bool:
    """
    Verify all tasks are installed.
    
    Returns:
        True if all tasks exist
    """
    print("\n" + "="*60)
    print("VERIFYING INSTALLATION")
    print("="*60)
    
    all_exist = True
    
    for task_key, task_config in TASKS.items():
        exists = task_exists(task_config["name"])
        if exists:
            print(f"  ✅ {task_config['name']}")
        else:
            print(f"  ❌ {task_config['name']} - NOT FOUND")
            all_exist = False
    
    print("="*60)
    
    if all_exist:
        print("✅ All tasks verified successfully!")
    else:
        print("⚠️  Some tasks are missing. Run with --install to create them.")
    
    return all_exist


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("WINDOWS TASK SCHEDULER SETUP")
    print("Gold Tier AI Employee System")
    print("="*60)
    print(f"\nScript Directory: {SCRIPT_DIR}")
    print(f"Python Executable: {PYTHON_EXECUTABLE}")
    print()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "--install":
            install_all_tasks()
        elif arg == "--uninstall":
            uninstall_all_tasks()
        elif arg == "--verify":
            verify_installation()
        elif arg == "--list":
            list_ai_tasks()
        elif arg == "--help":
            print_help()
        else:
            print(f"Unknown argument: {arg}")
            print_help()
    else:
        # Interactive mode
        print("Usage:")
        print("  python setup_windows_scheduler.py --install    Install all tasks")
        print("  python setup_windows_scheduler.py --uninstall  Remove all tasks")
        print("  python setup_windows_scheduler.py --verify     Verify installation")
        print("  python setup_windows_scheduler.py --list       List all tasks")
        print("  python setup_windows_scheduler.py --help       Show this help")
        print()
        
        choice = input("\nWhat would you like to do? (install/uninstall/verify/list): ").strip().lower()
        
        if choice == "install":
            install_all_tasks()
        elif choice == "uninstall":
            uninstall_all_tasks()
        elif choice == "verify":
            verify_installation()
        elif choice == "list":
            list_ai_tasks()
        else:
            print("Invalid choice. Use --help for usage information.")


def print_help():
    """Print help information"""
    print("""
Windows Task Scheduler Setup - Gold Tier AI Employee

USAGE:
    python setup_windows_scheduler.py [OPTION]

OPTIONS:
    --install    Install all scheduled tasks
    --uninstall  Remove all scheduled tasks
    --verify     Verify all tasks are installed
    --list       List all scheduled tasks
    --help       Show this help message

TASKS CREATED:
    1. CEO Briefing     - Daily at 9:00 AM
    2. Monitoring Agent - Every 5 minutes
    3. Ralph Loop       - Every 1 minute
    4. Daily Summary    - Daily at 6:00 PM

REQUIREMENTS:
    - Administrator privileges
    - Python 3.10+
    - All dependencies installed

EXAMPLES:
    python setup_windows_scheduler.py --install
    python setup_windows_scheduler.py --uninstall
    python setup_windows_scheduler.py --verify
""")


if __name__ == "__main__":
    main()
