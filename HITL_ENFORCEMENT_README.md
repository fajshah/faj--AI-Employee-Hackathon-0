# 🔐 PLATINUM TIER HITL ENFORCEMENT SYSTEM
## Human-in-the-Loop Security & Enforcement

---

## 📖 OVERVIEW

The **Platinum Tier HITL (Human-in-the-Loop) Enforcement System** provides cryptographic security guarantees that:

1. **Cloud cannot execute final actions** - Only creates drafts
2. **Local executes after approval** - Only after human approval
3. **Approval metadata required** - APPROVED_BY and APPROVED_AT mandatory
4. **Tamper detection** - Hash verification on all files
5. **Audit trail** - Cryptographic logging of all actions

---

## 🔐 SECURITY RULES (ENFORCED)

### Rule 1: Cloud Execution Blocked
```
☁️ Cloud Components:
  ✅ CAN: Create drafts
  ✅ CAN: Write to Pending_Approval/
  ❌ CANNOT: Execute actions
  ❌ CANNOT: Move files to Approved/
```

### Rule 2: Local Execution After Approval
```
💻 Local Components:
  ✅ CAN: Execute from Approved/ only
  ✅ CAN: Move to Done/ after execution
  ❌ CANNOT: Execute from Pending_Approval/
  ❌ CANNOT: Execute without approval metadata
```

### Rule 3: Approval Metadata Required
```json
{
  "APPROVED_BY": "admin@company.com",    // REQUIRED
  "APPROVED_AT": "2025-02-26T10:30:00",  // REQUIRED
  "approval_id": "approval_1740585600",  // REQUIRED
  "approval_method": "manual",           // REQUIRED
  "signature": "hmac-sha256-..."         // CRYPTOGRAPHIC
}
```

### Rule 4: Execution Rejected If Missing
```
If APPROVED_BY or APPROVED_AT missing:
  → Execution BLOCKED
  → Error logged to Audit/
  → Alert generated
```

### Rule 5: All Executions Logged
```
Every execution logged with:
  - Unique execution ID
  - Timestamp
  - Actor (who executed)
  - Approver (who approved)
  - Hash signature
  - Previous hash (chain linkage)
```

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│ CLOUD SIDE (Cannot Execute)                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Create Draft → Write Pending_Approval/ → [SECURITY BOUNDARY]      │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ Approval Request File
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ HUMAN APPROVAL                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Review → Approve → Add APPROVED_BY + APPROVED_AT → Move to Approved/
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ Approved File (with metadata)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LOCAL SIDE (Execution Guard)                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. approval_validator.py validates metadata                        │
│  2. execution_guard.py checks approval before allowing              │
│  3. audit_logger.py logs execution with hash signature              │
│  4. Execute action → Move to Done/                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 QUICK START

### 1. Install Dependencies

```bash
pip install python-dotenv cryptography
```

### 2. Configure Environment

```bash
# Copy example
cp .env.platinum.example .env.platinum

# Edit with security settings
```

Required settings:
```bash
# HITL Enforcement
HITL_STRICT_MODE=true
BLOCK_CLOUD_EXECUTION=true
ENABLE_HASH_VERIFICATION=true
ENABLE_EXECUTION_SIGNATURES=true
ENABLE_AUDIT_SIGNATURES=true
ENABLE_MERKLE_TREE=true

# Security Keys (CHANGE IN PRODUCTION!)
APPROVAL_SECRET_KEY=change-this-to-secure-random-string
EXECUTION_SECRET_KEY=change-this-to-secure-random-string
AUDIT_SECRET_KEY=change-this-to-secure-random-string

# Approval Settings
APPROVAL_EXPIRY_HOURS=72
DEFAULT_APPROVER=admin@company.com
```

### 3. Test Components

```bash
# Test Approval Validator
python approval_validator.py --status

# Test Execution Guard
python execution_guard.py --status

# Test Audit Logger
python audit_logger.py --status
```

---

## 📁 FILE STRUCTURE

```
hackthone-0/
├── approval_validator.py         # Validate approval metadata
├── execution_guard.py            # Guard execution points
├── audit_logger.py               # Cryptographic audit logging
├── HITL_ENFORCEMENT_README.md    # This documentation
│
├── Pending_Approval/             # Awaiting approval
├── Approved/                     # Approved (ready for execution)
├── Done/                         # Executed successfully
├── Error/                        # Execution failed
│
├── Audit/
│   ├── chains/                   # Audit chain files
│   │   └── chain_*.json
│   ├── validation_*.json         # Validation records
│   ├── execution_*.json          # Execution records
│   └── audit_export_*.json       # Exported trails
│
└── Logs/
    ├── approval_validator.log
    ├── execution_guard.log
    └── audit_logger.log
```

