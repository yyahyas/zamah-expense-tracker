import sys
import json

# Files and folders to protect
PROTECTED = [
    "zamah.db",
    "app.py",
    "CLAUDE.md",
    ".mcp.json",
    "requirements.txt",
    ".env",
    "templates",
    "static",
    "database",
]

def is_dangerous(text):
    if not text:
        return False, ""
    text_lower = text.lower()
    for item in PROTECTED:
        if item in text_lower:
            dangerous_cmds = ["rm ", "del ", "delete", "drop table", "drop database", "shutil.rmtree", "os.remove"]
            for cmd in dangerous_cmds:
                if cmd in text_lower:
                    return True, item
    return False, ""

try:
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    check_text = ""
    if tool == "Bash":
        check_text = tool_input.get("command", "")
    elif tool in ["Write", "Edit", "MultiEdit"]:
        check_text = tool_input.get("file_path", "")

    dangerous, matched = is_dangerous(check_text)

    if dangerous:
        print(json.dumps({
            "decision": "block",
            "reason": f"BLOCKED: Attempt to delete or damage protected file/folder: '{matched}'. This is protected and cannot be deleted."
        }))
    else:
        print(json.dumps({"decision": "approve"}))

except Exception as e:
    print(json.dumps({"decision": "approve"}))
