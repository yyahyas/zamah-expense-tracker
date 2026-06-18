import sys
import json
from datetime import datetime

LOG_FILE = r"C:\Users\SAMAUNG\Downloads\CLAUDE CODE\zamah-expense-tracker\.claude\hooks\activity.log"

try:
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    detail = ""
    if tool == "Bash":
        detail = tool_input.get("command", "")[:100]
    elif tool in ["Write", "Edit", "MultiEdit"]:
        detail = tool_input.get("file_path", "")
    elif tool == "Read":
        detail = tool_input.get("file_path", "")
    elif tool == "TodoWrite":
        detail = str(tool_input.get("todos", ""))[:100]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] TOOL: {tool} | {detail}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

except Exception as e:
    pass

print(json.dumps({"decision": "approve"}))
