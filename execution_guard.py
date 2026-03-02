"""
Platinum Tier Execution Guard
==============================
Human-in-the-Loop (HITL) execution enforcement system

Security Rules:
- Cloud cannot execute final actions
- Only Local can execute after file moved to Approved/
- File must include APPROVED_BY and APPROVED_AT
- System must reject execution if approval metadata missing
- Tamper detection with hash verification
- All executions logged with cryptographic signatures
"""

import os
import sys
import json
import hashlib
import logging
import time
import hmac
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.platinum')

# Import validator
from approval_validator import ApprovalValidator, ValidationResult

# Configure logging
class ExecutionGuardLogger:
    """Dual logging: File + Console"""
    
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


logger_wrapper = ExecutionGuardLogger(
    name='execution_guard',
    log_file='Logs/execution_guard.log'
)
logger = logger_wrapper.get_logger()


@dataclass
class ExecutionRecord:
    """Execution audit record"""
    execution_id: str
    file_path: str
    file_name: str
    action_type: str
    approved_by: str
    approved_at: str
    approval_id: str
    executed_by: str
    executed_at: str
    validation_result: Dict[str, Any]
    hash_verified: bool
    signature: str
    status: str  # allowed, blocked, error
    error_message: Optional[str] = None


class ExecutionGuard:
    """
    Platinum Tier Execution Guard
    
    Responsibilities:
    - Guard all execution points
    - Validate approval before allowing execution
    - Block cloud-side execution attempts
    - Log all execution attempts with signatures
    - Enforce Human-in-the-Loop rules
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-HITL-Guard"
        
        # Configuration
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.strict_mode = os.getenv('HITL_STRICT_MODE', 'true').lower() == 'true'
        self.block_cloud_execution = os.getenv('BLOCK_CLOUD_EXECUTION', 'true').lower() == 'true'
        self.enable_signatures = os.getenv('ENABLE_EXECUTION_SIGNATURES', 'true').lower() == 'true'
        
        # Directories
        self.base_dir = Path(os.getenv('CLOUD_BASE_DIR', '.'))
        self.pending_approval_dir = self.base_dir / 'Pending_Approval'
        self.approved_dir = self.base_dir / 'Approved'
        self.done_dir = self.base_dir / 'Done'
        self.error_dir = self.base_dir / 'Error'
        self.logs_dir = self.base_dir / 'Logs'
        self.audit_dir = self.base_dir / 'Audit'
        
        self._create_directories()
        
        # Initialize validator
        self.validator = ApprovalValidator()
        
        # Execution tracking
        self.executions: List[ExecutionRecord] = []
        
        # Statistics
        self.stats = {
            'executions_attempted': 0,
            'executions_allowed': 0,
            'executions_blocked': 0,
            'cloud_blocks': 0,
            'approval_failures': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Secret key for signatures
        self.secret_key = os.getenv('EXECUTION_SECRET_KEY', 'change-this-in-production')
        
        logger.info(f"Execution Guard initialized v{self.version}")
        logger.info(f"Strict mode: {self.strict_mode}")
        logger.info(f"Block cloud execution: {self.block_cloud_execution}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [self.pending_approval_dir, self.approved_dir, self.done_dir, 
                self.error_dir, self.logs_dir, self.audit_dir]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory verified: {dir_path}")
    
    def _generate_execution_signature(self, record: ExecutionRecord) -> str:
        """
        Generate HMAC signature for execution record
        
        Args:
            record: Execution record
        
        Returns:
            HMAC-SHA256 signature (hex)
        """
        sig_data = {
            'execution_id': record.execution_id,
            'file_path': record.file_path,
            'action_type': record.action_type,
            'approved_by': record.approved_by,
            'executed_by': record.executed_by,
            'executed_at': record.executed_at
        }
        sig_str = json.dumps(sig_data, sort_keys=True, separators=(',', ':'))
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            sig_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _is_cloud_context(self) -> bool:
        """
        Detect if running in cloud context
        
        Returns:
            True if cloud context detected
        """
        # Check environment variables
        cloud_indicators = [
            os.getenv('CLOUD_ENV', '').lower() == 'true',
            os.getenv('AWS_EXECUTION_ENV') is not None,
            os.getenv('AZURE_FUNCTIONS_ENV') is not None,
            os.getenv('GCP_FUNCTION') is not None,
            os.getenv('CLOUD_RUN', '').lower() == 'true'
        ]
        
        return any(cloud_indicators)
    
    def _check_file_location(self, file_path: Path) -> Tuple[bool, str]:
        """
        Check if file is in correct directory for execution
        
        Args:
            file_path: Path to file
        
        Returns:
            (is_valid, message)
        """
        file_str = str(file_path)
        
        # File must be in Approved/ directory for execution
        if str(self.approved_dir) in file_str:
            return True, "File in Approved/ directory"
        
        # File in Pending_Approval/ - not yet approved
        if str(self.pending_approval_dir) in file_str:
            return False, "File in Pending_Approval/ - requires approval first"
        
        # File in Done/ - already executed
        if str(self.done_dir) in file_str:
            return False, "File already executed (in Done/)"
        
        # File in Error/ - previously failed
        if str(self.error_dir) in file_str:
            return False, "File in Error/ - previously failed execution"
        
        return False, f"File not in recognized directory: {file_path}"
    
    def guard_execution(self, file_path: Path, action_type: str, 
                       executor: str = 'system') -> Tuple[bool, str, Optional[ExecutionRecord]]:
        """
        Guard an execution attempt
        
        Args:
            file_path: Path to file being executed
            action_type: Type of action (invoice, email, post, etc.)
            executor: Executor identifier
        
        Returns:
            (allowed, message, execution_record)
        """
        logger.info(f"Guard check: {file_path.name} ({action_type})")
        
        self.stats['executions_attempted'] += 1
        
        # Generate execution ID
        execution_id = f"exec_{int(time.time())}_{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}"
        executed_at = datetime.now().isoformat()
        
        # Initialize execution record
        record = ExecutionRecord(
            execution_id=execution_id,
            file_path=str(file_path),
            file_name=file_path.name,
            action_type=action_type,
            approved_by='unknown',
            approved_at='unknown',
            approval_id='unknown',
            executed_by=executor,
            executed_at=executed_at,
            validation_result={},
            hash_verified=False,
            signature='',
            status='pending'
        )
        
        # CHECK 1: Cloud context detection
        if self.block_cloud_execution and self._is_cloud_context():
            record.status = 'blocked'
            record.error_message = "Cloud execution blocked by HITL policy"
            self.stats['cloud_blocks'] += 1
            self.stats['executions_blocked'] += 1
            
            logger.error(f"✗ BLOCKED: Cloud execution attempt for {file_path.name}")
            self._save_execution_record(record)
            self.executions.append(record)
            
            return False, "Cloud execution blocked by HITL policy", record
        
        # CHECK 2: File location
        location_valid, location_msg = self._check_file_location(file_path)
        if not location_valid:
            record.status = 'blocked'
            record.error_message = location_msg
            self.stats['executions_blocked'] += 1
            
            logger.error(f"✗ BLOCKED: {location_msg} for {file_path.name}")
            self._save_execution_record(record)
            self.executions.append(record)
            
            return False, location_msg, record
        
        # CHECK 3: File exists
        if not file_path.exists():
            record.status = 'error'
            record.error_message = f"File not found: {file_path}"
            self.stats['executions_blocked'] += 1
            
            logger.error(f"✗ ERROR: File not found: {file_path}")
            self._save_execution_record(record)
            self.executions.append(record)
            
            return False, f"File not found: {file_path}", record
        
        # CHECK 4: Validate approval metadata
        validation_result = self.validator.validate_approval_file(file_path)
        record.validation_result = asdict(validation_result)
        record.approved_by = validation_result.approved_by
        record.approved_at = validation_result.approved_at
        record.approval_id = validation_result.approval_id
        record.hash_verified = validation_result.hash_verified
        
        if not validation_result.valid:
            record.status = 'blocked'
            record.error_message = f"Approval validation failed: {'; '.join(validation_result.errors)}"
            self.stats['approval_failures'] += 1
            self.stats['executions_blocked'] += 1
            
            logger.error(f"✗ BLOCKED: Approval validation failed for {file_path.name}")
            logger.error(f"   Errors: {validation_result.errors}")
            self._save_execution_record(record)
            self.executions.append(record)
            
            return False, f"Approval validation failed: {'; '.join(validation_result.errors)}", record
        
        # CHECK 5: Strict mode - verify hash
        if self.strict_mode and not validation_result.hash_verified:
            record.status = 'blocked'
            record.error_message = "Hash verification failed in strict mode"
            self.stats['executions_blocked'] += 1
            
            logger.error(f"✗ BLOCKED: Hash verification failed for {file_path.name}")
            self._save_execution_record(record)
            self.executions.append(record)
            
            return False, "Hash verification failed", record
        
        # All checks passed - execution allowed
        record.status = 'allowed'
        record.signature = self._generate_execution_signature(record)
        self.stats['executions_allowed'] += 1
        
        logger.info(f"✓ ALLOWED: Execution approved for {file_path.name} by {validation_result.approved_by}")
        self._save_execution_record(record)
        self.executions.append(record)
        
        return True, f"Execution allowed (approval: {validation_result.approval_id})", record
    
    def _save_execution_record(self, record: ExecutionRecord):
        """Save execution record to audit log"""
        audit_entry = {
            'execution_record': asdict(record),
            'saved_at': datetime.now().isoformat()
        }
        
        audit_file = self.audit_dir / f"execution_{record.execution_id}.json"
        
        if not self.dry_run:
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump(audit_entry, f, indent=2)
        
        logger.debug(f"Execution record saved: {audit_file.name}")
    
    def execute_with_guard(self, file_path: Path, action_type: str,
                          execute_func: Callable, executor: str = 'system') -> Tuple[bool, Any]:
        """
        Execute a function with guard protection
        
        Args:
            file_path: Path to file
            action_type: Type of action
            execute_func: Function to execute
            executor: Executor identifier
        
        Returns:
            (success, result)
        """
        # Guard check
        allowed, message, record = self.guard_execution(file_path, action_type, executor)
        
        if not allowed:
            return False, message
        
        # Execute the function
        try:
            logger.info(f"Executing {action_type} for {file_path.name}")
            
            if self.dry_run:
                logger.info(f"[DRY_RUN] Would execute {action_type}")
                result = f"DRY_RUN: {action_type} would be executed"
            else:
                result = execute_func()
            
            logger.info(f"✓ Execution completed: {file_path.name}")
            return True, result
        
        except Exception as e:
            logger.error(f"✗ Execution failed: {str(e)}")
            return False, str(e)
    
    def guard_decorator(self, action_type: str, executor: str = 'system'):
        """
        Decorator for guarding functions
        
        Usage:
            @guard.guard_decorator('invoice_confirm', 'admin')
            def confirm_invoice(file_path):
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(file_path, *args, **kwargs):
                allowed, message, record = self.guard_execution(
                    Path(file_path), action_type, executor
                )
                
                if not allowed:
                    raise PermissionError(f"HITL Guard blocked execution: {message}")
                
                return func(file_path, *args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_status(self) -> Dict[str, Any]:
        """Get guard status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        
        return {
            'version': self.version,
            'status': 'running',
            'uptime': str(uptime),
            'dry_run': self.dry_run,
            'strict_mode': self.strict_mode,
            'block_cloud_execution': self.block_cloud_execution,
            'statistics': self.stats,
            'recent_executions': len(self.executions),
            'timestamp': datetime.now().isoformat()
        }
    
    def list_blocked_attempts(self, hours: int = 24) -> List[ExecutionRecord]:
        """List blocked execution attempts in last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        blocked = [
            e for e in self.executions
            if e.status in ['blocked', 'error']
            and datetime.fromisoformat(e.executed_at) > cutoff
        ]
        
        return blocked


async def main():
    """Main entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Execution Guard')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    parser.add_argument('--test', type=str, help='Test guard with file')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    args = parser.parse_args()
    
    guard = ExecutionGuard()
    
    if args.status:
        status = guard.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.test:
        file_path = Path(args.test)
        allowed, message, record = guard.guard_execution(file_path, 'test_action')
        print(f"Allowed: {allowed}")
        print(f"Message: {message}")
        if record:
            print(f"Execution ID: {record.execution_id}")
            print(f"Status: {record.status}")
        return
    
    if args.dry_run:
        guard.dry_run = True
    
    # Demo mode
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🔐  PLATINUM TIER EXECUTION GUARD  🔐                ║
║                                                           ║
║     Version: {guard.version}
║     Strict Mode: {guard.strict_mode}
║     Block Cloud: {guard.block_cloud_execution}
║                                                           ║
║     SECURITY RULES:                                       ║
║     ✓ Cloud execution blocked                            ║
║     ✓ Approval required before execution                 ║
║     ✓ File must be in Approved/ directory                ║
║     ✓ Hash verification enforced                         ║
║     ✓ All executions logged with signature               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Show status
    status = guard.get_status()
    print(f"\n📊 Guard Status:")
    print(f"   Executions Attempted: {status['statistics']['executions_attempted']}")
    print(f"   Executions Allowed: {status['statistics']['executions_allowed']}")
    print(f"   Executions Blocked: {status['statistics']['executions_blocked']}")
    print(f"   Cloud Blocks: {status['statistics']['cloud_blocks']}")
    print(f"   Approval Failures: {status['statistics']['approval_failures']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
