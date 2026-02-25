# 🔄 Live Agent Activity - Implementation Guide

Hindi/Urdu me complete guide ke Live Agent Activity feature ke liye jo vault me agent logs se read karta hai aur dashboard ko update karta hai.

---

## 📋 Overview

Ye feature apko real-time me dikhata hai ke apke saare AI agents kya kar rahe hain:

- **Current Task**: Har agent abhi kya kar raha hai
- **Time Spent**: Kitni der se ye task chal raha hai
- **Pending Actions**: Kitne tasks pending hain
- **Status Color**:
  - 🟢 **Green** = Active (pichle 30 seconds me)
  - 🟡 **Yellow** = Pending (pichle 5 minutes me)
  - 🔴 **Red** = Idle (5+ minutes se inactive)

**Auto-Refresh**: Dashboard har 10 seconds me automatically update hota hai.

---

## 📁 File Structure

```
hackthone-0/
├── utils/
│   ├── agent_activity_monitor.py    # Main monitor class
│   └── log_agent.py                 # Helper for logging
│
├── AI_Employee_Vault/
│   └── Logs/
│       └── agent_activity.json      # Activity log file
│
└── dashboard/
    ├── app_enhanced.py              # Flask app with API routes
    └── templates/
        └── dashboard_enhanced.html  # Dashboard UI
```

---

## 🚀 Kaise Kaam Karta Hai

### 1. Agent Activity Log Hoti Hai

Jab bhi koi agent koi action karta hai, wo log file me save hota hai:

```python
# Example: Business agent idea generate karta hai
from utils.log_agent import log_action

log_action('business', 'Generating business ideas', 'completed', {
    'ideas_count': 5
})
```

### 2. Dashboard API Se Data Fetch Karta Hai

Dashboard har 10 seconds me `/api/agents` endpoint ko call karta hai:

```javascript
async function refreshAgents() {
    const response = await fetch('/api/agents');
    const agents = await response.json();
    
    // Update UI with agent data
    displayAgents(agents);
}

setInterval(refreshAgents, 10000);  // 10 seconds
```

### 3. Monitor Status Calculate Karta Hai

```python
def get_agent_status(self, agent_id):
    # Get last activity timestamp
    last_activity = get_last_activity(agent_id)
    
    # Calculate time difference
    time_diff = now() - last_activity
    
    # Determine status
    if time_diff < 30 seconds:
        status = "active" (🟢)
    elif time_diff < 5 minutes:
        status = "pending" (🟡)
    else:
        status = "idle" (🔴)
```

---

## 💻 Implementation Steps

### Step 1: Agent Activity Monitor Class

`utils/agent_activity_monitor.py` me already bana hua hai.

**Key Methods:**

```python
monitor = AgentActivityMonitor()

# Log an action
monitor.log_agent_action('business', 'Generating ideas', 'completed')

# Get agent status
status = monitor.get_agent_status('orchestrator')

# Get all agents status
all_agents = monitor.get_all_agents_status()

# Get pending actions
pending = monitor.get_pending_actions()

# Get statistics
stats = monitor.get_agent_statistics(hours=24)
```

### Step 2: Agents Me Logging Add Karein

Apne existing agents me logging add karein:

**Example: Business Agent**

```python
# Agents/business_agent.py
from utils.log_agent import log_action, log_started, log_completed

class BusinessAgent:
    def generate_business_ideas(self, count=5):
        log_started('business', f'Generating {count} business ideas')
        
        try:
            # Your existing code
            ideas = self._generate_ideas(count)
            
            log_completed('business', 'Generated business ideas', {
                'ideas_count': len(ideas)
            })
            
            return ideas
        except Exception as e:
            from utils.log_agent import log_failed
            log_failed('business', 'Generating ideas', str(e))
            raise
```

**Example: Client Finder Agent**

```python
# Agents/client_finder_agent.py
from utils.log_agent import log_action

class ClientFinderAgent:
    def find_clients(self, count=5):
        log_action('client_finder', f'Finding {count} clients', 'started')
        
        clients = self._search_clients(count)
        
        log_action('client_finder', 'Found clients', 'completed', {
            'clients_count': len(clients),
            'niche': self.niche
        })
        
        return clients
```

