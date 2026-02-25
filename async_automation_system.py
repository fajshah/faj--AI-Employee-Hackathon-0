import asyncio
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Setup logging
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/screenshots", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/executor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AsyncAutomationSystem:
    def __init__(self):
        self.linkedin_session_dir = "linkedin_session"
        self.wa_session_dir = "wa_session"
        self.approved_dir = "approved"
        self.done_dir = "done"
        self.failed_dir = "failed"

        # Create required directories
        os.makedirs(self.approved_dir, exist_ok=True)
        os.makedirs(self.done_dir, exist_ok=True)
        os.makedirs(self.failed_dir, exist_ok=True)
        os.makedirs(self.linkedin_session_dir, exist_ok=True)
        os.makedirs(self.wa_session_dir, exist_ok=True)

    async def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """
        Generic retry function with exponential backoff
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} for {func.__name__}")
                result = await func()
                logger.info(f"Success on attempt {attempt + 1} for {func.__name__}")
                return result
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:  # Don't wait after the last attempt
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                                 f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {max_retries} attempts failed for {func.__name__}: {str(e)}")

        # If all retries failed, raise the last exception
        raise last_exception

    async def post_linkedin(self, content: str) -> bool:
        """
        Async LinkedIn posting function with retry logic
        """
        async def _post_linkedin_impl():
            browser = None
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch_persistent_context(
                        user_data_dir=self.linkedin_session_dir,
                        headless=False
                    )

                    page = await browser.new_page()
                    await page.goto("https://www.linkedin.com/feed/", wait_until="networkidle")
                    await page.wait_for_timeout(5000)

                    # Wait for and click "Start a post" button
                    try:
                        start_post_button = page.locator("div[role='button']").filter(has_text="Start a post").first
                        await start_post_button.wait_for(state="visible", timeout=60000)
                        await start_post_button.click()
                        logger.info("Clicked 'Start a post' button")
                    except PlaywrightTimeoutError:
                        logger.error("Could not find 'Start a post' button")
                        # Try alternative selector
                        alternative_button = page.locator("button[aria-label*='post' i]").first
                        await alternative_button.wait_for(state="visible", timeout=30000)
                        await alternative_button.click()
                        logger.info("Clicked alternative 'Start a post' button")

                    await page.wait_for_timeout(3000)

                    # Fill the textbox
                    textbox = page.locator("div[role='textbox']").first
                    await textbox.wait_for(state="visible", timeout=30000)
                    await textbox.click()
                    await textbox.fill("")
                    await textbox.fill(content)
                    logger.info("Filled post content")

                    await page.wait_for_timeout(2000)

                    # Add random delay before posting
                    import random
                    random_delay = random.uniform(2, 5)
                    await asyncio.sleep(random_delay)

                    # Click Post button
                    post_button = page.locator("button").filter(has_text="Post").last
                    await post_button.wait_for(state="visible", timeout=30000)
                    await post_button.click()

                    await page.wait_for_timeout(5000)

                    # Take screenshot on success
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"logs/screenshots/linkedin_success_{timestamp}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"Screenshot saved: {screenshot_path}")

                    return True

            except Exception as e:
                logger.error(f"LinkedIn posting failed: {str(e)}")
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
                raise
            finally:
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass

        return await self._retry_with_backoff(_post_linkedin_impl)

    async def post_whatsapp(self, number: str, message: str) -> bool:
        """
        Async WhatsApp posting function with retry logic
        """
        async def _post_whatsapp_impl():
            browser = None
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch_persistent_context(
                        user_data_dir=self.wa_session_dir,
                        headless=False
                    )

                    page = await browser.new_page()
                    await page.goto("https://web.whatsapp.com", wait_until="networkidle")

                    # Wait for login QR to disappear (indicates login complete)
                    logger.info("Waiting for WhatsApp Web to load (max 15 seconds)...")
                    await page.wait_for_timeout(15000)

                    # Search for contact
                    search_box = page.locator("div[contenteditable='true']").first
                    await search_box.wait_for(state="visible", timeout=30000)
                    await search_box.click()
                    await search_box.fill(number)

                    await page.wait_for_timeout(3000)

                    # Select the chat by pressing Enter
                    await page.keyboard.press("Enter")

                    await page.wait_for_timeout(2000)

                    # Find message box and send message
                    message_box = page.locator("div[contenteditable='true']").nth(1)
                    await message_box.wait_for(state="visible", timeout=30000)
                    await message_box.fill(message)

                    await page.keyboard.press("Enter")

                    await page.wait_for_timeout(3000)

                    # Take screenshot on success
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"logs/screenshots/whatsapp_success_{timestamp}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    logger.info(f"Screenshot saved: {screenshot_path}")

                    return True

            except Exception as e:
                logger.error(f"WhatsApp posting failed: {str(e)}")
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
                raise
            finally:
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass

        return await self._retry_with_backoff(_post_whatsapp_impl)

    async def execute_task(self, task_data: Dict[str, Any]) -> bool:
        """
        Execute a single task based on its platform
        """
        try:
            platform = task_data.get('platform', '').lower()

            if platform == 'linkedin':
                content = task_data.get('content', '')
                return await self.post_linkedin(content)
            elif platform == 'whatsapp':
                number = task_data.get('number', '')
                message = task_data.get('message', '')
                return await self.post_whatsapp(number, message)
            else:
                logger.error(f"Unsupported platform: {platform}")
                return False

        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return False

    async def process_approved_folder(self):
        """
        Process all JSON files in the approved folder
        """
        try:
            approved_files = [f for f in os.listdir(self.approved_dir) if f.endswith('.json')]

            if not approved_files:
                logger.info("No files to process in approved folder")
                return

            logger.info(f"Found {len(approved_files)} files to process")

            for filename in approved_files:
                file_path = os.path.join(self.approved_dir, filename)

                try:
                    # Read task data
                    with open(file_path, 'r', encoding='utf-8') as f:
                        task_data = json.load(f)

                    logger.info(f"Processing task from {filename}")

                    # Execute the task
                    success = await self.execute_task(task_data)

                    # Move file based on result
                    if success:
                        destination = os.path.join(self.done_dir, filename)
                        shutil.move(file_path, destination)
                        logger.info(f"Task {filename} completed successfully, moved to done")
                    else:
                        destination = os.path.join(self.failed_dir, filename)
                        shutil.move(file_path, destination)
                        logger.error(f"Task {filename} failed, moved to failed")

                except Exception as e:
                    logger.error(f"Error processing {filename}: {str(e)}")
                    # Move to failed even if there was an error reading the file
                    destination = os.path.join(self.failed_dir, filename)
                    source_path = os.path.join(self.approved_dir, filename)
                    if os.path.exists(source_path):
                        shutil.move(source_path, destination)
                        logger.info(f"Failed to process {filename}, moved to failed")

        except Exception as e:
            logger.error(f"Error processing approved folder: {str(e)}")

    async def monitor_approved_folder(self, interval: int = 5):
        """
        Continuously monitor the approved folder for new tasks
        """
        logger.info("Starting approved folder monitor...")

        while True:
            try:
                await self.process_approved_folder()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in folder monitor: {str(e)}")
                await asyncio.sleep(interval)

    async def run_single_task(self, platform: str, **kwargs):
        """
        Run a single task directly (for testing purposes)
        """
        if platform.lower() == 'linkedin':
            content = kwargs.get('content', '')
            return await self.post_linkedin(content)
        elif platform.lower() == 'whatsapp':
            number = kwargs.get('number', '')
            message = kwargs.get('message', '')
            return await self.post_whatsapp(number, message)
        else:
            logger.error(f"Unsupported platform: {platform}")
            return False

# Example usage functions
async def create_task_file(platform: str, content: str, number: str = None, message: str = None):
    """
    Helper function to create a task file in the approved folder
    """
    os.makedirs("approved", exist_ok=True)

    task_data = {
        "platform": platform,
        "content": content,
        "number": number,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

    filename = f"task_{platform}_{int(time.time())}.json"
    filepath = os.path.join("approved", filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(task_data, f, indent=2)

    logger.info(f"Created task file: {filepath}")
    return filepath

# Example usage
async def main():
    """
    Example main function demonstrating usage
    """
    system = AsyncAutomationSystem()

    # Example: Create a LinkedIn task
    await create_task_file("linkedin", "This is an automated LinkedIn post!")

    # Example: Create a WhatsApp task
    await create_task_file("whatsapp", "Hello from AI!", "+919999999999", "Hello from AI!")

    # Process the approved folder once
    await system.process_approved_folder()

    # Or run continuously
    # await system.monitor_approved_folder()

if __name__ == "__main__":
    # For testing purposes, run a single execution
    asyncio.run(main())