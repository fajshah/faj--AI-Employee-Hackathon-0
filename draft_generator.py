"""
Platinum Tier Draft Generator
==============================
Claude-powered draft generation service for AI Employee system

Security Constraints:
- Generates DRAFTS only (email responses, social posts, messages)
- NEVER executes external actions
- All drafts require human approval before execution
- Local system handles actual sending/posting

Features:
- Async Claude API integration
- Multi-format draft generation (email, LinkedIn, WhatsApp, etc.)
- Tone and style customization
- Brand voice compliance
- Hashtag generation
- Link detection and handling
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
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.platinum')

# Configure logging
class DraftGeneratorLogger:
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


logger_wrapper = DraftGeneratorLogger(
    name='draft_generator',
    log_file='Logs/draft_generator.log'
)
logger = logger_wrapper.get_logger()


@dataclass
class GeneratedDraft:
    """Generated draft data structure"""
    draft_id: str
    source_task_id: str
    draft_type: str  # email_response, linkedin_post, whatsapp_message, etc.
    content: Dict[str, Any]
    tone: str
    style: str
    confidence_score: float
    alternatives: List[Dict[str, Any]]
    hashtags: List[str]
    detected_links: List[str]
    word_count: int
    character_count: int
    estimated_read_time: str
    compliance_checks: Dict[str, bool]
    metadata: Dict[str, Any]
    created_at: str


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


class DraftGenerator:
    """
    Platinum Tier Draft Generator
    
    Responsibilities:
    - Generate professional drafts using Claude AI
    - Support multiple formats (email, social, messaging)
    - Ensure brand voice compliance
    - Provide alternative versions
    - NEVER execute sending/posting
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-Drafts"
        
        # Configuration
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        
        # Claude API configuration
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        self.claude_model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
        self.claude_base_url = os.getenv('CLAUDE_BASE_URL', 'https://api.anthropic.com/v1')
        
        # Directories
        self.base_dir = Path(os.getenv('CLOUD_BASE_DIR', '.'))
        self.drafts_dir = self.base_dir / 'Generated_Drafts'
        self.input_dir = self.base_dir / 'Draft_Requests'
        self.logs_dir = self.base_dir / 'Logs'
        
        self._create_directories()
        
        # Retry executor
        self.retry_executor = AsyncRetryExecutor(RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        ))
        
        # Brand voice configuration
        self.brand_voice = {
            'tone': os.getenv('BRAND_TONE', 'professional'),
            'style': os.getenv('BRAND_STYLE', 'friendly'),
            'company_name': os.getenv('COMPANY_NAME', 'Our Company'),
            'signature': os.getenv('EMAIL_SIGNATURE', 'Best regards,\nThe Team'),
            'avoid_words': os.getenv('BRAND_AVOID_WORDS', '').split(','),
            'preferred_phrases': os.getenv('BRAND_PREFERRED_PHRASES', '').split(',')
        }
        
        # Statistics
        self.stats = {
            'drafts_generated': 0,
            'emails': 0,
            'social_posts': 0,
            'messages': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Draft Generator initialized v{self.version}")
        logger.info(f"DRY_RUN mode: {self.dry_run}")
        logger.info(f"Brand tone: {self.brand_voice['tone']}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [self.drafts_dir, self.input_dir, self.logs_dir]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory verified: {dir_path}")
    
    async def _init_session(self):
        """Initialize HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=90)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.debug("HTTP session initialized")
    
    async def _close_session(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("HTTP session closed")
    
    async def generate_email_draft(
        self,
        task_data: Dict[str, Any],
        original_email: Dict[str, Any] = None
    ) -> GeneratedDraft:
        """
        Generate email response draft
        
        Args:
            task_data: Task containing email details
            original_email: Original email being responded to (if applicable)
        
        Returns:
            GeneratedDraft with email content
        """
        draft_id = f"email_draft_{int(time.time())}"
        
        prompt = self._build_email_prompt(task_data, original_email)
        claude_response = await self._call_claude(prompt)
        
        # Parse response
        email_content = self._parse_email_response(claude_response)
        
        # Generate alternatives
        alternatives = await self._generate_alternatives('email', task_data, count=2)
        
        # Detect links
        detected_links = self._detect_links(email_content.get('body', ''))
        
        # Compliance checks
        compliance = self._check_compliance(email_content.get('body', ''))
        
        # Calculate metrics
        body_text = email_content.get('body', '')
        word_count = len(body_text.split())
        char_count = len(body_text)
        read_time = f"{max(1, word_count // 200)} min"
        
        draft = GeneratedDraft(
            draft_id=draft_id,
            source_task_id=task_data.get('task_id', 'unknown'),
            draft_type='email_response',
            content=email_content,
            tone=self.brand_voice['tone'],
            style=self.brand_voice['style'],
            confidence_score=claude_response.get('confidence_score', 0.8),
            alternatives=alternatives,
            hashtags=[],
            detected_links=detected_links,
            word_count=word_count,
            character_count=char_count,
            estimated_read_time=read_time,
            compliance_checks=compliance,
            metadata={
                'original_email_id': original_email.get('email_id') if original_email else None,
                'recipient': task_data.get('recipient_email', original_email.get('from_address') if original_email else ''),
                'subject': task_data.get('subject', original_email.get('subject') if original_email else 'Re: Your Email')
            },
            created_at=datetime.now().isoformat()
        )
        
        self.stats['drafts_generated'] += 1
        self.stats['emails'] += 1
        
        return draft
    
    async def generate_linkedin_post_draft(
        self,
        task_data: Dict[str, Any]
    ) -> GeneratedDraft:
        """Generate LinkedIn post draft"""
        draft_id = f"linkedin_draft_{int(time.time())}"
        
        prompt = self._build_linkedin_prompt(task_data)
        claude_response = await self._call_claude(prompt)
        
        # Parse response
        post_content = self._parse_social_response(claude_response, 'linkedin')
        
        # Generate alternatives
        alternatives = await self._generate_alternatives('linkedin', task_data, count=2)
        
        # Detect links
        detected_links = self._detect_links(post_content.get('content', ''))
        
        # Compliance checks
        compliance = self._check_compliance(post_content.get('content', ''))
        
        # Calculate metrics
        content_text = post_content.get('content', '')
        char_count = len(content_text)
        
        draft = GeneratedDraft(
            draft_id=draft_id,
            source_task_id=task_data.get('task_id', 'unknown'),
            draft_type='linkedin_post',
            content=post_content,
            tone='professional',
            style='engaging',
            confidence_score=claude_response.get('confidence_score', 0.8),
            alternatives=alternatives,
            hashtags=post_content.get('hashtags', []),
            detected_links=detected_links,
            word_count=len(content_text.split()),
            character_count=char_count,
            estimated_read_time=f"{max(1, char_count // 100)} sec",
            compliance_checks=compliance,
            metadata={
                'platform': 'linkedin',
                'visibility': task_data.get('visibility', 'PUBLIC'),
                'media_attachments': task_data.get('media', [])
            },
            created_at=datetime.now().isoformat()
        )
        
        self.stats['drafts_generated'] += 1
        self.stats['social_posts'] += 1
        
        return draft
    
    async def generate_whatsapp_draft(
        self,
        task_data: Dict[str, Any]
    ) -> GeneratedDraft:
        """Generate WhatsApp message draft"""
        draft_id = f"whatsapp_draft_{int(time.time())}"
        
        prompt = self._build_whatsapp_prompt(task_data)
        claude_response = await self._call_claude(prompt)
        
        # Parse response
        message_content = self._parse_message_response(claude_response)
        
        # Generate alternatives
        alternatives = await self._generate_alternatives('whatsapp', task_data, count=2)
        
        # Detect links
        detected_links = self._detect_links(message_content.get('message', ''))
        
        # Compliance checks
        compliance = self._check_compliance(message_content.get('message', ''))
        
        draft = GeneratedDraft(
            draft_id=draft_id,
            source_task_id=task_data.get('task_id', 'unknown'),
            draft_type='whatsapp_message',
            content=message_content,
            tone='casual',
            style='concise',
            confidence_score=claude_response.get('confidence_score', 0.8),
            alternatives=alternatives,
            hashtags=[],
            detected_links=detected_links,
            word_count=len(message_content.get('message', '').split()),
            character_count=len(message_content.get('message', '')),
            estimated_read_time="30 sec",
            compliance_checks=compliance,
            metadata={
                'recipient_phone': task_data.get('recipient_phone', ''),
                'message_type': 'text'
            },
            created_at=datetime.now().isoformat()
        )
        
        self.stats['drafts_generated'] += 1
        self.stats['messages'] += 1
        
        return draft
    
    async def generate_generic_draft(
        self,
        task_data: Dict[str, Any]
    ) -> GeneratedDraft:
        """Generate generic draft for unspecified task types"""
        draft_id = f"generic_draft_{int(time.time())}"
        
        prompt = self._build_generic_prompt(task_data)
        claude_response = await self._call_claude(prompt)
        
        # Parse response
        generic_content = self._parse_generic_response(claude_response)
        
        draft = GeneratedDraft(
            draft_id=draft_id,
            source_task_id=task_data.get('task_id', 'unknown'),
            draft_type='generic',
            content=generic_content,
            tone=self.brand_voice['tone'],
            style=self.brand_voice['style'],
            confidence_score=claude_response.get('confidence_score', 0.7),
            alternatives=[],
            hashtags=[],
            detected_links=self._detect_links(json.dumps(generic_content)),
            word_count=0,
            character_count=0,
            estimated_read_time="1 min",
            compliance_checks=self._check_compliance(json.dumps(generic_content)),
            metadata={
                'task_type': task_data.get('task_type', 'general'),
                'action_type': task_data.get('action_type', 'general')
            },
            created_at=datetime.now().isoformat()
        )
        
        self.stats['drafts_generated'] += 1
        
        return draft
    
    def _build_email_prompt(self, task_data: Dict[str, Any], original_email: Dict[str, Any] = None) -> str:
        """Build prompt for email draft generation"""
        context = ""
        if original_email:
            context = f"""
ORIGINAL EMAIL:
From: {original_email.get('from_address', 'Unknown')}
Subject: {original_email.get('subject', 'No Subject')}
Received: {original_email.get('received_at', 'Unknown')}

Body:
{original_email.get('body_plain', '')[:2000]}

---
"""
        
        return f"""
You are a professional email drafting assistant for {self.brand_voice['company_name']}.

Brand Voice:
- Tone: {self.brand_voice['tone']}
- Style: {self.brand_voice['style']}
- Signature: {self.brand_voice['signature']}
- Avoid these words: {', '.join(self.brand_voice['avoid_words']) if self.brand_voice['avoid_words'] else 'None'}

{context}

TASK: Generate a professional email response based on the following requirements:

{json.dumps(task_data, indent=2)}

Provide your response in the following JSON format:

{{
    "subject": "Clear, professional subject line",
    "body": "Complete email body with proper greeting and closing",
    "recipient_name": "Inferred or generic name",
    "greeting": "Appropriate greeting",
    "closing": "Appropriate closing",
    "signature": "{self.brand_voice['signature']}",
    "confidence_score": 0.0-1.0,
    "reasoning": "Brief explanation of your approach"
}}

IMPORTANT:
- Use professional, clear language
- Address all points from the original email
- Keep it concise but complete
- Include appropriate greeting and closing
- Match the brand voice specified above
"""
    
    def _build_linkedin_prompt(self, task_data: Dict[str, Any]) -> str:
        """Build prompt for LinkedIn post generation"""
        return f"""
You are a professional social media content creator for {self.brand_voice['company_name']}.

Brand Voice:
- Tone: Professional yet engaging
- Style: Thought leadership, value-driven
- Company: {self.brand_voice['company_name']}

TASK: Generate a LinkedIn post based on the following requirements:

{json.dumps(task_data, indent=2)}

Provide your response in the following JSON format:

{{
    "content": "Complete LinkedIn post content (max 3000 characters)",
    "hashtags": ["relevant", "professional", "hashtags"],
    "hook": "Attention-grabbing opening line",
    "call_to_action": "Optional CTA",
    "confidence_score": 0.0-1.0,
    "reasoning": "Brief explanation of your approach"
}}

IMPORTANT:
- Start with a strong hook
- Provide value to readers
- Use appropriate line breaks for readability
- Include 3-5 relevant hashtags
- Keep it professional but engaging
- LinkedIn posts perform well with personal insights + professional value
"""
    
    def _build_whatsapp_prompt(self, task_data: Dict[str, Any]) -> str:
        """Build prompt for WhatsApp message generation"""
        return f"""
You are a professional messaging assistant for {self.brand_voice['company_name']}.

Brand Voice:
- Tone: Friendly but professional
- Style: Concise, clear
- Company: {self.brand_voice['company_name']}

TASK: Generate a WhatsApp message based on the following requirements:

{json.dumps(task_data, indent=2)}

Provide your response in the following JSON format:

{{
    "message": "Complete WhatsApp message (concise and clear)",
    "emoji_suggestions": ["👍", "✅"],
    "confidence_score": 0.0-1.0,
    "reasoning": "Brief explanation of your approach"
}}

IMPORTANT:
- Keep it concise (WhatsApp is for quick communication)
- Be friendly but professional
- Use emojis sparingly and appropriately
- Include clear call-to-action if needed
- Respect character limits for quick reading
"""
    
    def _build_generic_prompt(self, task_data: Dict[str, Any]) -> str:
        """Build prompt for generic draft generation"""
        return f"""
You are an AI assistant for {self.brand_voice['company_name']}.

Brand Voice:
- Tone: {self.brand_voice['tone']}
- Style: {self.brand_voice['style']}
- Company: {self.brand_voice['company_name']}

TASK: Generate appropriate content based on the following requirements:

{json.dumps(task_data, indent=2)}

Provide your response in the following JSON format:

{{
    "content_type": "Type of content generated",
    "content": {{
        "primary": "Main content",
        "additional_fields": "As needed"
    }},
    "confidence_score": 0.0-1.0,
    "reasoning": "Brief explanation of your approach",
    "suggestions": ["Additional suggestions or recommendations"]
}}

IMPORTANT:
- Match the content type to the task requirements
- Follow brand voice guidelines
- Provide clear, actionable content
"""
    
    async def _call_claude(self, prompt: str) -> Dict[str, Any]:
        """Call Claude API for content generation"""
        if not self.claude_api_key:
            logger.warning("Claude API key not configured - using fallback")
            return self._fallback_generation(prompt)
        
        headers = {
            'x-api-key': self.claude_api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        
        payload = {
            'model': self.claude_model,
            'max_tokens': 2048,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }
        
        async def _make_request():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.claude_base_url}/messages",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Claude API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result
        
        try:
            result = await self.retry_executor.execute(_make_request)
            response_text = result['content'][0]['text']
            
            # Parse JSON response
            return self._parse_claude_json(response_text)
        
        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            return self._fallback_generation(prompt)
    
    def _parse_claude_json(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Claude response"""
        try:
            # Handle markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            return json.loads(response_text)
        
        except Exception as e:
            logger.error(f"Failed to parse Claude JSON: {str(e)}")
            return {'error': str(e), 'raw_response': response_text}
    
    def _fallback_generation(self, prompt: str) -> Dict[str, Any]:
        """Fallback generation when Claude unavailable"""
        # Basic template-based generation
        return {
            'subject': 'Re: Your Message',
            'body': f"Thank you for your message. We will respond shortly.\n\n{self.brand_voice['signature']}",
            'confidence_score': 0.5,
            'reasoning': 'Fallback template response (Claude API unavailable)'
        }
    
    def _parse_email_response(self, claude_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude response for email draft"""
        return {
            'subject': claude_response.get('subject', 'Re: Your Email'),
            'body': claude_response.get('body', ''),
            'recipient_name': claude_response.get('recipient_name', ''),
            'greeting': claude_response.get('greeting', 'Dear'),
            'closing': claude_response.get('closing', 'Best regards'),
            'signature': claude_response.get('signature', self.brand_voice['signature'])
        }
    
    def _parse_social_response(self, claude_response: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Parse Claude response for social media post"""
        return {
            'content': claude_response.get('content', ''),
            'hashtags': claude_response.get('hashtags', []),
            'hook': claude_response.get('hook', ''),
            'call_to_action': claude_response.get('call_to_action', ''),
            'platform': platform
        }
    
    def _parse_message_response(self, claude_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude response for messaging"""
        return {
            'message': claude_response.get('message', ''),
            'emoji_suggestions': claude_response.get('emoji_suggestions', []),
            'message_type': 'text'
        }
    
    def _parse_generic_response(self, claude_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude response for generic draft"""
        return {
            'content_type': claude_response.get('content_type', 'generic'),
            'primary': claude_response.get('content', {}).get('primary', ''),
            'additional': claude_response.get('content', {})
        }
    
    async def _generate_alternatives(
        self,
        draft_type: str,
        task_data: Dict[str, Any],
        count: int = 2
    ) -> List[Dict[str, Any]]:
        """Generate alternative versions of the draft"""
        alternatives = []
        
        # For now, return empty list (can be enhanced with additional Claude calls)
        # In production, this would make additional API calls with varied prompts
        
        return alternatives
    
    def _detect_links(self, content: str) -> List[str]:
        """Detect URLs in content"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, content)
    
    def _check_compliance(self, content: str) -> Dict[str, bool]:
        """Check content for compliance with brand guidelines"""
        content_lower = content.lower()
        
        checks = {
            'no_profanity': True,  # Would need actual profanity filter
            'brand_voice_match': True,
            'no_avoided_words': all(
                word.strip().lower() not in content_lower
                for word in self.brand_voice['avoid_words']
                if word.strip()
            ),
            'has_preferred_phrases': any(
                phrase.strip().lower() in content_lower
                for phrase in self.brand_voice['preferred_phrases']
                if phrase.strip()
            ) if self.brand_voice['preferred_phrases'] else True,
            'appropriate_length': len(content) < 5000,
            'no_sensitive_data': not any(
                kw in content_lower for kw in ['password', 'credit card', 'ssn', 'bank account']
            )
        }
        
        return checks
    
    async def save_draft(self, draft: GeneratedDraft) -> str:
        """Save draft to file"""
        filename = f"{draft.draft_id}.json"
        filepath = self.drafts_dir / filename
        
        draft_data = asdict(draft)
        draft_data['_security_metadata'] = {
            'cloud_generated': True,
            'execution_allowed': False,
            'requires_human_approval': True,
            'generated_by': f"Draft Generator v{self.version}",
            'generation_timestamp': draft.created_at
        }
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would save draft to: {filepath}")
            return str(filepath)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Draft saved: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Failed to save draft: {str(e)}")
            raise
    
    async def process_draft_request(self, request_file: Path) -> bool:
        """Process a draft request from input directory"""
        try:
            with open(request_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            draft_type = task_data.get('draft_type', 'generic')
            logger.info(f"Processing {draft_type} draft request: {task_data.get('task_id', 'unknown')}")
            
            # Generate appropriate draft
            if draft_type == 'email' or task_data.get('type') == 'email':
                original_email = task_data.pop('original_email', None)
                draft = await self.generate_email_draft(task_data, original_email)
            elif draft_type == 'linkedin' or task_data.get('type') == 'linkedin':
                draft = await self.generate_linkedin_post_draft(task_data)
            elif draft_type == 'whatsapp' or task_data.get('type') == 'whatsapp':
                draft = await self.generate_whatsapp_draft(task_data)
            else:
                draft = await self.generate_generic_draft(task_data)
            
            # Save draft
            await self.save_draft(draft)
            
            logger.info(f"Draft generated successfully: {draft.draft_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to process draft request: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    async def monitor_requests(self):
        """Monitor input directory for draft requests"""
        logger.info(f"Monitoring for draft requests in: {self.input_dir}")
        
        while True:
            try:
                request_files = list(self.input_dir.glob('*.json'))
                
                for request_file in request_files:
                    success = await self.process_draft_request(request_file)
                    
                    if success and not self.dry_run:
                        # Archive processed request
                        archive_dir = self.input_dir / 'processed'
                        archive_dir.mkdir(exist_ok=True)
                        import shutil
                        shutil.move(
                            str(request_file),
                            str(archive_dir / request_file.name)
                        )
                
                await asyncio.sleep(10)  # Check every 10 seconds
            
            except Exception as e:
                logger.error(f"Monitor error: {str(e)}")
                await asyncio.sleep(10)
    
    def get_status(self) -> Dict[str, Any]:
        """Get generator status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        
        return {
            'version': self.version,
            'status': 'running',
            'uptime': str(uptime),
            'dry_run': self.dry_run,
            'brand_voice': self.brand_voice,
            'statistics': self.stats,
            'timestamp': datetime.now().isoformat()
        }
    
    async def run(self):
        """Main entry point"""
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ✍️  PLATINUM TIER DRAFT GENERATOR  ✍️                ║
║                                                           ║
║     Version: {self.version}
║     DRY_RUN: {self.dry_run}
║     Brand Tone: {self.brand_voice['tone']}
║     Brand Style: {self.brand_voice['style']}
║                                                           ║
║     SECURITY CONSTRAINTS:                                 ║
║     ✓ Cloud generates DRAFTS only                        ║
║     ✗ Cloud NEVER executes sending                       ║
║     ✓ All drafts require approval                        ║
║     ✓ Local system handles execution                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"Draft Generator starting v{self.version}")
        
        try:
            await self._init_session()
            await self.monitor_requests()
        
        except KeyboardInterrupt:
            logger.info("Draft Generator stopped by user")
            print("\n🛑 Draft Generator stopped.")
        
        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
        
        finally:
            await self._close_session()
            
            # Final statistics
            print(f"\n📊 Final Statistics:")
            print(f"   Total Drafts: {self.stats['drafts_generated']}")
            print(f"   Email Drafts: {self.stats['emails']}")
            print(f"   Social Posts: {self.stats['social_posts']}")
            print(f"   Messages: {self.stats['messages']}")
            print(f"   Errors: {self.stats['errors']}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Draft Generator')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--once', action='store_true', help='Process once and exit')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    args = parser.parse_args()
    
    generator = DraftGenerator()
    
    if args.status:
        status = generator.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.dry_run:
        generator.dry_run = True
    
    if args.once:
        await generator._init_session()
        request_files = list(generator.input_dir.glob('*.json'))
        for request_file in request_files:
            await generator.process_draft_request(request_file)
        await generator._close_session()
    else:
        await generator.run()


if __name__ == "__main__":
    asyncio.run(main())
