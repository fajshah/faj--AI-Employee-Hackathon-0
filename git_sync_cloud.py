"""
Platinum Tier Git Sync - Cloud Side
=====================================
Automatic Git synchronization for cloud deployment

Features:
- Auto-pull every 2 minutes
- Auto-push after writing drafts
- Conflict resolution using claim-by-move rule
- Secure file filtering (never sync secrets)
- Production-grade logging
- Safe error handling
- No infinite push loops

Security:
- NEVER sync: .env, /sessions, /secrets, tokens
- Only sync: Pending_Approval/, Generated_Drafts/, CEO_Briefings/, Plans/
"""

import os
import sys
import json
import asyncio
import logging
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.platinum')

# Configure logging
class GitSyncLogger:
    """Dual logging: File + Console"""
    
    def __init__(self, name: str, log_file: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers = []
        
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


logger_wrapper = GitSyncLogger(
    name='git_sync_cloud',
    log_file='Logs/git_sync_cloud.log'
)
logger = logger_wrapper.get_logger()


@dataclass
class SyncStats:
    """Sync statistics"""
    pulls_completed: int = 0
    pushes_completed: int = 0
    conflicts_resolved: int = 0
    errors: int = 0
    last_pull: Optional[str] = None
    last_push: Optional[str] = None
    last_error: Optional[str] = None
    start_time: str = ""
    
    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now().isoformat()


class GitSyncCloud:
    """
    Platinum Tier Git Sync - Cloud Side
    
    Responsibilities:
    - Auto-pull from Git vault every 2 minutes
    - Auto-push after writing drafts
    - Conflict resolution using claim-by-move
    - Secure file filtering
    - Prevent infinite push loops
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-GitSync-Cloud"
        
        # Configuration
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.git_enabled = os.getenv('GIT_SYNC_ENABLED', 'false').lower() == 'true'
        
        # Git configuration
        self.git_repo_path = os.getenv('GIT_VAULT_PATH', '.vault')
        self.git_branch = os.getenv('GIT_BRANCH', 'main')
        self.git_remote = os.getenv('GIT_REMOTE', 'origin')
        self.git_email = os.getenv('GIT_EMAIL', 'cloud@ai-employee.local')
        self.git_user = os.getenv('GIT_USER', 'cloud-orchestrator')
        
        # Sync intervals
        self.pull_interval = int(os.getenv('GIT_PULL_INTERVAL', '120'))  # 2 minutes
        self.push_debounce = int(os.getenv('GIT_PUSH_DEBOUNCE', '30'))  # 30 seconds
        
        # Directories
        self.base_dir = Path(os.getenv('CLOUD_BASE_DIR', '.'))
        self.pending_approval_dir = self.base_dir / 'Pending_Approval'
        self.generated_drafts_dir = self.base_dir / 'Generated_Drafts'
        self.ceo_briefings_dir = self.base_dir / 'CEO_Briefings'
        self.plans_dir = self.base_dir / 'Plans'
        self.logs_dir = self.base_dir / 'Logs'
        self.vault_dir = Path(self.git_repo_path)
        
        # Directories to sync (secure subset only)
        self.sync_dirs = [
            'Pending_Approval',
            'Generated_Drafts',
            'CEO_Briefings',
            'Plans'
        ]
        
        # Files/directories NEVER to sync
        self.never_sync = [
            '.env',
            '.env.platinum',
            '.env.gold',
            '.env.local',
            'tokens',
            'sessions',
            'linkedin_session',
            'wa_session',
            'session',
            'secrets',
            'Logs',
            '__pycache__',
            '*.pyc',
            '.gitignore'
        ]
        
        # Create directories
        self._create_directories()
        
        # Statistics
        self.stats = SyncStats()
        
        # Push debounce tracking (prevent infinite loops)
        self.last_push_time: Optional[datetime] = None
        self.push_pending = False
        self.consecutive_push_failures = 0
        self.max_consecutive_failures = 5
        
        # File tracking for conflict resolution
        self.local_file_hashes: Dict[str, str] = {}
        self.remote_file_hashes: Dict[str, str] = {}
        
        logger.info(f"Git Sync Cloud initialized v{self.version}")
        logger.info(f"Git enabled: {self.git_enabled}")
        logger.info(f"Pull interval: {self.pull_interval}s")
        logger.info(f"Vault path: {self.git_repo_path}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [self.vault_dir, self.logs_dir]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory verified: {dir_path}")
    
    def _run_git_command(self, args: List[str], cwd: Path = None) -> Tuple[bool, str, str]:
        """
        Run Git command with error handling
        
        Returns: (success, stdout, stderr)
        """
        if not self.git_enabled:
            return False, "", "Git sync disabled"
        
        cmd = ['git'] + args
        cwd = cwd or self.vault_dir
        
        try:
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            return success, result.stdout.strip(), result.stderr.strip()
        
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timed out: {' '.join(cmd)}")
            return False, "", "Command timed out"
        except FileNotFoundError:
            logger.error("Git not found in PATH")
            return False, "", "Git not installed"
        except Exception as e:
            logger.error(f"Git command failed: {str(e)}")
            return False, "", str(e)
    
    def _init_git_repo(self) -> bool:
        """Initialize Git repository if not exists"""
        if not self.git_enabled:
            return False
        
        if not self.vault_dir.exists():
            self.vault_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created vault directory: {self.vault_dir}")
        
        # Check if already initialized
        git_dir = self.vault_dir / '.git'
        if not git_dir.exists():
            logger.info("Initializing Git repository...")
            success, stdout, stderr = self._run_git_command(['init'])
            if not success:
                logger.error(f"Git init failed: {stderr}")
                return False
            logger.info("Git repository initialized")
        
        # Configure Git user
        self._run_git_command(['config', 'user.email', self.git_email])
        self._run_git_command(['config', 'user.name', self.git_user])
        
        return True
    
    def _setup_remote(self, remote_url: str) -> bool:
        """Setup Git remote"""
        if not remote_url:
            logger.warning("No remote URL configured")
            return False
        
        # Remove existing remote
        self._run_git_command(['remote', 'remove', self.git_remote])
        
        # Add new remote
        success, stdout, stderr = self._run_git_command(['remote', 'add', self.git_remote, remote_url])
        if not success:
            logger.error(f"Failed to add remote: {stderr}")
            return False
        
        logger.info(f"Remote configured: {self.git_remote} -> {remote_url}")
        return True
    
    def _fetch(self) -> bool:
        """Fetch from remote"""
        logger.info("Fetching from remote...")
        success, stdout, stderr = self._run_git_command(['fetch', self.git_remote])
        if not success:
            logger.error(f"Fetch failed: {stderr}")
            return False
        logger.debug("Fetch completed")
        return True
    
    def _pull(self) -> bool:
        """Pull from remote with conflict handling"""
        logger.info("Pulling from remote...")
        
        # First fetch
        if not self._fetch():
            return False
        
        # Check for conflicts before pull
        success, stdout, stderr = self._run_git_command([
            'merge', '--no-commit', '--no-ff',
            f'{self.git_remote}/{self.git_branch}'
        ])
        
        if not success:
            # Check if it's a conflict
            if 'conflict' in stderr.lower() or 'conflict' in stdout.lower():
                logger.warning("Conflicts detected during pull - resolving...")
                self._resolve_conflicts('pull')
                # Commit the resolution
                self._run_git_command(['commit', '-m', 'Auto-resolve conflicts (pull)'])
            else:
                logger.error(f"Pull failed: {stderr}")
                return False
        
        # Alternative: use pull with strategy
        success, stdout, stderr = self._run_git_command([
            'pull', '--strategy-option=ours',
            self.git_remote, self.git_branch
        ])
        
        if success:
            self.stats.pulls_completed += 1
            self.stats.last_pull = datetime.now().isoformat()
            logger.info(f"Pull completed successfully")
        else:
            logger.error(f"Pull failed: {stderr}")
            self.stats.errors += 1
            self.stats.last_error = stderr
        
        return success
    
    def _push(self, force: bool = False) -> bool:
        """
        Push to remote with debounce protection
        
        Args:
            force: Force push even if within debounce period
        """
        if not self.git_enabled:
            return False
        
        # Check debounce (prevent infinite loops)
        now = datetime.now()
        if not force and self.last_push_time:
            elapsed = (now - self.last_push_time).total_seconds()
            if elapsed < self.push_debounce:
                logger.debug(f"Push debounced ({elapsed:.0f}s < {self.push_debounce}s)")
                self.push_pending = True
                return True
        
        # Check consecutive failures
        if self.consecutive_push_failures >= self.max_consecutive_failures:
            logger.error(f"Too many consecutive push failures ({self.consecutive_push_failures})")
            return False
        
        logger.info("Pushing to remote...")
        
        # Stage all changes
        success, stdout, stderr = self._run_git_command(['add', '-A'])
        if not success:
            logger.error(f"Git add failed: {stderr}")
            return False
        
        # Check if there are changes to commit
        success, stdout, stderr = self._run_git_command(['status', '--porcelain'])
        if not stdout.strip():
            logger.debug("No changes to push")
            self.last_push_time = now
            return True
        
        # Commit
        commit_msg = f"Auto-commit: Cloud sync {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        success, stdout, stderr = self._run_git_command(['commit', '-m', commit_msg])
        if not success:
            logger.error(f"Git commit failed: {stderr}")
            return False
        
        # Push
        success, stdout, stderr = self._run_git_command(['push', self.git_remote, self.git_branch])
        if not success:
            logger.error(f"Push failed: {stderr}")
            self.consecutive_push_failures += 1
            self.stats.errors += 1
            self.stats.last_error = stderr
            
            # Check if it's a conflict (remote has changes)
            if 'rejected' in stderr.lower() or 'conflict' in stderr.lower():
                logger.warning("Remote has changes - pulling first...")
                self._pull()
                # Retry push after pull
                return self._push(force=True)
            
            return False
        
        # Success
        self.last_push_time = now
        self.push_pending = False
        self.consecutive_push_failures = 0
        self.stats.pushes_completed += 1
        self.stats.last_push = datetime.now().isoformat()
        
        logger.info(f"Push completed successfully")
        return True
    
    def _resolve_conflicts(self, operation: str):
        """
        Resolve conflicts using claim-by-move rule
        
        Rule: If file was moved to Approved/Done locally, keep local version
              Otherwise, prefer remote version for safety
        """
        logger.info(f"Resolving conflicts ({operation})...")
        
        # Get list of conflicted files
        success, stdout, stderr = self._run_git_command(['diff', '--name-only', '--diff-filter=U'])
        if not stdout.strip():
            return
        
        conflicted_files = stdout.strip().split('\n')
        
        for file_path in conflicted_files:
            if not file_path.strip():
                continue
            
            full_path = self.vault_dir / file_path.strip()
            logger.warning(f"Resolving conflict: {file_path}")
            
            # Claim-by-move rule:
            # If file exists in Approved/ or Done/ locally, keep local version
            # Otherwise, prefer remote (safer for cloud)
            
            if 'Approved' in file_path or 'Done' in file_path:
                # Keep local version (claim by move)
                logger.info(f"Keeping local version (claim-by-move): {file_path}")
                self._run_git_command(['add', str(full_path)])
            else:
                # Prefer remote version (safer)
                logger.info(f"Preferring remote version: {file_path}")
                self._run_git_command(['checkout', '--theirs', file_path])
                self._run_git_command(['add', str(full_path)])
            
            self.stats.conflicts_resolved += 1
        
        logger.info(f"Resolved {len(conflicted_files)} conflict(s)")
    
    def _should_sync_file(self, file_path: Path) -> bool:
        """Check if file should be synced (security filter)"""
        # Check against never_sync list
        for pattern in self.never_sync:
            if pattern.startswith('/'):
                # Directory pattern
                if pattern[1:] in str(file_path):
                    return False
            elif pattern.endswith('*'):
                # Extension pattern
                if file_path.suffix == pattern[1:]:
                    return False
            else:
                # Exact match or contains
                if pattern in str(file_path) or file_path.name == pattern:
                    return False
        
        # Only sync from approved directories
        file_str = str(file_path)
        for sync_dir in self.sync_dirs:
            if sync_dir in file_str:
                return True
        
        return False
    
    def _sync_to_vault(self) -> bool:
        """Sync cloud files to vault directory"""
        logger.info("Syncing files to vault...")
        
        files_synced = 0
        
        for sync_dir in self.sync_dirs:
            source_dir = self.base_dir / sync_dir
            if not source_dir.exists():
                continue
            
            vault_subdir = self.vault_dir / sync_dir
            vault_subdir.mkdir(parents=True, exist_ok=True)
            
            for file_path in source_dir.glob('**/*'):
                if file_path.is_file() and self._should_sync_file(file_path):
                    try:
                        # Copy to vault
                        rel_path = file_path.relative_to(self.base_dir)
                        dest_path = self.vault_dir / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        if not self.dry_run:
                            shutil.copy2(file_path, dest_path)
                        
                        files_synced += 1
                        logger.debug(f"Synced: {rel_path}")
                    
                    except Exception as e:
                        logger.error(f"Failed to sync {file_path}: {str(e)}")
                        self.stats.errors += 1
        
        logger.info(f"Synced {files_synced} file(s) to vault")
        return files_synced > 0
    
    def _sync_from_vault(self) -> bool:
        """Sync vault files back to cloud directories"""
        logger.info("Syncing files from vault...")
        
        files_synced = 0
        
        for sync_dir in self.sync_dirs:
            vault_subdir = self.vault_dir / sync_dir
            if not vault_subdir.exists():
                continue
            
            dest_dir = self.base_dir / sync_dir
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path in vault_subdir.glob('**/*'):
                if file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(self.vault_dir)
                        dest_path = self.base_dir / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        if not self.dry_run:
                            shutil.copy2(file_path, dest_path)
                        
                        files_synced += 1
                        logger.debug(f"Synced: {rel_path}")
                    
                    except Exception as e:
                        logger.error(f"Failed to sync {file_path}: {str(e)}")
                        self.stats.errors += 1
        
        logger.info(f"Synced {files_synced} file(s) from vault")
        return files_synced > 0
    
    def trigger_push(self):
        """Trigger a push (called after writing drafts)"""
        if not self.git_enabled:
            return
        
        logger.debug("Push triggered")
        self.push_pending = True
    
    async def _auto_pull_loop(self):
        """Automatic pull loop (every 2 minutes)"""
        logger.info(f"Starting auto-pull loop (interval: {self.pull_interval}s)")
        
        while True:
            try:
                # Pull from remote
                self._pull()
                
                # Sync from vault to cloud directories
                self._sync_from_vault()
                
                await asyncio.sleep(self.pull_interval)
            
            except Exception as e:
                logger.error(f"Auto-pull error: {str(e)}")
                self.stats.errors += 1
                await asyncio.sleep(self.pull_interval)
    
    async def _auto_push_loop(self):
        """Automatic push loop (check every 10 seconds)"""
        logger.info("Starting auto-push loop")
        
        while True:
            try:
                if self.push_pending:
                    # Sync files to vault first
                    self._sync_to_vault()
                    
                    # Push to remote
                    self._push()
                
                await asyncio.sleep(10)
            
            except Exception as e:
                logger.error(f"Auto-push error: {str(e)}")
                self.stats.errors += 1
                await asyncio.sleep(10)
    
    def get_status(self) -> Dict[str, Any]:
        """Get sync status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats.start_time)
        
        return {
            'version': self.version,
            'status': 'running',
            'uptime': str(uptime),
            'git_enabled': self.git_enabled,
            'vault_path': str(self.vault_dir),
            'pull_interval': self.pull_interval,
            'push_debounce': self.push_debounce,
            'statistics': {
                'pulls_completed': self.stats.pulls_completed,
                'pushes_completed': self.stats.pushes_completed,
                'conflicts_resolved': self.stats.conflicts_resolved,
                'errors': self.stats.errors,
                'last_pull': self.stats.last_pull,
                'last_push': self.stats.last_push,
                'last_error': self.stats.last_error,
                'consecutive_failures': self.consecutive_push_failures
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def save_status(self):
        """Save status to file"""
        status_file = self.logs_dir / 'git_sync_cloud_status.json'
        status = self.get_status()
        
        if not self.dry_run:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)
    
    async def run(self):
        """Main entry point"""
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🔀  PLATINUM TIER GIT SYNC - CLOUD  🔀               ║
║                                                           ║
║     Version: {self.version}
║     DRY_RUN: {self.dry_run}
║     Git Enabled: {self.git_enabled}
║     Vault: {self.git_repo_path}
║                                                           ║
║     Sync Schedule:                                        ║
║     • Auto-pull: Every {self.pull_interval}s                 ║
║     • Auto-push: After draft writes (debounced)          ║
║                                                           ║
║     Security:                                             ║
║     • NEVER sync: .env, tokens, sessions, secrets        ║
║     • ONLY sync: Pending_Approval, Drafts, Briefings    ║
║     • Conflict resolution: claim-by-move                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"Git Sync Cloud starting v{self.version}")
        
        # Initialize Git repo
        if self.git_enabled:
            self._init_git_repo()
            
            # Setup remote if configured
            remote_url = os.getenv('GIT_REMOTE_URL')
            if remote_url:
                self._setup_remote(remote_url)
        
        try:
            # Run both loops concurrently
            await asyncio.gather(
                self._auto_pull_loop(),
                self._auto_push_loop()
            )
        
        except KeyboardInterrupt:
            logger.info("Git Sync Cloud stopped by user")
            print("\n🛑 Git Sync Cloud stopped.")
        
        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
        
        finally:
            # Save final status
            self.save_status()
            
            # Print statistics
            status = self.get_status()
            print(f"\n📊 Final Statistics:")
            print(f"   Pulls Completed: {status['statistics']['pulls_completed']}")
            print(f"   Pushes Completed: {status['statistics']['pushes_completed']}")
            print(f"   Conflicts Resolved: {status['statistics']['conflicts_resolved']}")
            print(f"   Errors: {status['statistics']['errors']}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Git Sync - Cloud')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    parser.add_argument('--init', action='store_true', help='Initialize Git repo and exit')
    parser.add_argument('--pull', action='store_true', help='Pull once and exit')
    parser.add_argument('--push', action='store_true', help='Push once and exit')
    args = parser.parse_args()
    
    sync = GitSyncCloud()
    
    if args.status:
        status = sync.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.init:
        sync._init_git_repo()
        remote_url = os.getenv('GIT_REMOTE_URL')
        if remote_url:
            sync._setup_remote(remote_url)
        print("Git repository initialized")
        return
    
    if args.pull:
        sync._pull()
        sync._sync_from_vault()
        return
    
    if args.push:
        sync._sync_to_vault()
        sync._push()
        return
    
    if args.dry_run:
        sync.dry_run = True
    
    await sync.run()


if __name__ == "__main__":
    asyncio.run(main())