---

## 💼 COMPONENT DETAILS

### 1. Approval Validator (`approval_validator.py`)

**Purpose**: Validate approval metadata in files

**Features**:
- ✅ Check APPROVED_BY field (required)
- ✅ Check APPROVED_AT field (required)
- ✅ Hash verification (tamper detection)
- ✅ Signature verification (HMAC-SHA256)
- ✅ Approval expiry checking
- ✅ Approver authorization validation
- ✅ Audit logging of all validations

**Usage**:
```python
from approval_validator import ApprovalValidator

validator = ApprovalValidator()

# Validate a file
from pathlib import Path
result = validator.validate_approval_file(
    Path("Approved/approval_invoice_123.json")
)

print(f"Valid: {result.valid}")
print(f"Approved By: {result.approved_by}")
print(f"Approved At: {result.approved_at}")
print(f"Hash Verified: {result.hash_verified}")
print(f"Tamper Detected: {result.tamper_detected}")

if result.errors:
    print(f"Errors: {result.errors}")
```

**Validation Result**:
```python
@dataclass
class ValidationResult:
    valid: bool              # Overall validity
    approval_id: str         # Approval identifier
    approved_by: str         # Who approved
    approved_at: str         # When approved
    errors: List[str]        # Validation errors
    warnings: List[str]      # Warnings
    tamper_detected: bool    # Tampering flag
    hash_verified: bool      # Hash check passed
    timestamp: str           # Validation time
    file_hash: str           # Computed file hash
```

---

### 2. Execution Guard (`execution_guard.py`)

**Purpose**: Guard all execution points

**Features**:
- ✅ Cloud context detection
- ✅ File location verification
- ✅ Approval validation before execution
- ✅ Hash verification in strict mode
- ✅ Execution blocking if invalid
- ✅ Cryptographic execution signatures
- ✅ Decorator for function protection

**Usage**:
```python
from execution_guard import ExecutionGuard

guard = ExecutionGuard()

# Guard an execution
from pathlib import Path
allowed, message, record = guard.guard_execution(
    file_path=Path("Approved/approval_invoice_123.json"),
    action_type="invoice_post",
    executor="admin@company.com"
)

if allowed:
    # Execute the action
    result = execute_invoice()
else:
    print(f"Execution blocked: {message}")
```

**Decorator Usage**:
```python
from execution_guard import ExecutionGuard

guard = ExecutionGuard()

@guard.guard_decorator('invoice_confirm', 'admin')
def confirm_invoice(file_path):
    # This function can only be called if:
    # 1. File is in Approved/
    # 2. Has valid approval metadata
    # 3. Not in cloud context
    ...
```

**Execution Record**:
```python
@dataclass
class ExecutionRecord:
    execution_id: str       # Unique execution ID
    file_path: str          # File being executed
    file_name: str          # File name
    action_type: str        # Type of action
    approved_by: str        # Who approved
    approved_at: str        # When approved
    approval_id: str        # Approval ID
    executed_by: str        # Who executed
    executed_at: str        # When executed
    validation_result: dict # Validation details
    hash_verified: bool     # Hash check passed
    signature: str          # Execution signature
    status: str             # allowed, blocked, error
    error_message: str      # Error if any
```

---

### 3. Audit Logger (`audit_logger.py`)

**Purpose**: Cryptographic audit logging

**Features**:
- ✅ Hash-signed audit entries
- ✅ Immutable audit chain
- ✅ Merkle tree integrity
- ✅ Tamper detection
- ✅ Time-stamped logs
- ✅ Audit trail export

**Usage**:
```python
from audit_logger import AuditLogger

logger = AuditLogger()

# Log approval
logger.log_approval(
    approval_id="approval_001",
    approver="admin@company.com",
    target="invoice_123",
    result="success",
    details={'amount': 5000.00}
)

# Log execution
logger.log_execution(
    execution_id="exec_001",
    executor="system",
    target="invoice_123",
    action_type="invoice_post",
    result="success"
)

# Log validation
logger.log_validation(
    validation_id="val_001",
    validator="approval_validator",
    target="approval_001",
    result="success"
)

# Log error
logger.log_error(
    error_id="err_001",
    actor="system",
    target="invoice_123",
    error_message="Execution failed",
    details={'reason': 'network timeout'}
)
```

