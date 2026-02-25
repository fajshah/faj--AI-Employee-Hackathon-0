# LinkedIn Post Testing Guide

## System Overview
Aapka LinkedIn automation system 3 main components par kaam karta hai:
1. **Post Creation** (`trigger_posts_real.py`) - LinkedIn posts create karta hai
2. **Approval System** - Posts ko approve karne ke liye manual step
3. **Orchestration** (`master_orchestrator_real.py`) - Posts ko LinkedIn par share karta hai

## Pre-requisites
- Python installed
- Playwright installed (for browser automation)
- System properly set up with all folders
- **IMPORTANT**: LinkedIn account must be logged in manually in the browser session
- **NEW**: Async Playwright implementation with improved stability

## Step-by-Step Testing Guide

### Step 1: LinkedIn Browser Session Setup
**IMPORTANT**: Pehele se LinkedIn par logged in hona chahiye persistent session ke liye.

Manual step:
1. Go to `session` folder in your project directory
2. Open Chrome browser manually with user data dir pointing to this session folder
3. Log in to your LinkedIn account manually in this browser
4. Ensure you can post manually in this browser

### Step 2: WhatsApp Browser Session Setup (NEW)
**NEW**: WhatsApp Web ke liye separate session folder created hai: `wa_session`

Manual step:
1. Go to `wa_session` folder in your project directory
2. Open Chrome browser manually with user data dir pointing to this wa_session folder
3. Log in to your WhatsApp Web account manually in this browser
4. Ensure WhatsApp Web properly loads in this browser

### Step 2: Post Creation
Command run karein:
```
python -c "from trigger_posts_real import create_post; create_post('linkedin', 'Your test message here')"
```

Yeh command kya karega:
- Ek naya post file create karega `Pending_Approval` folder mein
- Filename format: `POST_linkedin_YYYYMMDD_HHMMSS.md`
- Post content: Aapke diya gaya message

### Step 3: Manual Approval
Command run karein:
```
# Sabse naye LinkedIn post file ka name dekhne ke liye:
ls -la Pending_Approval/ | grep linkedin | sort | tail -5

# Phir us file ko approve karein:
mv Pending_Approval/POST_linkedin_*.md Approved/
```

Yeh command kya karega:
- Post `Pending_Approval` folder se `Approved` folder mein move hoga
- Ab orchestrator yeh post process kar sakta hai

### Step 4: Post Execution
Command run karein:
```
python single_run_orchestrator.py
```

Yeh command kya karega:
- `Approved` folder mein check karega
- LinkedIn post process karega (async version)
- Success/Failure ke hisab se file ko `Done` ya `Logs` folder mein move karega

### Step 5: Result Check
Check karein:
```
# Successfully processed posts:
ls -la Done/

# Failed posts:
ls -la Logs/ | grep failed

# Executor logs (errors dekhne ke liye):
cat Logs/executor.log
```

## Testing Examples

### Basic Test
1. Create test post:
   ```
   python -c "from trigger_posts_real import create_post; create_post('linkedin', 'Testing LinkedIn automation')"
   ```

2. Approve it:
   ```
   mv Pending_Approval/POST_linkedin_*.md Approved/
   ```

3. Process it:
   ```
   python single_run_orchestrator.py
   ```

4. Check result:
   ```
   ls -la Approved/  # Should be empty
   ls -la Logs/      # Check for failed files
   ```

### Multi-line Test
```
python -c "from trigger_posts_real import create_post; create_post('linkedin', 'First line\\nSecond line\\nThird line')"
```

### Emoji Test
```
python -c "from trigger_posts_real import create_post; create_post('linkedin', 'Testing with emoji: 😊🚀')"
```

## Common Issues & Solutions

### Issue: LinkedIn post fail ho raha hai (Authentication Required)
**Solution**:
- Check `Logs/executor.log` file
- Ensure your LinkedIn account is logged in the persistent session
- Open browser in session folder and manually log in to LinkedIn
- Verify you can manually post in that browser

### Issue: "Start a post" button not found
**Solution**:
- LinkedIn UI might have changed
- Check if the button text is same or different
- Verify in the session browser

### Issue: File names showing garbled characters
**Solution**:
- This is Windows console encoding issue
- System still processes files correctly internally

### Issue: Orchestrator not detecting files
**Solution**:
- Check if file is in `Approved` folder
- Ensure folder names are correct

## Troubleshooting Commands

Check current status:
```
echo "=== Folder Contents ==="
echo "Pending_Approval:"
ls -la Pending_Approval/ | grep linkedin | wc -l
echo "Approved:"
ls -la Approved/ | wc -l
echo "Done:"
ls -la Done/ | wc -l
echo "Logs:"
ls -la Logs/ | grep failed | wc -l
```

## Expected Results

### Successful Execution:
- Input: File in `Approved` folder
- Output: File moves to `Done` folder
- Log: Success message in console

### Failed Execution:
- Input: File in `Approved` folder
- Output: File moves to `Logs` folder with "failed_" prefix
- Log: Error details in `Logs/executor.log`

## Safety Notes
- System automatically handles file management
- Failed posts are preserved in Logs folder for debugging
- No data loss occurs during normal operation
- Ensure you have LinkedIn account access permissions

## Next Steps
1. First complete browser session setup with login
2. Start with simple test messages
3. Verify workflow with basic posts
4. Check logs for any errors
5. Gradually move to complex posts