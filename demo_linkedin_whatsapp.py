import os
import time
import shutil
import json
from pathlib import Path
from playwright.async_api import async_playwright
import asyncio

# Folder paths
BASE_DIR = Path(__file__).parent
APPROVED = BASE_DIR / "Approved"
DONE = BASE_DIR / "completed"
LOGS = BASE_DIR / "Logs"
LINKEDIN_DIR = BASE_DIR / "LinkedIn_Posts"
WHATSAPP_DIR = BASE_DIR / "WhatsApp_Tasks"

print("🚀 Starting LinkedIn + WhatsApp Demo Orchestrator...")

async def post_to_linkedin(content):
    """Post content to LinkedIn"""
    print("📱 Posting to LinkedIn...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="linkedin_session",
            headless=False
        )

        page = await browser.new_page()
        await page.goto("https://www.linkedin.com/feed/")
        await page.wait_for_timeout(5000)

        # Click "Start a post" button
        start = page.locator("div[role='button']").filter(has_text="Start a post")
        await start.first.click()
        print("   ✓ Clicked 'Start a post'")

        await page.wait_for_timeout(3000)

        # Fill the post content
        editor = page.locator("div[contenteditable='true']").first
        await editor.wait_for(state="visible", timeout=10000)
        await editor.click()
        await editor.fill(content)
        print("   ✓ Filled post content")

        await asyncio.sleep(2)

        # Click Post button
        post_btn = page.locator("button").filter(has_text="Post").last
        await post_btn.click()
        print("   ✓ Clicked Post button")

        await page.wait_for_timeout(5000)
        await browser.close()
        print("   ✓ LinkedIn post completed!\n")

def send_whatsapp(number, message):
    """Send WhatsApp message"""
    print("📱 Sending WhatsApp message...")
    print(f"   To: {number}")
    print(f"   Message: {message}")
    # Note: Actual WhatsApp automation would go here
    # For demo, we're logging the action
    print("   ✓ WhatsApp message sent (demo mode)\n")

def run_demo():
    """Main demo loop"""
    while True:
        # List approved tasks
        tasks = list(APPROVED.glob("*.json"))
        if not tasks:
            print("✅ No approved tasks found. Waiting for files...")
            time.sleep(5)
            continue

        for task_file in tasks:
            try:
                print(f"\n📌 Processing task: {task_file.name}")
                with open(task_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                platform = data.get("platform")
                
                if platform == "linkedin":
                    content = data.get("content", data.get("message", ""))
                    asyncio.run(post_to_linkedin(content))
                    
                elif platform == "whatsapp":
                    number = data.get("number", "")
                    message = data.get("message", "")
                    send_whatsapp(number, message)
                else:
                    print(f"   ⚠️ Unknown platform: {platform}")
                
                # Move file to done folder after success
                DONE.mkdir(exist_ok=True)
                shutil.move(str(task_file), DONE / task_file.name)
                print(f"✅ Task completed and moved to done: {task_file.name}\n")

            except Exception as e:
                print(f"❌ Task failed: {task_file.name}")
                print(f"   Error: {e}\n")
                # Move to logs
                LOGS.mkdir(exist_ok=True)
                (LOGS / f"failed_{task_file.name}").write_text(str(e))

        # Pause briefly before next iteration
        time.sleep(3)

if __name__ == "__main__":
    run_demo()
