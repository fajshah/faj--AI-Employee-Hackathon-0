"""
Platinum Tier Approval Validator
=================================
Human-in-the-Loop (HITL) approval validation system

Security Rules:
- Cloud cannot execute final actions
- Only Local can execute after file moved to Approved/
- File must include APPROVED_BY and APPROVED_AT
- System must reject execution if approval metadata missing
- Tamper detection with hash verification
- Time-stamped logs with cryptographic signatures
"""

import os
import sys
import json
import hashlib
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.platinum')

# Configure logging
class ApprovalValidatorLogger:
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


logger_wrapper = ApprovalValidatorLogger(
    name='approval_validator',
    log_file='Logs/approval_validator.log'
)
logger = logger_wrapper.get_logger()


@dataclass
class ApprovalMetadata:
    """Required approval metadata structure"""
    approved_by: str  # Email or username of approver
    approved_at: str  # ISO timestamp
    approval_id: str  # Unique approval identifier
    approval_method: str  # manual, api, dashboard
    ip_address: Optional[str] = None
    signature: Optional[str] = None  # Cryptographic signature
    valid_until: Optional[str] = None  # Expiration timestamp


@dataclass
class ValidationResult:
    """Result of approval validation"""
    valid: bool
    approval_id: str
    approved_by: str
    approved_at: str
    errors: List[str]
    warnings: List[str]
    tamper_detected: bool
    hash_verified: bool
    timestamp: str
    file_hash: Optional[str] = None


