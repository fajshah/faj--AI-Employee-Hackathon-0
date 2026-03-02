"""
Platinum Tier CEO Weekly Briefing Generator
============================================
Executive briefing generation service for AI Employee system

Security Constraints:
- READS data from local/cloud sources only
- Generates briefing documents (no external actions)
- Aggregates data without exposing sensitive details
- All briefings are drafts requiring review before distribution

Features:
- Async data aggregation from multiple sources
- Claude-powered executive summary generation
- Multi-format output (PDF, HTML, Markdown, JSON)
- KPI tracking and visualization
- Task completion analytics
- Financial summaries
- Team activity reports
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
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.platinum')

# Configure logging
class BriefingLogger:
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


logger_wrapper = BriefingLogger(
    name='ceo_briefing_generator',
    log_file='Logs/ceo_briefing.log'
)
logger = logger_wrapper.get_logger()


@dataclass
class BriefingSection:
    """Briefing section data structure"""
    title: str
    content: str
    priority: str  # HIGH, MEDIUM, LOW
    data_points: List[Dict[str, Any]] = field(default_factory=list)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)


@dataclass
class WeeklyBriefing:
    """Weekly briefing document"""
    briefing_id: str
    period_start: str
    period_end: str
    generated_at: str
    executive_summary: str
    sections: List[BriefingSection]
    kpis: Dict[str, Any]
    highlights: List[str]
    concerns: List[str]
    recommendations: List[str]
    next_week_priorities: List[str]
    metadata: Dict[str, Any]
    formats: Dict[str, str]  # format -> file path


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


class CEOBriefingGenerator:
    """
    Platinum Tier CEO Weekly Briefing Generator
    
    Responsibilities:
    - Aggregate data from multiple sources
    - Generate executive summaries using Claude AI
    - Create multi-format briefing documents
    - Track KPIs and trends
    - NEVER execute external actions
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-Briefing"
        
        # Configuration
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.claude_enabled = os.getenv('CLAUDE_API_KEY') is not None
        
        # Claude API configuration
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        self.claude_model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
        self.claude_base_url = os.getenv('CLAUDE_BASE_URL', 'https://api.anthropic.com/v1')
        
        # Directories
        self.base_dir = Path(os.getenv('CLOUD_BASE_DIR', '.'))
        self.briefings_dir = self.base_dir / 'CEO_Briefings'
        self.logs_dir = self.base_dir / 'Logs'
        self.data_dir = self.base_dir / 'Reports'
        
        self._create_directories()
        
        # Retry executor
        self.retry_executor = AsyncRetryExecutor(RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        ))
        
        # Briefing schedule
        self.briefing_day = os.getenv('BRIEFING_DAY', 'sunday')
        self.briefing_time = os.getenv('BRIEFING_TIME', '18:00')
        
        # Data sources
        self.data_sources = {
            'tasks': self.base_dir / 'Done',
            'errors': self.base_dir / 'Error',
            'pending': self.base_dir / 'Pending_Approval',
            'approved': self.base_dir / 'Approved',
            'logs': self.logs_dir,
            'accounting': self.base_dir / 'Accounting'
        }
        
        # Company configuration
        self.company_name = os.getenv('COMPANY_NAME', 'Our Company')
        self.ceo_name = os.getenv('CEO_NAME', 'CEO')
        
        # Statistics
        self.stats = {
            'briefings_generated': 0,
            'data_points_processed': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"CEO Briefing Generator initialized v{self.version}")
        logger.info(f"DRY_RUN mode: {self.dry_run}")
        logger.info(f"Claude AI enabled: {self.claude_enabled}")
        logger.info(f"Briefing schedule: {self.briefing_day} at {self.briefing_time}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [self.briefings_dir, self.logs_dir, self.data_dir]
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
    
    def _get_period_dates(self) -> Tuple[datetime, datetime]:
        """Get start and end dates for the weekly period"""
        now = datetime.now()
        
        # Find most recent Sunday (or configured briefing day)
        days_since_sunday = (now.weekday() + 1) % 7
        period_end = now - timedelta(days=days_since_sunday)
        period_end = period_end.replace(hour=23, minute=59, second=59)
        
        period_start = period_end - timedelta(days=6)
        period_start = period_start.replace(hour=0, minute=0, second=0)
        
        return period_start, period_end
    
    async def _collect_task_data(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Collect task completion data"""
        task_data = {
            'completed': [],
            'failed': [],
            'pending': [],
            'by_type': defaultdict(int),
            'by_source': defaultdict(int),
            'total_completed': 0,
            'total_failed': 0,
            'success_rate': 0.0
        }
        
        # Scan Done directory
        done_dir = self.data_sources['tasks']
        if done_dir.exists():
            for task_file in done_dir.glob('*.json'):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task = json.load(f)
                    
                    # Check if within period
                    task_date = self._parse_task_date(task)
                    if period_start <= task_date <= period_end:
                        task_data['completed'].append(task)
                        task_data['by_type'][task.get('task_type', 'general')] += 1
                        task_data['by_source'][task.get('source', 'unknown')] += 1
                except Exception as e:
                    logger.debug(f"Error reading task file {task_file}: {str(e)}")
        
        # Scan Error directory
        error_dir = self.data_sources['errors']
        if error_dir.exists():
            for task_file in error_dir.glob('*.json'):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task = json.load(f)
                    
                    task_date = self._parse_task_date(task)
                    if period_start <= task_date <= period_end:
                        task_data['failed'].append(task)
                except Exception as e:
                    logger.debug(f"Error reading error file {task_file}: {str(e)}")
        
        # Scan Pending directory
        pending_dir = self.data_sources['pending']
        if pending_dir.exists():
            task_data['pending_count'] = len(list(pending_dir.glob('*.json')))
        
        # Calculate statistics
        task_data['total_completed'] = len(task_data['completed'])
        task_data['total_failed'] = len(task_data['failed'])
        
        total = task_data['total_completed'] + task_data['total_failed']
        if total > 0:
            task_data['success_rate'] = task_data['total_completed'] / total * 100
        
        self.stats['data_points_processed'] += task_data['total_completed'] + task_data['total_failed']
        
        return task_data
    
    async def _collect_financial_data(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Collect financial data from accounting directory"""
        financial_data = {
            'invoices_created': 0,
            'total_revenue': 0.0,
            'expenses_logged': 0,
            'total_expenses': 0.0,
            'net': 0.0,
            'transactions': []
        }
        
        accounting_dir = self.data_sources['accounting']
        if accounting_dir.exists():
            for file in accounting_dir.glob('*.json'):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                    
                    record_date = self._parse_task_date(record)
                    if period_start <= record_date <= period_end:
                        financial_data['transactions'].append(record)
                        
                        if record.get('type') == 'invoice':
                            financial_data['invoices_created'] += 1
                            amount = float(record.get('amount', 0))
                            financial_data['total_revenue'] += amount
                        
                        elif record.get('type') == 'expense':
                            financial_data['expenses_logged'] += 1
                            amount = float(record.get('amount', 0))
                            financial_data['total_expenses'] += amount
                
                except Exception as e:
                    logger.debug(f"Error reading financial record {file}: {str(e)}")
        
        financial_data['net'] = financial_data['total_revenue'] - financial_data['total_expenses']
        self.stats['data_points_processed'] += len(financial_data['transactions'])
        
        return financial_data
    
    async def _collect_activity_data(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Collect agent activity data from logs"""
        activity_data = {
            'by_agent': defaultdict(int),
            'by_action': defaultdict(int),
            'total_actions': 0,
            'peak_hours': [],
            'daily_breakdown': defaultdict(int)
        }
        
        # Scan log files
        logs_dir = self.data_sources['logs']
        if logs_dir.exists():
            for log_file in logs_dir.glob('*.json'):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_entry = json.load(f)
                    
                    log_date = self._parse_task_date(log_entry)
                    if period_start <= log_date <= period_end:
                        agent = log_entry.get('agent', log_entry.get('component', 'unknown'))
                        action = log_entry.get('action', 'unknown')
                        
                        activity_data['by_agent'][agent] += 1
                        activity_data['by_action'][action] += 1
                        activity_data['total_actions'] += 1
                        
                        day_key = log_date.strftime('%Y-%m-%d')
                        activity_data['daily_breakdown'][day_key] += 1
                
                except Exception as e:
                    logger.debug(f"Error reading log file {log_file}: {str(e)}")
        
        # Find peak hours (simplified)
        activity_data['peak_hours'] = ['09:00-10:00', '14:00-15:00']  # Default
        
        self.stats['data_points_processed'] += activity_data['total_actions']
        
        return activity_data
    
    def _parse_task_date(self, data: Dict[str, Any]) -> datetime:
        """Parse date from task/log data"""
        date_fields = ['created_at', 'timestamp', 'received_at', 'date', '_timestamp']
        
        for field in date_fields:
            if field in data:
                try:
                    date_str = data[field]
                    if isinstance(date_str, str):
                        # Handle various date formats
                        for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                            try:
                                return datetime.strptime(date_str[:19], fmt)
                            except ValueError:
                                continue
                except Exception:
                    pass
        
        return datetime.now()
    
    async def _generate_executive_summary(
        self,
        task_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        activity_data: Dict[str, Any]
    ) -> str:
        """Generate executive summary using Claude AI"""
        if not self.claude_enabled:
            return self._generate_basic_summary(task_data, financial_data, activity_data)
        
        prompt = f"""
You are an executive assistant preparing a weekly briefing for the CEO of {self.company_name}.

Based on the following data, write a concise, professional executive summary (3-5 paragraphs) that:
1. Highlights key accomplishments
2. Notes important metrics
3. Identifies any concerns
4. Provides context for the week's performance

WEEKLY DATA:

Task Completion:
- Total Completed: {task_data['total_completed']}
- Total Failed: {task_data['total_failed']}
- Success Rate: {task_data['success_rate']:.1f}%
- By Type: {dict(task_data['by_type'])}
- By Source: {dict(task_data['by_source'])}

Financial Summary:
- Invoices Created: {financial_data['invoices_created']}
- Total Revenue: ${financial_data['total_revenue']:.2f}
- Total Expenses: ${financial_data['total_expenses']:.2f}
- Net: ${financial_data['net']:.2f}

Activity Metrics:
- Total Actions: {activity_data['total_actions']}
- By Agent: {dict(activity_data['by_agent'])}

Write the executive summary in a professional, confident tone. Focus on insights, not just raw numbers.
"""
        
        headers = {
            'x-api-key': self.claude_api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        
        payload = {
            'model': self.claude_model,
            'max_tokens': 1024,
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
                    return result['content'][0]['text']
        
        try:
            summary = await self.retry_executor.execute(_call_claude)
            return summary
        
        except Exception as e:
            logger.error(f"Claude API call failed: {str(e)}")
            return self._generate_basic_summary(task_data, financial_data, activity_data)
    
    def _generate_basic_summary(
        self,
        task_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        activity_data: Dict[str, Any]
    ) -> str:
        """Generate basic summary without Claude AI"""
        return f"""
WEEKLY EXECUTIVE SUMMARY
========================

This week, the AI Employee system processed {task_data['total_completed']} tasks with a {task_data['success_rate']:.1f}% success rate.

KEY METRICS:
• Tasks Completed: {task_data['total_completed']}
• Success Rate: {task_data['success_rate']:.1f}%
• Revenue: ${financial_data['total_revenue']:.2f}
• Net Income: ${financial_data['net']:.2f}
• Total System Actions: {activity_data['total_actions']}

TOP PERFORMERS:
{chr(10).join(f'• {agent}: {count} actions' for agent, count in sorted(activity_data['by_agent'].items(), key=lambda x: -x[1])[:5])}

The system continues to operate effectively, handling communications, social media posting, and financial operations autonomously.
"""
    
    async def _generate_sections(
        self,
        task_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        activity_data: Dict[str, Any]
    ) -> List[BriefingSection]:
        """Generate briefing sections"""
        sections = []
        
        # Task Performance Section
        sections.append(BriefingSection(
            title="Task Performance",
            content=f"""
## Task Completion Summary

| Metric | Value |
|--------|-------|
| Total Completed | {task_data['total_completed']} |
| Total Failed | {task_data['total_failed']} |
| Success Rate | {task_data['success_rate']:.1f}% |
| Pending Approval | {task_data.get('pending_count', 0)} |

### By Task Type
{self._format_breakdown(task_data['by_type'])}

### By Source
{self._format_breakdown(task_data['by_source'])}
""",
            priority="HIGH",
            data_points=[
                {'label': 'Completed', 'value': task_data['total_completed']},
                {'label': 'Failed', 'value': task_data['total_failed']},
                {'label': 'Success Rate', 'value': f"{task_data['success_rate']:.1f}%"}
            ],
            action_items=[
                "Review failed tasks for patterns",
                "Optimize high-volume task sources"
            ] if task_data['total_failed'] > 0 else []
        ))
        
        # Financial Summary Section
        sections.append(BriefingSection(
            title="Financial Summary",
            content=f"""
## Financial Performance

| Metric | Value |
|--------|-------|
| Invoices Created | {financial_data['invoices_created']} |
| Total Revenue | ${financial_data['total_revenue']:.2f} |
| Total Expenses | ${financial_data['total_expenses']:.2f} |
| **Net** | **${financial_data['net']:.2f}** |

### Transaction Breakdown
Total transactions this period: {len(financial_data['transactions'])}
""",
            priority="HIGH",
            data_points=[
                {'label': 'Revenue', 'value': f"${financial_data['total_revenue']:.2f}"},
                {'label': 'Expenses', 'value': f"${financial_data['total_expenses']:.2f}"},
                {'label': 'Net', 'value': f"${financial_data['net']:.2f}"}
            ],
            action_items=[]
        ))
        
        # System Activity Section
        sections.append(BriefingSection(
            title="System Activity",
            content=f"""
## AI Agent Activity

| Metric | Value |
|--------|-------|
| Total Actions | {activity_data['total_actions']} |

### By Agent
{self._format_breakdown(activity_data['by_agent'])}

### By Action Type
{self._format_breakdown(activity_data['by_action'])}

### Daily Breakdown
{self._format_breakdown(activity_data['daily_breakdown'])}
""",
            priority="MEDIUM",
            data_points=[
                {'label': 'Total Actions', 'value': activity_data['total_actions']}
            ],
            action_items=[]
        ))
        
        # Pending Approvals Section
        if task_data.get('pending_count', 0) > 0:
            sections.append(BriefingSection(
                title="Pending Approvals",
                content=f"""
## Awaiting Your Review

There are **{task_data.get('pending_count', 0)}** tasks pending approval.

These tasks have been flagged as sensitive or high-value and require human review before execution.

### Action Required
Please review pending tasks in the Pending_Approval directory.
""",
                priority="HIGH",
                data_points=[
                    {'label': 'Pending', 'value': task_data.get('pending_count', 0)}
                ],
                action_items=[
                    "Review pending approvals in dashboard",
                    "Approve or reject pending tasks"
                ]
            ))
        
        return sections
    
    def _format_breakdown(self, data: dict) -> str:
        """Format breakdown data as markdown table"""
        if not data:
            return "*No data available*"
        
        lines = ["| Item | Count |", "|------|-------|"]
        for item, count in sorted(data.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"| {item} | {count} |")
        return '\n'.join(lines)
    
    async def _generate_highlights_and_concerns(
        self,
        task_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        activity_data: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """Generate highlights and concerns lists"""
        highlights = []
        concerns = []
        
        # Highlights
        if task_data['success_rate'] >= 95:
            highlights.append(f"Excellent task success rate: {task_data['success_rate']:.1f}%")
        if task_data['total_completed'] > 50:
            highlights.append(f"High task volume processed: {task_data['total_completed']} tasks")
        if financial_data['net'] > 0:
            highlights.append(f"Positive net financial position: ${financial_data['net']:.2f}")
        if activity_data['total_actions'] > 100:
            highlights.append(f"High system activity: {activity_data['total_actions']} actions")
        
        # Concerns
        if task_data['success_rate'] < 90:
            concerns.append(f"Task success rate below target: {task_data['success_rate']:.1f}%")
        if task_data['total_failed'] > 5:
            concerns.append(f"High number of failed tasks: {task_data['total_failed']}")
        if financial_data['net'] < 0:
            concerns.append(f"Negative net financial position: ${financial_data['net']:.2f}")
        if task_data.get('pending_count', 0) > 10:
            concerns.append(f"Large pending approval queue: {task_data.get('pending_count', 0)} tasks")
        
        return highlights, concerns
    
    async def _generate_recommendations(
        self,
        task_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        activity_data: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on data"""
        recommendations = []
        
        if task_data['total_failed'] > 0:
            recommendations.append("Review and analyze failed tasks to identify patterns")
        
        if task_data.get('pending_count', 0) > 5:
            recommendations.append("Clear pending approval queue to unblock automated workflows")
        
        if financial_data['invoices_created'] == 0 and financial_data['total_revenue'] == 0:
            recommendations.append("Review invoicing processes to ensure revenue capture")
        
        # Find top agent
        if activity_data['by_agent']:
            top_agent = max(activity_data['by_agent'].items(), key=lambda x: x[1])
            recommendations.append(f"Consider scaling {top_agent[0]} capacity (highest activity: {top_agent[1]} actions)")
        
        if not recommendations:
            recommendations.append("System operating normally - continue monitoring")
        
        return recommendations
    
    async def _generate_next_week_priorities(
        self,
        task_data: Dict[str, Any],
        highlights: List[str],
        concerns: List[str]
    ) -> List[str]:
        """Generate next week priorities"""
        priorities = []
        
        # Address concerns first
        if concerns:
            priorities.append(f"Address {len(concerns)} identified concern(s)")
        
        # Continue successes
        if highlights:
            priorities.append("Maintain current performance levels")
        
        # Standard priorities
        priorities.append("Monitor task completion rates")
        priorities.append("Review and optimize agent performance")
        
        return priorities[:5]  # Limit to 5 priorities
    
    def _generate_markdown_briefing(self, briefing: WeeklyBriefing) -> str:
        """Generate Markdown format briefing"""
        md = f"""# Weekly Executive Briefing
## {self.company_name}

**Period**: {briefing.period_start} to {briefing.period_end}  
**Generated**: {briefing.generated_at}  
**Prepared for**: {self.ceo_name}

---

## Executive Summary

{briefing.executive_summary}

---

## Key Performance Indicators

{self._format_kpis_markdown(briefing.kpis)}

---

## Highlights This Week

{chr(10).join(f"✅ {h}" for h in briefing.highlights)}

---

## Areas of Concern

{chr(10).join(f"⚠️ {c}" for c in briefing.concerns) if briefing.concerns else "*No concerns identified*"}

---

## Detailed Sections

{chr(10).join(self._format_section_markdown(s) for s in briefing.sections)}

---

## Recommendations

{chr(10).join(f"• {r}" for r in briefing.recommendations)}

---

## Next Week's Priorities

{chr(10).join(f"{i+1}. {p}" for i, p in enumerate(briefing.next_week_priorities))}

---

*Briefing generated by Platinum Tier CEO Briefing Generator v{self.version}*
"""
        return md
    
    def _format_kpis_markdown(self, kpis: Dict[str, Any]) -> str:
        """Format KPIs as markdown table"""
        lines = ["| KPI | Value |", "|-----|-------|"]
        for key, value in kpis.items():
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, float):
                formatted_value = f"{value:.2f}" if 'revenue' in key.lower() or 'expense' in key.lower() else f"{value:.1f}%"
            else:
                formatted_value = str(value)
            lines.append(f"| {formatted_key} | {formatted_value} |")
        return '\n'.join(lines)
    
    def _format_section_markdown(self, section: BriefingSection) -> str:
        """Format a single section as markdown"""
        md = f"### {section.title}\n\n"
        md += section.content
        if section.action_items:
            md += "\n\n#### Action Items\n"
            for item in section.action_items:
                md += f"- [ ] {item}\n"
        return md
    
    def _generate_html_briefing(self, briefing: WeeklyBriefing) -> str:
        """Generate HTML format briefing"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Weekly Executive Briefing - {self.company_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
        h2 {{ color: #34495e; }}
        h3 {{ color: #7f8c8d; }}
        .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; }}
        .kpi {{ display: inline-block; background: #3498db; color: white; padding: 15px; margin: 5px; border-radius: 5px; }}
        .highlight {{ color: #27ae60; }}
        .concern {{ color: #e74c3c; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>Weekly Executive Briefing</h1>
    <p><strong>{self.company_name}</strong></p>
    <p>Period: {briefing.period_start} to {briefing.period_end}</p>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        {briefing.executive_summary.replace(chr(10), '<br>')}
    </div>
    
    <h2>Key Metrics</h2>
    {self._format_kpis_html(briefing.kpis)}
    
    <h2>Highlights</h2>
    <ul class="highlight">
        {''.join(f'<li>✅ {h}</li>' for h in briefing.highlights)}
    </ul>
    
    <h2>Concerns</h2>
    <ul class="concern">
        {''.join(f'<li>⚠️ {c}</li>' for c in briefing.concerns) if briefing.concerns else '<li><em>No concerns identified</em></li>'}
    </ul>
    
    <h2>Sections</h2>
    {chr(10).join(self._format_section_html(s) for s in briefing.sections)}
    
    <div class="footer">
        Generated by Platinum Tier CEO Briefing Generator v{self.version}
    </div>
</body>
</html>"""
        return html
    
    def _format_kpis_html(self, kpis: Dict[str, Any]) -> str:
        """Format KPIs as HTML"""
        html = '<div>'
        for key, value in kpis.items():
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, float):
                formatted_value = f"{value:.2f}" if 'revenue' in key.lower() else f"{value:.1f}%"
            else:
                formatted_value = str(value)
            html += f'<div class="kpi"><strong>{formatted_key}</strong><br>{formatted_value}</div>'
        html += '</div>'
        return html
    
    def _format_section_html(self, section: BriefingSection) -> str:
        """Format a section as HTML"""
        html = f"<h3>{section.title}</h3>"
        html += section.content.replace('\n', '<br>')
        if section.action_items:
            html += "<h4>Action Items</h4><ul>"
            for item in section.action_items:
                html += f"<li>{item}</li>"
            html += "</ul>"
        return html
    
    async def _save_briefing(self, briefing: WeeklyBriefing) -> Dict[str, str]:
        """Save briefing in multiple formats"""
        paths = {}
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"CEO_Briefing_{timestamp}"
        
        # Markdown
        md_content = self._generate_markdown_briefing(briefing)
        md_path = self.briefings_dir / f"{base_filename}.md"
        if not self.dry_run:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Markdown briefing saved: {md_path}")
        paths['markdown'] = str(md_path)
        
        # HTML
        html_content = self._generate_html_briefing(briefing)
        html_path = self.briefings_dir / f"{base_filename}.html"
        if not self.dry_run:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML briefing saved: {html_path}")
        paths['html'] = str(html_path)
        
        # JSON
        json_path = self.briefings_dir / f"{base_filename}.json"
        if not self.dry_run:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(briefing), f, indent=2)
            logger.info(f"JSON briefing saved: {json_path}")
        paths['json'] = str(json_path)
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would save briefing to: {self.briefings_dir / base_filename}.*")
        
        return paths
    
    async def generate_briefing(self) -> WeeklyBriefing:
        """Generate complete weekly briefing"""
        logger.info("Starting briefing generation...")
        
        # Get period dates
        period_start, period_end = self._get_period_dates()
        
        # Collect data from all sources
        logger.info("Collecting task data...")
        task_data = await self._collect_task_data(period_start, period_end)
        
        logger.info("Collecting financial data...")
        financial_data = await self._collect_financial_data(period_start, period_end)
        
        logger.info("Collecting activity data...")
        activity_data = await self._collect_activity_data(period_start, period_end)
        
        # Generate executive summary
        logger.info("Generating executive summary...")
        executive_summary = await self._generate_executive_summary(task_data, financial_data, activity_data)
        
        # Generate sections
        logger.info("Generating briefing sections...")
        sections = await self._generate_sections(task_data, financial_data, activity_data)
        
        # Generate highlights and concerns
        logger.info("Analyzing highlights and concerns...")
        highlights, concerns = await self._generate_highlights_and_concerns(task_data, financial_data, activity_data)
        
        # Generate recommendations
        logger.info("Generating recommendations...")
        recommendations = await self._generate_recommendations(task_data, financial_data, activity_data)
        
        # Generate next week priorities
        logger.info("Setting next week priorities...")
        next_week_priorities = await self._generate_next_week_priorities(task_data, highlights, concerns)
        
        # Compile KPIs
        kpis = {
            'tasks_completed': task_data['total_completed'],
            'tasks_failed': task_data['total_failed'],
            'success_rate': task_data['success_rate'],
            'revenue': financial_data['total_revenue'],
            'expenses': financial_data['total_expenses'],
            'net_income': financial_data['net'],
            'total_actions': activity_data['total_actions'],
            'pending_approvals': task_data.get('pending_count', 0)
        }
        
        # Create briefing
        briefing = WeeklyBriefing(
            briefing_id=f"briefing_{int(time.time())}",
            period_start=period_start.strftime('%Y-%m-%d'),
            period_end=period_end.strftime('%Y-%m-%d'),
            generated_at=datetime.now().isoformat(),
            executive_summary=executive_summary,
            sections=sections,
            kpis=kpis,
            highlights=highlights,
            concerns=concerns,
            recommendations=recommendations,
            next_week_priorities=next_week_priorities,
            metadata={
                'company': self.company_name,
                'prepared_for': self.ceo_name,
                'generator_version': self.version,
                'data_sources': list(self.data_sources.keys()),
                'claude_enabled': self.claude_enabled
            },
            formats={}
        )
        
        # Save briefing
        logger.info("Saving briefing...")
        briefing.formats = await self._save_briefing(briefing)
        
        self.stats['briefings_generated'] += 1
        
        logger.info(f"Briefing generated successfully: {briefing.briefing_id}")
        return briefing
    
    async def run_scheduled(self):
        """Run briefing generation on schedule"""
        logger.info(f"Starting scheduled briefing generation ({self.briefing_day} at {self.briefing_time})")
        
        while True:
            try:
                now = datetime.now()
                
                # Check if it's briefing day and time
                day_match = now.strftime('%A').lower() == self.briefing_day
                time_match = now.strftime('%H:%M') == self.briefing_time
                
                if day_match and time_match:
                    logger.info("Scheduled briefing time reached!")
                    await self.generate_briefing()
                    # Wait an hour to avoid duplicate runs
                    await asyncio.sleep(3600)
                else:
                    # Check every 30 minutes
                    await asyncio.sleep(1800)
            
            except Exception as e:
                logger.error(f"Scheduled briefing error: {str(e)}")
                await asyncio.sleep(1800)
    
    def get_status(self) -> Dict[str, Any]:
        """Get generator status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        
        return {
            'version': self.version,
            'status': 'running',
            'uptime': str(uptime),
            'dry_run': self.dry_run,
            'claude_enabled': self.claude_enabled,
            'schedule': f"{self.briefing_day} at {self.briefing_time}",
            'statistics': self.stats,
            'timestamp': datetime.now().isoformat()
        }
    
    async def run(self):
        """Main entry point"""
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     📊  PLATINUM TIER CEO BRIEFING GENERATOR  📊         ║
║                                                           ║
║     Version: {self.version}
║     DRY_RUN: {self.dry_run}
║     Claude AI: {self.claude_enabled}
║     Schedule: {self.briefing_day} at {self.briefing_time}
║                                                           ║
║     SECURITY CONSTRAINTS:                                 ║
║     ✓ Cloud READS data only                              ║
║     ✗ Cloud NEVER executes actions                       ║
║     ✓ Generates briefing documents                       ║
║     ✓ Local system handles distribution                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"CEO Briefing Generator starting v{self.version}")
        
        try:
            await self._init_session()
            
            # Generate one briefing immediately
            briefing = await self.generate_briefing()
            
            print(f"\n📊 Briefing Generated Successfully!")
            print(f"   Period: {briefing.period_start} to {briefing.period_end}")
            print(f"   Formats: {', '.join(briefing.formats.keys())}")
            print(f"   Location: {self.briefings_dir}")
            
            # Continue with scheduled generation
            await self.run_scheduled()
        
        except KeyboardInterrupt:
            logger.info("CEO Briefing Generator stopped by user")
            print("\n🛑 CEO Briefing Generator stopped.")
        
        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
        
        finally:
            await self._close_session()
            
            # Final statistics
            print(f"\n📊 Final Statistics:")
            print(f"   Briefings Generated: {self.stats['briefings_generated']}")
            print(f"   Data Points Processed: {self.stats['data_points_processed']}")
            print(f"   Errors: {self.stats['errors']}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier CEO Briefing Generator')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--once', action='store_true', help='Generate once and exit')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    args = parser.parse_args()
    
    generator = CEOBriefingGenerator()
    
    if args.status:
        status = generator.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.dry_run:
        generator.dry_run = True
    
    if args.once:
        await generator._init_session()
        await generator.generate_briefing()
        await generator._close_session()
    else:
        await generator.run()


if __name__ == "__main__":
    asyncio.run(main())
