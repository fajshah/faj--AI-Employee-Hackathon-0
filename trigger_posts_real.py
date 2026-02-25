import os, time

PENDING = "Pending_Approval"
os.makedirs(PENDING, exist_ok=True)

def create_post(platform, content, number=None):
    """
    Create a post draft.
    - platform: linkedin / instagram / whatsapp
    - content: text content
    - number: only for whatsapp (string)
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    if platform.lower() == "whatsapp" and number:
        filename = f"POST_whatsapp_{timestamp}.md"
        with open(os.path.join(PENDING, filename), "w", encoding="utf-8") as f:
            f.write(f"{number}|{content}")
    else:
        filename = f"POST_{platform}_{timestamp}.md"
        with open(os.path.join(PENDING, filename), "w", encoding="utf-8") as f:
            f.write(content)

    print(f"Created post draft: {filename}")