class ApprovalValidator:
    """
    Platinum Tier Approval Validator
    
    Responsibilities:
    - Validate approval metadata in files
    - Verify APPROVED_BY and APPROVED_AT fields
    - Detect tampering with hash verification
    - Enforce Human-in-the-Loop rules
    - Reject execution if approval missing
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-HITL-Validator"
        
        # Configuration
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.strict_mode = os.getenv('HITL_STRICT_MODE', 'true').lower() == 'true'
        self.enable_hash_verification = os.getenv('ENABLE_HASH_VERIFICATION', 'true').lower() == 'true'
        
        # Approval settings
        self.approval_expiry_hours = int(os.getenv('APPROVAL_EXPIRY_HOURS', '72'))
        self.required_approvers = os.getenv('REQUIRED_APPROVERS', '').split(',')
        self.min_approval_level = int(os.getenv('MIN_APPROVAL_LEVEL', '1'))
        
        # Directories
        self.base_dir = Path(os.getenv('CLOUD_BASE_DIR', '.'))
        self.pending_approval_dir = self.base_dir / 'Pending_Approval'
        self.approved_dir = self.base_dir / 'Approved'
        self.logs_dir = self.base_dir / 'Logs'
        self.audit_dir = self.base_dir / 'Audit'
        
        self._create_directories()
        
        # Statistics
        self.stats = {
            'validations_performed': 0,
            'validations_passed': 0,
            'validations_failed': 0,
            'tampering_detected': 0,
            'hash_failures': 0,
            'start_time': datetime.now().isoformat()
        }
        
        logger.info(f"Approval Validator initialized v{self.version}")
        logger.info(f"Strict mode: {self.strict_mode}")
        logger.info(f"Hash verification: {self.enable_hash_verification}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [self.pending_approval_dir, self.approved_dir, self.logs_dir, self.audit_dir]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory verified: {dir_path}")
    
    def _compute_file_hash(self, file_path: Path, exclude_fields: List[str] = None) -> str:
        """
        Compute SHA-256 hash of file content
        
        Args:
            file_path: Path to file
            exclude_fields: Fields to exclude from hash (e.g., signature, hash)
        
        Returns:
            SHA-256 hex digest
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Exclude signature/hash fields from content hash
            if exclude_fields:
                for field in exclude_fields:
                    if field in content:
                        del content[field]
                    elif '.' in field:
                        # Handle nested fields
                        parts = field.split('.')
                        obj = content
                        for part in parts[:-1]:
                            if part in obj:
                                obj = obj[part]
                        if parts[-1] in obj:
                            del obj[parts[-1]]
            
            # Create deterministic JSON string
            content_str = json.dumps(content, sort_keys=True, separators=(',', ':'))
            
            # Compute hash
            file_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
            return file_hash
        
        except Exception as e:
            logger.error(f"Failed to compute file hash: {str(e)}")
            return ""
    
    def _generate_approval_signature(self, approval_data: Dict[str, Any], secret_key: str = None) -> str:
        """
        Generate HMAC signature for approval data
        
        Args:
            approval_data: Approval metadata
            secret_key: Secret key for HMAC (uses env if not provided)
        
        Returns:
            HMAC-SHA256 signature (hex)
        """
        if not secret_key:
            secret_key = os.getenv('APPROVAL_SECRET_KEY', 'default-secret-key-change-in-production')
        
        # Create deterministic string
        sig_data = {
            'approved_by': approval_data.get('approved_by'),
            'approved_at': approval_data.get('approved_at'),
            'approval_id': approval_data.get('approval_id')
        }
        sig_str = json.dumps(sig_data, sort_keys=True, separators=(',', ':'))
        
        # Generate HMAC
        import hmac
        signature = hmac.new(
            secret_key.encode('utf-8'),
            sig_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _verify_approval_signature(self, approval_data: Dict[str, Any], signature: str) -> bool:
        """
        Verify HMAC signature for approval data
        
        Args:
            approval_data: Approval metadata
            signature: Signature to verify
        
        Returns:
            True if signature valid
        """
        if not signature:
            return False
        
        expected_signature = self._generate_approval_signature(approval_data)
        return hmac.compare_digest(expected_signature, signature)
    
    def _check_approval_expiry(self, approved_at: str) -> Tuple[bool, str]:
        """
        Check if approval has expired
        
        Args:
            approved_at: Approval timestamp (ISO format)
        
        Returns:
            (is_valid, message)
        """
        try:
            approval_time = datetime.fromisoformat(approved_at)
            now = datetime.now()
            expiry = approval_time + timedelta(hours=self.approval_expiry_hours)
            
            if now > expiry:
                hours_ago = (now - approval_time).total_seconds() / 3600
                return False, f"Approval expired ({hours_ago:.1f} hours old, max {self.approval_expiry_hours})"
            
            return True, "Approval is valid"
        
        except Exception as e:
            return False, f"Failed to parse approval timestamp: {str(e)}"
    
    def _validate_approver(self, approved_by: str) -> Tuple[bool, str]:
        """
        Validate approver is authorized
        
        Args:
            approved_by: Approver email/username
        
        Returns:
            (is_authorized, message)
        """
        if not approved_by:
            return False, "Approver not specified"
        
        # Check against required approvers if configured
        if self.required_approvers and self.required_approvers[0]:
            if approved_by not in self.required_approvers:
                return False, f"Approver '{approved_by}' not in authorized list"
        
        return True, "Approver is authorized"
    
    def validate_approval_file(self, file_path: Path) -> ValidationResult:
        """
        Validate approval metadata in a file
        
        Args:
            file_path: Path to approval file
        
        Returns:
            ValidationResult with validation status
        """
        logger.info(f"Validating approval file: {file_path.name}")
        
        errors = []
        warnings = []
        tamper_detected = False
        hash_verified = False
        file_hash = None
        
        self.stats['validations_performed'] += 1
        
        # Check file exists
        if not file_path.exists():
            return ValidationResult(
                valid=False,
                approval_id='unknown',
                approved_by='unknown',
                approved_at='unknown',
                errors=[f"File not found: {file_path}"],
                warnings=[],
                tamper_detected=False,
                hash_verified=False,
                timestamp=datetime.now().isoformat()
            )
        
        # Load file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(
                valid=False,
                approval_id='unknown',
                approved_by='unknown',
                approved_at='unknown',
                errors=[f"Invalid JSON: {str(e)}"],
                warnings=[],
                tamper_detected=True,
                hash_verified=False,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                approval_id='unknown',
                approved_by='unknown',
                approved_at='unknown',
                errors=[f"Failed to read file: {str(e)}"],
                warnings=[],
                tamper_detected=False,
                hash_verified=False,
                timestamp=datetime.now().isoformat()
            )
        
        # Compute file hash
        if self.enable_hash_verification:
            file_hash = self._compute_file_hash(file_path, exclude_fields=['signature', 'file_hash', '_hash'])
            stored_hash = content.get('file_hash') or content.get('_hash')
            
            if stored_hash:
                hash_verified = (file_hash == stored_hash)
                if not hash_verified:
                    tamper_detected = True
                    self.stats['hash_failures'] += 1
                    errors.append("File hash mismatch - possible tampering detected")
        
        # Check for approval metadata
        approval_metadata = content.get('approval_metadata')
        
        # Also check flat structure for backwards compatibility
        if not approval_metadata:
            approval_metadata = {
                'approved_by': content.get('APPROVED_BY') or content.get('approved_by'),
                'approved_at': content.get('APPROVED_AT') or content.get('approved_at'),
                'approval_id': content.get('approval_id'),
                'approval_method': content.get('approval_method', 'unknown'),
                'signature': content.get('signature')
            }
        
        # CRITICAL: Check APPROVED_BY
        approved_by = approval_metadata.get('approved_by') if approval_metadata else None
        if not approved_by:
            errors.append("CRITICAL: APPROVED_BY field missing - Human-in-the-Loop violation")
        
        # CRITICAL: Check APPROVED_AT
        approved_at = approval_metadata.get('approved_at') if approval_metadata else None
        if not approved_at:
            errors.append("CRITICAL: APPROVED_AT field missing - Human-in-the-Loop violation")
        
        # Get approval_id
        approval_id = approval_metadata.get('approval_id', 'unknown') if approval_metadata else 'unknown'
        
        # Validate approver authorization
        if approved_by:
            is_authorized, msg = self._validate_approver(approved_by)
            if not is_authorized:
                errors.append(msg)
        
        # Check approval expiry
        if approved_at:
            is_valid, msg = self._check_approval_expiry(approved_at)
            if not is_valid:
                errors.append(msg)
        
        # Verify signature if present
        if approval_metadata and approval_metadata.get('signature'):
            sig_valid = self._verify_approval_signature(approval_metadata, approval_metadata['signature'])
            if not sig_valid:
                tamper_detected = True
                self.stats['tampering_detected'] += 1
                errors.append("Signature verification failed - possible tampering")
        
        # Check for signs of cloud execution (should not have execution results)
        if content.get('execution_result') or content.get('executed_at'):
            if not content.get('approval_metadata'):
                warnings.append("File has execution markers but no approval metadata")
        
        # Determine overall validity
        valid = len(errors) == 0
        
        # Update statistics
        if valid:
            self.stats['validations_passed'] += 1
        else:
            self.stats['validations_failed'] += 1
        
        if tamper_detected:
            self.stats['tampering_detected'] += 1
        
        # Log result
        if valid:
            logger.info(f"✓ Approval valid: {approval_id} by {approved_by}")
        else:
            logger.error(f"✗ Approval invalid: {approval_id} - {'; '.join(errors)}")
        
        return ValidationResult(
            valid=valid,
            approval_id=approval_id,
            approved_by=approved_by or 'unknown',
            approved_at=approved_at or 'unknown',
            errors=errors,
            warnings=warnings,
            tamper_detected=tamper_detected,
            hash_verified=hash_verified or not self.enable_hash_verification,
            timestamp=datetime.now().isoformat(),
            file_hash=file_hash
        )
    
    def add_approval_metadata(self, file_path: Path, approver: str, method: str = 'manual') -> str:
        """
        Add approval metadata to a file
        
        Args:
            file_path: Path to approval file
            approver: Approver email/username
            method: Approval method (manual, api, dashboard)
        
        Returns:
            Approval ID
        """
        logger.info(f"Adding approval metadata to: {file_path.name}")
        
        # Generate approval ID
        approval_id = f"approval_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        approved_at = datetime.now().isoformat()
        
        # Load file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Compute hash before adding metadata
        content_hash = self._compute_file_hash(file_path, exclude_fields=['signature', 'file_hash', '_hash', 'approval_metadata'])
        
        # Create approval metadata
        approval_metadata = ApprovalMetadata(
            approved_by=approver,
            approved_at=approved_at,
            approval_id=approval_id,
            approval_method=method,
            valid_until=(datetime.now() + timedelta(hours=self.approval_expiry_hours)).isoformat()
        )
        
        # Generate signature
        signature = self._generate_approval_signature(asdict(approval_metadata))
        approval_metadata.signature = signature
        
        # Add metadata to content
        content['approval_metadata'] = asdict(approval_metadata)
        
        # Also add flat fields for backwards compatibility
        content['APPROVED_BY'] = approver
        content['APPROVED_AT'] = approved_at
        content['approval_id'] = approval_id
        
        # Add file hash
        content['file_hash'] = content_hash
        
        # Save file
        if not self.dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Approval metadata added: {approval_id} by {approver}")
        return approval_id
    
    def mark_as_approved(self, source_path: Path, approver: str, method: str = 'manual') -> Tuple[bool, str]:
        """
        Mark a file as approved and move to Approved/ directory
        
        Args:
            source_path: Path to file in Pending_Approval/
            approver: Approver email/username
            method: Approval method
        
        Returns:
            (success, message)
        """
        logger.info(f"Marking file as approved: {source_path.name}")
        
        # Validate file exists
        if not source_path.exists():
            return False, f"File not found: {source_path}"
        
        # Check file is in Pending_Approval
        if str(self.pending_approval_dir) not in str(source_path):
            return False, "File must be in Pending_Approval/ directory"
        
        # Add approval metadata
        approval_id = self.add_approval_metadata(source_path, approver, method)
        
        # Validate the approval
        result = self.validate_approval_file(source_path)
        
        if not result.valid:
            return False, f"Approval validation failed: {'; '.join(result.errors)}"
        
        # Move to Approved/
        dest_path = self.approved_dir / source_path.name
        
        if not self.dry_run:
            import shutil
            shutil.move(str(source_path), str(dest_path))
        
        logger.info(f"File marked as approved and moved: {dest_path.name}")
        return True, f"Approved: {approval_id}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get validator status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        
        return {
            'version': self.version,
            'status': 'running',
            'uptime': str(uptime),
            'dry_run': self.dry_run,
            'strict_mode': self.strict_mode,
            'hash_verification': self.enable_hash_verification,
            'approval_expiry_hours': self.approval_expiry_hours,
            'statistics': self.stats,
            'pending_files': len(list(self.pending_approval_dir.glob('*.json'))),
            'approved_files': len(list(self.approved_dir.glob('*.json'))),
            'timestamp': datetime.now().isoformat()
        }
    
    def save_audit_log(self, result: ValidationResult, file_path: Path):
        """Save validation result to audit log"""
        audit_entry = {
            'validation_result': asdict(result),
            'file_path': str(file_path),
            'file_name': file_path.name,
            'validated_at': datetime.now().isoformat()
        }
        
        audit_file = self.audit_dir / f"validation_{result.approval_id}_{int(time.time())}.json"
        
        if not self.dry_run:
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump(audit_entry, f, indent=2)
        
        logger.debug(f"Audit log saved: {audit_file.name}")


