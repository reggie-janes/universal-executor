' Universal Executor — silent Windows launcher (system Python, no uv).
' Double-click to run the app with no console window.
' Equivalent to: cd <this folder> && pythonw main.py

Set shell = CreateObject("WScript.Shell")
Set fso   = CreateObject("Scripting.FileSystemObject")

shell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)

' --- Check 1: pythonw.exe is on PATH ---------------------------------------
exitCode = shell.Run("cmd /c where pythonw >nul 2>&1", 0, True)
If exitCode <> 0 Then
    MsgBox "Python was not found on PATH." & vbCrLf & vbCrLf & _
           "Install Python 3.11 or newer from:" & vbCrLf & _
           "    https://www.python.org/downloads/" & vbCrLf & vbCrLf & _
           "During install, tick 'Add python.exe to PATH'.", _
           vbExclamation, "Universal Executor"
    WScript.Quit 1
End If

' --- Check 2: dearpygui is importable in the global interpreter ------------
exitCode = shell.Run("cmd /c python -c ""import dearpygui.dearpygui"" >nul 2>&1", 0, True)
If exitCode <> 0 Then
    MsgBox "The 'dearpygui' package is not installed in the global Python." & vbCrLf & vbCrLf & _
           "Open Command Prompt or PowerShell and run:" & vbCrLf & _
           "    pip install dearpygui" & vbCrLf & vbCrLf & _
           "Then double-click this launcher again.", _
           vbExclamation, "Universal Executor"
    WScript.Quit 1
End If

' --- Launch silently --------------------------------------------------------
' 0 = hidden window, False = don't wait for the app to exit.
shell.Run "pythonw main.py", 0, False
