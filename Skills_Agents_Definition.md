# Skills & Agents Definition

## Available Skills

### 1. read_task
- **Purpose:** Read markdown file in `/Needs_Action/` and parse metadata (title, type, sensitive)
- **Input:** File path to task markdown file
- **Output:** Dictionary containing task metadata
- **Implementation:** `parse_task_file()` method in TaskAgent class

### 2. create_plan
- **Purpose:** Create plan file in `/Plans/PLAN_<task_title>.md` with checkboxes
- **Input:** Task title and details
- **Output:** Plan markdown file with checklist
- **Implementation:** `create_plan()` method in TaskAgent class

### 3. request_approval
- **Purpose:** If `sensitive: yes`, generate `/Pending_Approval/APPROVAL_<task_title>.md` and wait for approval
- **Input:** Task file path
- **Output:** Moves task to Pending Approval folder
- **Implementation:** Logic in `process_task()` method when sensitive=yes

### 4. mark_done
- **Purpose:** Move original task file to `/Done/`
- **Input:** Task file path
- **Output:** Moves task to Done folder
- **Implementation:** `check_approved_tasks()` method in TaskAgent class

### 5. log_action
- **Purpose:** Log task action in `/Logs/YYYY-MM-DD.log` in JSON format
- **Input:** Task ID, action, status, details
- **Output:** Timestamped log file
- **Implementation:** `log_action()` method in TaskAgent class

## Agent Definition

### task_agent
- **Role:** Local Personal AI Employee running in VS Code
- **Tier:** Bronze (simple task management)
- **Responsibilities:**
  - Monitor /Needs_Action/ for new tasks
  - Process tasks according to sensitivity flags
  - Create plans for all tasks
  - Handle approval workflow for sensitive tasks
  - Log all actions
  - Maintain folder organization

### Main Loop Behavior
1. Continuously scan /Needs_Action/ for new task files
2. For each task:
   - Parse metadata using read_task skill
   - Create plan using create_plan skill
   - If sensitive, use request_approval skill
   - When complete, use mark_done skill
   - Log all actions using log_action skill

## Usage Example
```
# The agent runs continuously in the background
# New tasks added to /Needs_Action/ are automatically processed
# Sensitive tasks require manual approval in /Approved/ folder
# All actions are logged in /Logs/ folder
```