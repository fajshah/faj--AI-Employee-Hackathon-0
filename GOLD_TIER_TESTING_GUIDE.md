# 🏆 GOLD TIER TESTING GUIDE
## Complete Testing Instructions for Gold Tier Features

---

## 📋 PREREQUISITES

Before testing, ensure you have:

1. **Installed Gold Tier Dependencies:**
   ```bash
   pip install -r requirements_gold.txt
   ```

2. **Configured Environment Variables:**
   - Copy `.env.gold` to `.env` or update values
   - Add your real API credentials

3. **Completed OAuth Authentication:**
   ```bash
   python authenticate_gmail.py
   ```

4. **Directory Structure Created:**
   ```
   hackthone-0/
   ├── Logs/
   ├── Needs_Action/
   ├── Approved/
   ├── Pending_Approval/
   ├── Done/
   ├── Error/
   └── tokens/
       └── gmail_token.json
   ```

---

## 🧪 TEST 1: MCP SERVER HEALTH CHECK

### Purpose
Verify the Gold Tier MCP Server is running and all services are connected.

### Steps

1. **Start the MCP Server:**
   ```bash
   python MCP_Server_Gold.py
   ```

2. **Wait for initialization** (should see "Gold Tier MCP Server starting on localhost:5001")

3. **Test Health Endpoint:**
   ```bash
   curl http://localhost:5001/health
   ```

### Expected Response
```json
{
  "status": "healthy",
  "tier": "gold",
  "timestamp": "2026-02-16T...",
  "services": {
    "gmail": "connected",
    "linkedin": "connected",
    "whatsapp": "connected"
  }
}
```

### Verification
- ✅ Server responds with status "healthy"
- ✅ Tier shows "gold"
- ✅ Services show connection status

---

## 📧 TEST 2: GMAIL EMAIL SENDING

### Purpose
Verify real emails are sent via Gmail API.

### Steps

1. **Ensure MCP Server is running** (from Test 1)

2. **Copy Example Task:**
   ```bash
   copy example_tasks\gmail_email_task.json Needs_Action\
   ```

3. **Send Test Email via API:**
   ```bash
   curl -X POST http://localhost:5001/api/email/send ^
     -H "Content-Type: application/json" ^
     -d "{\"task_id\": \"test_email_001\", \"to\": \"your-test-email@gmail.com\", \"subject\": \"Gold Tier Test\", \"body\": \"This is a test email from Gold Tier MCP Server\"}"
   ```

4. **Check your email inbox** for the test email

### Expected Response
```json
{
  "status": "success",
  "task_id": "test_email_001",
  "message": "Email sent to your-test-email@gmail.com",
  "result": {
    "message_id": "...",
    "status": "sent",
    "method": "gmail_api"
  }
}
```

### Verification
- ✅ API returns success status
- ✅ Email received in inbox
- ✅ Log file created in `Logs/mcp_action_test_email_*.json`

### Troubleshooting
- If Gmail API fails, check OAuth token in `tokens/gmail_token.json`
- Re-run `python authenticate_gmail.py` if needed
- Check Gmail API is enabled in Google Cloud Console

---

## 💼 TEST 3: LINKEDIN POSTING

### Purpose
Verify real posts are published to LinkedIn.

### Steps

1. **Ensure MCP Server is running**

2. **Post to LinkedIn via API:**
   ```bash
   curl -X POST http://localhost:5001/api/social/post ^
     -H "Content-Type: application/json" ^
     -d "{\"task_id\": \"test_linkedin_001\", \"content\": \"Testing Gold Tier LinkedIn integration! #GoldTier #AI\", \"hashtags\": [\"GoldTier\", \"AI\", \"Testing\"]}"
   ```

3. **Check your LinkedIn profile** for the new post

### Expected Response
```json
{
  "status": "success",
  "task_id": "test_linkedin_001",
  "message": "Post published to LinkedIn",
  "result": {
    "post_id": "...",
    "status": "published",
    "visibility": "PUBLIC"
  }
}
```

