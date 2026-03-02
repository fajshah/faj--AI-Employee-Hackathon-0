"""
Platinum Tier Audit Logger
===========================
Cryptographic audit logging system for Human-in-the-Loop enforcement

Features:
- Hash-signed audit entries
- Tamper detection
- Time-stamped logs
- Merkle tree integrity verification
- Production-level structure
- Immutable audit trail
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
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.platinum')

# Configure logging
class AuditLoggerLogger:
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


logger_wrapper = AuditLoggerLogger(
    name='audit_logger',
    log_file='Logs/audit_logger.log'
)
logger = logger_wrapper.get_logger()


@dataclass
class AuditEntry:
    """Single audit log entry"""
    entry_id: str
    timestamp: str
    event_type: str  # approval, execution, validation, error
    actor: str  # Who performed the action
    action: str  # What action was performed
    target: str  # What was acted upon
    result: str  # success, failure, blocked
    details: Dict[str, Any] = field(default_factory=dict)
    previous_hash: str = ""
    entry_hash: str = ""
    signature: str = ""


@dataclass
class AuditChain:
    """Audit chain with integrity verification"""
    chain_id: str
    created_at: str
    entries: List[AuditEntry] = field(default_factory=list)
    merkle_root: str = ""
    total_entries: int = 0


class AuditLogger:
    """
    Platinum Tier Audit Logger
    
    Responsibilities:
    - Create hash-signed audit entries
    - Maintain immutable audit chain
    - Detect tampering with hash verification
    - Generate Merkle tree for integrity
    - Provide audit trail for compliance
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-Audit-Logger"
        
        # Configuration
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.enable_signatures = os.getenv('ENABLE_AUDIT_SIGNATURES', 'true').lower() == 'true'
        self.enable_merkle_tree = os.getenv('ENABLE_MERKLE_TREE', 'true').lower() == 'true'
        self.retention_days = int(os.getenv('AUDIT_RETENTION_DAYS', '365'))
        
        # Directories
        self.base_dir = Path(os.getenv('CLOUD_BASE_DIR', '.'))
        self.audit_dir = self.base_dir / 'Audit'
        self.logs_dir = self.base_dir / 'Logs'
        self.chains_dir = self.audit_dir / 'chains'
        
        self._create_directories()
        
        # Secret key for signatures
        self.secret_key = os.getenv('AUDIT_SECRET_KEY', 'change-this-in-production')
        
        # Current audit chain
        self.current_chain: Optional[AuditChain] = None
        self.entry_hashes: List[str] = []
        
        # Statistics
        self.stats = {
            'entries_logged': 0,
            'chains_created': 0,
            'tampering_detected': 0,
            'verifications_performed': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Load or create chain
        self._load_or_create_chain()
        
        logger.info(f"Audit Logger initialized v{self.version}")
        logger.info(f"Signatures enabled: {self.enable_signatures}")
        logger.info(f"Merkle tree enabled: {self.enable_merkle_tree}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [self.audit_dir, self.logs_dir, self.chains_dir]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory verified: {dir_path}")
    
    def _generate_entry_id(self) -> str:
        """Generate unique entry ID"""
        return f"audit_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
    
    def _compute_entry_hash(self, entry: AuditEntry) -> str:
        """
        Compute SHA-256 hash of audit entry
        
        Args:
            entry: Audit entry
        
        Returns:
            SHA-256 hex digest
        """
        # Create deterministic content (excluding hash fields)
        content = {
            'entry_id': entry.entry_id,
            'timestamp': entry.timestamp,
            'event_type': entry.event_type,
            'actor': entry.actor,
            'action': entry.action,
            'target': entry.target,
            'result': entry.result,
            'details': entry.details,
            'previous_hash': entry.previous_hash
        }
        
        content_str = json.dumps(content, sort_keys=True, separators=(',', ':'))
        entry_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        
        return entry_hash
    
    def _generate_signature(self, entry: AuditEntry) -> str:
        """
        Generate HMAC signature for audit entry
        
        Args:
            entry: Audit entry
        
        Returns:
            HMAC-SHA256 signature (hex)
        """
        sig_data = {
            'entry_id': entry.entry_id,
            'timestamp': entry.timestamp,
            'event_type': entry.event_type,
            'actor': entry.actor,
            'action': entry.action,
            'target': entry.target,
            'result': entry.result,
            'entry_hash': entry.entry_hash
        }
        sig_str = json.dumps(sig_data, sort_keys=True, separators=(',', ':'))
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            sig_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _compute_merkle_root(self, hashes: List[str]) -> str:
        """
        Compute Merkle tree root from list of hashes
        
        Args:
            hashes: List of entry hashes
        
        Returns:
            Merkle root hash
        """
        if not hashes:
            return hashlib.sha256(b'empty').hexdigest()
        
        # If odd number of hashes, duplicate last
        current_level = hashes.copy()
        if len(current_level) % 2 == 1:
            current_level.append(current_level[-1])
        
        # Build tree bottom-up
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i + 1]
                parent_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
                next_level.append(parent_hash)
            
            current_level = next_level
            if len(current_level) % 2 == 1 and len(current_level) > 1:
                current_level.append(current_level[-1])
        
        return current_level[0] if current_level else ""
    
    def _load_or_create_chain(self):
        """Load existing chain or create new one"""
        # Find latest chain file
        chain_files = sorted(self.chains_dir.glob('chain_*.json'))
        
        if chain_files:
            # Load latest chain
            latest_chain = chain_files[-1]
            try:
                with open(latest_chain, 'r', encoding='utf-8') as f:
                    chain_data = json.load(f)
                
                self.current_chain = AuditChain(
                    chain_id=chain_data['chain_id'],
                    created_at=chain_data['created_at'],
                    entries=[AuditEntry(**e) for e in chain_data.get('entries', [])],
                    merkle_root=chain_data.get('merkle_root', ''),
                    total_entries=chain_data.get('total_entries', 0)
                )
                
                # Rebuild entry hashes
                self.entry_hashes = [e.entry_hash for e in self.current_chain.entries]
                
                logger.info(f"Loaded existing chain: {self.current_chain.chain_id}")
                logger.info(f"Chain entries: {len(self.current_chain.entries)}")
            
            except Exception as e:
                logger.error(f"Failed to load chain: {str(e)}")
                self._create_new_chain()
        else:
            self._create_new_chain()
    
    def _create_new_chain(self):
        """Create new audit chain"""
        chain_id = f"chain_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
        self.current_chain = AuditChain(
            chain_id=chain_id,
            created_at=datetime.now().isoformat(),
            entries=[],
            merkle_root="",
            total_entries=0
        )
        
        self.entry_hashes = []
        self.stats['chains_created'] += 1
        
        logger.info(f"Created new audit chain: {chain_id}")
    
    def log(self, event_type: str, actor: str, action: str, target: str,
            result: str, details: Dict[str, Any] = None) -> AuditEntry:
        """
        Log an audit entry
        
        Args:
            event_type: Type of event (approval, execution, validation, error)
            actor: Who performed the action
            action: What action was performed
            target: What was acted upon
            result: success, failure, blocked
            details: Additional details
        
        Returns:
            AuditEntry object
        """
        logger.debug(f"Logging {event_type}: {action} by {actor}")
        
        # Create entry
        entry_id = self._generate_entry_id()
        timestamp = datetime.now().isoformat()
        
        # Get previous hash
        previous_hash = self.entry_hashes[-1] if self.entry_hashes else "genesis"
        
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            event_type=event_type,
            actor=actor,
            action=action,
            target=target,
            result=result,
            details=details or {},
            previous_hash=previous_hash
        )
        
        # Compute entry hash
        entry.entry_hash = self._compute_entry_hash(entry)
        
        # Generate signature
        if self.enable_signatures:
            entry.signature = self._generate_signature(entry)
        
        # Add to chain
        if self.current_chain:
            self.current_chain.entries.append(entry)
            self.current_chain.total_entries += 1
        
        self.entry_hashes.append(entry.entry_hash)
        self.stats['entries_logged'] += 1
        
        # Update Merkle root
        if self.enable_merkle_tree:
            self.current_chain.merkle_root = self._compute_merkle_root(self.entry_hashes)
        
        # Save entry immediately (append to chain file)
        if not self.dry_run:
            self._save_entry(entry)
        
        logger.debug(f"Audit entry logged: {entry_id}")
        return entry
    
    def _save_entry(self, entry: AuditEntry):
        """Save single entry to chain file"""
        chain_file = self.chains_dir / f"{self.current_chain.chain_id}.json"
        
        # Load existing or create new
        if chain_file.exists():
            with open(chain_file, 'r', encoding='utf-8') as f:
                chain_data = json.load(f)
        else:
            chain_data = {
                'chain_id': self.current_chain.chain_id,
                'created_at': self.current_chain.created_at,
                'entries': [],
                'merkle_root': '',
                'total_entries': 0
            }
        
        # Add entry
        chain_data['entries'].append(asdict(entry))
        chain_data['total_entries'] = len(chain_data['entries'])
        chain_data['merkle_root'] = self.current_chain.merkle_root
        
        # Save
        with open(chain_file, 'w', encoding='utf-8') as f:
            json.dump(chain_data, f, indent=2)
    
    def verify_chain_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify audit chain integrity
        
        Returns:
            (is_valid, list of errors)
        """
        logger.info("Verifying audit chain integrity...")
        
        errors = []
        self.stats['verifications_performed'] += 1
        
        if not self.current_chain or not self.current_chain.entries:
            return True, []
        
        # Verify hash chain
        previous_hash = "genesis"
        for i, entry in enumerate(self.current_chain.entries):
            # Verify previous hash linkage
            if entry.previous_hash != previous_hash:
                errors.append(f"Entry {i}: Hash chain broken at {entry.entry_id}")
                self.stats['tampering_detected'] += 1
            
            # Verify entry hash
            computed_hash = self._compute_entry_hash(entry)
            if computed_hash != entry.entry_hash:
                errors.append(f"Entry {i}: Hash mismatch at {entry.entry_id}")
                self.stats['tampering_detected'] += 1
            
            # Verify signature
            if self.enable_signatures and entry.signature:
                expected_sig = self._generate_signature(entry)
                if not hmac.compare_digest(expected_sig, entry.signature):
                    errors.append(f"Entry {i}: Signature invalid at {entry.entry_id}")
                    self.stats['tampering_detected'] += 1
            
            previous_hash = entry.entry_hash
        
        # Verify Merkle root
        if self.enable_merkle_tree:
            computed_root = self._compute_merkle_root(self.entry_hashes)
            if computed_root != self.current_chain.merkle_root:
                errors.append(f"Merkle root mismatch: expected {self.current_chain.merkle_root}, got {computed_root}")
                self.stats['tampering_detected'] += 1
        
        if errors:
            logger.error(f"Chain integrity verification FAILED: {len(errors)} errors")
            for error in errors[:5]:  # Log first 5 errors
                logger.error(f"  - {error}")
        else:
            logger.info("Chain integrity verification PASSED")
        
        return len(errors) == 0, errors
    
    def log_approval(self, approval_id: str, approver: str, target: str,
                    result: str, details: Dict[str, Any] = None) -> AuditEntry:
        """Log approval event"""
        return self.log(
            event_type='approval',
            actor=approver,
            action='approve',
            target=target,
            result=result,
            details=details or {'approval_id': approval_id}
        )
    
    def log_execution(self, execution_id: str, executor: str, target: str,
                     action_type: str, result: str, details: Dict[str, Any] = None) -> AuditEntry:
        """Log execution event"""
        return self.log(
            event_type='execution',
            actor=executor,
            action=f'execute_{action_type}',
            target=target,
            result=result,
            details=details or {'execution_id': execution_id}
        )
    
    def log_validation(self, validation_id: str, validator: str, target: str,
                      result: str, details: Dict[str, Any] = None) -> AuditEntry:
        """Log validation event"""
        return self.log(
            event_type='validation',
            actor=validator,
            action='validate',
            target=target,
            result=result,
            details=details or {'validation_id': validation_id}
        )
    
    def log_error(self, error_id: str, actor: str, target: str,
                  error_message: str, details: Dict[str, Any] = None) -> AuditEntry:
        """Log error event"""
        return self.log(
            event_type='error',
            actor=actor,
            action='error',
            target=target,
            result='failure',
            details=details or {'error_id': error_id, 'error_message': error_message}
        )
    
    def get_audit_trail(self, start_date: str = None, end_date: str = None,
                       event_type: str = None, actor: str = None) -> List[AuditEntry]:
        """
        Get filtered audit trail
        
        Args:
            start_date: ISO format start date
            end_date: ISO format end date
            event_type: Filter by event type
            actor: Filter by actor
        
        Returns:
            List of matching AuditEntry objects
        """
        if not self.current_chain:
            return []
        
        results = []
        
        for entry in self.current_chain.entries:
            # Filter by date
            if start_date and entry.timestamp < start_date:
                continue
            if end_date and entry.timestamp > end_date:
                continue
            
            # Filter by event type
            if event_type and entry.event_type != event_type:
                continue
            
            # Filter by actor
            if actor and entry.actor != actor:
                continue
            
            results.append(entry)
        
        return results
    
    def export_audit_trail(self, output_path: Path = None) -> str:
        """
        Export complete audit trail
        
        Args:
            output_path: Output file path
        
        Returns:
            Path to exported file
        """
        if not output_path:
            output_path = self.audit_dir / f"audit_export_{int(time.time())}.json"
        
        export_data = {
            'chain_id': self.current_chain.chain_id if self.current_chain else 'none',
            'exported_at': datetime.now().isoformat(),
            'total_entries': self.current_chain.total_entries if self.current_chain else 0,
            'merkle_root': self.current_chain.merkle_root if self.current_chain else '',
            'entries': [asdict(e) for e in self.current_chain.entries] if self.current_chain else []
        }
        
        if not self.dry_run:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
        
        logger.info(f"Audit trail exported: {output_path}")
        return str(output_path)
    
    def get_status(self) -> Dict[str, Any]:
        """Get logger status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        
        return {
            'version': self.version,
            'status': 'running',
            'uptime': str(uptime),
            'dry_run': self.dry_run,
            'signatures_enabled': self.enable_signatures,
            'merkle_tree_enabled': self.enable_merkle_tree,
            'current_chain': self.current_chain.chain_id if self.current_chain else 'none',
            'statistics': self.stats,
            'timestamp': datetime.now().isoformat()
        }


