# ☁️ PLATINUM TIER CLOUD ORCHESTRATOR
## Complete Implementation Guide

---

## 📖 OVERVIEW

The **Platinum Tier Cloud Orchestrator** transforms your Gold Tier AI Employee system from local-only execution to a **hybrid cloud architecture** with strict security boundaries:

| Component | Location | Responsibility |
|-----------|----------|----------------|
| **Cloud Orchestrator** | Cloud | Draft generation, task analysis |
| **Gmail Cloud Watcher** | Cloud | Read-only email monitoring |
| **Draft Generator** | Cloud | Claude-powered content creation |
| **CEO Briefing Generator** | Cloud | Executive reporting |
| **Local Executor** | Local | Actual action execution |
| **Human Approval** | Local | Review & approve drafts |

---

## 🔐 SECURITY CONSTRAINTS (NON-NEGOTIABLE)

### Cloud Components CAN:
- ✅ Read emails from Gmail
- ✅ Analyze tasks using Claude AI
- ✅ Generate draft responses/posts/messages
- ✅ Create executive briefings
- ✅ Write drafts to `Pending_Approval/` directory
- ✅ Sync state via Git vault

### Cloud Components CANNOT:
- ❌ Send emails
- ❌ Post to LinkedIn/social media
- ❌ Send WhatsApp messages
- ❌ Execute payments or financial transactions
- ❌ Access OAuth tokens or session cookies
- ❌ Execute any external API actions

---

## 🚀 QUICK START

### 1. Install Dependencies

```bash
pip install -r requirements_platinum.txt
```

### 2. Configure Environment

```bash
# Copy example file
cp .env.platinum.example .env.platinum

# Edit with your credentials
# Required: CLAUDE_API_KEY, GMAIL credentials (for watcher)
```

### 3. Test in DRY_RUN Mode

```bash
# Test Cloud Orchestrator
python cloud_orchestrator.py --dry-run --status

# Test Gmail Watcher (single scan)
python gmail_cloud_watcher.py --dry-run --once

# Test Draft Generator
python draft_generator.py --dry-run --status

# Test CEO Briefing Generator
python ceo_weekly_briefing.py --dry-run --once
```

### 4. Deploy to Cloud

```bash
# Example: Docker deployment
docker build -t cloud-orchestrator .
docker run -e CLAUDE_API_KEY=xxx cloud-orchestrator
```

---

## 📁 FILE STRUCTURE

```
hackthone-0/
├── cloud_orchestrator.py        # Main cloud orchestration service
├── gmail_cloud_watcher.py       # Async Gmail monitoring
├── draft_generator.py           # Claude-powered draft generation
├── ceo_weekly_briefing.py       # Executive briefing generator
├── requirements_platinum.txt    # Cloud dependencies
├── .env.platinum.example        # Environment template
│
├── Cloud_Storage/               # Cloud sync directory
│   ├── inbox/                   # New tasks from cloud
│   ├── processed/               # Processed tasks
│   └── gmail_processed/         # Processed emails
│
├── Pending_Approval/            # Drafts awaiting approval
├── Generated_Drafts/            # AI-generated drafts
├── CEO_Briefings/               # Weekly executive briefings
├── Plans/                       # Task plans (Claude-generated)
│
└── Logs/                        # All component logs
    ├── cloud_orchestrator.log
    ├── gmail_cloud_watcher.log
    ├── draft_generator.log
    └── ceo_briefing.log
```

---

## 🏗️ ARCHITECTURE