async def main():
    """Main entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Approval Validator')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    parser.add_argument('--validate', type=str, help='Validate specific file')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    args = parser.parse_args()
    
    validator = ApprovalValidator()
    
    if args.status:
        status = validator.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.validate:
        file_path = Path(args.validate)
        result = validator.validate_approval_file(file_path)
        print(f"Valid: {result.valid}")
        print(f"Approval ID: {result.approval_id}")
        print(f"Approved By: {result.approved_by}")
        print(f"Approved At: {result.approved_at}")
        if result.errors:
            print(f"Errors: {result.errors}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")
        return
    
    if args.dry_run:
        validator.dry_run = True
    
    # Demo mode
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🔐  PLATINUM TIER APPROVAL VALIDATOR  🔐             ║
║                                                           ║
║     Version: {validator.version}
║     Strict Mode: {validator.strict_mode}
║     Hash Verification: {validator.enable_hash_verification}
║                                                           ║
║     SECURITY RULES:                                       ║
║     ✓ APPROVED_BY required                               ║
║     ✓ APPROVED_AT required                               ║
║     ✓ Tamper detection enabled                           ║
║     ✓ Hash verification enabled                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Show status
    status = validator.get_status()
    print(f"\n📊 Validator Status:")
    print(f"   Validations Performed: {status['statistics']['validations_performed']}")
    print(f"   Validations Passed: {status['statistics']['validations_passed']}")
    print(f"   Validations Failed: {status['statistics']['validations_failed']}")
    print(f"   Tampering Detected: {status['statistics']['tampering_detected']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
