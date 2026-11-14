' Boltsmith - silent launcher (no console window)
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
d = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = d
uv = sh.ExpandEnvironmentStrings("%USERPROFILE%") & "\.local\bin\uv.exe"
If fso.FileExists(uv) Then
  sh.Run """" & uv & """ run --python 3.12 --with build123d==0.13.0 --with bd_warehouse==0.4.0 python """ & d & "\fastener_gui.py""", 0, False
Else
  ' first start: show the console (installs uv and downloads the CAD kernel)
  sh.Run "cmd /c """ & d & "\Fastener_Generator.bat""", 1, False
End If
