#!/usr/bin/env python3
"""
Runner script for the async automation system
"""
import asyncio
import os
from async_automation_system import AsyncAutomationSystem, create_task_file

async def run_async_system():
    print("Starting Async Automation System...")

    # Create system instance
    system = AsyncAutomationSystem()

    # Create some test tasks
    print("Creating test tasks...")

    # LinkedIn task
    await create_task_file(
        platform="linkedin",
        content="Hello LinkedIn! This is an automated post from our async system."
    )

    # WhatsApp task
    await create_task_file(
        platform="whatsapp",
        content="Test WhatsApp message",
        number="+919999999999",
        message="Hello from our async automation system!"
    )

    print("Test tasks created")
    print("Current folder status:")
    print(f"   Approved: {len(os.listdir('approved'))} files")
    print(f"   Done: {len(os.listdir('done'))} files")
    print(f"   Failed: {len(os.listdir('failed'))} files")

    print("Processing approved tasks...")

    # Process the approved folder
    await system.process_approved_folder()

    print("Final folder status:")
    print(f"   Approved: {len(os.listdir('approved'))} files")
    print(f"   Done: {len(os.listdir('done'))} files")
    print(f"   Failed: {len(os.listdir('failed'))} files")

    print("Async Automation System completed!")

    # Show recent log entries
    if os.path.exists("logs/executor.log"):
        print("\nRecent log entries:")
        with open("logs/executor.log", "r") as f:
            lines = f.readlines()
            for line in lines[-10:]:  # Show last 10 lines
                print(f"   {line.strip()}")

if __name__ == "__main__":
    asyncio.run(run_async_system())