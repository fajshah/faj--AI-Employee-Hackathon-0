# 📧 Send Email Button (Gmail/Outlook) - Complete Guide

Hindi/Urdu me complete guide ke Send Email Button feature ke liye jo AI-generated emails ko Gmail/Outlook me automatically open karta hai.

---

## 📋 Overview

Ye feature apko deta hai:

- **🤖 AI-Generated Emails**: Professional emails client info ke basis pe
- **🎯 One-Click Open**: Gmail, Outlook, ya Yahoo me draft automatically open
- **📝 Multiple Templates**: Outreach, Follow-up, Proposal, Meeting Request, etc.
- **⏰ Follow-up Scheduling**: Automatic follow-up emails schedule karein
- **💾 Draft Saving**: Saare drafts vault me save hote hain
- **📊 Statistics**: Email drafts ka complete tracking

---

## 🎨 Features

### 1. Email Types (7 Templates)

| Type | Use Case |
|------|----------|
| **Outreach** | Initial contact with potential client |
| **Follow-up** | Second touch after initial email |
| **Proposal** | Detailed proposal with pricing |
| **Meeting Request** | Schedule a call/meeting |
| **Thank You** | Post-meeting thank you |
| **Cold Outreach** | First contact with results |
| **Partnership** | Partnership opportunities |

### 2. Email Clients Supported