### Cloud Orchestrator Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ CLOUD COMPONENTS (This Package)                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Gmail Cloud      │  │ Cloud            │  │ Draft            │  │
│  │ Watcher          │  │ Orchestrator     │  │ Generator        │  │
│  │                  │  │                  │  │                  │  │
│  │ • Read emails    │  │ • Analyze tasks  │  │ • Email drafts   │  │
│  │ • Parse content  │  │ • Claude AI      │  │ • Social posts   │  │
│  │ • Create tasks   │  │ • Generate drafts│  │ • WhatsApp msgs  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                     │                     │            │
│           └─────────────────────┼─────────────────────┘            │
│                                 │                                  │
│                                 ▼                                  │
│                    ┌────────────────────────┐                     │
│                    │ Pending_Approval/      │                     │
│                    │ (Security Boundary)    │                     │
│                    └────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ Git Sync
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LOCAL COMPONENTS (Gold Tier)                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Human Approval   │  │ Local            │  │ MCP Server       │  │
│  │ Interface        │  │ Orchestrator     │  │                  │  │
│  │                  │  │                  │  │                  │  │
│  │ • Review drafts  │  │ • Execute tasks  │  │ • Send emails    │  │
│  │ • Approve/Reject │  │ • After approval │  │ • Post LinkedIn  │  │
│  │ • Add comments   │  │ • Local APIs     │  │ • Send WhatsApp  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 COMPONENT DETAILS

### 1. Cloud Orchestrator (`cloud_orchestrator.py`)

**Purpose**: Main coordination service for cloud operations

**Features**:
- Async task processing
- Claude AI integration for analysis
- Draft generation and filing
- Git vault sync for audit trail
- Cloud storage integration (S3, Azure, GCS)

**API Endpoints** (if deployed as service):
```
GET  /health          - Health check
GET  /status          - System status
POST /task/analyze    - Analyze task with Claude
POST /task/draft      - Generate task draft
GET  /briefing/latest - Get latest CEO briefing
```

**Configuration**:
```bash
# Required
CLAUDE_API_KEY=your_key_here
CLOUD_STORAGE_TYPE=local|s3|azure|gcs
DRY_RUN=true

# Optional
MONITOR_INTERVAL_SECONDS=30
GIT_SYNC_ENABLED=false
```

---

### 2. Gmail Cloud Watcher (`gmail_cloud_watcher.py`)

**Purpose**: Read-only Gmail monitoring

**Features**:
- Async Gmail API integration
- Email classification (category, priority, sentiment)
- Entity extraction (dates, money, deadlines)
- Task creation from emails
- Attachment detection

**Security**:
- **READ-ONLY** - Uses `gmail.readonly` scope
- Cannot send emails
- Cannot modify labels
- Cannot delete emails

**Configuration**:
```bash
# Required for Gmail integration
GMAIL_API_ENABLED=true
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

# Monitoring
GMAIL_SCAN_INTERVAL=60
GMAIL_MAX_RESULTS=50
```

**Email Classification**:
| Category | Keywords |
|----------|----------|
| inquiry | question, inquiry, ask, wondering |
| request | request, please, could you |
| complaint | complaint, unhappy, disappointed |
| urgent | urgent, asap, immediately |
| meeting | meeting, schedule, calendar |
| invoice | invoice, payment, bill |
| support | support, help, technical |

---

### 3. Draft Generator (`draft_generator.py`)

**Purpose**: Claude-powered content generation

**Features**:
- Email response drafts
- LinkedIn post drafts
- WhatsApp message drafts
- Generic task drafts
- Alternative versions
- Brand voice compliance
- Link detection
- Hashtag generation

**Draft Types**:
```python
# Email Draft
{
    "draft_type": "email_response",
    "content": {
        "subject": "Re: Your Email",
        "body": "Dear...",
        "greeting": "Dear",
        "closing": "Best regards"
    }
}

# LinkedIn Post
{
    "draft_type": "linkedin_post",
    "content": {
        "content": "Post text...",
        "hashtags": ["AI", "Automation"]
    }
}

# WhatsApp Message
{
    "draft_type": "whatsapp_message",
    "content": {
        "message": "Hi! Quick question...",
        "emoji_suggestions": ["👍"]
    }
}
```

**Brand Voice Configuration**:
```bash
BRAND_TONE=professional
BRAND_STYLE=friendly
COMPANY_NAME=Your Company
EMAIL_SIGNATURE="Best regards,\nThe Team"
BRAND_AVOID_WORDS=guarantee,promise
BRAND_PREFERRED_PHRASES=value-driven,customer-focused
```

---

### 4. CEO Weekly Briefing Generator (`ceo_weekly_briefing.py`)

**Purpose**: Automated executive reporting

