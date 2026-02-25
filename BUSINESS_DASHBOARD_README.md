# 🤖 AI Employee Business Dashboard

A complete autonomous AI employee system with a modern web dashboard that automatically generates business ideas, finds potential clients, and sends outreach messages.

---

## 🎯 Features

### Autonomous Business Operations
- **Business Idea Generator** - Automatically generates profitable business ideas
- **Client Finder** - Identifies potential clients with detailed profiles
- **Outreach Agent** - Creates personalized outreach messages
- **Auto-Send Emails** - Sends outreach via connected Gmail/MCP Server

### Web Dashboard
- **Real-time Status** - Monitor all system components
- **Statistics Tracking** - Ideas, clients, outreach, tasks completed
- **Autonomous Mode Toggle** - Start/stop automation with one click
- **Modern Dark UI** - ChatGPT-style interface

---

## 📁 File Structure

```
hackthone-0/
├── dashboard/
│   ├── app.py                    # Flask web server
│   ├── templates/
│   │   └── dashboard.html        # Modern dashboard UI
│   └── static/
│       └── css/
│
├── Agents/
│   ├── business_agent.py         # Business idea generator
│   ├── client_finder_agent.py    # Client discovery
│   └── outreach_agent.py         # Outreach message generator
│
├── autonomous_business_loop.py   # Main orchestration loop
├── requirements_dashboard.txt    # Python dependencies
└── BUSINESS_DASHBOARD_README.md  # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_dashboard.txt
```

### 2. Start the Dashboard

```bash
python dashboard/app.py
```

Dashboard will be available at: **http://localhost:5050/dashboard**

### 3. Start Autonomous Loop (Optional)

In a separate terminal:

```bash
# Run continuous loop (every 60 seconds)
python autonomous_business_loop.py

# Or run single cycle for testing
python autonomous_business_loop.py --once

# Dry run mode (no emails sent)
python autonomous_business_loop.py --dry-run
```

---

## 📊 Dashboard Features

### System Status
Real-time health checks for:
- MCP Server (Port 5001)
- Gmail Connection
- LinkedIn Connection
- WhatsApp Connection

### Statistics
- Business Ideas Generated
- Clients Found
- Outreach Messages Created
- Tasks Completed

### Controls
- **Autonomous Mode Toggle** - Turn automation ON/OFF
- **Run Cycle Now** - Manually trigger a business cycle
- **Refresh Data** - Update all statistics

---

## 🤖 AI Agents

### Business Agent
Generates profitable business ideas including:
- AI Automation Agency
- LinkedIn Ghostwriting
- Web Development Services
- Chatbot Development
- Social Media Management
- And 7+ more service types

### Client Finder Agent
Identifies potential clients with:
- Name and Title
- Company and Industry
- Platform (LinkedIn, etc.)
- Specific Needs
- Budget Range
- Contact Information
- Priority Score

### Outreach Agent
Creates personalized messages:
- Customized per client need
- Multiple template variations
- Follow-up message support
- Tracks sent status

---

## ⚙️ Configuration

### Environment Variables (.env.gold)

```bash
# MCP Server
MCP_SERVER_URL=http://localhost:5001

# Admin Email (fallback)
ADMIN_EMAIL=admin@example.com

# Business Loop Settings
BUSINESS_LOOP_INTERVAL=60
IDEAS_PER_CYCLE=2
CLIENTS_PER_CYCLE=3
MAX_OUTREACH_PER_CYCLE=5
DRY_RUN=False
```

### Loop Intervals

| Setting | Default | Description |
|---------|---------|-------------|
| `BUSINESS_LOOP_INTERVAL` | 60s | Time between cycles |
| `IDEAS_PER_CYCLE` | 2 | Business ideas per cycle |
| `CLIENTS_PER_CYCLE` | 3 | Clients found per cycle |
| `MAX_OUTREACH_PER_CYCLE` | 5 | Max emails sent per cycle |

---

## 📂 Data Storage

