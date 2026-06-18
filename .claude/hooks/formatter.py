import sys
import json
import subprocess

try:
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    file_path = ""
    if tool in ["Write", "Edit", "MultiEdit"]:
        file_path = tool_input.get("file_path", "")

    if file_path:
        if file_path.endswith(".py"):
            subprocess.run(
                ["black", file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif file_path.endswith((".html", ".css", ".js")):
            subprocess.run(
                ["prettier", "--write", file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

except Exception as e:
    pass

print(json.dumps({"decision": "approve"}))