- ✅ **Gmail** (https://mail.google.com)
- ✅ **Outlook** (https://outlook.live.com)
- ✅ **Yahoo Mail** (https://mail.yahoo.com)

### 3. Follow-up Scheduling

- 2 days
- 3 days (default)
- 5 days
- 1 week

---

## 📁 File Structure

```
hackthone-0/
├── utils/
│   └── email_draft_generator.py      # Main email generator class
│
├── AI_Employee_Vault/
│   └── Email_Drafts/
│       ├── draft_*.json              # Individual drafts
│       └── follow_ups.json           # Scheduled follow-ups
│
└── dashboard/
    ├── app_enhanced.py               # Flask app with email routes
    └── templates/
        └── dashboard_enhanced.html   # Dashboard with email modal
```

---

## 🚀 Kaise Kaam Karta Hai

### Step 1: Client Card Se Button Click

Dashboard me har client card ke sath **📧 Email** button hota hai:

```
┌─────────────────────────────────────────┐
│ 👤 John Smith                           │
│ TechCorp Inc • Technology               │
│                                         │
│ [📧 Email] [💼 LinkedIn]                │
└─────────────────────────────────────────┘
```

### Step 2: Modal Open Hota Hai

Button click karne se modal open hota hai:

```
┌─────────────────────────────────────────────────┐
│  📧 Generate & Send Email                    ✕  │
├─────────────────────────────────────────────────┤
│  Client: John Smith at TechCorp Inc            │
│                                                 │
│  Email Type: [Initial Outreach ▼]              │
│  Email Client: [Gmail ▼]                       │
│                                                 │
│  Subject: Quick question about TechCorp's...   │
│                                                 │
│  Body:                                          │
│  Hi John,                                       │
│                                                 │
│  I hope this email finds you well...           │
│                                                 │
│  ☑ Schedule Follow-up                          │
│    Follow-up after: [3 days ▼]                 │
│                                                 │
│  [Cancel] [Copy] [Open in Email Client]        │
└─────────────────────────────────────────────────┘
```

### Step 3: AI Email Generate Karta Hai

```python
# Email generation logic
draft = email_generator.generate_draft(client, email_type)

# Subject aur body personalize hoti hai
subject = f"Quick question about {company}'s {need}"
body = """Hi {name},

I specialize in helping {industry} companies..."""
```

### Step 4: Email Client Me Open Hota Hai

```python
# Gmail URL generate karna
url = "https://mail.google.com/mail/?view=cm&fs=1"
url += f"&to={email}"
url += f"&su={urllib.parse.quote(subject)}"
url += f"&body={urllib.parse.quote(body)}"

# Browser me open karna
webbrowser.open(url)
```

### Step 5: Follow-up Schedule (Optional)

```python
# Follow-up schedule karna
if schedule_followup:
    follow_up_date = datetime.now() + timedelta(days=3)
    schedule = {
        'draft_id': draft_id,
        'scheduled_date': follow_up_date.isoformat(),
        'status': 'scheduled'
    }
```

---

## 💻 Implementation

### Email Generator Class

`utils/email_draft_generator.py`:

```python
class AIDraftGenerator:
    def __init__(self, vault_dir=None):
        self.vault_dir = Path(vault_dir) if vault_dir else \
                        Path(__file__).parent.parent / "AI_Employee_Vault"
        self.drafts_dir = self.vault_dir / "Email_Drafts"
        self.templates = self._load_templates()
    
    def generate_draft(self, client: Dict, email_type: str) -> Dict:
        """Generate email draft"""
        template = self.templates.get(email_type)
        
        # Personalize with client info
        subject = template['subject'].format(
            name=client.get('name', 'there'),
            company=client.get('company', 'your company'),
            industry=client.get('industry', 'business'),
            need=client.get('need', 'automation')
        )
        
        body = template['body'].format(...)
        
        return {
            'id': f"draft_{timestamp}",
            'to': client.get('email', ''),
            'subject': subject,
            'body': body,
            'email_type': email_type,
            'client_name': client.get('name'),
            'generated_at': datetime.now().isoformat()
        }
    
    def open_draft(self, draft: Dict, email_client: str) -> str:
        """Open email client with draft"""
        url_template = self.email_clients[email_client]
        
        # URL encode
        to = urllib.parse.quote(draft['to'])
        subject = urllib.parse.quote(draft['subject'])
        body = urllib.parse.quote(draft['body'])
        
        url = url_template.format(to=to, subject=subject, body=body)
        
        # Open in browser
        webbrowser.open(url)
        
        return url
```

### Flask API Routes

`dashboard/app_enhanced.py`:

```python
# Initialize email generator
email_generator = AIDraftGenerator()

@app.route('/api/email/generate', methods=['POST'])
def api_generate_draft():
    """Generate email draft"""
    data = request.json
    client = data.get('client', {})
    email_type = data.get('type', 'outreach')
    
    draft = email_generator.generate_draft(client, email_type)
    email_generator.save_draft(draft)
    
    return jsonify(draft)

@app.route('/api/email/generate-and-open', methods=['POST'])
def api_generate_and_open():
    """Generate and open in email client"""
    data = request.json
    client = data.get('client', {})
    email_type = data.get('type', 'outreach')
    email_client = data.get('email_client', 'gmail')
    
    draft = email_generator.generate_and_open(
        client, email_type, email_client
    )
    
    return jsonify(draft)

@app.route('/api/email/follow-up', methods=['POST'])
def api_schedule_follow_up():
    """Schedule follow-up email"""
    data = request.json
    draft_id = data.get('draft_id')
    days = data.get('days', 3)
    
    drafts = email_generator.get_all_drafts()
    draft = next(d for d in drafts if d['id'] == draft_id)
    
    schedule = email_generator.schedule_follow_up(draft, days)
    
    return jsonify(schedule)
```

### Dashboard JavaScript

`dashboard/templates/dashboard_enhanced.html`:

```javascript
function showEmailModal(client) {
    currentEmailData = client;
    
    // Show modal
    document.getElementById('email-modal').classList.add('active');
    
    // Generate preview
    generateEmailPreview();
}

async function generateEmailPreview() {
    const emailType = document.getElementById('email-type').value;
    
    const response = await fetch('/api/email/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            client: currentEmailData, 
            type: emailType 
        })
    });
    
    const data = await response.json();
    
    document.getElementById('email-subject').textContent = data.subject;
    document.getElementById('email-body').textContent = data.body;
}

async function openEmailInClient() {
    const emailClient = document.getElementById('email-client-select').value;
    const scheduleFollowup = document.getElementById('schedule-followup').checked;
    
    const response = await fetch('/api/email/generate-and-open', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            client: currentEmailData,
            type: 'outreach',
            email_client: emailClient
        })
    });
    
    // Schedule follow-up if checked
    if (scheduleFollowup) {
        await fetch('/api/email/follow-up', {
            method: 'POST',
            body: JSON.stringify({
                draft_id: data.id,
                days: 3
            })
        });
    }
    
    alert('✅ Email opened in ' + emailClient + '!');
}
```

---

## 🎯 Usage Examples

### Example 1: Dashboard Se Email Bhejna

1. Dashboard open karein: http://localhost:5050/dashboard
2. Clients section me jayein
3. Kisi client card par **📧 Email** button click karein
4. Email type select karein (Outreach, Follow-up, etc.)
5. Email client select karein (Gmail, Outlook, Yahoo)
6. Follow-up schedule karna ho to checkbox check karein
7. **Open in Email Client** button click karein
8. Email client me draft open hoga, edit karke send karein

### Example 2: Python Se Direct

```python
from utils.email_draft_generator import AIDraftGenerator

generator = AIDraftGenerator()

client = {
    'name': 'John Smith',
    'company': 'TechCorp',
    'industry': 'Technology',
    'email': 'john@techcorp.com'
}

# Generate and open
draft = generator.generate_and_open(
    client,
    email_type='outreach',
    email_client='gmail'
)

print(f"Draft ID: {draft['id']}")
print(f"Subject: {draft['subject']}")
```

### Example 3: API Se

```bash
# Generate draft
curl -X POST http://localhost:5050/api/email/generate \
  -H "Content-Type: application/json" \
  -d '{
    "client": {
      "name": "John Smith",
      "company": "TechCorp",
      "email": "john@techcorp.com"
    },
    "type": "outreach"
  }'

# Generate and open
curl -X POST http://localhost:5050/api/email/generate-and-open \
  -H "Content-Type: application/json" \
  -d '{
    "client": {"name": "John", "company": "TechCorp", "email": "john@test.com"},
    "type": "proposal",
    "email_client": "gmail"
  }'

# Schedule follow-up
curl -X POST http://localhost:5050/api/email/follow-up \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "draft_20260220192540_7977",
    "days": 3
  }'
```

---

## 📊 Email Templates

### 1. Outreach Template

```
Subject: Quick question about {company}'s {need}

Hi {name},

I hope this email finds you well. I came across your profile and 
was impressed by your work at {company}.

I specialize in helping {industry} companies like yours streamline 
operations through AI automation. Based on my research, I believe 
we could help {company}:

• Reduce manual workload by 40-60%
• Save 20+ hours per week on repetitive tasks
• Improve operational efficiency significantly

Would you be open to a quick 15-minute call this week to explore 
how we might add value to {company}?

Best regards,
{sender_name}
AI Employee Team

P.S. We're currently offering a free automation audit for select companies.
```

### 2. Follow-up Template

```
Subject: Following up - {company} automation opportunity

Hi {name},

I wanted to follow up on my previous email regarding automation 
opportunities at {company}.

I understand you're busy, so I'll keep this brief. We've recently 
helped several {industry} companies achieve remarkable results:

• 3x faster processing times
• 50% reduction in operational costs
• Significant improvement in team productivity

If now isn't a good time, I'd be happy to reconnect next month.

Best regards,
{sender_name}
```

### 3. Proposal Template

```
Subject: Proposal for {company} - AI Automation Solution

Hi {name},

Thank you for your interest in exploring AI automation solutions 
for {company}.

Based on our discussion, here's a tailored proposal:

**Scope of Work:**
1. Process audit and analysis
2. Custom AI workflow design
3. Implementation and integration
4. Training and support

**Timeline:** 4-6 weeks
**Investment:** Starting at $5,000

**Expected ROI:**
• Break-even within 2-3 months
• 200-300% ROI in first year

Would you like to schedule a call to discuss the details?

Best regards,
{sender_name}
```

---

## 📁 Draft Storage

### Saved Drafts Location

`AI_Employee_Vault/Email_Drafts/draft_YYYYMMDDHHMMSS_XXXX.json`

### Draft File Structure

```json
{
  "id": "draft_20260220192540_7977",
  "to": "john@techcorp.com",
  "subject": "Quick question about TechCorp Inc's automation",
  "body": "Hi John,\n\nI hope this email finds you well...",
  "email_type": "outreach",
  "client_name": "John Smith",
  "client_company": "TechCorp Inc",
  "generated_at": "2026-02-20T19:25:40",
  "sender_name": "AI Employee Team",
  "status": "draft",
  "sent": false,
  "opened_in_client": true,
  "email_client": "gmail"
}
```

### Follow-up Schedule File

`AI_Employee_Vault/Email_Drafts/follow_ups.json`:

```json
[
  {
    "id": "followup_draft_20260220192540_7977",
    "original_draft_id": "draft_20260220192540_7977",
    "follow_up_type": "follow_up",
    "scheduled_date": "2026-02-23T19:25:40",
    "client_name": "John Smith",
    "client_company": "TechCorp Inc",
    "status": "scheduled",
    "created_at": "2026-02-20T19:25:40"
  }
]
```

---

## 🔧 Testing

### Test Email Generator

```bash
cd D:\hackthone-0
python utils/email_draft_generator.py
```

### Test Dashboard

```bash
python dashboard/app_enhanced.py
```

Visit: http://localhost:5050/dashboard

### Test API Endpoints

```bash
# Get all drafts
curl http://localhost:5050/api/email/drafts

# Get specific draft
curl http://localhost:5050/api/email/draft/draft_20260220192540_7977

# Get statistics
curl http://localhost:5050/api/email/stats
```

---

## 🎨 Customization

### Add New Email Template

`email_draft_generator.py` me `self.templates` dictionary me add karein:

```python
self.templates['custom'] = {
    'subject': 'Custom subject for {company}',
    'body': """Hi {name},

Your custom email body here...

Best regards,
{sender_name}"""
}
```

### Add New Email Client

```python
self.email_clients['custom_client'] = \
    'https://email.client.com/compose?to={to}&subject={subject}&body={body}'
```

### Change Follow-up Intervals

Dashboard HTML me change karein:

```html
<select class="filter-select" id="followup-days">
    <option value="1">1 day</option>
    <option value="2">2 days</option>
    <option value="3" selected>3 days</option>
</select>
```

---

## 🛠️ Troubleshooting

### Email Client Nahi Khul Raha

**Problem**: Button click karne se email client nahi khulta

**Solution**:
1. Check popup blocker disabled hai
2. Browser console me errors check karein
3. Direct URL test karein:
   ```
   https://mail.google.com/mail/?view=cm&fs=1&to=test@test.com
   ```

### Draft Save Nahi Ho Raha

**Problem**: Drafts save nahi ho rahe

**Solution**:
1. Check `AI_Employee_Vault/Email_Drafts/` directory exists
2. Directory permissions check karein
3. Flask console me errors check karein

### Email Preview Show Nahi Ho Rahi

**Problem**: Modal me email preview nahi aa rahi

**Solution**:
1. Browser console me network errors check karein
2. API endpoint test karein:
   ```bash
   curl -X POST http://localhost:5050/api/email/generate ...
   ```
3. Flask server running hai check karein

---

## ✅ Quick Start

1. **Start Dashboard**:
   ```bash
   python dashboard/app_enhanced.py
   ```

2. **Open Browser**:
   ```
   http://localhost:5050/dashboard
   ```

3. **Go to Clients Section**:
   - Clients list me kisi client par click karein

4. **Click Email Button**:
   - 📧 Email button par click karein

5. **Select Options**:
   - Email type select karein
   - Email client select karein
   - Follow-up schedule karein (optional)

6. **Open in Email Client**:
   - "Open in Email Client" button click karein
   - Gmail/Outlook me draft open hoga

7. **Edit and Send**:
   - Email edit karein (agar zaroorat ho)
   - Send button click karein

---

## 📝 Summary

- ✅ **7 Email Templates**: Outreach, Follow-up, Proposal, etc.
- ✅ **3 Email Clients**: Gmail, Outlook, Yahoo
- ✅ **AI Personalization**: Client info se auto-personalize
- ✅ **One-Click Open**: Direct email client me
- ✅ **Follow-up Scheduling**: Automatic reminders
- ✅ **Draft Saving**: Saare drafts vault me save
- ✅ **Statistics Tracking**: Complete analytics
- ✅ **API Integration**: RESTful API endpoints

---

**📧 Send Email Button - Complete Implementation Ready!**
