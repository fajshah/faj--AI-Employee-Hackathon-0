import time
import random

def execute_task(platform, content, metadata=None):
    """
    Simplified social media executor
    In a real implementation, this would connect to actual social media APIs
    """
    print(f"Attempting to post to {platform}...")

    # Simulate different platforms
    if platform.lower() == "linkedin":
        print(f"[LINKEDIN] Posting to LinkedIn: {content[:50]}...")
    elif platform.lower() == "facebook":
        print(f"[FACEBOOK] Posting to Facebook: {content[:50]}...")
    elif platform.lower() == "instagram":
        print(f"[INSTAGRAM] Posting to Instagram: {content[:50]}...")
    elif platform.lower() == "whatsapp":
        number = metadata.get('number', 'Unknown') if metadata else 'Unknown'
        print(f"[WHATSAPP] Sending WhatsApp to {number}: {content[:50]}...")
    elif platform.lower() == "gmail":
        to = metadata.get('to', 'Unknown') if metadata else 'Unknown'
        subject = metadata.get('subject', 'No Subject') if metadata else 'No Subject'
        print(f"[GMAIL] Sending email to {to} - Subject: {subject}")
    else:
        print(f"[UNKNOWN] Unknown platform: {platform}")
        return False

    # Simulate processing time
    time.sleep(1)

    # Simulate success/failure (90% success rate)
    success = random.random() < 0.9

    if success:
        print(f"[SUCCESS] Successfully posted to {platform}")
        return True
    else:
        print(f"[ERROR] Failed to post to {platform}")
        return False

# For testing purposes
if __name__ == "__main__":
    print("Testing executor...")
    result = execute_task("linkedin", "Hello LinkedIn!", {})
    print(f"Result: {result}")