**Features**:
- Weekly data aggregation
- Claude-powered executive summary
- Multi-format output (MD, HTML, JSON)
- KPI tracking
- Task completion analytics
- Financial summaries
- Agent activity reports

**Briefing Sections**:
1. Executive Summary
2. Key Performance Indicators
3. Highlights This Week
4. Areas of Concern
5. Task Performance
6. Financial Summary
7. System Activity
8. Pending Approvals
9. Recommendations
10. Next Week's Priorities

**Output Formats**:
- **Markdown** (`.md`) - Human readable
- **HTML** (`.html`) - Email/web ready
- **JSON** (`.json`) - Programmatic access

**Schedule**:
```bash
# Configure briefing schedule
BRIEFING_DAY=sunday
BRIEFING_TIME=18:00
```

**KPIs Tracked**:
| KPI | Description |
|-----|-------------|
| tasks_completed | Total tasks finished |
| tasks_failed | Total tasks failed |
| success_rate | Success percentage |
| revenue | Total revenue |
| expenses | Total expenses |
| net_income | Revenue - Expenses |
| total_actions | All system actions |
| pending_approvals | Awaiting review |

---

## 🔄 WORKFLOW EXAMPLES

### Example 1: Email Response Workflow

```
1. Gmail Cloud Watcher scans inbox
   └─> Finds new email from client

2. Watcher parses email
   └─> Extracts: subject, body, sender, priority
   └─> Classifies: category=inquiry, priority=HIGH

3. Creates task in Cloud_Storage/inbox/
   └─> task_gmail_abc123.json

4. Cloud Orchestrator picks up task
   └─> Sends to Claude for analysis
   └─> Claude determines: requires_approval=True
       (contains "quote" keyword)

5. Draft Generator creates response
   └─> Professional email draft
   └─> Brand voice compliant
   └─> 3 alternative versions

6. Draft saved to Pending_Approval/
   └─> draft_email_abc123.json
   └─> Plan_abc123.md created

7. [SECURITY BOUNDARY]
   Cloud stops here. Local system takes over.

8. Human reviews draft (local interface)
   └─> Approves with minor edits

9. Local Orchestrator executes
   └─> Sends via MCP Server / Gmail API
   └─> Moves to Done/
```

### Example 2: Weekly Briefing Workflow

```
1. Scheduled time arrives (Sunday 18:00)

2. CEO Briefing Generator activates
   └─> Collects task data from Done/
   └─> Collects financial data from Accounting/
   └─> Collects activity data from Logs/

3. Claude generates executive summary
   └─> Analyzes trends
   └─> Identifies highlights/concerns
   └─> Creates recommendations

4. Briefing compiled in multiple formats
   └─> CEO_Briefings/20250226_180000.md
   └─> CEO_Briefings/20250226_180000.html
   └─> CEO_Briefings/20250226_180000.json

5. Notification sent (optional)
   └─> Email to CEO: "Weekly briefing ready"

6. CEO reviews briefing
   └─> Opens HTML version in browser
   └─> Reviews KPIs and recommendations
```

---

## 🧪 TESTING GUIDE

### Test Cloud Orchestrator

```bash
# Check status
python cloud_orchestrator.py --status

# Run in dry-run mode (10 seconds)
python cloud_orchestrator.py --dry-run --interval 10

# Test with sample task
echo '{"task_id": "test_001", "description": "Test task"}' > Cloud_Storage/inbox/test_001.json
python cloud_orchestrator.py --dry-run --once
```

### Test Gmail Watcher

```bash
# Check status
python gmail_cloud_watcher.py --status

# Single scan (dry-run)
python gmail_cloud_watcher.py --dry-run --once

# Continuous monitoring (dry-run)
python gmail_cloud_watcher.py --dry-run --interval 30
```

### Test Draft Generator

```bash
# Check status
python draft_generator.py --status

# Create draft request
cat > Draft_Requests/test_email.json << EOF
{
    "task_id": "draft_test_001",
    "draft_type": "email",
    "recipient_email": "test@example.com",
    "subject": "Test Email",
    "context": "Respond to inquiry about services"
}
EOF

# Generate draft
python draft_generator.py --dry-run --once
```

