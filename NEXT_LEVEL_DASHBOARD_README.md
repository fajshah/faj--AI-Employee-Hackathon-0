# 🚀 Next Level AI Employee Dashboard

A fully integrated, autonomous AI employee system with live agent activity tracking, email/LinkedIn integration, auto client finder with scoring, and revenue tracking.

---

## ✨ Features Overview

### 1. 🔄 Live Agent Activity
- **Real-time monitoring** of all AI agents
- **Status indicators**: Green (active), Yellow (pending), Red (idle)
- **Current task display** with time spent
- **Auto-refresh** every 5 seconds

### 2. 📧 Send Email Button
- **AI-generated email drafts** for each client
- **Professional templates**: Outreach, Follow-up, Proposal
- **One-click open** in Gmail/Outlook
- **Manual review** before sending

### 3. 💼 Post to LinkedIn Button
- **AI-generated LinkedIn posts**
- **Multiple topics**: Business, Success, Tips, Announcement
- **Auto-copy to clipboard**
- **Direct link** to LinkedIn feed

### 4. 🎯 Auto Client Finder
- **Intelligent lead scoring** (0-100)
- **Tier categorization**: A (Hot), B (Warm), C (Cold), D (Long Shot)
- **Revenue potential estimation**
- **Multi-source discovery**: LinkedIn, directories, websites
- **Filter by niche and location**

### 5. 📊 Revenue Tracker
- **Total sales tracking**
- **Pending invoices management**
- **Projected revenue calculation**
- **Weekly/Monthly revenue charts**
- **Trend analysis** with percentage changes

---

## 📁 File Structure

```
hackthone-0/
├── dashboard/
│   ├── app.py                      # Main Flask app (updated)
│   ├── app_enhanced.py             # Enhanced Flask app (alternative)
│   └── templates/
│       ├── dashboard.html          # Original dashboard
│       └── dashboard_enhanced.html # Next Level dashboard
│
├── Agents/
│   ├── business_agent.py           # Business idea generator
│   ├── client_finder_agent.py      # Base client finder
│   └── outreach_agent.py           # Outreach message generator
│
├── AI_Employee_Vault/
│   ├── Inbox/
│   │   └── business_ideas.json     # Generated ideas
│   ├── Needs_Action/
│   │   ├── clients.json            # Basic clients
│   │   ├── clients_advanced.json   # Scored clients
│   │   └── outreach.json           # Outreach messages
│   ├── Reports/
│   │   └── business_cycle_*.json   # Cycle reports
│   └── revenue_data.json           # Revenue tracking
│
├── Logs/
│   ├── agent_activity.json         # Agent activity log
│   └── *.log                       # System logs
│
├── autonomous_business_loop.py     # Main automation loop
└── NEXT_LEVEL_DASHBOARD_README.md  # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install flask requests python-dotenv schedule chart.js
```

### 2. Start the Dashboard

```bash
python dashboard/app.py
```

Dashboard will be available at: **http://localhost:5050/dashboard**

### 3. Start Autonomous Loop (Optional)

In a separate terminal:

```bash
python autonomous_business_loop.py
```

---

## 🎨 Dashboard Sections

### Live Agent Activity

Displays 8 AI agents with real-time status:

| Agent | Icon | Description |
|-------|------|-------------|
| Orchestrator | 🧠 | Master controller & task router |
| Business | 💡 | Generates business ideas |
| Client Finder | 🔍 | Finds potential clients |
| Outreach | 📧 | Creates outreach messages |
| Monitoring | 👁️ | Monitors inbox & tasks |
| Comms | 💬 | Handles communications |
| Finance | 📈 | Manages revenue & invoices |
| Audit | 📋 | Generates reports |

**Status Colors:**
- 🟢 **Green**: Active (last 30 seconds)
- 🟡 **Yellow**: Pending (last 5 minutes)
- 🔴 **Red**: Idle (no recent activity)

---

### Client Management

#### Client Scoring System

| Score | Tier | Label | Priority |
|-------|------|-------|----------|
| 80-100 | A | 🔴 Hot Lead | Immediate |
| 60-79 | B | 🟠 Warm Lead | This Week |
| 40-59 | C | 🟡 Cold Lead | This Month |
| 0-39 | D | ⚪ Long Shot | Nurture |

#### Scoring Factors

1. **Budget Range** (0-25 points)
2. **Decision Maker** (0-20 points)
3. **Company Size** (0-20 points)
4. **Need Alignment** (0-20 points)
5. **Platform/Engagement** (0-15 points)

#### Client Actions

Each client card has action buttons:

- **📧 Send Email**: Generate & send AI draft
- **💼 LinkedIn**: Create & post LinkedIn content