All data is stored in `AI_Employee_Vault/`:

```
AI_Employee_Vault/
├── Inbox/
│   └── business_ideas.json     # Generated business ideas
├── Needs_Action/
│   ├── clients.json            # Found clients
│   └── outreach.json           # Outreach messages
└── Reports/
    ├── business_cycle_0001.json
    ├── business_cycle_0002.json
    └── latest_cycle.json       # Most recent cycle
```

---

## 🔌 API Endpoints

### Dashboard API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System health status |
| `/api/stats` | GET | Current statistics |
| `/api/start_autonomous` | POST | Start autonomous mode |
| `/api/stop_autonomous` | POST | Stop autonomous mode |
| `/api/trigger_cycle` | POST | Run single business cycle |
| `/api/business_ideas` | GET | Get all business ideas |
| `/api/clients` | GET | Get all found clients |
| `/api/outreach` | GET | Get all outreach messages |
| `/api/tasks` | GET | Get pending tasks |
| `/api/logs` | GET | Get system logs |
| `/api/send_outreach` | POST | Send outreach email |

---

## 🧪 Testing

### Test Business Agent

```bash
python Agents/business_agent.py
```

### Test Client Finder

```bash
python Agents/client_finder_agent.py
```

### Test Outreach Agent

```bash
python Agents/outreach_agent.py
```

### Test Full Cycle

```bash
python autonomous_business_loop.py --once --dry-run
```

---

## 🎨 Dashboard UI

The dashboard features a modern dark theme with:

- **Sidebar Navigation** - Quick access to all sections
- **Status Cards** - Real-time component health
- **Statistics Grid** - Key metrics at a glance
- **Control Panel** - Autonomous mode toggle
- **Business Ideas Section** - View all generated ideas
- **Clients Section** - Browse potential clients
- **Outreach Section** - Track messages
- **Logs Section** - System activity

---

## 🔄 Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS LOOP                           │
│                     (Every 60 seconds)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Generate Business Ideas                            │
│  → Save to AI_Employee_Vault/Inbox/business_ideas.json     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Find Potential Clients                             │
│  → Save to AI_Employee_Vault/Needs_Action/clients.json     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Generate Outreach Messages                         │
│  → Save to AI_Employee_Vault/Needs_Action/outreach.json    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Send Outreach Emails                               │
│  → Via MCP Server (Port 5001)                              │
│  → Mark as sent in outreach.json                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Save Cycle Report                                  │
│  → AI_Employee_Vault/Reports/business_cycle_XXXX.json      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting

### Dashboard Won't Start

```bash
# Check if port 5050 is available
netstat -ano | findstr :5050

# Kill process if needed
taskkill /PID <PID> /F
```

### MCP Server Connection Failed

```bash
# Ensure MCP Server is running
python MCP_Server_Gold.py

# Check health
curl http://localhost:5001/health
```

### Agents Not Working

```bash
# Install dependencies
pip install -r requirements_dashboard.txt

# Check Python version (3.8+)
python --version
```

---

## 📈 Production Deployment

### Windows Service

Use NSSM or Windows Task Scheduler to run as a service:

```bash
# Task Scheduler
schtasks /create /tn "AI Employee Dashboard" /tr "python C:\path\to\dashboard\app.py" /sc onstart
```

### Linux Systemd

```ini
[Unit]
Description=AI Employee Business Dashboard
After=network.target

[Service]
Type=simple
User=ai-employee
WorkingDirectory=/opt/ai-employee
ExecStart=/usr/bin/python3 dashboard/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📝 License

Part of the Gold Tier AI Employee System.

---

## 🎯 Next Steps

1. **Configure Credentials** - Edit `.env.gold` with your API keys
2. **Start Dashboard** - `python dashboard/app.py`
3. **Enable Autonomous Mode** - Click toggle in dashboard
4. **Monitor Results** - Watch statistics update in real-time

---

**🤖 AI Employee Business Dashboard - Your Autonomous Business Development Team!**
