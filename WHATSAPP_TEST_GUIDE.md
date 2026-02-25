# WhatsApp Message Testing Guide

## System Overview
Aapka WhatsApp automation system 3 main components par kaam karta hai:
1. **Message Creation** (`trigger_posts_real.py`) - WhatsApp messages create karta hai
2. **Approval System** - Messages ko approve karne ke liye manual step
3. **Orchestration** (`master_orchestrator_real.py`) - Messages ko WhatsApp par send karta hai

## Pre-requisites
- Python installed
- Playwright installed (for browser automation)
- System properly set up with all folders
- WhatsApp Web access (stable internet connection)

## Step-by-Step Testing Guide

### Step 1: Message Creation
Command run karein:
```
python -c "from trigger_posts_real import create_post; create_post('whatsapp', '+91_your_number_here', 'Your test message here')"
```

Yeh command kya karega:
- Ek naya message file create karega `Pending_Approval` folder mein
- Filename format: `POST_whatsapp_YYYYMMDD_HHMMSS.md`
- File content format: `+91_your_number_here|Your test message here`

### Step 2: Manual Approval
Command run karein:
```
# Sabse naye WhatsApp message file ka name dekhne ke liye:
ls -la Pending_Approval/ | grep whatsapp | sort | tail -5

# Phir us file ko approve karein:
mv Pending_Approval/POST_whatsapp_*.md Approved/
```

Yeh command kya karega:
- Message `Pending_Approval` folder se `Approved` folder mein move hoga
- Ab orchestrator yeh message process kar sakta hai

### Step 3: Message Execution
Command run karein:
```
python single_run_orchestrator.py
```

Yeh command kya karega:
- `Approved` folder mein check karega
- WhatsApp message process karega
- Success/Failure ke hisab se file ko `Done` ya `Logs` folder mein move karega

### Step 4: Result Check
Check karein:
```
# Successfully processed messages:
ls -la Done/

# Failed messages:
ls -la Logs/ | grep failed

# Executor logs (errors dekhne ke liye):
cat Logs/executor.log
```

## Testing Examples

### Basic Test
1. Create test message:
   ```
   python -c "from trigger_posts_real import create_post; create_post('whatsapp', '+919876543210', 'Testing WhatsApp automation')"
   ```

2. Approve it:
   ```
   mv Pending_Approval/POST_whatsapp_*.md Approved/
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

### Multi-line Message Test
```
python -c "from trigger_posts_real import create_post; create_post('whatsapp', '+919876543210', 'First line\\nSecond line\\nThird line')"
```

### Emoji Test
```
python -c "from trigger_posts_real import create_post; create_post('whatsapp', '+919876543210', 'Testing with emoji: 😊🚀')"
```

### Long Message Test
```
python -c "from trigger_posts_real import create_post; create_post('whatsapp', '+919876543210', 'This is a longer message to test the WhatsApp automation system. It includes multiple sentences to see how the system handles longer content in the automated messaging workflow.')"
```

## Common Issues & Solutions

### Issue: WhatsApp message fail ho raha hai
**Solution**:
- Check `Logs/executor.log` file
- Possible reasons: Authentication, UI changes, or Playwright session issue
- Ensure WhatsApp Web account logged in browser session

### Issue: Number not found
**Solution**:
- Number must be in international format (+91XXXXXXXXXX)
- Contact must be in your WhatsApp contacts (for direct search)
- Try with saved contact first

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
ls -la Pending_Approval/ | grep whatsapp | wc -l
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
- Failed messages are preserved in Logs folder for debugging
- No data loss occurs during normal operation
- Only send messages to contacts who have consented to receive automated messages

## Next Steps
1. Start with simple test messages to yourself
2. Verify workflow with basic messages
3. Check logs for any errors
4. Gradually move to sending messages to others
5. Test with different message types and lengths