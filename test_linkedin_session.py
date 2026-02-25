import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="linkedin_session",
            headless=False
        )
        page = await browser.new_page()
        await page.goto("https://www.linkedin.com/feed/")
        await page.wait_for_timeout(5000)

asyncio.run(test())
