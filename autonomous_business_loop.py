"""
Autonomous Business Loop
Main orchestrator for autonomous AI employee business operations

This module runs continuously, generating business ideas, finding clients,
and sending outreach messages automatically.
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.gold')

# Configure logging
LOGS_DIR = Path(__file__).parent / "Logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "autonomous_business.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AutonomousBusinessLoop")

# Import agents
sys.path.insert(0, str(Path(__file__).parent / "Agents"))
from business_agent import BusinessAgent
from client_finder_agent import ClientFinderAgent
from outreach_agent import OutreachAgent

# Configuration
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://localhost:5001')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
LOOP_INTERVAL_SECONDS = int(os.getenv('BUSINESS_LOOP_INTERVAL', '60'))
IDEAS_PER_CYCLE = int(os.getenv('IDEAS_PER_CYCLE', '2'))
CLIENTS_PER_CYCLE = int(os.getenv('CLIENTS_PER_CYCLE', '3'))
MAX_OUTREACH_PER_CYCLE = int(os.getenv('MAX_OUTREACH_PER_CYCLE', '5'))
DRY_RUN = os.getenv('DRY_RUN', 'False').lower() == 'true'

# Base paths
BASE_DIR = Path(__file__).parent
VAULT_DIR = BASE_DIR / "AI_Employee_Vault"


class AutonomousBusinessLoop:
    """Main autonomous business operations loop"""
    
    def __init__(self, vault_dir=None):
        self.vault_dir = Path(vault_dir) if vault_dir else VAULT_DIR
        self.running = False
        
        # Initialize agents
        self.business_agent = BusinessAgent(self.vault_dir)
        self.client_finder = ClientFinderAgent(self.vault_dir)
        self.outreach_agent = OutreachAgent(self.vault_dir)
        
        # Statistics
        self.stats = {
            "cycles_run": 0,
            "ideas_generated": 0,
            "clients_found": 0,
            "outreach_sent": 0,
            "errors": 0,
            "last_cycle": None,
            "start_time": None
        }
        
        # Ensure directories exist
        (self.vault_dir / "Inbox").mkdir(parents=True, exist_ok=True)
        (self.vault_dir / "Needs_Action").mkdir(parents=True, exist_ok=True)
        (self.vault_dir / "Reports").mkdir(parents=True, exist_ok=True)
    
    def run_business_cycle(self):
        """
        Run a complete business cycle:
        1. Generate business ideas
        2. Find potential clients
        3. Generate outreach messages
        4. Send outreach emails
        
        Returns:
            dict: Cycle results
        """
        cycle_start = datetime.now()
        logger.info(f"🚀 Starting business cycle #{self.stats['cycles_run'] + 1}")
        
        results = {
            "cycle_number": self.stats['cycles_run'] + 1,
            "timestamp": cycle_start.isoformat(),
            "ideas_generated": 0,
            "clients_found": 0,
            "outreach_generated": 0,
            "outreach_sent": 0,
            "errors": []
        }
        
        try:
            # Step 1: Generate business ideas
            logger.info("📌 Step 1: Generating business ideas...")
            try:
                new_ideas, total_ideas = self.business_agent.run(count=IDEAS_PER_CYCLE)
                results["ideas_generated"] = new_ideas
                self.stats["ideas_generated"] += new_ideas
                logger.info(f"   ✓ Generated {new_ideas} new ideas (Total: {total_ideas})")
            except Exception as e:
                error_msg = f"Error generating business ideas: {e}"
                logger.error(f"   ❌ {error_msg}")
                results["errors"].append(error_msg)
                self.stats["errors"] += 1
            
            # Step 2: Find potential clients
            logger.info("🎯 Step 2: Finding potential clients...")
            try:
                new_clients, total_clients = self.client_finder.run(count=CLIENTS_PER_CYCLE)
                results["clients_found"] = new_clients
                self.stats["clients_found"] += new_clients
                logger.info(f"   ✓ Found {new_clients} new clients (Total: {total_clients})")
            except Exception as e:
                error_msg = f"Error finding clients: {e}"
                logger.error(f"   ❌ {error_msg}")
                results["errors"].append(error_msg)
                self.stats["errors"] += 1
            
            # Step 3: Generate outreach messages
            logger.info("📧 Step 3: Generating outreach messages...")
            try:
                new_outreach, total_outreach = self.outreach_agent.run()
                results["outreach_generated"] = new_outreach
                logger.info(f"   ✓ Generated {new_outreach} new outreach messages (Total: {total_outreach})")
            except Exception as e:
                error_msg = f"Error generating outreach: {e}"
                logger.error(f"   ❌ {error_msg}")
                results["errors"].append(error_msg)
                self.stats["errors"] += 1
            
            # Step 4: Send outreach emails (if not dry run)
            logger.info("📤 Step 4: Sending outreach emails...")
            try:
                sent_count = self._send_outreach_emails(limit=MAX_OUTREACH_PER_CYCLE)
                results["outreach_sent"] = sent_count
                self.stats["outreach_sent"] += sent_count
                logger.info(f"   ✓ Sent {sent_count} outreach emails")
            except Exception as e:
                error_msg = f"Error sending outreach emails: {e}"
                logger.error(f"   ❌ {error_msg}")
                results["errors"].append(error_msg)
                self.stats["errors"] += 1
            
            # Update stats
            self.stats["cycles_run"] += 1
            self.stats["last_cycle"] = cycle_start.isoformat()
            
            if self.stats["start_time"] is None:
                self.stats["start_time"] = cycle_start.isoformat()
            
            # Save cycle report
            self._save_cycle_report(results)
            
            cycle_end = datetime.now()
            duration = (cycle_end - cycle_start).total_seconds()
            logger.info(f"✅ Business cycle completed in {duration:.2f} seconds")
            
        except Exception as e:
            error_msg = f"Critical error in business cycle: {e}"
            logger.error(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            self.stats["errors"] += 1
        
        return results
    
    def _send_outreach_emails(self, limit=5):
        """
        Send pending outreach emails via MCP Server
        
        Args:
            limit: Maximum number of emails to send per cycle
            
        Returns:
            int: Number of emails sent
        """
        pending_outreach = self.outreach_agent.get_pending_outreach()
        
        if not pending_outreach:
            logger.info("   No pending outreach to send")
            return 0
        
        sent_count = 0
        
        for outreach in pending_outreach[:limit]:
            if DRY_RUN:
                logger.info(f"   [DRY RUN] Would send to: {outreach.get('to', 'unknown')}")
                self.outreach_agent.mark_as_sent(outreach.get('id'))
                sent_count += 1
                continue
            
            try:
                # Send via MCP Server
                response = requests.post(
                    f"{MCP_SERVER_URL}/api/email/send",
                    json={
                        "to": outreach.get('to', ADMIN_EMAIL),
                        "subject": outreach.get('subject', 'Business Opportunity'),
                        "body": outreach.get('message', '')
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"   ✓ Sent to: {outreach.get('to')}")
                    self.outreach_agent.mark_as_sent(outreach.get('id'))
                    sent_count += 1
                else:
                    logger.warning(f"   ⚠️  Failed to send to {outreach.get('to')}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"   ❌ Error sending to {outreach.get('to')}: {e}")
            except Exception as e:
                logger.error(f"   ❌ Unexpected error: {e}")
        
        return sent_count
    
    def _save_cycle_report(self, results):
        """
        Save cycle report to file
        
        Args:
            results: Cycle results dictionary
        """
        reports_dir = self.vault_dir / "Reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = reports_dir / f"business_cycle_{results['cycle_number']:04d}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Also update latest report
        latest_report = reports_dir / "latest_cycle.json"
        with open(latest_report, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    def get_stats(self):
        """
        Get current statistics
        
        Returns:
            dict: Current statistics
        """
        return self.stats.copy()
    
    def run_continuous(self, interval=None):
        """
        Run business cycles continuously
        
        Args:
            interval: Seconds between cycles (default: LOOP_INTERVAL_SECONDS)
        """
        if interval is None:
            interval = LOOP_INTERVAL_SECONDS
        
        self.running = True
        self.stats["start_time"] = datetime.now().isoformat()
        
        logger.info("=" * 60)
        logger.info("🤖 AUTONOMOUS BUSINESS LOOP STARTED")
        logger.info(f"   Cycle interval: {interval} seconds")
        logger.info(f"   Ideas per cycle: {IDEAS_PER_CYCLE}")
        logger.info(f"   Clients per cycle: {CLIENTS_PER_CYCLE}")
        logger.info(f"   Max outreach per cycle: {MAX_OUTREACH_PER_CYCLE}")
        logger.info(f"   Dry run: {DRY_RUN}")
        logger.info("=" * 60)
        
        while self.running:
            try:
                self.run_business_cycle()
                
                # Wait for next cycle
                logger.info(f"⏳ Waiting {interval} seconds until next cycle...")
                for i in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("\n🛑 Received interrupt signal, stopping...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(10)  # Wait before retrying
        
        logger.info("✅ Autonomous business loop stopped")
    
    def stop(self):
        """Stop the continuous loop"""
        self.running = False


# Global instance for module-level access
_loop_instance = None


def get_loop_instance():
    """Get or create the global loop instance"""
    global _loop_instance
    if _loop_instance is None:
        _loop_instance = AutonomousBusinessLoop()
    return _loop_instance


def run_business_cycle():
    """
    Run a single business cycle (convenience function)
    
    Returns:
        dict: Cycle results
    """
    loop = get_loop_instance()
    return loop.run_business_cycle()


def get_stats():
    """
    Get current statistics (convenience function)
    
    Returns:
        dict: Current statistics
    """
    loop = get_loop_instance()
    return loop.get_stats()


def start_autonomous_loop(interval=None):
    """
    Start the autonomous loop in a blocking manner
    
    Args:
        interval: Optional interval in seconds
    """
    loop = get_loop_instance()
    loop.run_continuous(interval)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🤖  AUTONOMOUS BUSINESS LOOP  🤖                     ║
║                                                           ║
║     Generating Ideas • Finding Clients • Sending Outreach ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomous Business Loop')
    parser.add_argument('--interval', type=int, default=LOOP_INTERVAL_SECONDS,
                        help=f'Interval between cycles in seconds (default: {LOOP_INTERVAL_SECONDS})')
    parser.add_argument('--once', action='store_true',
                        help='Run only one cycle and exit')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run in dry-run mode (no actual emails sent)')
    
    args = parser.parse_args()

    if args.dry_run:
        DRY_RUN = True  # Override for this session
        logger.info("🔸 Running in DRY-RUN mode (no emails will be sent)")
    
    loop = AutonomousBusinessLoop()
    
    if args.once:
        # Run single cycle
        results = loop.run_business_cycle()
        print("\n" + "=" * 60)
        print("  CYCLE RESULTS")
        print("=" * 60)
        print(f"  Ideas generated: {results['ideas_generated']}")
        print(f"  Clients found: {results['clients_found']}")
        print(f"  Outreach generated: {results['outreach_generated']}")
        print(f"  Outreach sent: {results['outreach_sent']}")
        print(f"  Errors: {len(results['errors'])}")
        print("=" * 60)
    else:
        # Run continuous
        try:
            loop.run_continuous(interval=args.interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopped by user")
            loop.stop()