---

### Email Generation

**3 Email Templates:**

1. **Outreach**: Initial contact email
2. **Follow-up**: Second touch email
3. **Proposal**: Detailed proposal email

**Email Workflow:**
1. Click email button on client card
2. AI generates personalized draft
3. Review in modal
4. Click "Send Email"
5. Opens in Gmail/Outlook for final review
6. Send manually or schedule follow-up

---

### LinkedIn Post Generator

**4 Post Topics:**

1. **Business**: Thought leadership content
2. **Success**: Client success stories
3. **Tips**: Educational content
4. **Announcement**: Offers & promotions

**Post Workflow:**
1. Click LinkedIn button
2. Select post topic
3. AI generates professional post
4. Content copied to clipboard
5. Opens LinkedIn in new tab
6. Paste and publish

---

### Revenue Tracker

**Metrics Tracked:**

- Total Sales (all-time)
- Pending Invoices
- Closed Deals Count
- Projected Revenue
- Weekly Trend (%)
- Monthly Trend (%)

**Revenue Chart:**
- Line chart showing weekly revenue
- Last 12 weeks of data
- Interactive hover tooltips
- Auto-updates with new deals

**Add Invoice:**
```javascript
POST /api/add-invoice
{
  "client": "Company Name",
  "amount": 5000,
  "due_date": "2026-03-20"
}
```

**Mark as Paid:**
```javascript
POST /api/mark-paid/{invoice_id}
```

---

## 🔌 API Endpoints

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System health & status |
| `/api/agents` | GET | Live agent activity |
| `/api/stats` | GET | Overall statistics |

### Clients

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/clients` | GET | Get all clients |
| `/api/find-clients` | POST | Find new clients |

### Email & LinkedIn

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/email-draft` | POST | Generate email draft |
| `/api/linkedin-post` | POST | Generate LinkedIn post |
| `/api/send-email` | POST | Send email |

### Revenue

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/revenue` | GET | Get revenue data |
| `/api/add-invoice` | POST | Add new invoice |
| `/api/mark-paid/{id}` | POST | Mark invoice paid |

### Automation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/start_autonomous` | POST | Start autonomous mode |
| `/api/stop_autonomous` | POST | Stop autonomous mode |
| `/api/trigger-cycle` | POST | Run business cycle |

---

## 🎯 Auto Client Finder Usage

### Find Clients via UI

1. Go to Clients section
2. Select niche filter (optional)
3. Click "Find Clients" button
4. System searches and scores clients
5. New clients appear in list

### Find Clients via API

```bash
curl -X POST http://localhost:5050/api/find-clients \
  -H "Content-Type: application/json" \
  -d '{"niche": "Technology", "count": 10}'
```

### Response

```json
{
  "status": "success",
  "clients_found": 10,
  "new_clients": 8,
  "clients": [
    {
      "id": "client_20260220_001",
      "name": "Tech Startup Founder",
      "company": "TechAI Systems",
      "lead_score": 85,
      "tier": "A",
      "tier_label": "Hot Lead",
      "revenue_potential": {
        "min": 10000,
        "max": 50000,
        "estimated": 30000
      }
    }
  ]
}
```

---

## 📊 Revenue Tracking

### View Revenue Data

```bash
curl http://localhost:5050/api/revenue
```

### Add Invoice

```bash
curl -X POST http://localhost:5050/api/add-invoice \
  -H "Content-Type: application/json" \
  -d '{"client": "Acme Corp", "amount": 7500, "due_date": "2026-03-20"}'
```

### Mark Invoice Paid

```bash
curl -X POST http://localhost:5050/api/mark-paid/inv_20260220_001
```

### Revenue Data Structure

```json
{
  "total_sales": 45000,
  "pending_invoices": 2,
  "pending_amount": 15000,
  "closed_deals": 6,
  "projected_revenue": 60000,
  "weekly_trend": 12.5,
  "monthly_trend": 8.3,
  "weekly_data": [
    {"week": "2026-W07", "revenue": 12000, "deals": 2}
  ],
  "monthly_data": [
    {"month": "2026-02", "revenue": 25000, "deals": 4}
  ]
}
```

---

## 🎨 UI Components

### Stats Cards
- 4 cards showing key metrics
- Color-coded icons
- Trend indicators
- Gradient top borders

### Agent Cards
- Grid layout (responsive)
- Status indicator dots
- Current task display
- Time spent tracking

### Client Cards
- Avatar with initials
- Name, company, industry
- Tier badge (Hot/Warm/Cold)
- Lead score badge
- Action buttons

### Revenue Chart
- Chart.js powered
- Line chart with gradient fill
- Responsive design
- Interactive tooltips

