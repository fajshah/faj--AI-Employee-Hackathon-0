"""
Platinum Tier Gmail Cloud Watcher
==================================
Async Gmail monitoring service for cloud deployment

Security Constraints:
- READS emails only (no sending from cloud)
- Creates task drafts for cloud orchestrator
- NEVER executes email sending
- All sending happens locally after approval

Features:
- Async Gmail API integration
- Intelligent email classification
- Attachment handling
- Thread tracking
- Comprehensive logging
- Retry logic with exponential backoff
- DRY_RUN mode for testing
"""

import os
import sys
import json
import asyncio
import logging
import time
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.platinum')

# Configure logging
class CloudWatcherLogger:
    """Dual logging: File + Cloud"""
    
    def __init__(self, name: str, log_file: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if log_file:
            Path(log_file).parent.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
    
    def get_logger(self) -> logging.Logger:
        return self.logger


logger_wrapper = CloudWatcherLogger(
    name='gmail_cloud_watcher',
    log_file='Logs/gmail_cloud_watcher.log'
)
logger = logger_wrapper.get_logger()


@dataclass
class EmailTask:
    """Email task data structure"""
    task_id: str
    source: str
    email_id: str
    thread_id: str
    from_address: str
    to_address: str
    subject: str
    body_plain: str
    body_html: Optional[str]
    received_at: str
    has_attachments: bool
    attachment_info: List[Dict[str, Any]]
    labels: List[str]
    priority: str
    requires_response: bool
    sentiment: str
    category: str
    extracted_entities: Dict[str, Any]
    raw_message: Optional[str] = None


class RetryConfig:
    """Retry configuration"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class AsyncRetryExecutor:
    """Async retry executor"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    async def execute(
        self,
        func,
        *args,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """Execute with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (self.config.exponential_base ** attempt),
                        self.config.max_delay
                    )
                    
                    if self.config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All attempts failed. Last error: {str(e)}")
        
        raise last_exception


class GmailCloudWatcher:
    """
    Platinum Tier Gmail Cloud Watcher
    
    Responsibilities:
    - Monitor Gmail inbox asynchronously
    - Parse and classify emails
    - Extract action items
    - Create task drafts for cloud orchestrator
    - NEVER send emails from cloud
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-Gmail"
        
        # Configuration
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.gmail_api_enabled = os.getenv('GMAIL_API_ENABLED', 'true').lower() == 'true'
        
        # Gmail API configuration
        self.gmail_client_id = os.getenv('GMAIL_CLIENT_ID')
        self.gmail_client_secret = os.getenv('GMAIL_CLIENT_SECRET')
        self.gmail_refresh_token = os.getenv('GMAIL_REFRESH_TOKEN')
        self.gmail_token_file = os.getenv('GMAIL_TOKEN_FILE', 'tokens/gmail_token.json')
        self.gmail_scopes = ['https://www.googleapis.com/auth/gmail.readonly']
        
        # Directories
        self.base_dir = Path(os.getenv('CLOUD_BASE_DIR', '.'))
        self.cloud_storage_dir = self.base_dir / 'Cloud_Storage'
        self.inbox_dir = self.cloud_storage_dir / 'inbox'
        self.archive_dir = self.cloud_storage_dir / 'gmail_processed'
        self.logs_dir = self.base_dir / 'Logs'
        
        self._create_directories()
        
        # Retry executor
        self.retry_executor = AsyncRetryExecutor(RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        ))
        
        # Monitoring configuration
        self.scan_interval = int(os.getenv('GMAIL_SCAN_INTERVAL', '60'))
        self.max_results = int(os.getenv('GMAIL_MAX_RESULTS', '50'))
        self.label_ids = os.getenv('GMAIL_LABEL_IDS', 'INBOX').split(',')
        
        # State tracking
        self.processed_message_ids = set()
        self.last_sync_time = datetime.now()
        
        # Statistics
        self.stats = {
            'emails_scanned': 0,
            'tasks_created': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # OAuth token
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Gmail Cloud Watcher initialized v{self.version}")
        logger.info(f"DRY_RUN mode: {self.dry_run}")
        logger.info(f"Gmail API enabled: {self.gmail_api_enabled}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [self.inbox_dir, self.archive_dir, self.logs_dir]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory verified: {dir_path}")
    
    async def _init_session(self):
        """Initialize HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.debug("HTTP session initialized")
    
    async def _close_session(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("HTTP session closed")
    
    async def _refresh_access_token(self) -> str:
        """Refresh OAuth access token"""
        if not self.gmail_client_id or not self.gmail_client_secret or not self.gmail_refresh_token:
            logger.warning("Gmail OAuth credentials not configured")
            return None
        
        token_url = 'https://oauth2.googleapis.com/token'
        payload = {
            'client_id': self.gmail_client_id,
            'client_secret': self.gmail_client_secret,
            'refresh_token': self.gmail_refresh_token,
            'grant_type': 'refresh_token'
        }
        
        async def _refresh():
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Token refresh failed: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result
        
        try:
            result = await self.retry_executor.execute(_refresh)
            self.access_token = result['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=result.get('expires_in', 3600))
            logger.info("Access token refreshed successfully")
            return self.access_token
        
        except Exception as e:
            logger.error(f"Failed to refresh access token: {str(e)}")
            return None
    
    async def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return True
        
        return await self._refresh_access_token() is not None
    
    async def _list_messages(self, query: str = None) -> List[Dict[str, str]]:
        """List Gmail messages"""
        if not self.gmail_api_enabled:
            logger.warning("Gmail API disabled - using simulation mode")
            return await self._simulate_messages()
        
        await self._ensure_valid_token()
        
        if not self.access_token:
            logger.error("No valid access token available")
            return []
        
        base_url = 'https://www.googleapis.com/gmail/v1/users/me/messages'
        params = {
            'maxResults': self.max_results,
            'labelIds': self.label_ids
        }
        
        if query:
            params['q'] = query
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        async def _fetch():
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Gmail API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result.get('messages', [])
        
        try:
            messages = await self.retry_executor.execute(_fetch)
            logger.info(f"Fetched {len(messages)} messages from Gmail")
            return messages
        
        except Exception as e:
            logger.error(f"Failed to list messages: {str(e)}")
            return []
    
    async def _simulate_messages(self) -> List[Dict[str, str]]:
        """Simulate Gmail messages for testing"""
        # In dry-run mode, create simulated emails
        return [
            {'id': f'sim_{int(time.time())}_1', 'threadId': 'thread_1'},
            {'id': f'sim_{int(time.time())}_2', 'threadId': 'thread_2'}
        ]
    
    async def _get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get full message details"""
        if message_id.startswith('sim_'):
            return await self._simulate_message_details(message_id)
        
        await self._ensure_valid_token()
        
        if not self.access_token:
            return None
        
        url = f'https://www.googleapis.com/gmail/v1/users/me/messages/{message_id}'
        params = {'format': 'full'}
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        async def _fetch():
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Gmail API error: {response.status} - {error_text}")
                    
                    return await response.json()
        
        try:
            message = await self.retry_executor.execute(_fetch)
            return message
        
        except Exception as e:
            logger.error(f"Failed to get message {message_id}: {str(e)}")
            return None
    
    async def _simulate_message_details(self, message_id: str) -> Dict[str, Any]:
        """Simulate message details for testing"""
        return {
            'id': message_id,
            'threadId': f'thread_{message_id}',
            'labelIds': ['INBOX', 'UNREAD'],
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'To', 'value': 'admin@company.com'},
                    {'name': 'Subject', 'value': f'Test Email {message_id}'}
                ],
                'body': {
                    'data': base64.urlsafe_b64encode(
                        b'This is a simulated test email body for testing purposes.'
                    ).decode('utf-8')
                }
            },
            'internalDate': str(int(time.time() * 1000))
        }
    
    def _parse_message(self, message_data: Dict[str, Any]) -> EmailTask:
        """Parse Gmail message into EmailTask"""
        payload = message_data.get('payload', {})
        headers = {h['name']: h['value'] for h in payload.get('headers', [])}
        
        # Extract body
        body_plain = ''
        body_html = None
        
        if 'body' in payload:
            body_data = payload['body'].get('data', '')
            if body_data:
                try:
                    body_plain = base64.urlsafe_b64decode(body_data).decode('utf-8')
                except:
                    body_plain = ''
        
        # Check for multipart
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    part_data = part.get('body', {}).get('data', '')
                    if part_data:
                        try:
                            body_plain = base64.urlsafe_b64decode(part_data).decode('utf-8')
                        except:
                            pass
                elif part.get('mimeType') == 'text/html':
                    part_data = part.get('body', {}).get('data', '')
                    if part_data:
                        try:
                            body_html = base64.urlsafe_b64decode(part_data).decode('utf-8')
                        except:
                            pass
        
        # Check for attachments
        has_attachments = False
        attachment_info = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    has_attachments = True
                    attachment_info.append({
                        'filename': part.get('filename'),
                        'mimeType': part.get('mimeType'),
                        'size': part.get('body', {}).get('length', 0)
                    })
        
        # Generate task ID
        message_id = message_data.get('id', 'unknown')
        task_id = f"gmail_{message_id[:8]}_{int(time.time())}"
        
        # Parse received date
        received_timestamp = int(message_data.get('internalDate', 0)) / 1000
        received_at = datetime.fromtimestamp(received_timestamp).isoformat() if received_timestamp else datetime.now().isoformat()
        
        # Classify email
        subject = headers.get('Subject', '')
        from_address = headers.get('From', '')
        to_address = headers.get('To', '')
        
        category, priority, requires_response, sentiment, entities = self._classify_email(
            subject=subject,
            body=body_plain,
            from_address=from_address
        )
        
        task = EmailTask(
            task_id=task_id,
            source='gmail',
            email_id=message_id,
            thread_id=message_data.get('threadId', ''),
            from_address=from_address,
            to_address=to_address,
            subject=subject,
            body_plain=body_plain,
            body_html=body_html,
            received_at=received_at,
            has_attachments=has_attachments,
            attachment_info=attachment_info,
            labels=message_data.get('labelIds', []),
            priority=priority,
            requires_response=requires_response,
            sentiment=sentiment,
            category=category,
            extracted_entities=entities
        )
        
        return task
    
    def _classify_email(
        self,
        subject: str,
        body: str,
        from_address: str
    ) -> Tuple[str, str, bool, str, Dict[str, Any]]:
        """
        Classify email and extract metadata
        
        Returns: (category, priority, requires_response, sentiment, entities)
        """
        content = f"{subject} {body}".lower()
        
        # Category detection
        category = 'general'
        category_keywords = {
            'inquiry': ['question', 'inquiry', 'ask', 'wondering', 'information'],
            'request': ['request', 'please', 'could you', 'would you'],
            'complaint': ['complaint', 'unhappy', 'disappointed', 'issue', 'problem'],
            'urgent': ['urgent', 'asap', 'immediately', 'emergency'],
            'meeting': ['meeting', 'schedule', 'calendar', 'appointment'],
            'invoice': ['invoice', 'payment', 'bill', 'receipt'],
            'support': ['support', 'help', 'technical', 'bug', 'error']
        }
        
        for cat, keywords in category_keywords.items():
            if any(kw in content for kw in keywords):
                category = cat
                break
        
        # Priority detection
        priority = 'MEDIUM'
        if any(kw in content for kw in ['urgent', 'asap', 'emergency', 'immediately']):
            priority = 'URGENT'
        elif any(kw in content for kw in ['important', 'priority', 'soon']):
            priority = 'HIGH'
        elif any(kw in content for kw in ['when convenient', 'no rush', 'whenever']):
            priority = 'LOW'
        
        # Response requirement
        requires_response = False
        response_indicators = [
            '?', 'please reply', 'let me know', 'get back to me',
            'your response', 'waiting for', 'expecting'
        ]
        if any(ind in content.lower() for ind in response_indicators):
            requires_response = True
        
        # Sentiment analysis (basic)
        sentiment = 'neutral'
        positive_words = ['great', 'excellent', 'thank', 'appreciate', 'good', 'happy', 'pleased']
        negative_words = ['unhappy', 'disappointed', 'frustrated', 'angry', 'poor', 'bad', 'issue']
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        
        # Entity extraction
        entities = {
            'sender_domain': from_address.split('@')[-1] if '@' in from_address else '',
            'has_deadline': any(kw in content for kw in ['deadline', 'by tomorrow', 'by friday', 'due date']),
            'mentions_money': any(kw in content for kw in ['$', 'usd', 'eur', 'payment', 'invoice', 'price']),
            'mentions_dates': self._detect_dates(content)
        }
        
        return category, priority, requires_response, sentiment, entities
    
    def _detect_dates(self, content: str) -> List[str]:
        """Detect date mentions in content"""
        import re
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b(today|tomorrow|yesterday|next week|this week|this month)\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dates.extend(matches)
        
        return dates[:5]  # Limit to 5 dates
    
    async def _create_task_file(self, email_task: EmailTask) -> str:
        """Create task file in cloud storage inbox"""
        filename = f"{email_task.task_id}.json"
        filepath = self.inbox_dir / filename
        
        task_data = {
            'task_id': email_task.task_id,
            'title': f"Email: {email_task.subject[:100]}",
            'description': email_task.body_plain[:500],
            'source': 'gmail',
            'source_email_id': email_task.email_id,
            'source_thread_id': email_task.thread_id,
            'from': email_task.from_address,
            'to': email_task.to_address,
            'subject': email_task.subject,
            'received_at': email_task.received_at,
            'category': email_task.category,
            'priority': email_task.priority,
            'sentiment': email_task.sentiment,
            'requires_response': email_task.requires_response,
            'has_attachments': email_task.has_attachments,
            'attachment_info': email_task.attachment_info,
            'labels': email_task.labels,
            'extracted_entities': email_task.extracted_entities,
            'suggested_actions': self._suggest_actions(email_task),
            'metadata': {
                'watcher': f"Gmail Cloud Watcher v{self.version}",
                'processed_at': datetime.now().isoformat()
            }
        }
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would create task file: {filepath}")
            logger.info(f"[DRY_RUN] Task data preview: {json.dumps(task_data, indent=2)[:500]}...")
            return str(filepath)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Task file created: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Failed to create task file: {str(e)}")
            raise
    
    def _suggest_actions(self, email_task: EmailTask) -> List[Dict[str, Any]]:
        """Suggest actions based on email content"""
        actions = []
        
        if email_task.requires_response:
            actions.append({
                'action_type': 'draft_response',
                'priority': email_task.priority,
                'description': 'Draft email response'
            })
        
        if email_task.category == 'meeting':
            actions.append({
                'action_type': 'schedule_meeting',
                'priority': 'HIGH',
                'description': 'Schedule meeting from email'
            })
        
        if email_task.category == 'invoice':
            actions.append({
                'action_type': 'process_invoice',
                'priority': 'HIGH',
                'description': 'Process invoice/payment request',
                'requires_approval': True
            })
        
        if email_task.has_attachments:
            actions.append({
                'action_type': 'process_attachments',
                'priority': 'MEDIUM',
                'description': f'Process {len(email_task.attachment_info)} attachment(s)'
            })
        
        if not actions:
            actions.append({
                'action_type': 'review_and_respond',
                'priority': email_task.priority,
                'description': 'Review email and respond if necessary'
            })
        
        return actions
    
    async def _process_single_message(self, message_data: Dict[str, Any]) -> bool:
        """Process a single Gmail message"""
        message_id = message_data.get('id', 'unknown')
        
        try:
            # Skip if already processed
            if message_id in self.processed_message_ids:
                logger.debug(f"Message {message_id} already processed, skipping")
                return True
            
            # Get full message
            message = await self._get_message(message_id)
            if not message:
                logger.warning(f"Could not retrieve message {message_id}")
                return False
            
            # Parse message
            email_task = self._parse_message(message)
            logger.info(f"Parsed email: {email_task.subject[:50]}...")
            
            # Create task file
            await self._create_task_file(email_task)
            
            # Update state
            self.processed_message_ids.add(message_id)
            self.stats['emails_scanned'] += 1
            self.stats['tasks_created'] += 1
            
            logger.info(f"Message {message_id} processed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    async def _scan_and_process(self):
        """Main scan and process loop"""
        logger.info("Starting Gmail scan...")
        
        # List messages
        messages = await self._list_messages()
        
        if not messages:
            logger.info("No new messages found")
            return
        
        logger.info(f"Found {len(messages)} message(s) to process")
        
        # Process each message
        for message_data in messages:
            await self._process_single_message(message_data)
        
        # Update last sync time
        self.last_sync_time = datetime.now()
        
        logger.info(f"Scan complete. Processed {len(messages)} message(s)")
    
    def get_status(self) -> Dict[str, Any]:
        """Get watcher status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        
        return {
            'version': self.version,
            'status': 'running',
            'uptime': str(uptime),
            'dry_run': self.dry_run,
            'last_sync': self.last_sync_time.isoformat(),
            'processed_count': len(self.processed_message_ids),
            'statistics': self.stats,
            'timestamp': datetime.now().isoformat()
        }
    
    async def run(self):
        """Main entry point"""
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     📧  PLATINUM TIER GMAIL CLOUD WATCHER  📧            ║
║                                                           ║
║     Version: {self.version}
║     DRY_RUN: {self.dry_run}
║     Gmail API: {self.gmail_api_enabled}
║     Scan Interval: {self.scan_interval}s
║                                                           ║
║     SECURITY CONSTRAINTS:                                 ║
║     ✓ Cloud READS emails only                            ║
║     ✗ Cloud NEVER sends emails                           ║
║     ✓ Creates task drafts for approval                   ║
║     ✓ Local system handles sending                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"Gmail Cloud Watcher starting v{self.version}")
        
        try:
            await self._init_session()
            
            while True:
                try:
                    await self._scan_and_process()
                    
                    # Log statistics periodically
                    if self.stats['emails_scanned'] % 10 == 0:
                        logger.info(f"Statistics: {json.dumps(self.stats, indent=2)}")
                    
                    await asyncio.sleep(self.scan_interval)
                
                except Exception as e:
                    logger.error(f"Scan error: {str(e)}")
                    await asyncio.sleep(self.scan_interval)
        
        except KeyboardInterrupt:
            logger.info("Gmail Cloud Watcher stopped by user")
            print("\n🛑 Gmail Cloud Watcher stopped.")
        
        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
        
        finally:
            await self._close_session()
            
            # Final statistics
            print(f"\n📊 Final Statistics:")
            print(f"   Emails Scanned: {self.stats['emails_scanned']}")
            print(f"   Tasks Created: {self.stats['tasks_created']}")
            print(f"   Errors: {self.stats['errors']}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Gmail Cloud Watcher')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--interval', type=int, help='Scan interval in seconds')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()
    
    watcher = GmailCloudWatcher()
    
    if args.status:
        status = watcher.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.dry_run:
        watcher.dry_run = True
    
    if args.interval:
        watcher.scan_interval = args.interval
    
    if args.once:
        await watcher._init_session()
        await watcher._scan_and_process()
        await watcher._close_session()
    else:
        await watcher.run()


if __name__ == "__main__":
    asyncio.run(main())