**Verify Chain Integrity**:
```python
# Verify entire audit chain
is_valid, errors = logger.verify_chain_integrity()

if is_valid:
    print("✓ Audit chain integrity verified")
else:
    print(f"✗ Integrity issues: {errors}")
```

**Export Audit Trail**:
```python
# Export complete trail
export_path = logger.export_audit_trail()
print(f"Audit trail exported: {export_path}")
```

---

## 🔄 COMPLETE WORKFLOW EXAMPLE

### Step 1: Cloud Creates Draft
```python
# Cloud side (odoo_cloud_client.py)
from odoo_cloud_client import OdooCloudClient

client = OdooCloudClient()

# Create draft invoice (cannot confirm!)
draft = await client.create_draft_invoice(
    partner_name="Acme Corp",
    invoice_lines=[...],
    total_amount=5000.00
)
# File written to Pending_Approval/
```

### Step 2: Human Approves
```python
# Human approval interface
from approval_validator import ApprovalValidator

validator = ApprovalValidator()

# Mark as approved (adds APPROVED_BY, APPROVED_AT)
success, message = validator.mark_as_approved(
    source_path=Path("Pending_Approval/approval_invoice_123.json"),
    approver="admin@company.com",
    method="manual"
)
# File moved to Approved/
```

### Step 3: Local Executes (With Guard)
```python
# Local side (odoo_local_executor.py)
from execution_guard import ExecutionGuard

guard = ExecutionGuard()

# Guard check before execution
allowed, message, record = guard.guard_execution(
    file_path=Path("Approved/approval_invoice_123.json"),
    action_type="invoice_post",
    executor="admin@company.com"
)

if not allowed:
    raise PermissionError(f"HITL blocked: {message}")

# Execute (only if allowed)
result = confirm_invoice_in_odoo()

# Log to audit
from audit_logger import AuditLogger
logger = AuditLogger()
logger.log_execution(
    execution_id=record.execution_id,
    executor="admin@company.com",
    target="invoice_123",
    action_type="invoice_post",
    result="success"
)
```

---

## 🛡️ SECURITY FEATURES

### 1. Hash Verification

```python
# Compute file hash (excluding signature fields)
def _compute_file_hash(file_path, exclude_fields=None):
    with open(file_path, 'r') as f:
        content = json.load(f)
    
    # Remove signature fields
    for field in (exclude_fields or []):
        if field in content:
            del content[field]
    
    # Deterministic JSON
    content_str = json.dumps(content, sort_keys=True)
    
    # SHA-256
    return hashlib.sha256(content_str.encode()).hexdigest()
```

### 2. HMAC Signatures

```python
# Generate signature
def _generate_signature(data, secret_key):
    sig_str = json.dumps(data, sort_keys=True)
    return hmac.new(
        secret_key.encode(),
        sig_str.encode(),
        hashlib.sha256
    ).hexdigest()

# Verify signature
def _verify_signature(data, signature, secret_key):
    expected = _generate_signature(data, secret_key)
    return hmac.compare_digest(expected, signature)
```

### 3. Merkle Tree Integrity

```python
# Build Merkle tree from entry hashes
def _compute_merkle_root(hashes):
    if not hashes:
        return hashlib.sha256(b'empty').hexdigest()
    
    current_level = hashes.copy()
    
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            combined = current_level[i] + current_level[i + 1]
            parent_hash = hashlib.sha256(combined.encode()).hexdigest()
            next_level.append(parent_hash)
        current_level = next_level
    
    return current_level[0]
```

### 4. Hash Chain Linkage

```python
# Each entry links to previous
entry.previous_hash = previous_entry.entry_hash

# Genesis entry
genesis_hash = "genesis"

# Verify chain
for entry in entries:
    if entry.previous_hash != expected_previous:
        raise TamperingDetected("Hash chain broken")
    expected_previous = entry.entry_hash
```

---

## 📋 CONFIGURATION REFERENCE

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HITL_STRICT_MODE` | ✅ | true | Strict validation |
| `BLOCK_CLOUD_EXECUTION` | ✅ | true | Block cloud attempts |
| `ENABLE_HASH_VERIFICATION` | ✅ | true | Hash checking |
| `ENABLE_EXECUTION_SIGNATURES` | - | true | Execution signatures |
| `ENABLE_AUDIT_SIGNATURES` | - | true | Audit signatures |
| `ENABLE_MERKLE_TREE` | - | true | Merkle tree integrity |
| `APPROVAL_SECRET_KEY` | ✅ | - | Approval HMAC key |
| `EXECUTION_SECRET_KEY` | ✅ | - | Execution HMAC key |
| `AUDIT_SECRET_KEY` | ✅ | - | Audit HMAC key |
| `APPROVAL_EXPIRY_HOURS` | - | 72 | Approval validity |
| `AUDIT_RETENTION_DAYS` | - | 365 | Log retention |

---

## 🧪 TESTING GUIDE

### Test Approval Validator

```bash
# Check status
python approval_validator.py --status

