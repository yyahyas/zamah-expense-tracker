import sys
import json
import subprocess

try:
    data = json.load(sys.stdin)
except:
    pass

ps_script = """
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.Visible = $true
$notify.ShowBalloonTip(5000, 'Zamah - Claude Needs You', 'Claude has finished and may be waiting for input!', [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -Seconds 6
$notify.Dispose()
"""

subprocess.run(
    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

print(json.dumps({"decision": "approve"}))
