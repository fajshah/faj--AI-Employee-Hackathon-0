"""
Platinum Tier Cloud Orchestrator
================================
Main cloud orchestration service for AI Employee system

Security Constraints:
- Cloud handles DRAFT generation ONLY
- Cloud NEVER executes WhatsApp, LinkedIn posting, or payments
- Cloud writes draft files into Pending_Approval
- Local execution after human approval
- Git-based vault sync for state management

Architecture:
- Async/Await throughout
- Comprehensive logging with CloudWatch support
- Exponential backoff retry logic
- DRY_RUN mode for testing
- Production-ready error handling
"""

import os
import sys
import json
import asyncio
import logging
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.platinum')

# Configure logging with support for both file and cloud logging
class CloudOrchestratorLogger:
    """Dual logging: File + Cloud (CloudWatch/Azure Monitor ready)"""
    
    def __init__(self, name: str, log_file: str = None, cloud_enabled: bool = False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # File handler
        if log_file:
            Path(log_file).parent.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        
        # Console handler (for cloud stdout)
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


# Initialize logging
logger_wrapper = CloudOrchestratorLogger(
    name='cloud_orchestrator',
    log_file='Logs/cloud_orchestrator.log',
    cloud_enabled=os.getenv('CLOUD_LOGGING_ENABLED', 'false').lower() == 'true'
)
logger = logger_wrapper.get_logger()


@dataclass
class TaskDraft:
    """Task draft data structure"""
    task_id: str
    title: str
    description: str
    task_type: str  # email, whatsapp, linkedin, finance, general
    action_type: str
    source: str
    priority: str  # LOW, MEDIUM, HIGH, URGENT
    created_at: str
    draft_content: Dict[str, Any]
    requires_approval: bool
    approval_reason: str
    metadata: Dict[str, Any]
    claude_analysis: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    status: str = 'draft'


class RetryConfig:
    """Retry configuration with exponential backoff"""
    
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
    """Async retry executor with exponential backoff and jitter"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    async def execute(
        self,
        func,
        *args,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""
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
                        delay *= (0.5 + random.random() * 0.5)  # 0.5x to 1.0x
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.config.max_retries + 1} attempts failed. "
                        f"Last error: {str(e)}"
                    )
        
        raise last_exception


class CloudOrchestrator:
    """
    Platinum Tier Cloud Orchestrator
    
    Responsibilities:
    - Monitor cloud storage for new tasks
    - Generate drafts using Claude AI
    - Write draft files to Pending_Approval
    - Sync state via Git vault
    - NEVER execute external actions
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-Cloud"
        
        # Configuration
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.cloud_enabled = os.getenv('CLOUD_ENABLED', 'true').lower() == 'true'
        self.git_sync_enabled = os.getenv('GIT_SYNC_ENABLED', 'false').lower() == 'true'
        
        # Directory paths (for local testing/sync)
        self.base_dir = Path(os.getenv('CLOUD_BASE_DIR', '.'))
        self.pending_approval_dir = self.base_dir / 'Pending_Approval'
        self.plans_dir = self.base_dir / 'Plans'
        self.logs_dir = self.base_dir / 'Logs'
        self.cloud_storage_dir = self.base_dir / 'Cloud_Storage'
        
        # Create directories
        self._create_directories()
        
        # Retry executor
        self.retry_executor = AsyncRetryExecutor(RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        ))
        
        # Claude API configuration
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        self.claude_model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
        self.claude_base_url = os.getenv('CLAUDE_BASE_URL', 'https://api.anthropic.com/v1')
        
        # Cloud storage configuration
        self.cloud_storage_type = os.getenv('CLOUD_STORAGE_TYPE', 'local')  # local, s3, azure, gcs
        self.cloud_bucket = os.getenv('CLOUD_STORAGE_BUCKET')
        
        # Git vault configuration
        self.git_repo_path = os.getenv('GIT_VAULT_PATH', '.vault')
        self.git_branch = os.getenv('GIT_BRANCH', 'main')
        
        # Monitoring interval
        self.monitor_interval = int(os.getenv('MONITOR_INTERVAL_SECONDS', '30'))
        
        # Statistics
        self.stats = {
            'tasks_processed': 0,
            'drafts_created': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # HTTP session for API calls
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Cloud Orchestrator initialized v{self.version}")
        logger.info(f"DRY_RUN mode: {self.dry_run}")
        logger.info(f"Cloud storage type: {self.cloud_storage_type}")
        logger.info(f"Git sync enabled: {self.git_sync_enabled}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [
            self.pending_approval_dir,
            self.plans_dir,
            self.logs_dir,
            self.cloud_storage_dir
        ]
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
    
    async def _fetch_cloud_tasks(self) -> List[Dict[str, Any]]:
        """
        Fetch new tasks from cloud storage
        
        In production, this would connect to:
        - AWS S3
        - Azure Blob Storage
        - Google Cloud Storage
        - Or a database
        """
        tasks = []
        
        if self.cloud_storage_type == 'local':
            # Local file system (for testing)
            inbox_dir = self.cloud_storage_dir / 'inbox'
            inbox_dir.mkdir(exist_ok=True)
            
            task_files = list(inbox_dir.glob('*.json'))
            for task_file in task_files:
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task_data = json.load(f)
                        task_data['_source_file'] = str(task_file)
                        tasks.append(task_data)
                except Exception as e:
                    logger.error(f"Error reading task file {task_file}: {str(e)}")
        
        elif self.cloud_storage_type == 's3':
            # AWS S3 implementation (placeholder)
            tasks = await self._fetch_from_s3()
        
        elif self.cloud_storage_type == 'azure':
            # Azure Blob Storage implementation (placeholder)
            tasks = await self._fetch_from_azure()
        
        elif self.cloud_storage_type == 'gcs':
            # Google Cloud Storage implementation (placeholder)
            tasks = await self._fetch_from_gcs()
        
        logger.info(f"Fetched {len(tasks)} task(s) from cloud storage")
        return tasks
    
    async def _fetch_from_s3(self) -> List[Dict[str, Any]]:
        """Fetch tasks from AWS S3 (placeholder)"""
        # Implementation would use aioboto3
        logger.warning("S3 storage not fully implemented - using local fallback")
        return []
    
    async def _fetch_from_azure(self) -> List[Dict[str, Any]]:
        """Fetch tasks from Azure Blob Storage (placeholder)"""
        logger.warning("Azure storage not fully implemented - using local fallback")
        return []
    
    async def _fetch_from_gcs(self) -> List[Dict[str, Any]]:
        """Fetch tasks from Google Cloud Storage (placeholder)"""
        logger.warning("GCS storage not fully implemented - using local fallback")
        return []
    
    async def _analyze_with_claude(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze task using Claude AI
        
        Returns:
        - Task classification
        - Draft content
        - Approval requirement assessment
        - Confidence score
        """
        if not self.claude_api_key:
            logger.warning("Claude API key not configured - using basic analysis")
            return self._basic_analysis(task_data)
        
        prompt = self._build_claude_prompt(task_data)
        
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
        
        async def _call_claude():
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
            result = await self.retry_executor.execute(_call_claude)
            claude_response = result['content'][0]['text']
            
            # Parse Claude's analysis
            analysis = self._parse_claude_analysis(claude_response, task_data)
            logger.info(f"Claude analysis completed for task {task_data.get('task_id', 'unknown')}")
            return analysis
        
        except Exception as e:
            logger.error(f"Claude analysis failed: {str(e)}")
            return self._basic_analysis(task_data)
    
    def _build_claude_prompt(self, task_data: Dict[str, Any]) -> str:
        """Build prompt for Claude AI analysis"""
        return f"""
You are an AI task analyzer for a business automation system. Analyze the following task and provide structured output.

TASK DATA:
{json.dumps(task_data, indent=2)}

Provide your analysis in the following JSON format:

{{
    "task_type": "email|whatsapp|linkedin|finance|general",
    "action_type": "specific action to take",
    "priority": "LOW|MEDIUM|HIGH|URGENT",
    "requires_approval": true|false,
    "approval_reason": "reason if approval required",
    "draft_content": {{
        "subject": "email subject if applicable",
        "body": "message body",
        "recipient": "recipient info",
        "additional_fields": "as needed"
    }},
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation of your analysis",
    "suggested_hashtags": ["relevant", "hashtags"],
    "risk_assessment": "low|medium|high",
    "sensitive_keywords_detected": ["keyword1", "keyword2"]
}}

IMPORTANT:
- If the task involves payments, money transfers, or financial transactions, mark requires_approval as true
- If the task involves external communication to clients, mark requires_approval as true
- If the task contains sensitive keywords (payment, confidential, contract, etc.), mark requires_approval as true
- Provide a confidence score based on how clear the task requirements are
- Generate professional, well-formatted draft content
"""
    
    def _parse_claude_analysis(self, response_text: str, original_task: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            analysis = json.loads(response_text)
            return analysis
        
        except Exception as e:
            logger.error(f"Failed to parse Claude response: {str(e)}")
            return self._basic_analysis(original_task)
    
    def _basic_analysis(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic rule-based analysis (fallback when Claude unavailable)"""
        content_str = json.dumps(task_data).lower()
        
        # Detect task type
        task_type = 'general'
        if any(kw in content_str for kw in ['email', 'mail', 'send to']):
            task_type = 'email'
        elif 'whatsapp' in content_str or 'phone' in content_str:
            task_type = 'whatsapp'
        elif any(kw in content_str for kw in ['linkedin', 'post', 'social']):
            task_type = 'linkedin'
        elif any(kw in content_str for kw in ['invoice', 'payment', 'finance', 'odoo']):
            task_type = 'finance'
        
        # Detect approval requirements
        approval_keywords = [
            'payment', 'money', 'transfer', 'salary', 'confidential',
            'contract', 'agreement', 'client', 'invoice', 'bill'
        ]
        requires_approval = any(kw in content_str for kw in approval_keywords)
        approval_reason = None
        if requires_approval:
            detected = [kw for kw in approval_keywords if kw in content_str]
            approval_reason = f"Contains sensitive keywords: {', '.join(detected)}"
        
        # Generate basic draft
        draft_content = {
            'subject': task_data.get('subject', 'No Subject'),
            'body': task_data.get('message', task_data.get('body', task_data.get('description', ''))),
            'recipient': task_data.get('recipient_email', task_data.get('to', task_data.get('recipient_phone', '')))
        }
        
        return {
            'task_type': task_type,
            'action_type': f'send_{task_type}' if task_type in ['email', 'whatsapp'] else f'post_{task_type}',
            'priority': task_data.get('priority', 'MEDIUM'),
            'requires_approval': requires_approval,
            'approval_reason': approval_reason,
            'draft_content': draft_content,
            'confidence_score': 0.7,
            'reasoning': 'Basic rule-based analysis',
            'risk_assessment': 'medium' if requires_approval else 'low'
        }
    
    async def _generate_task_draft(self, task_data: Dict[str, Any], analysis: Dict[str, Any]) -> TaskDraft:
        """Generate task draft from analysis"""
        task_id = task_data.get('task_id', f"task_{int(time.time())}")
        
        draft = TaskDraft(
            task_id=task_id,
            title=task_data.get('title', f"Task {task_id}"),
            description=task_data.get('description', ''),
            task_type=analysis.get('task_type', 'general'),
            action_type=analysis.get('action_type', 'general_action'),
            source=task_data.get('source', 'cloud'),
            priority=analysis.get('priority', 'MEDIUM'),
            created_at=datetime.now().isoformat(),
            draft_content=analysis.get('draft_content', {}),
            requires_approval=analysis.get('requires_approval', True),
            approval_reason=analysis.get('approval_reason', 'Standard approval required'),
            metadata=task_data.get('metadata', {}),
            claude_analysis=analysis,
            confidence_score=analysis.get('confidence_score', 0.5),
            status='draft'
        )
        
        return draft
    
    async def _write_draft_file(self, draft: TaskDraft) -> str:
        """
        Write draft file to Pending_Approval directory
        
        This is the key security boundary:
        - Cloud ONLY writes drafts
        - Local system handles execution after approval
        """
        filename = f"draft_{draft.task_id}_{int(time.time())}.json"
        filepath = self.pending_approval_dir / filename
        
        draft_data = asdict(draft)
        draft_data['_security_metadata'] = {
            'cloud_generated': True,
            'execution_allowed': False,
            'requires_human_approval': draft.requires_approval,
            'generated_by': f"Cloud Orchestrator v{self.version}",
            'generation_timestamp': datetime.now().isoformat()
        }
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would write draft to: {filepath}")
            logger.info(f"[DRY_RUN] Draft content: {json.dumps(draft_data, indent=2)[:500]}...")
            return str(filepath)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Draft written: {filepath}")
            
            # Also create a Plan.md file for visibility
            await self._create_plan_md(draft, filepath)
            
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Failed to write draft file: {str(e)}")
            raise
    
    async def _create_plan_md(self, draft: TaskDraft, draft_path: Path):
        """Create Plan.md file for the draft"""
        plan_content = f"""# Task Plan: {draft.task_id}

## Task Information
- **Task ID**: {draft.task_id}
- **Title**: {draft.title}
- **Type**: {draft.task_type}
- **Priority**: {draft.priority}
- **Created**: {draft.created_at}
- **Source**: {draft.source}

## AI Analysis
- **Confidence Score**: {draft.confidence_score:.0%}
- **Risk Assessment**: {draft.claude_analysis.get('risk_assessment', 'unknown') if draft.claude_analysis else 'unknown'}
- **Reasoning**: {draft.claude_analysis.get('reasoning', 'N/A') if draft.claude_analysis else 'Basic analysis'}

## Approval Status
- **Requires Approval**: {'Yes' if draft.requires_approval else 'No'}
- **Reason**: {draft.approval_reason}

## Draft Content
```json
{json.dumps(draft.draft_content, indent=2)}
```

## Execution Steps
1. **Human Review Required** - Review draft content for accuracy
2. **Approve/Reject** - Move to Approved/ or reject with reason
3. **Local Execution** - Local orchestrator will execute after approval
4. **Verification** - Confirm successful execution
5. **Archive** - Move to Done/ folder

## Security Notes
- This draft was generated by Cloud Orchestrator
- Cloud does NOT execute external actions
- All execution happens locally after approval
- Git vault sync tracks all state changes

---
*Generated by Platinum Tier Cloud Orchestrator v{self.version}*
"""
        
        plan_path = self.plans_dir / f"{draft.task_id}_Plan.md"
        
        if not self.dry_run:
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(plan_content)
            logger.debug(f"Plan created: {plan_path}")
    
    async def _sync_to_git_vault(self, draft_path: str):
        """
        Sync draft to Git vault for version control
        
        This enables:
        - Audit trail
        - Rollback capability
        - Distributed state
        """
        if not self.git_sync_enabled:
            return
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would sync {draft_path} to Git vault")
            return
        
        try:
            import subprocess
            
            git_dir = Path(self.git_repo_path)
            git_dir.mkdir(exist_ok=True)
            
            # Copy draft to vault
            vault_draft_path = git_dir / Path(draft_path).name
            import shutil
            shutil.copy2(draft_path, vault_draft_path)
            
            # Git operations
            os.chdir(git_dir)
            subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
            subprocess.run(
                ['git', 'commit', '-m', f'Add draft: {Path(draft_path).name}'],
                check=True,
                capture_output=True
            )
            subprocess.run(['git', 'push', 'origin', self.git_branch], check=True, capture_output=True)
            
            logger.info(f"Synced to Git vault: {vault_draft_path}")
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Git sync failed: {e.stderr.decode() if e.stderr else str(e)}")
        except Exception as e:
            logger.error(f"Git sync error: {str(e)}")
    
    async def _process_single_task(self, task_data: Dict[str, Any]) -> bool:
        """Process a single task through the cloud orchestration pipeline"""
        task_id = task_data.get('task_id', 'unknown')
        
        try:
            logger.info(f"Processing task: {task_id}")
            
            # Step 1: Analyze with Claude
            analysis = await self._analyze_with_claude(task_data)
            
            # Step 2: Generate draft
            draft = await self._generate_task_draft(task_data, analysis)
            
            # Step 3: Write draft file
            draft_path = await self._write_draft_file(draft)
            
            # Step 4: Sync to Git vault
            await self._sync_to_git_vault(draft_path)
            
            # Step 5: Archive processed task
            if '_source_file' in task_data and self.cloud_storage_type == 'local':
                archive_dir = self.cloud_storage_dir / 'processed'
                archive_dir.mkdir(exist_ok=True)
                import shutil
                shutil.move(
                    task_data['_source_file'],
                    archive_dir / Path(task_data['_source_file']).name
                )
            
            # Update statistics
            self.stats['tasks_processed'] += 1
            self.stats['drafts_created'] += 1
            
            logger.info(f"Task {task_id} processed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to process task {task_id}: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    async def _monitor_cloud_storage(self):
        """Main monitoring loop"""
        logger.info(f"Starting cloud storage monitor (interval: {self.monitor_interval}s)")
        
        while True:
            try:
                await self._init_session()
                
                # Fetch new tasks
                tasks = await self._fetch_cloud_tasks()
                
                # Process each task
                for task_data in tasks:
                    await self._process_single_task(task_data)
                
                # Log statistics periodically
                if self.stats['tasks_processed'] % 10 == 0:
                    logger.info(f"Statistics: {json.dumps(self.stats, indent=2)}")
                
                await asyncio.sleep(self.monitor_interval)
            
            except Exception as e:
                logger.error(f"Monitor loop error: {str(e)}")
                await asyncio.sleep(self.monitor_interval)
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        
        return {
            'version': self.version,
            'status': 'running',
            'uptime': str(uptime),
            'dry_run': self.dry_run,
            'cloud_storage_type': self.cloud_storage_type,
            'git_sync_enabled': self.git_sync_enabled,
            'statistics': self.stats,
            'timestamp': datetime.now().isoformat()
        }
    
    async def run(self):
        """Main entry point"""
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ☁️  PLATINUM TIER CLOUD ORCHESTRATOR  ☁️             ║
║                                                           ║
║     Version: {self.version}
║     DRY_RUN: {self.dry_run}
║     Cloud Storage: {self.cloud_storage_type}
║     Git Sync: {self.git_sync_enabled}
║                                                           ║
║     SECURITY CONSTRAINTS:                                 ║
║     ✓ Cloud generates DRAFTS only                        ║
║     ✗ Cloud NEVER executes actions                       ║
║     ✓ Local system handles execution                     ║
║     ✓ Human approval required                            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"Cloud Orchestrator starting v{self.version}")
        
        try:
            await self._monitor_cloud_storage()
        
        except KeyboardInterrupt:
            logger.info("Cloud Orchestrator stopped by user")
            print("\n🛑 Cloud Orchestrator stopped.")
        
        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
        
        finally:
            await self._close_session()
            
            # Final statistics
            print(f"\n📊 Final Statistics:")
            print(f"   Tasks Processed: {self.stats['tasks_processed']}")
            print(f"   Drafts Created: {self.stats['drafts_created']}")
            print(f"   Errors: {self.stats['errors']}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Cloud Orchestrator')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--interval', type=int, help='Monitor interval in seconds')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    args = parser.parse_args()
    
    orchestrator = CloudOrchestrator()
    
    if args.status:
        status = orchestrator.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.dry_run:
        orchestrator.dry_run = True
    
    if args.interval:
        orchestrator.monitor_interval = args.interval
    
    await orchestrator.run()


if __name__ == "__main__":
    asyncio.run(main())
