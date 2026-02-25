import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="wa_session",
            headless=False
        )
        page = await browser.new_page()
        await page.goto("https://web.whatsapp.com")
        print("Scan QR, wait until chats load, then press ENTER...")
        input()
        await browser.close()

asyncio.run(main())