**Example: Orchestrator**

```python
# Agents/orchestrator.py
from utils.log_agent import log_action

class OrchestratorAgent:
    def analyze_task(self, task):
        log_action('orchestrator', 'Analyzing task', 'started', {
            'task_id': task.id
        })
        
        analysis = self._analyze(task)
        
        log_action('orchestrator', 'Task analysis complete', 'completed', {
            'task_id': task.id,
            'priority': analysis.priority
        })
        
        return analysis
```

### Step 3: Dashboard API Routes

`dashboard/app_enhanced.py` me routes already hain:

```python
@app.route('/api/agents')
def api_agents():
    """Get all agents status"""
    agents = agent_monitor.get_all_agents_status()
    return jsonify(agents)

@app.route('/api/agents/<agent_id>')
def api_agent_detail(agent_id):
    """Get specific agent"""
    agent = agent_monitor.get_agent_status(agent_id)
    return jsonify(agent)

@app.route('/api/agents/log', methods=['POST'])
def api_log_agent_action():
    """Log an action"""
    data = request.json
    result = agent_monitor.log_agent_action(
        data.get('agent_id'),
        data.get('action'),
        data.get('status'),
        data.get('details')
    )
    return jsonify(result)
```

### Step 4: Dashboard UI Update

`dashboard/templates/dashboard_enhanced.html` me auto-refresh:

```javascript
// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    refreshAll();
    
    // Auto-refresh every 10 seconds
    setInterval(refreshAgents, 10000);
    setInterval(refreshStats, 15000);
});

// Refresh agents function
async function refreshAgents() {
    const response = await fetch('/api/agents');
    const agents = await response.json();
    
    const grid = document.getElementById('agents-grid');
    
    grid.innerHTML = agents.map(agent => `
        <div class="agent-card" style="border-left: 3px solid ${agent.color};">
            <div class="agent-header">
                <div class="agent-icon" style="color: ${agent.color};">
                    <i class="fas ${agent.icon}"></i>
                </div>
                <div class="agent-name">${agent.name}</div>
                <div class="agent-status ${agent.status}"></div>
            </div>
            <div class="agent-task">${agent.current_task}</div>
            <div class="agent-meta">
                <span>${agent.time_spent}</span>
                <span>${agent.tasks_completed} tasks</span>
            </div>
        </div>
    `).join('');
}
```

---

## 🎯 Usage Examples

### Example 1: Manual Logging

```python
from utils.log_agent import log_action

# Simple log
log_action('business', 'Generated 5 ideas', 'completed')

# With details
log_action('client_finder', 'Found 10 clients', 'completed', {
    'niche': 'Technology',
    'location': 'USA',
    'avg_score': 75
})
```

### Example 2: Decorator Usage

```python
from utils.log_agent import log_agent_action

@log_agent_action('outreach', 'Creating email drafts')
def generate_outreach(client):
    # Your code
    return draft

# Automatically logs:
# - "Creating email drafts - generate_outreach" (started)
# - "Creating email drafts - generate_outreach" (completed)
```

### Example 3: Start/Complete Pattern

```python
from utils.log_agent import log_started, log_completed, log_failed

def process_task(task):
    log_started('orchestrator', f'Processing task {task.id}')
    
    try:
        result = execute_task(task)
        log_completed('orchestrator', f'Processed task {task.id}', {
            'result': result
        })
    except Exception as e:
        log_failed('orchestrator', f'Processing task {task.id}', str(e))
        raise
```

---

## 📊 Dashboard Display

### Agent Card Structure

```
┌─────────────────────────────────────┐
│ 🧠 Orchestrator Agent        🟢    │
│ Master controller & task router     │
│                                     │
│ Analyzing new email task            │
│ 15s ago        5 tasks              │
└─────────────────────────────────────┘
```

### Status Colors

| Color | Status | Meaning |
|-------|--------|---------|
| 🟢 | Active | Pichle 30 seconds me activity thi |
| 🟡 | Pending | Pichle 5 minutes me activity thi |
| 🔴 | Idle | 5+ minutes se koi activity nahi |

