"""
Test the process_approved_tasks functionality of Action_Agent
"""

from Agents.Action_Agent import Action_Agent
import os

def test_process_approved():
    print("[ACTION] Testing process_approved_tasks functionality...")
    
    # Initialize the Action_Agent
    action_agent = Action_Agent()
    
    # Check initial directory contents
    initial_approved = len(os.listdir('Approved')) if os.path.exists('Approved') else 0
    initial_done = len(os.listdir('Done')) if os.path.exists('Done') else 0
    initial_error = len(os.listdir('Error')) if os.path.exists('Error') else 0
    
    print(f"Initial directory status:")
    print(f"  Approved: {initial_approved}")
    print(f"  Done: {initial_done}")
    print(f"  Error: {initial_error}")
    
    print('\n[ACTION] Processing tasks from Approved directory...')
    results = action_agent.process_approved_tasks()
    
    print(f'Processed {len(results)} tasks from Approved directory')
    for i, result in enumerate(results):
        print(f'  Task {i+1}: {result["status"]} - {result["message"]}')
    
    # Check directory contents after processing
    final_approved = len(os.listdir('Approved')) if os.path.exists('Approved') else 0
    final_done = len(os.listdir('Done')) if os.path.exists('Done') else 0
    final_error = len(os.listdir('Error')) if os.path.exists('Error') else 0
    
    print(f'\nFinal directory status after processing:')
    print(f'  Approved: {final_approved} (moved {initial_approved - final_approved})')
    print(f'  Done: {final_done} (added {final_done - initial_done})')
    print(f'  Error: {final_error} (added {final_error - initial_error})')

if __name__ == "__main__":
    test_process_approved()