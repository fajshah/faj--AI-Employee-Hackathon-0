import os
import time
import yaml
import re
from datetime import datetime
from pathlib import Path

# Import the real executor
from simple_executor import execute_task

def extract_yaml_metadata(content):
    """Extract YAML metadata from markdown content"""
    yaml_pattern = r'^---\n(.*?)\n---\n(.*)'
    match = re.match(yaml_pattern, content, re.DOTALL)

    if match:
        yaml_str = match.group(1)
        content_after_yaml = match.group(2)

        try:
            metadata = yaml.safe_load(yaml_str)
            return metadata, content_after_yaml
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            return None, content
    else:
        return {"platform": "unknown", "status": "unknown"}, content

def create_post(platform, content, **kwargs):
    """Create a post with YAML metadata"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"POST_{platform}_{timestamp}.md"

    # Prepare metadata
    metadata = {
        'platform': platform,
        'status': 'pending',
        'created': datetime.now().isoformat()
    }

    # Add any additional metadata
    for key, value in kwargs.items():
        metadata[key] = value

    # Create the content
    yaml_header = "---\n" + "\n".join([f"{k}: {v}" for k, v in metadata.items()]) + "\n---\n"
    full_content = yaml_header + content

    # Write to file
    filepath = Path("posts") / filename
    filepath.parent.mkdir(exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_content)

    print(f"Created post: {filepath.name}")
    return filepath

def process_post(filepath):
    """Process a single post"""
    # Convert to Path object if it's a string
    filepath = Path(filepath) if isinstance(filepath, str) else filepath
    print(f"Processing: {filepath.name}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    metadata, actual_content = extract_yaml_metadata(content)

    if metadata and 'platform' in metadata:
        platform = metadata['platform']
        print(f"Posting to {platform}: {actual_content[:50]}...")

        # Use the real executor
        result = execute_task(platform, actual_content, metadata)

        if result:
            # Move to completed
            completed_dir = Path("completed")
            completed_dir.mkdir(exist_ok=True)
            new_path = completed_dir / filepath.name
            filepath.rename(new_path)

            print(f"Moved to completed: {new_path.name}")
            return True
        else:
            # Move to failed
            failed_dir = Path("failed")
            failed_dir.mkdir(exist_ok=True)
            new_path = failed_dir / filepath.name
            filepath.rename(new_path)

            print(f"Moved to failed: {new_path.name}")
            return False
    else:
        print(f"❌ Error: No platform specified in {filepath.name}")
        return False

def main():
    print("Simple AI Social Media Manager")
    print("Commands:")
    print("  create [platform] [content] - Create a new post")
    print("  approve [filename] - Approve a post for processing")
    print("  list - List pending posts")
    print("  exit - Exit the program")
    print()

    # Create directories
    Path("posts").mkdir(exist_ok=True)
    Path("completed").mkdir(exist_ok=True)

    while True:
        command = input("Enter command: ").strip()

        if command.startswith("create "):
            parts = command[7:].split(" ", 1)
            if len(parts) >= 2:
                platform, content = parts[0], parts[1]

                # Handle special cases for whatsapp and gmail
                if platform == "whatsapp" and len(content.split(" ", 1)) >= 2:
                    number, msg = content.split(" ", 1)
                    create_post(platform, msg, number=number)
                elif platform == "gmail" and len(content.split(" ", 2)) >= 3:
                    to, subject, body = content.split(" ", 2)
                    create_post(platform, body, to=to, subject=subject)
                else:
                    create_post(platform, content)
            else:
                print("Usage: create [platform] [content]")

        elif command.startswith("approve "):
            filename = command[8:]
            filepath = Path("posts") / filename

            if filepath.exists():
                result = process_post(filepath)
                if result:
                    print("✅ Post processed successfully!")
                else:
                    print("❌ Error processing post")
            else:
                print(f"File not found: {filepath}")

        elif command == "list":
            posts = list(Path("posts").glob("*.md"))
            if posts:
                print("Pending posts:")
                for p in posts:
                    print(f"  - {p.name}")
            else:
                print("No pending posts")

        elif command == "exit":
            break

        else:
            print("Unknown command")

    print("Goodbye!")

if __name__ == "__main__":
    main()