async def main():
    """Main entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Audit Logger')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    parser.add_argument('--verify', action='store_true', help='Verify chain integrity')
    parser.add_argument('--export', action='store_true', help='Export audit trail')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    args = parser.parse_args()
    
    logger_obj = AuditLogger()
    
    if args.status:
        status = logger_obj.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.verify:
        is_valid, errors = logger_obj.verify_chain_integrity()
        print(f"Chain Integrity: {'VALID' if is_valid else 'INVALID'}")
        if errors:
            print(f"Errors ({len(errors)}):")
            for error in errors[:10]:
                print(f"  - {error}")
        return
    
    if args.export:
        path = logger_obj.export_audit_trail()
        print(f"Audit trail exported: {path}")
        return
    
    if args.dry_run:
        logger_obj.dry_run = True
    
    # Demo mode
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🔐  PLATINUM TIER AUDIT LOGGER  🔐                   ║
║                                                           ║
║     Version: {logger_obj.version}
║     Signatures: {logger_obj.enable_signatures}
║     Merkle Tree: {logger_obj.enable_merkle_tree}
║                                                           ║
║     FEATURES:                                             ║
║     ✓ Hash-signed audit entries                          ║
║     ✓ Immutable audit chain                              ║
║     ✓ Tamper detection                                   ║
║     ✓ Merkle tree integrity                              ║
║     ✓ Time-stamped logs                                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Demo: Log some entries
    print("\n📝 Logging demo entries...")
    
    logger_obj.log_approval(
        approval_id="approval_001",
        approver="admin@company.com",
        target="invoice_123",
        result="success",
        details={'amount': 5000.00}
    )
    
    logger_obj.log_execution(
        execution_id="exec_001",
        executor="system",
        target="invoice_123",
        action_type="invoice_post",
        result="success"
    )
    
    logger_obj.log_validation(
        validation_id="val_001",
        validator="approval_validator",
        target="approval_001",
        result="success"
    )
    
    # Show status
    status = logger_obj.get_status()
    print(f"\n📊 Logger Status:")
    print(f"   Entries Logged: {status['statistics']['entries_logged']}")
    print(f"   Chains Created: {status['statistics']['chains_created']}")
    print(f"   Verifications: {status['statistics']['verifications_performed']}")
    
    # Verify integrity
    print("\n🔒 Verifying chain integrity...")
    is_valid, errors = logger_obj.verify_chain_integrity()
    print(f"   Integrity: {'✓ VALID' if is_valid else '✗ INVALID'}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
