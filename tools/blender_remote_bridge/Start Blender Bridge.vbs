Option Explicit
Dim shell, files, folder, python, code
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
python = "C:\Program Files\Python314\pythonw.exe"
If Not files.FileExists(python) Then
    python = "pythonw.exe"
End If
code = Chr(34) & python & Chr(34) & " " & Chr(34) & folder & "\launcher\app.py" & Chr(34)
shell.Run code, 1, False
