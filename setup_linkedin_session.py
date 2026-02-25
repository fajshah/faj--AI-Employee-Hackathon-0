import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="linkedin_session",
            headless=False
        )
        page = await browser.new_page()
        await page.goto("https://www.linkedin.com")
        print("Login manually, then press ENTER in terminal...")
        input()
        await browser.close()

asyncio.run(main())