### Test CEO Briefing

```bash
# Check status
python ceo_weekly_briefing.py --status

# Generate briefing
python ceo_weekly_briefing.py --dry-run --once

# View generated briefing
cat CEO_Briefings/CEO_Briefing_*.md
```

---

## 📊 LOGGING

All components use dual logging (file + console):

### Log Files
```
Logs/
├── cloud_orchestrator.log
├── gmail_cloud_watcher.log
├── draft_generator.log
└── ceo_briefing.log
```

### Log Format
```
2025-02-26 10:30:00 - INFO - Task test_001 processed successfully
2025-02-26 10:30:01 - WARNING - Attempt 1/3 failed: API timeout. Retrying in 2.00s...
2025-02-26 10:30:03 - ERROR - Claude API call failed: 401 Unauthorized
```

### Cloud Logging (Production)
```python
# Enable CloudWatch (AWS)
CLOUD_LOGGING_ENABLED=true

# Enable Azure Monitor
# Configure in azure settings
```

---

## 🛡️ SECURITY BEST PRACTICES

### 1. Credential Management

```bash
# NEVER commit credentials
echo ".env.platinum" >> .gitignore
echo "tokens/" >> .gitignore
echo "Cloud_Storage/" >> .gitignore

# Use secrets manager in production
# AWS: Secrets Manager
# Azure: Key Vault
# GCP: Secret Manager
```

### 2. Network Security

```python
# Deploy in VPC/private network
# Use security groups to restrict access
# Enable TLS for all API calls
```

### 3. Data Encryption

```python
# Encrypt data at rest (S3/Blob)
# Encrypt data in transit (HTTPS/TLS)
# Use KMS for key management
```

### 4. Access Control

```python
# IAM roles with least privilege
# Service accounts for cloud components
# Regular credential rotation
```

---

## 🚀 DEPLOYMENT OPTIONS

### Option 1: Docker Container

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements_platinum.txt .
RUN pip install -r requirements_platinum.txt

COPY cloud_orchestrator.py .
COPY gmail_cloud_watcher.py .
COPY draft_generator.py .
COPY ceo_weekly_briefing.py .

CMD ["python", "cloud_orchestrator.py"]
```

### Option 2: AWS Lambda

```python
# lambda_function.py
from cloud_orchestrator import CloudOrchestrator

orchestrator = CloudOrchestrator()

def lambda_handler(event, context):
    asyncio.run(orchestrator.run())
```

### Option 3: Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloud-orchestrator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cloud-orchestrator
  template:
    spec:
      containers:
      - name: orchestrator
        image: your-registry/cloud-orchestrator:latest
        env:
        - name: CLAUDE_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: claude-api-key
```

---

## 📈 MONITORING

### Health Checks

```bash
# Check all components
curl http://localhost:8080/health

# Expected response
{
    "status": "healthy",
    "components": {
        "orchestrator": "ok",
        "gmail_watcher": "ok",
        "draft_generator": "ok",
        "briefing_generator": "ok"
    }
}
```

### Metrics to Track

| Metric | Alert Threshold |
|--------|-----------------|
| Task processing latency | > 60 seconds |
| API error rate | > 5% |
| Draft generation failures | > 10% |
| Pending approvals queue | > 50 items |

---

## 🔧 TROUBLESHOOTING

### Common Issues

**Problem**: Claude API returns 401
**Solution**: Check `CLAUDE_API_KEY` in .env.platinum

**Problem**: Gmail watcher not finding emails
**Solution**: Verify OAuth scopes include `gmail.readonly`

**Problem**: Drafts not appearing in Pending_Approval
**Solution**: Check `CLOUD_BASE_DIR` configuration

**Problem**: Briefing generation fails
**Solution**: Ensure data directories exist and have permissions

---

## 📞 SUPPORT

For issues or questions:
1. Check logs in `Logs/`
2. Verify configuration in `.env.platinum`
3. Run with `--dry-run` to test safely
4. Review security constraints above

---

**Platinum Tier Cloud Orchestrator - Secure Cloud Integration! ☁️**