---

## 🔧 Testing

### Test Agent Activity Monitor

```bash
cd D:\hackthone-0
python utils/agent_activity_monitor.py
```

### Test Logger

```bash
python utils/log_agent.py
```

### Test Dashboard

```bash
python dashboard/app_enhanced.py
```

Visit: http://localhost:5050/dashboard

### Test API Endpoints

```bash
# Get all agents
curl http://localhost:5050/api/agents

# Get specific agent
curl http://localhost:5050/api/agents/orchestrator

# Get active agents only
curl http://localhost:5050/api/agents/active

# Get pending actions
curl http://localhost:5050/api/agents/pending

# Get statistics
curl http://localhost:5050/api/agents/stats?hours=24

# Log an action
curl -X POST http://localhost:5050/api/agents/log \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "business", "action": "Test action", "status": "completed"}'
```

---

## 📁 Log File Structure

`AI_Employee_Vault/Logs/agent_activity.json`:

```json
[
  {
    "id": "act_20260220163045_001",
    "agent_id": "business",
    "agent_name": "Business Agent",
    "action": "Generating business ideas",
    "status": "completed",
    "details": {
      "ideas_count": 5
    },
    "timestamp": "2026-02-20T16:30:45.123456",
    "timestamp_formatted": "2026-02-20 16:30:45"
  }
]
```

---

## 🎨 Customization

### Add New Agent

`agent_activity_monitor.py` me `self.agents` dictionary me add karein:

```python
self.agents = {
    "new_agent": {
        "id": "new_agent",
        "name": "New Agent",
        "icon": "fa-star",
        "description": "Does something amazing",
        "color": "#ff00ff"
    }
}
```

### Change Refresh Interval

Dashboard HTML me change karein:

```javascript
// Change from 10000 (10s) to desired milliseconds
setInterval(refreshAgents, 5000);  // 5 seconds
```

### Change Status Thresholds

`agent_activity_monitor.py` me `get_agent_status()` method:

```python
if seconds_ago < 60:  # Change threshold
    status = "active"
elif seconds_ago < 600:  # Change threshold
    status = "pending"
```

---

## 🛠️ Troubleshooting

### Agents Show as Idle

**Problem**: Saare agents red (idle) show ho rahe hain

**Solution**:
1. Check autonomous loop chal raha hai ya nahi
2. Manual activity log karein:
   ```python
   log_action('orchestrator', 'System running', 'completed')
   ```
3. Dashboard refresh karein (Ctrl+F5)

### Activity Log File Nahi Hai

**Problem**: `agent_activity.json` file nahi hai

**Solution**:
```python
# File automatically create hogi jab pehli activity log hogi
# Manually create karna ho to:
from pathlib import Path
Path('AI_Employee_Vault/Logs/agent_activity.json').touch()
```

### Dashboard Data Show Nahi Kar Raha

**Problem**: Dashboard blank hai

**Solution**:
1. Browser console me errors check karein
2. Flask console me errors check karein
3. API test karein:
   ```bash
   curl http://localhost:5050/api/agents
   ```

---

## ✅ Quick Start

1. **Start Dashboard**:
   ```bash
   python dashboard/app_enhanced.py
   ```

2. **Start Autonomous Loop**:
   ```bash
   python autonomous_business_loop.py
   ```

3. **Open Browser**:
   ```
   http://localhost:5050/dashboard
   ```

4. **Enable Autonomous Mode**:
   - Toggle switch ON karein
   - Agents active ho jayenge
   - Dashboard auto-refresh hoga har 10 seconds me

---

## 📝 Summary

- ✅ **12 AI Agents** tracked in real-time
- ✅ **Auto-refresh** every 10 seconds
- ✅ **Color-coded status**: Green/Yellow/Red
- ✅ **Current task** display
- ✅ **Time spent** tracking
- ✅ **Pending actions** counter
- ✅ **Activity logs** saved to vault
- ✅ **API endpoints** for integration

---

**🔄 Live Agent Activity - Complete Implementation Ready!**