### Modals
- Email draft modal
- LinkedIn post modal
- Backdrop blur effect
- Keyboard accessible

---

## ⚙️ Configuration

### Environment Variables (.env.gold)

```bash
# MCP Server
MCP_SERVER_URL=http://localhost:5001

# Email
GMAIL_TOKEN_FILE=tokens/gmail_token.json

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your_token_here

# WhatsApp
WHATSAPP_ACCESS_TOKEN=your_token_here

# Business Loop
BUSINESS_LOOP_INTERVAL=60
IDEAS_PER_CYCLE=2
CLIENTS_PER_CYCLE=3
MAX_OUTREACH_PER_CYCLE=5
DRY_RUN=False
```

---

## 🧪 Testing

### Test Dashboard

```bash
python dashboard/app.py
```

Visit: http://localhost:5050/dashboard

### Test Agent Activity

```bash
curl http://localhost:5050/api/agents
```

### Test Client Finder

```bash
curl -X POST http://localhost:5050/api/find-clients \
  -H "Content-Type: application/json" \
  -d '{"count": 5}'
```

### Test Email Draft

```bash
curl -X POST http://localhost:5050/api/email-draft \
  -H "Content-Type: application/json" \
  -d '{"client": {"name": "John Doe", "company": "Acme"}, "type": "outreach"}'
```

### Test LinkedIn Post

```bash
curl -X POST http://localhost:5050/api/linkedin-post \
  -H "Content-Type: application/json" \
  -d '{"topic": "business"}'
```

### Test Revenue

```bash
curl http://localhost:5050/api/revenue
```

---

## 🔄 Autonomous Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                 AUTONOMOUS LOOP                              │
│                  (Every 60 seconds)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Generate Business Ideas                                  │
│  2. Find & Score Clients                                     │
│  3. Generate Outreach Messages                               │
│  4. Send Emails (via MCP)                                    │
│  5. Update Revenue Data                                      │
│  6. Log Agent Activity                                       │
│  7. Save Cycle Report                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Dashboard Updates in Real-Time                              │
│  • Agent Activity (5s refresh)                               │
│  • Statistics (10s refresh)                                  │
│  • Revenue Chart (on demand)                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting

### Dashboard Won't Start

```bash
# Check port availability
netstat -ano | findstr :5050

# Kill process if needed
taskkill /PID <PID> /F
```

### Agents All Show as Idle

- Ensure autonomous loop is running
- Check agent activity log: `Logs/agent_activity.json`
- Trigger manual cycle: Click "Run Cycle Now"

### Client Finder Not Working

- Verify `Agents/client_finder_agent.py` exists
- Check for Python errors in console
- Ensure `AI_Employee_Vault/Needs_Action/` directory exists

### Revenue Chart Not Displaying

- Check if Chart.js is loaded (CDN link in HTML)
- Verify revenue data exists: `AI_Employee_Vault/revenue_data.json`
- Refresh browser cache (Ctrl+F5)

---

## 📈 Advanced Features

### Custom Email Templates

Edit `generate_email_draft()` in `dashboard/app.py`:

```python
templates['custom'] = {
    'subject': 'Your custom subject',
    'body': '''Your custom email body'''
}
```

### Custom LinkedIn Posts

Edit `generate_linkedin_post()` in `dashboard/app.py`:

```python
posts['custom'] = {
    'content': 'Your custom post content',
    'hashtags': ['#Your', '#Hashtags']
}
```

### Custom Client Scoring

Edit `calculate_lead_score()` in `AutoClientFinder`:

```python
def calculate_lead_score(self, client):
    score = 0
    # Add your custom scoring logic
    score += custom_factor * weight
    return min(score, 100)
```

---

## 🎯 Best Practices

1. **Review Before Sending**: Always review AI-generated emails before sending
2. **Personalize Outreach**: Add personal touches to automated messages
3. **Monitor Agent Activity**: Check dashboard regularly for issues
4. **Track Revenue**: Update invoices as deals close
5. **Score Clients**: Focus on A & B tier leads first
6. **A/B Test Posts**: Try different LinkedIn post topics

---

## 📝 License

Part of the Gold Tier AI Employee System.

---

## 🚀 Next Steps

1. **Start Dashboard**: `python dashboard/app.py`
2. **Enable Autonomous Mode**: Toggle switch in dashboard
3. **Find Clients**: Click "Find Clients" button
4. **Send Outreach**: Use email buttons on client cards
5. **Post to LinkedIn**: Generate and share content
6. **Track Revenue**: Add invoices as deals close
7. **Monitor Activity**: Watch agent status in real-time

---

**🚀 Next Level AI Employee Dashboard - Your Complete Business Automation Command Center!**