### Verification
- ✅ API returns success status
- ✅ Post appears on LinkedIn profile
- ✅ Log file created in `Logs/linkedin_action_*.json`

### Troubleshooting
- Verify `LINKEDIN_ACCESS_TOKEN` in `.env.gold`
- Check LinkedIn API permissions in developer portal
- Token may need to be refreshed periodically

---

## 💬 TEST 4: WHATSAPP MESSAGING

### Purpose
Verify real WhatsApp messages are sent via Business API.

### Steps

1. **Ensure MCP Server is running**

2. **Send WhatsApp Message via API:**
   ```bash
   curl -X POST http://localhost:5001/api/whatsapp/send ^
     -H "Content-Type: application/json" ^
     -d "{\"task_id\": \"test_whatsapp_001\", \"to\": \"+1234567890\", \"message\": \"Gold Tier WhatsApp test message!\", \"type\": \"text\"}"
   ```

3. **Check the recipient phone** for the WhatsApp message

### Expected Response
```json
{
  "status": "success",
  "task_id": "test_whatsapp_001",
  "message": "WhatsApp message sent to +1234567890",
  "result": {
    "message_id": "...",
    "status": "sent",
    "recipient": "+1234567890"
  }
}
```

### Verification
- ✅ API returns success status
- ✅ Message received on WhatsApp
- ✅ Log file created in `Logs/mcp_action_test_whatsapp_*.json`

### Troubleshooting
- Verify WhatsApp Business API credentials in `.env.gold`
- Phone number must be registered in WhatsApp Business Manager
- Message templates may be required for certain message types

---

## 🔗 TEST 5: LINK OPENING

### Purpose
Verify URLs are detected and opened in browser.

### Steps

1. **Ensure MCP Server is running**

2. **Test Link Opening:**
   ```bash
   curl -X POST http://localhost:5001/api/link/open ^
     -H "Content-Type: application/json" ^
     -d "{\"task_id\": \"test_link_001\", \"url\": \"https://www.google.com\", \"action\": \"open\"}"
   ```

3. **Check if default browser opens** the URL

### Expected Response
```json
{
  "status": "success",
  "task_id": "test_link_001",
  "result": {
    "url": "https://www.google.com",
    "action": "open",
    "status": "opened_in_browser"
  }
}
```

### Verification
- ✅ API returns success status
- ✅ Browser opens the URL
- ✅ Log file created

---

## 🔄 TEST 6: END-TO-END WORKFLOW

### Purpose
Verify complete workflow: Watcher → Task → Approval → Execution → Done

### Steps

1. **Start All Components:**
   ```bash
   # Terminal 1: MCP Server
   python MCP_Server_Gold.py

   # Terminal 2: Orchestrator
   python Orchestrator_Gold.py

   # Terminal 3: Gmail Watcher (optional)
   python Gmail_Watcher_Gold.py
   ```

2. **Create Test Task in Needs_Action:**
   - Copy `example_tasks/gmail_email_task.json` to `Needs_Action/`

3. **Watch the Workflow:**
   - Orchestrator picks up the task
   - Creates plan in `Plans/`
   - If sensitive → moves to `Pending_Approval/`
   - If approved → executes via MCP
   - Moves to `Done/`

4. **Check Logs:**
   - `Logs/orchestrator_action_*.json`
   - `Logs/mcp_action_*.json`

### Verification
- ✅ Task moves through all stages
- ✅ Plan.md created in `Plans/`
- ✅ Real action executed (email sent)
- ✅ Task ends in `Done/`
- ✅ All actions logged

---

## 📊 TEST 7: APPROVAL WORKFLOW

### Purpose
Verify sensitive tasks require approval before execution.

### Steps

