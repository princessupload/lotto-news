Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get script directory
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' Change to lottery-tracker directory
WshShell.CurrentDirectory = scriptPath

' Start the server in a visible window
WshShell.Run "cmd /k python server.py", 1, False

' Wait for server to start
WScript.Sleep 2500

' Open browser
WshShell.Run "http://localhost:8000", 1, False

' Start auto-updater in a visible window
WshShell.Run "cmd /k python auto_scheduler.py", 1, False
