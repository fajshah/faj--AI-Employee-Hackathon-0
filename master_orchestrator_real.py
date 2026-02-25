import os, time, shutil
import asyncio
from social_media_executor_real import post_linkedin, post_instagram, send_whatsapp

APPROVED_DIR = "Approved"
DONE_DIR = "Done"
LOGS = "Logs"

os.makedirs(DONE_DIR, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)

def monitor_folder():
    print("Master Orchestrator running...")
    while True:
        files = os.listdir(APPROVED_DIR)
        for file in files:
            filepath = os.path.join(APPROVED_DIR, file)
            content = open(filepath, encoding="utf-8").read()

            success = False
            if "linkedin" in file.lower():
                success = asyncio.run(post_linkedin(content))
            elif "instagram" in file.lower():
                success = asyncio.run(post_instagram(content))
            elif "whatsapp" in file.lower():
                number, msg = content.split("|")
                success = asyncio.run(send_whatsapp(number.strip(), msg.strip()))

            if success:
                shutil.move(filepath, os.path.join(DONE_DIR, file))
                print(f"✅ Completed: {file}")
            else:
                shutil.move(filepath, os.path.join(LOGS, "failed_" + file))
                print(f"❌ Failed: {file}")

        time.sleep(5)  # check every 5 seconds

if __name__ == "__main__":
    monitor_folder()