# Validate specific file
python approval_validator.py --validate Approved/approval_123.json

# Dry-run mode
python approval_validator.py --dry-run
```

### Test Execution Guard

```bash
# Check status
python execution_guard.py --status

# Test guard with file
python execution_guard.py --test Approved/approval_123.json

# Dry-run mode
python execution_guard.py --dry-run
```

### Test Audit Logger

```bash
# Check status
python audit_logger.py --status

# Verify chain integrity
python audit_logger.py --verify

# Export audit trail
python audit_logger.py --export

# Dry-run mode
python audit_logger.py --dry-run
```

---

## 📊 MONITORING

### Check Component Status

```bash
# Validator status
python approval_validator.py --status

# Guard status
python execution_guard.py --status

# Logger status
python audit_logger.py --status
```

### View Audit Logs

```bash
# List audit chains
ls -la Audit/chains/

# View recent validations
ls -la Audit/validation_*.json | tail -5

# View recent executions
ls -la Audit/execution_*.json | tail -5

# Export complete trail
python audit_logger.py --export
```

### Check for Tampering

```bash
# Verify chain integrity
python audit_logger.py --verify

# Check logs for errors
grep "tamper" Logs/*.log
grep "BLOCKED" Logs/execution_guard.log
```

---

## 🛠️ TROUBLESHOOTING

### Problem: Approval validation fails

```bash
# Check file has required fields
cat Approved/approval_123.json | jq '.approval_metadata'
cat Approved/approval_123.json | jq '.APPROVED_BY'
cat Approved/approval_123.json | jq '.APPROVED_AT'

# Re-add approval metadata
python -c "
from approval_validator import ApprovalValidator
from pathlib import Path
v = ApprovalValidator()
v.add_approval_metadata(
    Path('Pending_Approval/approval_123.json'),
    'admin@company.com'
)
"
```

### Problem: Execution blocked

```bash
# Check why blocked
python execution_guard.py --test Approved/approval_123.json

# Check file location
ls -la Approved/approval_123.json

# Verify approval
python approval_validator.py --validate Approved/approval_123.json
```

### Problem: Hash verification fails

```bash
# Possible tampering detected
# Check audit logs
cat Logs/approval_validator.log | grep "hash"

# Verify chain integrity
python audit_logger.py --verify

# If legitimate change, re-approve file
```

---

## 🚀 PRODUCTION DEPLOYMENT

### Security Key Generation

```bash
# Generate secure random keys
python -c "
import secrets
print('APPROVAL_SECRET_KEY=' + secrets.token_hex(32))
print('EXECUTION_SECRET_KEY=' + secrets.token_hex(32))
print('AUDIT_SECRET_KEY=' + secrets.token_hex(32))
"

# Add to .env.platinum (NEVER commit!)
```

### Environment Variables (Production)

```bash
# Production settings
HITL_STRICT_MODE=true
BLOCK_CLOUD_EXECUTION=true
ENABLE_HASH_VERIFICATION=true
ENABLE_EXECUTION_SIGNATURES=true
ENABLE_AUDIT_SIGNATURES=true
ENABLE_MERKLE_TREE=true

# Use secrets manager
APPROVAL_SECRET_KEY_FILE=/run/secrets/approval_key
EXECUTION_SECRET_KEY_FILE=/run/secrets/execution_key
AUDIT_SECRET_KEY_FILE=/run/secrets/audit_key
```

### Audit Retention

```bash
# Set retention period
AUDIT_RETENTION_DAYS=365

# Archive old chains
find Audit/chains/ -name "*.json" -mtime +365 -exec gzip {} \;

# Export before deletion
python audit_logger.py --export
```

---

## 📞 SUPPORT

### Documentation
- Quick start: This file
- Architecture: See diagrams above
- Security: Review hash/signature sections

### Logs
- Validator: `Logs/approval_validator.log`
- Guard: `Logs/execution_guard.log`
- Logger: `Logs/audit_logger.log`

### Commands
```bash
# Validate file
python approval_validator.py --validate <file>

# Test guard
python execution_guard.py --test <file>

# Verify integrity
python audit_logger.py --verify

# Export trail
python audit_logger.py --export
```

---

**Platinum Tier HITL Enforcement - Cryptographic Security, Production-Ready! 🔐**
