# 🔀 PLATINUM TIER GIT SYNC SYSTEM
## Automatic Git Synchronization for Hybrid Cloud Architecture

---

## 📖 OVERVIEW

The **Platinum Tier Git Sync System** provides automatic, secure synchronization between cloud and local components using Git as the synchronization backbone.

### Key Features
- ✅ **Auto-pull every 2 minutes** (cloud side)
- ✅ **Auto-push after writing drafts** (cloud side)
- ✅ **Pre-execution pull** (local side - CRITICAL)
- ✅ **Post-execution push** (local side)
- ✅ **Conflict resolution** using claim-by-move rule
- ✅ **Secure file filtering** (never sync secrets)
- ✅ **Debounce protection** (no infinite loops)
- ✅ **Production-grade logging**

---

## 🔐 SECURITY BOUNDARY

### NEVER Synced to Git (Protected)
```
❌ .env, .env.platinum, .env.gold (credentials)
❌ tokens/ (OAuth tokens)
❌ sessions/ (browser sessions)
❌ linkedin_session/ (LinkedIn auth)
❌ wa_session/ (WhatsApp auth)
❌ secrets/ (any secrets)
❌ Logs/ (operational logs)
```

### ONLY Synced to Git (Safe)
```
✅ Pending_Approval/ (drafts awaiting review)
✅ Generated_Drafts/ (AI-generated content)
✅ CEO_Briefings/ (executive reports)
✅ Plans/ (task execution plans)
```

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│ CLOUD SIDE (git_sync_cloud.py)                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Auto-Pull Loop (every 2 minutes)                            │   │
│  │ 1. Fetch from Git remote                                    │   │
│  │ 2. Pull latest changes                                      │   │
│  │ 3. Sync vault → cloud directories                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Auto-Push Loop (triggered by draft writes)                  │   │
│  │ 1. Sync cloud directories → vault                           │   │
│  │ 2. Commit changes                                           │   │
│  │ 3. Push to Git remote (debounced 30s)                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ Git Remote (GitHub/GitLab/Azure DevOps)
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│ LOCAL SIDE (git_sync_local.py)                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Pre-Execution Pull (BEFORE every task)                      │   │
│  │ CRITICAL: Ensures latest approved drafts                    │   │
│  │ 1. Pull from Git remote                                     │   │
│  │ 2. Sync vault → local directories                           │   │
│  │ 3. Proceed with execution                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Post-Execution Push (AFTER every task)                      │   │
│  │ 1. Sync local directories → vault                           │   │
│  │ 2. Commit changes (Done/ or Error/)                         │   │
│  │ 3. Push to Git remote (debounced 30s)                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 QUICK START

### 1. Install Dependencies

```bash
# Git is required
git --version

# Python dependencies
pip install -r requirements_platinum.txt
```

### 2. Configure Environment

```bash
# Copy example
cp .env.platinum.example .env.platinum

# Edit with your Git settings
```

Required settings in `.env.platinum`:
```bash
# Git Sync Configuration
GIT_SYNC_ENABLED=true
GIT_VAULT_PATH=.vault
GIT_BRANCH=main
GIT_REMOTE=origin
GIT_REMOTE_URL=https://github.com/your-org/ai-employee-vault.git
GIT_EMAIL=cloud@ai-employee.local
GIT_USER=cloud-orchestrator

# Sync intervals
GIT_PULL_INTERVAL=120      # 2 minutes
GIT_PUSH_DEBOUNCE=30       # 30 seconds
```

### 3. Initialize Git Vault

```bash
# Cloud side
python git_sync_cloud.py --init

# Local side
python git_sync_local.py --init
```

### 4. Setup Remote Repository

```bash
# Create a private Git repository (GitHub/GitLab/Azure DevOps)
# Then configure remote URL:

# In .env.platinum:
GIT_REMOTE_URL=https://github.com/your-org/ai-employee-vault.git

# Or set remote manually:
cd .vault
git remote add origin https://github.com/your-org/ai-employee-vault.git
git push -u origin main
```

### 5. Start Sync Services

