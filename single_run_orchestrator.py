import os, time, shutil
from social_media_executor_real import post_linkedin, post_instagram, send_whatsapp

APPROVED_DIR = "Approved"
DONE_DIR = "Done"
LOGS = "Logs"

os.makedirs(DONE_DIR, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)

def single_monitor():
    print("Single run - Master Orchestrator...")
    files = os.listdir(APPROVED_DIR)
    if not files:
        print("No files in Approved directory.")
        return

    for file in files:
        filepath = os.path.join(APPROVED_DIR, file)
        content = open(filepath, encoding="utf-8").read()

        success = False
        if "linkedin" in file.lower():
            print(f"Attempting LinkedIn post for: {file}")
            success = post_linkedin(content)
        elif "instagram" in file.lower():
            print(f"Attempting Instagram post for: {file}")
            success = post_instagram(content)
        elif "whatsapp" in file.lower():
            number, msg = content.split("|")
            print(f"Attempting WhatsApp message for: {file}")
            success = send_whatsapp(number.strip(), msg.strip())

        if success:
            shutil.move(filepath, os.path.join(DONE_DIR, file))
            print(f"[SUCCESS] Completed: {file}")
        else:
            shutil.move(filepath, os.path.join(LOGS, "failed_" + file))
            print(f"[FAILED] Failed: {file}")

if __name__ == "__main__":
    single_monitor()