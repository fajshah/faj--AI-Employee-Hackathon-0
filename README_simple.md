# Simple AI Social Media Manager

A simplified social media automation system that's easy to use and manage.

## Features

- Simple command-line interface
- Support for LinkedIn, Facebook, Instagram, WhatsApp, and Gmail
- YAML-based post format with metadata
- Manual approval workflow
- Post processing with success/failure handling

## Usage

### Create posts:

```bash
# Create a LinkedIn post
python -c "from simple_social_manager import create_post; create_post('linkedin', 'Your content here')"

# Create a Facebook post
python -c "from simple_social_manager import create_post; create_post('facebook', 'Your content here')"

# Create a WhatsApp message
python -c "from simple_social_manager import create_post; create_post('whatsapp', 'Your message', number='+923XXXXXXXXX')"

# Create a Gmail
python -c "from simple_social_manager import create_post; create_post('gmail', 'Message body', to='email@example.com', subject='Subject')"
```

### Process posts:

```bash
# Process a specific post
python -c "from simple_social_manager import process_post; process_post('posts/POST_linkedin_XXXX.md')"
```

### Interactive mode:

```bash
python simple_social_manager.py
```

Then use commands:
- `create [platform] [content]` - Create a new post
- `approve [filename]` - Approve a post for processing
- `list` - List pending posts
- `exit` - Exit the program

## How it works

1. Posts are created in the `posts/` directory with YAML metadata
2. Each post is manually approved by running the process command
3. Successful posts are moved to `completed/` directory
4. Failed posts are moved to `failed/` directory

## Directory Structure

```
├── posts/          # Pending posts
├── completed/      # Successfully processed posts
├── failed/         # Failed posts
├── simple_social_manager.py   # Main manager
└── simple_executor.py         # Social media executor
```