```bash
# Terminal 1 - Cloud sync
python git_sync_cloud.py

# Terminal 2 - Local sync
python git_sync_local.py
```

---

## 📁 FILE STRUCTURE

```
hackthone-0/
├── git_sync_cloud.py          # Cloud-side sync service
├── git_sync_local.py          # Local-side sync service
├── .gitignore.platinum        # Security-focused gitignore
├── GIT_SYNC_README.md         # This documentation
│
├── .vault/                    # Git vault directory
│   ├── .git/                  # Git repository
│   ├── Pending_Approval/      # Synced drafts
│   ├── Generated_Drafts/      # Synced drafts
│   ├── CEO_Briefings/         # Synced briefings
│   └── Plans/                 # Synced plans
│
├── Pending_Approval/          # Working directory (cloud)
├── Generated_Drafts/          # Working directory (cloud)
├── CEO_Briefings/             # Working directory (cloud)
├── Plans/                     # Working directory (cloud)
│
├── Approved/                  # Working directory (local)
├── Done/                      # Working directory (local)
├── Error/                     # Working directory (local)
│
└── Logs/
    ├── git_sync_cloud.log     # Cloud sync logs
    ├── git_sync_local.log     # Local sync logs
    ├── git_sync_cloud_status.json
    └── git_sync_local_status.json
```

---

## 🔄 SYNC WORKFLOW

### Cloud Side Workflow

```
1. Cloud Orchestrator writes draft
   └─> Pending_Approval/draft_001.json

2. Draft triggers Git sync
   └─> git_sync_cloud.py notified

3. Sync to vault
   └─> Copy to .vault/Pending_Approval/

4. Commit & push (debounced)
   └─> git commit -m "Auto-commit: Cloud sync..."
   └─> git push origin main

5. Remote repository updated
   └─> Available for local to pull
```

### Local Side Workflow

```
1. Local Orchestrator about to execute task
   └─> CRITICAL: Pre-execution pull triggered

2. Pull latest from remote
   └─> git pull origin main
   └─> Sync .vault → local directories

3. Execute task (after ensuring latest version)
   └─> Move file: Pending_Approval → Done

4. Post-execution push
   └─> Sync Done/ → .vault/Done/
   └─> git commit -m "Auto-commit: Local sync..."
   └─> git push origin main
```

---

## ⚔️ CONFLICT RESOLUTION

### Claim-by-Move Rule

When conflicts occur (same file modified in cloud and local), the system uses **claim-by-move** resolution:

| Scenario | Resolution | Reason |
|----------|------------|--------|
| File moved to `Done/` locally | **Keep local** | Execution completed - local has truth |
| File moved to `Error/` locally | **Keep local** | Execution failed - local has truth |
| File moved to `Approved/` locally | **Keep local** | Human approved - local decision |
| File in `Pending_Approval/` | **Keep local** | Human review in progress |
| File in `Generated_Drafts/` | **Keep remote** | Cloud is source of drafts |

### How It Works

```python
# In git_sync_local.py
def _resolve_conflicts(self, operation: str):
    for file_path in conflicted_files:
        if 'Done' in file_path or 'Error' in file_path:
            # Keep local version (claim-by-move - executed)
            logger.info(f"Keeping local version (executed): {file_path}")
            self._run_git_command(['add', str(full_path)])
        elif 'Approved' in file_path:
            # Keep local version (human approval)
            logger.info(f"Keeping local version (approved): {file_path}")
            self._run_git_command(['add', str(full_path)])
        else:
            # Default: prefer local for safety
            logger.info(f"Keeping local version: {file_path}")
            self._run_git_command(['add', str(full_path)])
```

---

## 🛡️ SECURITY FEATURES

### 1. File Filtering

```python
# Files/directories NEVER synced
self.never_sync = [
    '.env', '.env.platinum', '.env.gold',  # Credentials
    'tokens/',                              # OAuth tokens
    'sessions/', 'linkedin_session/',       # Browser sessions
    'wa_session/',                          # WhatsApp sessions
    'secrets/',                             # Any secrets
    'Logs/',                                # Operational logs
    '__pycache__/', '*.pyc'                 # Python cache
]
```

