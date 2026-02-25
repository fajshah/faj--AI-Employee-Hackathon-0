import asyncio
import random
from playwright.async_api import async_playwright

async def post():
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
        print("Clicked 'Start a post'")

        await page.wait_for_timeout(3000)

        # Try multiple selector options for the text editor
        try:
            # Option 1: Try the main editor div
            editor = page.locator("div[role='textbox'][aria-label*='post' i], div[role='textbox'][placeholder*='post' i]").first
            await editor.wait_for(state="visible", timeout=5000)
            await editor.click()
            await editor.fill("🚀 AI Employee is now fully autonomous! Gold Tier automation running successfully. #AI #Automation #BuildInPublic")
            print("Post content filled successfully")
        except Exception as e:
            print(f"First selector failed: {e}")
            # Option 2: Try a more generic approach
            editor = page.locator("div.ql-editor[role='textbox'], div[contenteditable='true']").first
            await editor.wait_for(state="visible", timeout=5000)
            await editor.click()
            await editor.fill("🚀 AI Employee is now fully autonomous! Gold Tier automation running successfully. #AI #Automation #BuildInPublic")
            print("Post content filled with fallback selector")

        await asyncio.sleep(random.randint(2,5))

        # Click Post button
        post_btn = page.locator("button").filter(has_text="Post").last
        await post_btn.click()
        print("Post button clicked")

        await page.wait_for_timeout(5000)
        await browser.close()
        print("Done!")

asyncio.run(post())
