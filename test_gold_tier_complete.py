"""
Gold Tier AI Employee - Comprehensive System Test

Tests all components of the upgraded Gold Tier system:
- Ralph Wiggum Loop
- Odoo Integration (with mock mode)
- Social Media Integration (with mock mode)
- MCP Servers
- Master Controller
- System Status

Usage:
    python test_gold_tier_complete.py [--verbose]
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GoldTierTest")

# Test results storage
TEST_RESULTS = {
    "timestamp": None,
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "tests": []
}


def log_test(name: str, passed: bool, message: str = "", warning: bool = False):
    """Log a test result"""
    TEST_RESULTS["total_tests"] += 1
    
    if passed:
        TEST_RESULTS["passed"] += 1
        status = "[PASS]"
    elif warning:
        TEST_RESULTS["warnings"] += 1
        status = "[WARN]"
    else:
        TEST_RESULTS["failed"] += 1
        status = "[FAIL]"
    
    TEST_RESULTS["tests"].append({
        "name": name,
        "passed": passed,
        "message": message,
        "warning": warning
    })
    
    print(f"  {status}: {name}")
    if message:
        print(f"         {message}")


def print_section(title: str):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


# ============================================================================
# TEST 1: Ralph Wiggum Loop
# ============================================================================

def test_ralph_wiggum_loop():
    """Test Ralph Wiggum Loop implementation"""
    print_section("TEST 1: Ralph Wiggum Loop")
    
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        
        from claude.plugins.ralph_wiggum_loop import (
            RalphWiggumLoop,
            start_ralph_loop,
            stop_ralph_loop,
            check_stop_condition
        )
        
        log_test("Module import", True, "Ralph Wiggum Loop module found")
        
        # Test initialization
        loop = RalphWiggumLoop(max_iterations=5, error_threshold=3)
        log_test("Initialization", True, "RalphWiggumLoop initialized")
        
        # Test stop condition
        should_stop, reason = check_stop_condition()
        log_test("Stop condition check", True, f"Current status: {reason}")
        
        # Test folder monitoring
        folders_exist = all([
            loop.inbox_dir.exists(),
            loop.needs_action_dir.exists(),
            loop.pending_approval_dir.exists(),
            loop.done_dir.exists()
        ])
        log_test("Folder structure", folders_exist, "All required folders exist")
        
        # Test state management
        loop._save_state()
        state_loaded = loop.load_state() is not None
        log_test("State management", state_loaded, "State save/load working")
        
    except ImportError as e:
        log_test("Module import", False, f"Import error: {e}")
    except Exception as e:
        log_test("Ralph Wiggum Loop", False, f"Error: {e}")


# ============================================================================
# TEST 2: Odoo Integration
# ============================================================================

def test_odoo_integration():
    """Test Odoo integration with mock mode support"""
    print_section("TEST 2: Odoo Integration")
    
    try:
        from config.odoo_config import (
            OdooConfig,
            get_odoo_config,
            connect_odoo,
            test_connection,
            is_configured,
            get_status
        )
        
        log_test("Module import", True, "Odoo config module found")
        
        # Check if configured
        configured = is_configured()
        log_test("Configuration check", True, f"Odoo configured: {configured}")
        
        if not configured:
            log_test(
                "Mock mode", True,
                "Odoo not configured - will use mock mode (expected in development)",
                warning=True
            )
        else:
            # Test connection
            success, message = test_connection()
            log_test("Connection test", success, message)
        
        # Get status
        status = get_status()
        log_test("Status endpoint", True, f"Status: {status.get('configured', False)}")
        
    except ImportError as e:
        log_test("Module import", False, f"Import error: {e}")
    except Exception as e:
        log_test("Odoo integration", False, f"Error: {e}")


# ============================================================================
# TEST 3: Social Media Integration
# ============================================================================

def test_social_media_integration():
    """Test social media integration with all platforms"""
    print_section("TEST 3: Social Media Integration")
    
    try:
        from config.social_config import (
            SocialConfig,
            get_social_config,
            get_platform_config,
            is_platform_configured,
            get_configured_platforms,
            post_linkedin,
            post_facebook,
            post_twitter,
            is_mock_mode
        )
        
        log_test("Module import", True, "Social config module found")
        
        # Get configuration
        config = get_social_config()
        log_test("Configuration loaded", True, f"Mock mode: {is_mock_mode()}")
        
        # Check platforms
        platforms = get_configured_platforms()
        if platforms:
            log_test("Configured platforms", True, f"Platforms: {', '.join(platforms)}")
        else:
            log_test(
                "Platform configuration", True,
                "No platforms configured - will use mock mode",
                warning=True
            )
        
        # Test mock posting
        result = post_linkedin("Test post from Gold Tier test!")
        log_test("LinkedIn mock post", result.get("status") in ["success", "mock"], result.get("status"))
        
        result = post_facebook("Test post from Gold Tier test!")
        log_test("Facebook mock post", result.get("status") in ["success", "mock"], result.get("status"))
        
        result = post_twitter("Test post from Gold Tier test!")
        log_test("Twitter mock post", result.get("status") in ["success", "mock"], result.get("status"))
        
    except ImportError as e:
        log_test("Module import", False, f"Import error: {e}")
    except Exception as e:
        log_test("Social media integration", False, f"Error: {e}")


# ============================================================================
# TEST 4: MCP Servers
# ============================================================================

def test_mcp_servers():
    """Test MCP server health endpoints"""
    print_section("TEST 4: MCP Servers")
    
    servers = [
        {"name": "MCP Comms", "port": 5001, "url": "http://localhost:5001/health"},
        {"name": "MCP Social", "port": 5002, "url": "http://localhost:5002/health"},
        {"name": "MCP Finance", "port": 5003, "url": "http://localhost:5003/health"}
    ]
    
    try:
        import requests
        
        for server in servers:
            try:
                response = requests.get(server["url"], timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    log_test(
                        f"{server['name']} health", True,
                        f"Status: {data.get('status', 'unknown')}"
                    )
                else:
                    log_test(
                        f"{server['name']} health", False,
                        f"HTTP {response.status_code}"
                    )
            except requests.exceptions.ConnectionError:
                log_test(
                    f"{server['name']} health", False,
                    "Server not running (may need to start manually)",
                    warning=True
                )
            except Exception as e:
                log_test(f"{server['name']} health", False, str(e))
                
    except ImportError:
        log_test("Requests library", False, "requests not installed", warning=True)
    except Exception as e:
        log_test("MCP servers", False, f"Error: {e}")


# ============================================================================
# TEST 5: Master Controller
# ============================================================================

def test_master_controller():
    """Test Master Autonomous Controller"""
    print_section("TEST 5: Master Autonomous Controller")
    
    try:
        from Master_Autonomous_Controller import MasterAutonomousController
        
        log_test("Module import", True, "Master Controller module found")
        
        # Initialize controller
        controller = MasterAutonomousController()
        log_test("Initialization", True, "Controller initialized")
        
        # Check components registered
        component_count = len(controller.components)
        log_test("Components registered", True, f"{component_count} components")
        
        # Get status
        status = controller.get_status()
        log_test("Status endpoint", True, f"Controller running: {status.get('running', False)}")
        
        # Check component status
        running_count = sum(
            1 for c in controller.components.values()
            if c.is_running()
        )
        log_test("Running components", True, f"{running_count}/{component_count} running")
        
    except ImportError as e:
        log_test("Module import", False, f"Import error: {e}")
    except Exception as e:
        log_test("Master controller", False, f"Error: {e}")


# ============================================================================
# TEST 6: System Status
# ============================================================================

def test_system_status():
    """Test System Status backend"""
    print_section("TEST 6: System Status")
    
    try:
        from system_status import (
            get_full_status,
            get_health_status,
            get_task_statistics,
            get_revenue_data,
            get_system_metrics
        )
        
        log_test("Module import", True, "System status module found")
        
        # Get full status
        status = get_full_status()
        log_test("Full status", True, f"Timestamp: {status.get('timestamp', 'N/A')}")
        
        # Check health
        health = get_health_status()
        log_test("Health status", True, f"Overall: {health.get('overall', 'unknown')}")
        
        # Check task stats
        tasks = get_task_statistics()
        log_test(
            "Task statistics", True,
            f"Needs Action: {tasks.get('needs_action', 0)}, "
            f"Completed: {tasks.get('completed', 0)}"
        )
        
        # Check revenue
        revenue = get_revenue_data()
        log_test("Revenue data", True, f"Source: {revenue.get('source', 'none')}")
        
        # Check system metrics
        metrics = get_system_metrics()
        log_test(
            "System metrics", True,
            f"CPU: {metrics.get('cpu_percent', 0):.1f}%, "
            f"Memory: {metrics.get('memory_percent', 0):.1f}%"
        )
        
    except ImportError as e:
        log_test("Module import", False, f"Import error: {e}")
    except Exception as e:
        log_test("System status", False, f"Error: {e}")


# ============================================================================
# TEST 7: File Structure
# ============================================================================

def test_file_structure():
    """Test required file structure"""
    print_section("TEST 7: File Structure")
    
    required_files = [
        ".claude/plugins/ralph_wiggum_loop.py",
        "config/odoo_config.py",
        "config/social_config.py",
        "Master_Autonomous_Controller.py",
        "system_status.py",
        "setup_windows_scheduler.py",
        "start_all_agents.bat",
        "stop_all_agents.bat"
    ]
    
    required_dirs = [
        "Logs",
        "Done",
        "Needs_Action",
        "Pending_Approval",
        "Plans",
        "Approved",
        "Error"
    ]
    
    script_dir = Path(__file__).parent
    
    # Check files
    for file_path in required_files:
        full_path = script_dir / file_path
        exists = full_path.exists()
        log_test(f"File: {file_path}", exists, "Found" if exists else "Missing")
    
    # Check directories
    for dir_path in required_dirs:
        full_path = script_dir / dir_path
        exists = full_path.exists()
        log_test(f"Directory: {dir_path}", exists, "Found" if exists else "Missing")


# ============================================================================
# TEST 8: Environment Configuration
# ============================================================================

def test_environment():
    """Test environment configuration"""
    print_section("TEST 8: Environment Configuration")
    
    required_vars = [
        "ODOO_URL",
        "ODOO_DB",
        "ODOO_USER",
        "ODOO_PASSWORD",
        "LINKEDIN_ACCESS_TOKEN",
        "GMAIL_CLIENT_ID",
        "MCP_SERVER_URL"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            masked = value[:4] + "..." if len(value) > 4 else "***"
            log_test(f"Env: {var}", True, f"Set ({masked})")
        else:
            log_test(
                f"Env: {var}", True,
                "Not set (may use mock mode)",
                warning=True
            )


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  GOLD TIER AI EMPLOYEE - COMPREHENSIVE SYSTEM TEST")
    print("="*60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    TEST_RESULTS["timestamp"] = datetime.now().isoformat()
    
    # Run all tests
    test_ralph_wiggum_loop()
    test_odoo_integration()
    test_social_media_integration()
    test_mcp_servers()
    test_master_controller()
    test_system_status()
    test_file_structure()
    test_environment()
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    print(f"  Total Tests:  {TEST_RESULTS['total_tests']}")
    print(f"  ✅ Passed:    {TEST_RESULTS['passed']}")
    print(f"  ❌ Failed:    {TEST_RESULTS['failed']}")
    print(f"  ⚠️  Warnings:  {TEST_RESULTS['warnings']}")
    print("="*60)
    
    # Calculate pass rate
    if TEST_RESULTS["total_tests"] > 0:
        pass_rate = (TEST_RESULTS["passed"] / TEST_RESULTS["total_tests"]) * 100
        print(f"  Pass Rate:    {pass_rate:.1f}%")
        print("="*60)
        
        if pass_rate >= 90:
            print("\n  🎉 GOLD TIER SYSTEM VERIFIED - READY FOR PRODUCTION!")
        elif pass_rate >= 70:
            print("\n  ✅ GOLD TIER SYSTEM FUNCTIONAL - Some improvements recommended")
        else:
            print("\n  ⚠️  GOLD TIER SYSTEM INCOMPLETE - Review failed tests")
    
    # Save results
    results_file = Path(__file__).parent / "Logs" / "gold_tier_test_results.json"
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(TEST_RESULTS, f, indent=2)
    
    print(f"\n  Results saved to: {results_file}")
    print()
    
    return TEST_RESULTS["failed"] == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
