# Windows Task Scheduler Setup

## Run at Startup

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Gold Tier AI Employee"
4. Trigger: "When I log on"
5. Action: "Start a program"
6. Program: `python.exe`
7. Arguments: `D:\hackthone-0\run_all.py`
8. Start in: `D:\hackthone-0`

## Individual Components

### MCP Servers
```
Program: python.exe
Arguments: D:\hackthone-0\MCP_Servers\MCP_Comms_Server.py
```

### Orchestrator
```
Program: python.exe
Arguments: D:\hackthone-0\Agents\Orchestrator_Agent.py
```

### Scheduler
```
Program: python.exe
Arguments: D:\hackthone-0\Scheduler\Gold_Tier_Scheduler.py
```

### Watchers
```
Program: python.exe
Arguments: D:\hackthone-0\Gmail_Watcher.py
```
