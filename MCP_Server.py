"""
MCP Server - Message Control Protocol
Handles external actions like sending emails, posting to social media, etc.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
import threading
import time
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/mcp_server.log'),
        logging.StreamHandler()
    ]
)

class MCPServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        self.action_counter = 0
        
        # Create logs directory if it doesn't exist
        Path("Logs").mkdir(exist_ok=True)
        
        logging.info("MCP Server initialized")
    
    def setup_routes(self):
        """Setup API routes for different actions"""
        @self.app.route('/api/action', methods=['POST'])
        def execute_action():
            return self.handle_action_request()
        
        @self.app.route('/api/email/send', methods=['POST'])
        def send_email():
            return self.handle_email_request()
        
        @self.app.route('/api/social/post', methods=['POST'])
        def post_social():
            return self.handle_social_post_request()
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    def handle_action_request(self):
        """Handle generic action requests"""
        try:
            data = request.json
            action_type = data.get('action_type')
            task_id = data.get('task_id', f'action_{self.action_counter}')
            self.action_counter += 1
            
            logging.info(f"Received action request: {action_type} for task {task_id}")
            
            # Log the action
            self.log_action(task_id, action_type, "received", data)
            
            # Execute the action based on type
            result = self.execute_action(action_type, data)
            
            # Log completion
            self.log_action(task_id, action_type, "completed", result)
            
            return jsonify({
                "status": "success",
                "task_id": task_id,
                "result": result
            })
        except Exception as e:
            logging.error(f"Error handling action request: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    def handle_email_request(self):
        """Handle email sending requests"""
        try:
            data = request.json
            task_id = data.get('task_id', f'email_{self.action_counter}')
            self.action_counter += 1
            
            logging.info(f"Received email request for task {task_id}")
            
            # Simulate email sending
            result = self.send_email_simulation(data)
            
            # Log the action
            self.log_action(task_id, "email_send", "completed", result)
            
            return jsonify({
                "status": "success",
                "task_id": task_id,
                "result": result
            })
        except Exception as e:
            logging.error(f"Error handling email request: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    def handle_social_post_request(self):
        """Handle social media posting requests"""
        try:
            data = request.json
            platform = data.get('platform', 'unknown')
            task_id = data.get('task_id', f'social_{self.action_counter}')
            self.action_counter += 1
            
            logging.info(f"Received {platform} post request for task {task_id}")
            
            # Simulate social media posting
            result = self.post_social_media_simulation(data)
            
            # Log the action
            self.log_action(task_id, f"social_post_{platform}", "completed", result)
            
            return jsonify({
                "status": "success",
                "task_id": task_id,
                "result": result
            })
        except Exception as e:
            logging.error(f"Error handling social post request: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    def execute_action(self, action_type, data):
        """Execute the requested action based on type"""
        if action_type == "email_send":
            return self.send_email_simulation(data)
        elif action_type == "social_post":
            return self.post_social_media_simulation(data)
        elif action_type == "file_process":
            return self.process_file_simulation(data)
        elif action_type == "system_command":
            return self.execute_system_command_simulation(data)
        else:
            return {"error": f"Unknown action type: {action_type}"}
    
    def send_email_simulation(self, data):
        """Simulate sending an email"""
        # In a real implementation, this would connect to an email service
        email_data = {
            "to": data.get('to', 'recipient@example.com'),
            "subject": data.get('subject', 'Default Subject'),
            "body": data.get('body', 'Default body content'),
            "status": "sent_simulation",
            "timestamp": datetime.now().isoformat()
        }
        
        logging.info(f"Email sent simulation: {email_data['subject']}")
        return email_data
    
    def post_social_media_simulation(self, data):
        """Simulate posting to social media"""
        # In a real implementation, this would connect to social media APIs
        post_data = {
            "platform": data.get('platform', 'unknown'),
            "content": data.get('content', 'Default content'),
            "hashtags": data.get('hashtags', []),
            "status": "posted_simulation",
            "timestamp": datetime.now().isoformat()
        }
        
        logging.info(f"Posted to {post_data['platform']}: {post_data['content'][:50]}...")
        return post_data
    
    def process_file_simulation(self, data):
        """Simulate file processing"""
        file_data = {
            "filename": data.get('filename', 'unknown'),
            "action": data.get('action', 'process'),
            "status": "processed_simulation",
            "timestamp": datetime.now().isoformat()
        }
        
        logging.info(f"File processed: {file_data['filename']}")
        return file_data
    
    def execute_system_command_simulation(self, data):
        """Simulate executing a system command"""
        cmd_data = {
            "command": data.get('command', 'unknown'),
            "status": "executed_simulation",
            "timestamp": datetime.now().isoformat()
        }
        
        logging.info(f"Command executed: {cmd_data['command']}")
        return cmd_data
    
    def log_action(self, task_id, action_type, status, details):
        """Log action to a file"""
        log_entry = {
            "task_id": task_id,
            "action_type": action_type,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        log_filename = f"Logs/mcp_action_{task_id}.json"
        with open(log_filename, 'w') as f:
            json.dump(log_entry, f, indent=2)
    
    def run(self, host='localhost', port=5001, debug=False):
        """Start the MCP server"""
        logging.info(f"MCP Server starting on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def main():
    server = MCPServer()
    server.run()

if __name__ == "__main__":
    main()