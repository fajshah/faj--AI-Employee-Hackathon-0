import os
import time
import shutil
from datetime import datetime

BASE = r"D:\hackthone-0"

INBOX = os.path.join(BASE, "Inbox")
NEEDS_ACTION = os.path.join(BASE, "Needs_Action")
LOG_FILE = os.path.join(BASE, "Logs", "activity.md")

os.makedirs(INBOX, exist_ok=True)
os.makedirs(NEEDS_ACTION, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

print("Started watching folder:", INBOX)
print("Tasks will be created in:", NEEDS_ACTION)

seen_files = set()

while True:
    files = os.listdir(INBOX)
    for file in files:
        src = os.path.join(INBOX, file)
        dst = os.path.join(NEEDS_ACTION, file)

        if file not in seen_files and os.path.isfile(src):
            shutil.move(src, dst)

            with open(LOG_FILE, "a") as log:
                log.write(f"\n{datetime.now()} - Moved {file} to Needs_Action")

            print(f"Moved: {file}")
            seen_files.add(file)

    time.sleep(2)