### 2. Directory Whitelist

```python
# ONLY these directories are synced
self.sync_dirs = [
    'Pending_Approval',    # Drafts awaiting review
    'Generated_Drafts',    # AI-generated content
    'CEO_Briefings',       # Executive reports
    'Plans'                # Task execution plans
]
```

### 3. Secure Git Configuration

```bash
# Configure Git user for audit trail
git config user.email "cloud@ai-employee.local"
git config user.name "cloud-orchestrator"

# Use HTTPS with credentials or SSH keys
git remote add origin https://github.com/org/vault.git
# OR
git remote add origin git@github.com:org/vault.git
```

---

## 🔧 COMMANDS REFERENCE

### Cloud Side Commands

```bash
# Show status
python git_sync_cloud.py --status

# Initialize Git repo
python git_sync_cloud.py --init

# Pull once (manual)
python git_sync_cloud.py --pull

# Push once (manual)
python git_sync_cloud.py --push

# Run continuous sync
python git_sync_cloud.py

# Dry-run mode (test without changes)
python git_sync_cloud.py --dry-run
```

### Local Side Commands

```bash
# Show status
python git_sync_local.py --status

# Initialize Git repo
python git_sync_local.py --init

# Pull once (manual)
python git_sync_local.py --pull

# Push once (manual)
python git_sync_local.py --push

# Pre-execution pull (for specific task)
python git_sync_local.py --pre-exec task_001

# Post-execution push (for specific task)
python git_sync_local.py --post-exec task_001

# Run continuous sync
python git_sync_local.py

# Dry-run mode (test without changes)
python git_sync_local.py --dry-run
```

---

## 📊 MONITORING

### Check Sync Status

```bash
# Cloud status
python git_sync_cloud.py --status

# Expected output:
{
    "version": "4.0.0-Platinum-GitSync-Cloud",
    "status": "running",
    "git_enabled": true,
    "statistics": {
        "pulls_completed": 45,
        "pushes_completed": 23,
        "conflicts_resolved": 2,
        "errors": 0,
        "last_pull": "2025-02-26T10:30:00",
        "last_push": "2025-02-26T10:28:00"
    }
}

# Local status
python git_sync_local.py --status
```

### View Logs

```bash
# Real-time cloud sync logs
tail -f Logs/git_sync_cloud.log

# Real-time local sync logs
tail -f Logs/git_sync_local.log

# Search for errors
grep "ERROR" Logs/git_sync_*.log

# Search for conflicts
grep "conflict" Logs/git_sync_*.log
```

### Status Files

```bash
# Cloud sync status
cat Logs/git_sync_cloud_status.json

# Local sync status
cat Logs/git_sync_local_status.json
```

---

## 🛠️ TROUBLESHOOTING

### Problem: Git not found

```bash
# Install Git
# Windows: https://git-scm.com/download/win
# macOS: brew install git
# Linux: sudo apt-get install git

# Verify installation
git --version
```

### Problem: Authentication failed

```bash
# For HTTPS: Use personal access token
git remote set-url origin https://TOKEN@github.com/org/vault.git

# For SSH: Ensure SSH key is configured
ssh-add ~/.ssh/id_rsa
ssh -T git@github.com
```

### Problem: Conflicts not resolving

```bash
# Manual conflict resolution
cd .vault
git status  # See conflicted files
git diff    # Review conflicts

# Choose local version
git checkout --ours <file>
git add <file>

# Or choose remote version
git checkout --theirs <file>
git add <file>

# Commit resolution
git commit -m "Manual conflict resolution"
git push
```

### Problem: Push rejected (non-fast-forward)

```bash
# Pull first, then push
cd .vault
git pull --rebase
git push

# Or force push (use with caution!)
git push --force-with-lease
```

### Problem: Infinite push loop

The system has built-in protection:

```python
# Debounce: Minimum 30 seconds between pushes
self.push_debounce = 30

# Max consecutive failures: Stop after 5 failures
self.max_consecutive_failures = 5
```

If loop still occurs:
```bash
# Stop sync service
Ctrl+C

# Check logs for cause
tail -f Logs/git_sync_*.log

# Restart with dry-run to diagnose
python git_sync_cloud.py --dry-run
```

