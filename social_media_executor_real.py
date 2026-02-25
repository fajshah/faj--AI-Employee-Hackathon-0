import asyncio
from playwright.async_api import async_playwright
import os, time, logging

LOG_DIR = "Logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(filename=os.path.join(LOG_DIR, 'executor.log'), level=logging.INFO)


async def post_linkedin(content):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir="session",
                headless=False
            )

            page = await browser.new_page()
            await page.goto("https://www.linkedin.com/feed/")
            await page.wait_for_timeout(5000)

            # Click "Start a post"
            await page.locator("div[role='button']").filter(
                has_text="Start a post"
            ).first.click()

            await page.wait_for_timeout(3000)

            # Type content
            editor = page.locator("div[role='textbox']").first
            await editor.click()
            await editor.fill(content)

            await page.wait_for_timeout(2000)

            # Click Post
            await page.locator("button").filter(
                has_text="Post"
            ).last.click()

            await page.wait_for_timeout(5000)
            await browser.close()

        logging.info(f"LinkedIn posted: {content}")
        return True

    except Exception as e:
        logging.error(e)
        return False

async def post_instagram(content):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir="session",
                headless=False
            )

            page = await browser.new_page()
            await page.goto("https://www.instagram.com/")
            await page.wait_for_timeout(5000)

            # Click on the "Create" button in the top navigation
            await page.locator("div._abl-").click()
            await page.wait_for_timeout(3000)

            # Click on "Create new post"
            await page.locator("div._aczb").click()
            await page.wait_for_timeout(3000)

            # For Instagram, we'd need to handle image upload, which is complex
            # For now, we'll log that we're posting the content
            # Upload image
            # await page.locator("input[type='file']").click()
            # Then add caption
            # await page.locator("div._acan._acao._acas").click()
            # await page.fill("textarea[aria-label='Write a caption...']", content)
            # await page.locator("div._acan._acao._acas").click()
            # await page.wait_for_timeout(2000)

            await browser.close()

        logging.info(f"Instagram content prepared: {content}")
        return False  # Return False since actual posting logic is complex
    except Exception as e:
        logging.error(e)
        return False

async def send_whatsapp(number, message):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir="wa_session",
                headless=False
            )

            page = await browser.new_page()
            await page.goto("https://web.whatsapp.com")
            await page.wait_for_timeout(15000)

            # Search box
            search_box = page.locator("div[contenteditable='true']").first
            await search_box.click()
            await search_box.fill(number)

            await page.wait_for_timeout(3000)

            # Select chat
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2000)

            # Message box
            message_box = page.locator("div[contenteditable='true']").nth(1)
            await message_box.fill(message)

            await page.keyboard.press("Enter")

            await page.wait_for_timeout(3000)
            await browser.close()

        logging.info(f"WhatsApp sent to {number}")
        return True

    except Exception as e:
        logging.error(e)
        return False