"""
Gold Tier Autonomous AI Employee System
Main entry point for the autonomous AI employee

Features:
- Multi-channel watchers (Gmail, WhatsApp, LinkedIn, Twitter, Facebook)
- Claude-powered reasoning loop
- Human-in-the-loop approval workflow
- MCP Server integration for real actions
- Odoo 19+ accounting integration
- Automated CEO briefings
- Multi-agent modular architecture
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding
class Utf8StreamHandler(logging.StreamHandler):
    """Stream handler that handles UTF-8 encoding for Windows console"""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if hasattr(stream, 'buffer'):
                stream.buffer.write((msg + self.terminator).encode('utf-8', errors='replace'))
                stream.flush()
            else:
                stream.write(msg + self.terminator)
                stream.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/gold_tier_agent.log', encoding='utf-8'),
        Utf8StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GoldTierAgent:
    """
    Autonomous AI Employee - Gold Tier
    Manages personal + business tasks across multiple channels
    """

    def __init__(self):
        self.version = "3.0.0-Gold-Autonomous"
        
        # Directory structure
        self.dirs = {
            'inbox': Path('Inbox'),
            'needs_action': Path('Needs_Action'),
            'whatsapp_inbox': Path('WhatsApp_Inbox'),
            'linkedin_posts': Path('LinkedIn_Posts'),
            'gmail_inbox': Path('Gmail_Inbox'),
            'plans': Path('Plans'),
            'done': Path('Done'),
            'logs': Path('Logs'),
            'pending_approval': Path('Pending_Approval'),
            'approved': Path('Approved'),
            'accounting': Path('Accounting'),
            'skills': Path('Skills'),
            'agents': Path('Agents'),
            'errors': Path('Error')
        }

        # Create all directories
        self._create_directories()

        # MCP Server connection
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:5001')

        # Agent status
        self.status = 'idle'
        self.tasks_processed = 0
        self.start_time = datetime.now()

        # Initialize components
        self.orchestrator = None
        self.watchers = {}
        self.agents = {}

        logger.info(f"Gold Tier Agent initialized v{self.version}")

    def _create_directories(self):
        """Create all required directories"""
        for dir_name, dir_path in self.dirs.items():
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Directory verified: {dir_name} -> {dir_path}")

    def initialize_components(self):
        """Initialize all system components"""
        logger.info("Initializing Gold Tier components...")

        # Import and initialize orchestrator
        try:
            from Agents.FTE_Orchestrator_Gold import GoldTierOrchestrator
            self.orchestrator = GoldTierOrchestrator()
            logger.info("✅ Orchestrator initialized")
        except ImportError as e:
            logger.warning(f"⚠️  Orchestrator not available: {e}")

        # Import and initialize watchers
        self._initialize_watchers()

        # Register agents
        self._register_agents()

        logger.info("✅ All components initialized")

    def _initialize_watchers(self):
        """Initialize all watchers"""
        watchers = {
            'gmail': 'Gmail_Watcher_Gold',
            'whatsapp': 'WhatsApp_Watcher_Gold',
            'linkedin': 'LinkedIn_Poster_Gold'
        }

        for name, module in watchers.items():
            try:
                mod = __import__(module.replace('_Gold', ''), fromlist=[''])
                watcher_class = getattr(mod, module)
                self.watchers[name] = watcher_class()
                logger.info(f"✅ {name} watcher initialized")
            except Exception as e:
                logger.warning(f"⚠️  {name} watcher not available: {e}")

    def _register_agents(self):
        """Register all AI agents"""
        agents = {
            'Comms_Agent': 'Communication agent (email, social media)',
            'Finance_Agent': 'Finance agent (Odoo, accounting)',
            'Monitoring_Agent': 'Monitoring agent (task detection)',
            'Action_Agent': 'General action agent'
        }

        for agent_name, description in agents.items():
            self.agents[agent_name] = {
                'description': description,
                'status': 'idle',
                'tasks_completed': 0
            }
            logger.info(f"✅ {agent_name} registered: {description}")

    def process_task_lifecycle(self):
        """Process complete task lifecycle"""
        logger.info("Processing task lifecycle...")

        if not self.orchestrator:
            logger.warning("Orchestrator not available, skipping task processing")
            return

        try:
            # Process tasks from Needs_Action
            self.orchestrator.process_needs_action()

            # Process approved tasks
            self.orchestrator.process_approved_tasks()

            self.tasks_processed += 1

        except Exception as e:
            logger.error(f"Error in task lifecycle: {str(e)}")

    def generate_status_report(self):
        """Generate current system status report"""
        uptime = datetime.now() - self.start_time
        
        report = {
            'version': self.version,
            'status': self.status,
            'uptime': str(uptime),
            'tasks_processed': self.tasks_processed,
            'timestamp': datetime.now().isoformat(),
            'directories': {
                name: len(list(path.glob('*.json'))) if path.exists() else 0
                for name, path in self.dirs.items()
            },
            'agents': self.agents
        }

        return report

    def save_status_report(self):
        """Save status report to Logs directory"""
        report = self.generate_status_report()
        
        report_file = self.dirs['logs'] / f"status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Status report saved: {report_file}")
        return report

    def run(self, cycle_seconds=5):
        """Main autonomous loop"""
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆  GOLD TIER AUTONOMOUS AI EMPLOYEE  🏆             ║
║                                                           ║
║     Version: {self.version}
║     Status: Autonomous Mode
║                                                           ║
║     Components:                                           ║
║     • Multi-Channel Watchers (Gmail, WhatsApp, LinkedIn) ║
║     • Claude Reasoning Loop                               ║
║     • Human-in-the-Loop Approval                          ║
║     • MCP Server (Email, Social, Odoo)                   ║
║     • Automated CEO Briefings                             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)

        logger.info(f"Gold Tier Agent starting autonomous mode (cycle: {cycle_seconds}s)")
        print(f"🤖 Gold Tier Agent running... (cycle: {cycle_seconds}s)")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                # Process task lifecycle
                self.process_task_lifecycle()

                # Save periodic status report
                if self.tasks_processed % 10 == 0:
                    self.save_status_report()

                time.sleep(cycle_seconds)

        except KeyboardInterrupt:
            logger.info("Gold Tier Agent stopped by user")
            print("\n🛑 Gold Tier Agent stopped.")
            
            # Final status report
            final_report = self.save_status_report()
            print(f"\n📊 Final Status:")
            print(f"   Tasks Processed: {self.tasks_processed}")
            print(f"   Uptime: {final_report['uptime']}")
            
        except Exception as e:
            logger.error(f"Critical error in Gold Tier Agent: {str(e)}")
            print(f"\n❌ Error: {str(e)}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Gold Tier Autonomous AI Employee')
    parser.add_argument('--cycle', type=int, default=5, help='Processing cycle in seconds')
    parser.add_argument('--init-only', action='store_true', help='Initialize only, don\'t run')
    args = parser.parse_args()

    # Create and initialize agent
    agent = GoldTierAgent()
    agent.initialize_components()

    if args.init_only:
        print("\n✅ Initialization complete. Run without --init-only to start autonomous mode.")
        return

    # Run autonomous mode
    agent.run(cycle_seconds=args.cycle)


if __name__ == "__main__":
    main()