---

## 🚀 DEPLOYMENT PATTERNS

### Pattern 1: Single Repository

```
GitHub Repository: ai-employee-vault
├── main branch (source of truth)
├── Cloud pulls from main
├── Cloud pushes to main
├── Local pulls from main
└── Local pushes to main
```

### Pattern 2: Fork-Based

```
GitHub Organization:
├── ai-employee-vault (main repo)
├── ai-employee-vault-cloud (cloud fork)
└── ai-employee-vault-local (local fork)

Cloud syncs with cloud fork
Local syncs with local fork
PRs between forks for review
```

### Pattern 3: Branch-Based

```
Single Repository:
├── main (source of truth)
├── cloud-branch (cloud writes here)
└── local-branch (local writes here)

Cloud: pull main, push cloud-branch
Local: pull main+cloud-branch, push local-branch
Merge via PR or automated merge
```

---

## 📋 CONFIGURATION REFERENCE

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GIT_SYNC_ENABLED` | false | Enable Git sync |
| `GIT_VAULT_PATH` | .vault | Git repository path |
| `GIT_BRANCH` | main | Branch name |
| `GIT_REMOTE` | origin | Remote name |
| `GIT_REMOTE_URL` | - | Remote URL (required) |
| `GIT_EMAIL` | cloud@... | Git user email |
| `GIT_USER` | cloud-orchestrator | Git user name |
| `GIT_PULL_INTERVAL` | 120 | Pull interval (seconds) |
| `GIT_PUSH_DEBOUNCE` | 30 | Push debounce (seconds) |
| `DRY_RUN` | true | Safe testing mode |

### Recommended Settings

```bash
# Production cloud deployment
GIT_SYNC_ENABLED=true
GIT_VAULT_PATH=/app/.vault
GIT_PULL_INTERVAL=120
GIT_PUSH_DEBOUNCE=30

# Production local deployment
GIT_SYNC_ENABLED=true
GIT_VAULT_PATH=/opt/ai-employee/.vault
GIT_PULL_INTERVAL=120
GIT_PUSH_DEBOUNCE=30

# Development/testing
DRY_RUN=true
GIT_SYNC_ENABLED=false  # Or use local-only
```

---

## 🎯 BEST PRACTICES

### 1. Always Pull Before Execution

```python
# Local orchestrator integration
def execute_task(task_id):
    # CRITICAL: Pull first!
    git_sync.pull_before_execution(task_id)
    
    # Now safe to execute
    result = execute(task_id)
    
    # Push after execution
    git_sync.push_after_execution(task_id)
```

### 2. Use Descriptive Commit Messages

```bash
# Auto-generated messages include timestamp
"Auto-commit: Cloud sync 2025-02-26 10:30:00"
"Auto-commit: Local sync 2025-02-26 10:35:00"

# Manual commits should be descriptive
git commit -m "Add draft: email response to client inquiry"
```

### 3. Monitor Sync Health

```bash
# Check status every hour
python git_sync_cloud.py --status
python git_sync_local.py --status

# Alert on errors
grep "ERROR" Logs/git_sync_*.log | tail -5
```

### 4. Regular Remote Backup

```bash
# Ensure remote is backed up
cd .vault
git remote -v
git fetch --all
git status
```

### 5. Test Conflict Resolution

```bash
# Simulate conflict scenario
# 1. Create file in cloud
# 2. Modify same file locally
# 3. Both push
# 4. Verify claim-by-move resolution

# Check logs for resolution
grep "claim-by-move" Logs/git_sync_*.log
```

---

## 📞 SUPPORT

### Documentation
- Quick start: This file
- Architecture: See diagram above
- Security: Review .gitignore.platinum

### Logs
- Cloud: `Logs/git_sync_cloud.log`
- Local: `Logs/git_sync_local.log`

### Status
- Cloud: `python git_sync_cloud.py --status`
- Local: `python git_sync_local.py --status`

---

**Platinum Tier Git Sync System - Secure, Automatic, Production-Ready! 🔀**
