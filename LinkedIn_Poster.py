"""
LinkedIn Poster - Silver Tier Component
Automatically posts business updates to LinkedIn
"""

import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
import requests
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/linkedin_poster.log'),
        logging.StreamHandler()
    ]
)

class LinkedInPoster:
    def __init__(self):
        self.posts_dir = "LinkedIn_Posts"
        self.logs_dir = "Logs"
        self.needs_action_dir = "Needs_Action"
        
        # Create directories if they don't exist
        self._create_directories()
        
        # Configuration - in a real system, these would come from environment variables
        self.linkedin_config = {
            'access_token': os.getenv('LINKEDIN_ACCESS_TOKEN', 'your_access_token'),
            'person_id': os.getenv('LINKEDIN_PERSON_ID', 'your_person_id'),
            'organization_id': os.getenv('LINKEDIN_ORGANIZATION_ID', 'your_org_id')
        }
        
        # MCP server connection
        self.mcp_server_url = 'http://localhost:5001/api'
        
        logging.info("LinkedIn Poster initialized")
    
    def _create_directories(self):
        """Create required directories if they don't exist"""
        dirs_to_create = [
            self.posts_dir,
            self.logs_dir,
            self.needs_action_dir
        ]
        
        for dir_path in dirs_to_create:
            path = Path(dir_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created directory: {dir_path}")
    
    def generate_business_update(self):
        """Generate a business update post"""
        business_updates = [
            {
                "title": "Industry Insights",
                "content": "Exciting developments in our industry this week! We're seeing innovative approaches to customer engagement that are reshaping how businesses connect with their audiences. Staying ahead of these trends is crucial for maintaining competitive advantage.",
                "hashtags": ["#Innovation", "#Business", "#Leadership"]
            },
            {
                "title": "Team Achievement",
                "content": "Proud to announce that our team has successfully completed another milestone in our project portfolio. This achievement reflects our commitment to excellence and collaborative effort. Grateful for such talented professionals!",
                "hashtags": ["#Teamwork", "#Achievement", "#Success"]
            },
            {
                "title": "Market Trends",
                "content": "Analyzing current market trends reveals interesting shifts in consumer behavior. Companies that adapt quickly to these changes position themselves for sustained growth. Agility and customer focus remain key differentiators.",
                "hashtags": ["#MarketTrends", "#Strategy", "#Growth"]
            },
            {
                "title": "Client Success Story",
                "content": "Just wrapped up an amazing project with a valued client! Seeing our solutions drive real business results is what motivates our team every day. Thank you for the trust and collaboration!",
                "hashtags": ["#Clients", "#Success", "#Partnership"]
            },
            {
                "title": "Thought Leadership",
                "content": "Reflecting on the importance of sustainable business practices. Today's companies have a responsibility to balance profit with purpose, creating value for all stakeholders while contributing positively to society.",
                "hashtags": ["#Leadership", "#Sustainability", "#Purpose"]
            }
        ]
        
        return random.choice(business_updates)
    
    def generate_sales_post(self):
        """Generate a sales-related post"""
        sales_posts = [
            {
                "title": "Sales Tip Tuesday",
                "content": "Building genuine relationships is the foundation of successful sales. Focus on understanding your client's challenges and how your solution addresses their specific needs. Trust leads to lasting partnerships.",
                "hashtags": ["#SalesTips", "#RelationshipBuilding", "#CustomerFocus"]
            },
            {
                "title": "Value Proposition",
                "content": "What sets us apart? Our commitment to delivering measurable results that exceed expectations. We don't just sell products; we provide solutions that drive meaningful business outcomes.",
                "hashtags": ["#Value", "#Results", "#Solutions"]
            },
            {
                "title": "Client-Centric Approach",
                "content": "Our success is measured by our clients' success. By deeply understanding their objectives, we can tailor our approach to deliver the most impactful solutions for their unique situations.",
                "hashtags": ["#ClientFocus", "#Partnership", "#Results"]
            },
            {
                "title": "Industry Expertise",
                "content": "Years of experience in our field have taught us that every client is unique. We leverage our expertise to provide customized strategies that align with specific business goals and market conditions.",
                "hashtags": ["#Expertise", "#CustomSolutions", "#Experience"]
            }
        ]
        
        return random.choice(sales_posts)
    
    def create_linkedin_post(self, post_type="business"):
        """Create a LinkedIn post"""
        if post_type == "sales":
            post_data = self.generate_sales_post()
        else:
            post_data = self.generate_business_update()
        
        # Generate a unique post ID
        post_id = f"linkedin_post_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Create post content
        post_content = {
            "id": post_id,
            "title": post_data["title"],
            "content": post_data["content"],
            "hashtags": post_data["hashtags"],
            "type": post_type,
            "scheduled_time": datetime.now().isoformat(),
            "status": "draft",
            "created_at": datetime.now().isoformat()
        }
        
        # Save the post draft
        post_filename = f"{post_id}.json"
        post_path = os.path.join(self.posts_dir, post_filename)
        
        with open(post_path, 'w', encoding='utf-8') as f:
            json.dump(post_content, f, indent=2)
        
        logging.info(f"Created LinkedIn post draft: {post_filename}")
        return post_path, post_content
    
    def post_to_linkedin_via_mcp(self, content, hashtags=None):
        """Post to LinkedIn using the MCP server"""
        try:
            payload = {
                "action_type": "social_post",
                "platform": "linkedin",
                "content": content,
                "hashtags": hashtags or [],
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(f"{self.mcp_server_url}/social/post", 
                                   json=payload, 
                                   headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                logging.info(f"LinkedIn post sent via MCP: {content[:50]}...")
                return response.json()
            else:
                logging.error(f"Failed to post to LinkedIn via MCP: {response.text}")
                return None
        except Exception as e:
            logging.error(f"Error posting to LinkedIn via MCP: {str(e)}")
            return None
    
    def schedule_daily_post(self):
        """Schedule a daily LinkedIn post"""
        # Create a business update
        post_path, post_content = self.create_linkedin_post("business")
        
        # Create a task to post it
        task_id = f"linkedin_task_{int(time.time())}"
        
        task_content = {
            "task_id": task_id,
            "task_type": "linkedin_post",
            "priority": "MEDIUM",
            "title": f"LinkedIn Post: {post_content['title']}",
            "description": f"Post to LinkedIn: {post_content['content'][:100]}...",
            "assigned_to": "Social_Agent",
            "deadline": datetime.now().strftime('%Y-%m-%d'),
            "status": "pending",
            "sensitive": False,
            "details": {
                "post_content": post_content['content'],
                "hashtags": post_content['hashtags'],
                "post_type": post_content['type']
            },
            "created_at": datetime.now().isoformat(),
            "source": "linkedin_scheduler"
        }
        
        # Save the task to Needs_Action
        task_filename = f"{task_id}.json"
        task_path = os.path.join(self.needs_action_dir, task_filename)
        
        with open(task_path, 'w', encoding='utf-8') as f:
            json.dump(task_content, f, indent=2)
        
        logging.info(f"Created scheduled LinkedIn post task: {task_filename}")
        return task_path
    
    def auto_generate_daily_posts(self):
        """Automatically generate daily posts"""
        logging.info("Generating daily LinkedIn posts...")
        
        # Generate a business update
        business_post_path, business_post = self.create_linkedin_post("business")
        
        # Create task for business post
        business_task_path = self.create_task_for_post(business_post, "business")
        
        # Generate a sales post every other day
        if datetime.now().day % 2 == 0:
            sales_post_path, sales_post = self.create_linkedin_post("sales")
            sales_task_path = self.create_task_for_post(sales_post, "sales")
            logging.info(f"Generated business and sales posts for today")
        else:
            logging.info(f"Generated business post for today")
    
    def create_task_for_post(self, post_content, post_type):
        """Create a task for a LinkedIn post"""
        task_id = f"linkedin_task_{post_content['id']}"
        
        task_content = {
            "task_id": task_id,
            "task_type": "linkedin_post",
            "priority": "MEDIUM",
            "title": f"LinkedIn {post_type.title()} Post: {post_content['title']}",
            "description": f"Post to LinkedIn: {post_content['content'][:100]}...",
            "assigned_to": "Social_Agent",
            "deadline": datetime.now().strftime('%Y-%m-%d'),
            "status": "pending",
            "sensitive": False,
            "details": {
                "post_content": post_content['content'],
                "hashtags": post_content['hashtags'],
                "post_type": post_type,
                "post_id": post_content['id']
            },
            "created_at": datetime.now().isoformat(),
            "source": "linkedin_auto_generator"
        }
        
        # Save the task to Needs_Action
        task_filename = f"{task_id}.json"
        task_path = os.path.join(self.needs_action_dir, task_filename)
        
        with open(task_path, 'w', encoding='utf-8') as f:
            json.dump(task_content, f, indent=2)
        
        logging.info(f"Created LinkedIn post task: {task_filename}")
        return task_path
    
    def run_daily_generation(self, interval_hours=24):
        """Run the daily post generation"""
        logging.info(f"LinkedIn Poster started, generating posts every {interval_hours} hours")
        
        print("LinkedIn Poster is running...")
        print("Automatically generating business and sales posts...")
        print(f"Generating new posts every {interval_hours} hours...")
        print("Press Ctrl+C to stop")
        
        try:
            # Generate initial posts
            self.auto_generate_daily_posts()
            
            while True:
                # Wait for the specified interval
                time.sleep(interval_hours * 3600)  # Convert hours to seconds
                
                # Generate new posts
                self.auto_generate_daily_posts()
                
        except KeyboardInterrupt:
            logging.info("LinkedIn Poster stopped by user")
            print("\nLinkedIn Poster stopped.")
        except Exception as e:
            error_msg = f"Error in LinkedIn Poster: {str(e)}"
            logging.error(error_msg)
            print(f"\nError: {error_msg}")

def main():
    poster = LinkedInPoster()
    poster.run_daily_generation()

if __name__ == "__main__":
    main()