1. **Create Sensitive Task:**
   ```json
   {
     "task_id": "test_sensitive_001",
     "task_type": "email",
     "action_type": "send_email",
     "sensitive": true,
     "recipient_email": "finance@company.com",
     "subject": "Payment Authorization",
     "message": "Please authorize payment for invoice #12345",
     "created_at": "2026-02-16T10:00:00"
   }
   ```

2. **Save to Needs_Action/**

3. **Verify Task Moves to Pending_Approval/**

4. **Manually Approve:**
   - Move task from `Pending_Approval/` to `Approved/`

5. **Verify Execution:**
   - Orchestrator processes approved task
   - Email is sent
   - Task moves to `Done/`

### Verification
- ✅ Sensitive task detected
- ✅ Task moved to `Pending_Approval/`
- ✅ Task waits for approval
- ✅ After approval, task executes
- ✅ Task moves to `Done/`

---

## ✅ VERIFICATION CHECKLIST

Use this checklist to confirm Gold Tier is fully operational:

### Environment Setup
- [ ] `.env.gold` configured with real credentials
- [ ] Gold Tier dependencies installed
- [ ] Gmail OAuth completed (`tokens/gmail_token.json` exists)

### MCP Server
- [ ] Server starts without errors
- [ ] Health endpoint returns "healthy"
- [ ] All services show "connected"

### Email Functionality
- [ ] Test email sent successfully
- [ ] Email received in inbox
- [ ] Action logged in `Logs/`

### LinkedIn Functionality
- [ ] Test post published
- [ ] Post visible on LinkedIn
- [ ] Action logged in `Logs/`

### WhatsApp Functionality
- [ ] Test message sent
- [ ] Message received on phone
- [ ] Action logged in `Logs/`

### Link Opening
- [ ] URL opens in browser
- [ ] Action logged in `Logs/`

### Workflow Integration
- [ ] Tasks flow: Needs_Action → Plans → (Approval) → Done
- [ ] Orchestrator processes tasks
- [ ] Watchers integrate properly

### Error Handling
- [ ] Invalid credentials show clear error
- [ ] Failed actions logged with error details
- [ ] Failed tasks move to `Error/`

---

## 🐛 COMMON ISSUES & SOLUTIONS

### Issue: Gmail API "Token Expired"
**Solution:** Re-run `python authenticate_gmail.py`

### Issue: LinkedIn "Invalid Access Token"
**Solution:** Refresh token in LinkedIn Developer Portal

### Issue: WhatsApp "Phone Number Not Found"
**Solution:** Verify phone number is registered in WhatsApp Business Manager

### Issue: MCP Server Won't Start
**Solution:** Check port 5001 isn't in use, verify Flask is installed

### Issue: Tasks Not Processing
**Solution:** Ensure Orchestrator is running, check file permissions

---

## 📝 TEST RESULTS TEMPLATE

```
Test Date: _______________
Tester: _______________

| Test | Status | Notes |
|------|--------|-------|
| MCP Server Health | ☐ Pass ☐ Fail | |
| Gmail Sending | ☐ Pass ☐ Fail | |
| LinkedIn Posting | ☐ Pass ☐ Fail | |
| WhatsApp Messaging | ☐ Pass ☐ Fail | |
| Link Opening | ☐ Pass ☐ Fail | |
| End-to-End Workflow | ☐ Pass ☐ Fail | |
| Approval Workflow | ☐ Pass ☐ Fail | |

Overall Gold Tier Status: ☐ Operational ☐ Issues Found

Issues to Address:
1.
2.
3.
```

---

## 🎯 NEXT STEPS AFTER TESTING

1. **Deploy to Production:**
   - Update `.env.gold` with production credentials
   - Set up as Windows Service or systemd service
   - Configure log rotation

2. **Monitor Performance:**
   - Set up log monitoring
   - Configure alerts for failures
   - Track API rate limits

3. **Scale Operations:**
   - Add more watcher instances
   - Implement load balancing
   - Set up database for task storage

---

**Gold Tier Testing Complete! 🎉**
