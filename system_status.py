"""
System Status Dashboard Backend

Provides comprehensive system status for the Gold Tier AI Employee.
Returns JSON data suitable for dashboard display.

Features:
- Component health status
- Task statistics
- Revenue tracking
- Recent activity
- System metrics

Usage:
    python system_status.py              # Print status JSON
    python system_status.py --dashboard  # Run as HTTP server
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv('.env.gold')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/system_status.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemStatus")

# Base directories
SCRIPT_DIR = Path(__file__).parent.absolute()
LOGS_DIR = SCRIPT_DIR / "Logs"
DONE_DIR = SCRIPT_DIR / "Done"
NEEDS_ACTION_DIR = SCRIPT_DIR / "Needs_Action"
PENDING_APPROVAL_DIR = SCRIPT_DIR / "Pending_Approval"
PLANS_DIR = SCRIPT_DIR / "Plans"


def count_files(directory: Path, pattern: str = "*.json") -> int:
    """Count files in a directory matching pattern"""
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def get_recent_files(directory: Path, pattern: str = "*.json", limit: int = 5) -> List[Dict]:
    """Get recent files from a directory"""
    if not directory.exists():
        return []
    
    files = list(directory.glob(pattern))
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    recent = []
    for f in files[:limit]:
        recent.append({
            "name": f.name,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            "size": f.stat().st_size
        })
    
    return recent


def get_mcp_server_status() -> Dict[str, Any]:
    """Get status of all MCP servers"""
    servers = {
        "mcp_comms": {"port": 5001, "healthy": False},
        "mcp_social": {"port": 5002, "healthy": False},
        "mcp_finance": {"port": 5003, "healthy": False}
    }
    
    try:
        import requests
        
        for server, info in servers.items():
            try:
                response = requests.get(f"http://localhost:{info['port']}/health", timeout=3)
                if response.status_code == 200:
                    servers[server]["healthy"] = True
                    servers[server]["response"] = response.json()
            except:
                servers[server]["healthy"] = False
    except:
        pass
    
    return servers


def get_task_statistics() -> Dict[str, Any]:
    """Get task processing statistics"""
    stats = {
        "needs_action": count_files(NEEDS_ACTION_DIR),
        "pending_approval": count_files(PENDING_APPROVAL_DIR),
        "plans": count_files(PLANS_DIR),
        "completed": count_files(DONE_DIR),
        "recent_completed": get_recent_files(DONE_DIR, limit=5)
    }
    
    # Calculate completion rate (tasks completed in last 24 hours)
    now = datetime.now()
    completed_24h = 0
    
    if DONE_DIR.exists():
        for f in DONE_DIR.glob("*.json"):
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if now - mtime < timedelta(hours=24):
                completed_24h += 1
    
    stats["completed_24h"] = completed_24h
    
    return stats


def get_revenue_data() -> Dict[str, Any]:
    """Get revenue data from Odoo or local tracking"""
    # Try to get from Odoo first
    try:
        from config.odoo_config import get_revenue_summary
        
        summary = get_revenue_summary()
        
        if summary.get("status") == "success":
            return {
                "source": "odoo",
                "revenue": summary.get("revenue", 0),
                "invoices_count": summary.get("invoices_count", 0),
                "currency": "USD"
            }
    except Exception as e:
        logger.debug(f"Odoo revenue fetch failed: {e}")
    
    # Fallback to local tracking
    revenue_file = SCRIPT_DIR / "AI_Employee_Vault" / "revenue_data.json"
    
    if revenue_file.exists():
        try:
            with open(revenue_file, 'r') as f:
                data = json.load(f)
            return {
                "source": "local",
                "revenue": data.get("total_revenue", 0),
                "last_updated": data.get("last_updated", "unknown")
            }
        except:
            pass
    
    return {
        "source": "none",
        "revenue": 0,
        "message": "No revenue tracking configured"
    }


def get_social_media_status() -> Dict[str, Any]:
    """Get social media configuration and posting status"""
    try:
        from config.social_config import get_status
        return get_status()
    except:
        return {
            "mock_mode": True,
            "configured_platforms": [],
            "message": "Social media not configured"
        }


def get_recent_activity() -> List[Dict]:
    """Get recent activity from logs"""
    activities = []
    
    # Read recent log files
    if LOGS_DIR.exists():
        log_files = sorted(LOGS_DIR.glob("*.json"), reverse=True)[:20]
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    log_entry = json.load(f)
                
                activities.append({
                    "timestamp": log_entry.get("timestamp", "unknown"),
                    "action": log_entry.get("action_type", log_entry.get("action", "unknown")),
                    "status": log_entry.get("status", "unknown"),
                    "task_id": log_entry.get("task_id", "unknown"),
                    "source": log_file.name
                })
            except:
                continue
    
    return activities[:10]  # Return last 10 activities


def get_system_metrics() -> Dict[str, Any]:
    """Get system resource metrics"""
    import psutil
    
    metrics = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_available_gb": psutil.virtual_memory().available / (1024**3),
        "disk_percent": psutil.disk_usage(str(SCRIPT_DIR)).percent,
        "disk_free_gb": psutil.disk_usage(str(SCRIPT_DIR)).free / (1024**3)
    }
    
    return metrics


def get_health_status() -> Dict[str, Any]:
    """Get overall system health status"""
    mcp_status = get_mcp_server_status()
    mcp_healthy = all(s["healthy"] for s in mcp_status.values())
    
    task_stats = get_task_statistics()
    error_count = count_files(SCRIPT_DIR / "Error")
    
    # Determine overall health
    if mcp_healthy and error_count < 5:
        overall = "healthy"
    elif error_count > 20:
        overall = "degraded"
    else:
        overall = "warning"
    
    return {
        "overall": overall,
        "mcp_servers": mcp_status,
        "mcp_healthy": mcp_healthy,
        "error_count": error_count,
        "tasks_pending": task_stats["needs_action"] + task_stats["pending_approval"]
    }


def get_full_status() -> Dict[str, Any]:
    """Get complete system status"""
    return {
        "timestamp": datetime.now().isoformat(),
        "health": get_health_status(),
        "tasks": get_task_statistics(),
        "revenue": get_revenue_data(),
        "social_media": get_social_media_status(),
        "recent_activity": get_recent_activity(),
        "system_metrics": get_system_metrics(),
        "components": {
            "agents_running": True,
            "mcp_servers": 3,
            "watchers_active": 3
        }
    }


def print_status():
    """Print formatted status to console"""
    status = get_full_status()
    
    print("\n" + "="*60)
    print("  GOLD TIER AI EMPLOYEE - SYSTEM STATUS")
    print("="*60)
    print(f"  Timestamp: {status['timestamp']}")
    print("="*60)
    
    # Health
    health = status["health"]
    health_icon = "✅" if health["overall"] == "healthy" else "⚠️" if health["overall"] == "warning" else "❌"
    print(f"\n  {health_icon} Overall Health: {health['overall'].upper()}")
    print(f"     MCP Servers: {'✅ All healthy' if health['mcp_healthy'] else '❌ Some issues'}")
    print(f"     Errors: {health['error_count']}")
    print(f"     Pending Tasks: {health['tasks_pending']}")
    
    # Tasks
    tasks = status["tasks"]
    print(f"\n  📊 Task Statistics:")
    print(f"     Needs Action: {tasks['needs_action']}")
    print(f"     Pending Approval: {tasks['pending_approval']}")
    print(f"     Plans Created: {tasks['plans']}")
    print(f"     Completed (24h): {tasks['completed_24h']}")
    print(f"     Total Completed: {tasks['completed']}")
    
    # Revenue
    revenue = status["revenue"]
    print(f"\n  💰 Revenue Tracking:")
    print(f"     Source: {revenue['source'].upper()}")
    print(f"     Revenue: ${revenue.get('revenue', 0):,.2f}")
    
    # Social Media
    social = status["social_media"]
    platforms = ", ".join(social.get("configured_platforms", [])) or "None"
    print(f"\n  📱 Social Media:")
    print(f"     Mock Mode: {social.get('mock_mode', True)}")
    print(f"     Configured: {platforms}")
    
    # System Metrics
    metrics = status["system_metrics"]
    print(f"\n  🖥️  System Metrics:")
    print(f"     CPU: {metrics['cpu_percent']:.1f}%")
    print(f"     Memory: {metrics['memory_percent']:.1f}% ({metrics['memory_available_gb']:.1f}GB available)")
    print(f"     Disk: {metrics['disk_percent']:.1f}% ({metrics['disk_free_gb']:.1f}GB free)")
    
    print("\n" + "="*60)


def run_dashboard_server(port: int = 8080):
    """Run HTTP server for dashboard"""
    from flask import Flask, jsonify, render_template_string
    
    app = Flask(__name__)
    
    # HTML Dashboard Template
    DASHBOARD_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gold Tier AI Employee Dashboard</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .status-ok { color: #22c55e; font-weight: bold; }
            .status-error { color: #ef4444; font-weight: bold; }
            .status-warn { color: #f59e0b; font-weight: bold; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            h1 { margin: 0; }
            h2 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏆 Gold Tier AI Employee Dashboard</h1>
            <p>Real-time system monitoring</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>🔌 MCP Servers</h2>
                <div id="servers">Loading...</div>
            </div>
            
            <div class="card">
                <h2>📊 Tasks</h2>
                <div id="tasks">Loading...</div>
            </div>
            
            <div class="card">
                <h2>⚙️ Configuration</h2>
                <div id="config">Loading...</div>
            </div>
            
            <div class="card">
                <h2>💻 System</h2>
                <div id="system">Loading...</div>
            </div>
        </div>
        
        <div class="card">
            <h2>📈 Recent Activity</h2>
            <div id="activity">Loading...</div>
        </div>
        
        <script>
            async function loadDashboard() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    // Update Servers
                    const servers = data.health.mcp_servers;
                    let serversHtml = '';
                    for (const [name, info] of Object.entries(servers)) {
                        const status = info.healthy ? '<span class="status-ok">● ONLINE</span>' : '<span class="status-error">● OFFLINE</span>';
                        serversHtml += `<div>${name.replace('_', ' ').toUpperCase()}: ${status} (Port ${info.port})</div>`;
                    }
                    document.getElementById('servers').innerHTML = serversHtml;
                    
                    // Update Tasks
                    const tasks = data.tasks;
                    document.getElementById('tasks').innerHTML = `
                        <div>Needs Action: <strong>${tasks.needs_action}</strong></div>
                        <div>Pending Approval: <strong>${tasks.pending_approval}</strong></div>
                        <div>Completed: <strong>${tasks.completed}</strong></div>
                    `;
                    
                    // Update Config
                    const config = data.social_media;
                    let platforms = config.configured_platforms.join(', ') || 'None';
                    document.getElementById('config').innerHTML = `
                        <div>Mock Mode: ${config.mock_mode ? '<span class="status-warn">Yes</span>' : '<span class="status-ok">No</span>'}</div>
                        <div>Platforms: ${platforms}</div>
                    `;
                    
                    // Update System
                    const metrics = data.system_metrics;
                    document.getElementById('system').innerHTML = `
                        <div>CPU: ${metrics.cpu_percent.toFixed(1)}%</div>
                        <div>Memory: ${metrics.memory_percent.toFixed(1)}%</div>
                        <div>Disk: ${metrics.disk_percent.toFixed(1)}%</div>
                    `;
                    
                    // Update Activity
                    const activity = data.recent_activity.slice(0, 5);
                    let activityHtml = '<table style="width:100%"><tr><th>Time</th><th>Action</th><th>Status</th></tr>';
                    activity.forEach(a => {
                        const time = new Date(a.timestamp).toLocaleTimeString();
                        const status = a.status === 'success' ? '<span class="status-ok">✓</span>' : '<span class="status-error">✗</span>';
                        activityHtml += `<tr><td>${time}</td><td>${a.action}</td><td>${status}</td></tr>`;
                    });
                    activityHtml += '</table>';
                    document.getElementById('activity').innerHTML = activityHtml;
                    
                } catch (error) {
                    console.error('Error loading dashboard:', error);
                }
            }
            
            loadDashboard();
            setInterval(loadDashboard, 10000);
        </script>
    </body>
    </html>
    """
    
    @app.route('/')
    def dashboard():
        return render_template_string(DASHBOARD_HTML)
    
    @app.route('/api/status')
    def api_status():
        return jsonify(get_full_status())
    
    @app.route('/api/health')
    def api_health():
        return jsonify(get_health_status())
    
    @app.route('/api/tasks')
    def api_tasks():
        return jsonify(get_task_statistics())
    
    @app.route('/api/revenue')
    def api_revenue():
        return jsonify(get_revenue_data())
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy"})
    
    logger.info(f"Starting dashboard server on port {port}")
    print(f"\n" + "="*60)
    print("  GOLD TIER DASHBOARD SERVER")
    print("="*60)
    print(f"  URL: http://localhost:{port}")
    print("="*60)
    print("\nAPI endpoints:")
    print("  GET /           - Visual Dashboard (Auto-refresh 10s)")
    print("  GET /api/status - Full system status")
    print("  GET /api/health - Health status")
    print("  GET /api/tasks  - Task statistics")
    print("  GET /api/revenue- Revenue data")
    print("="*60)
    print("\nPress CTRL+C to quit")
    
    app.run(host='localhost', port=port, debug=False, threaded=True)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='System Status Dashboard')
    parser.add_argument('--dashboard', action='store_true', help='Run as HTTP server')
    parser.add_argument('--port', type=int, default=8080, help='Dashboard server port')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    if args.dashboard:
        run_dashboard_server(args.port)
    elif args.json:
        print(json.dumps(get_full_status(), indent=2))
    else:
        print_status()


if __name__ == "__main__":
    main()
