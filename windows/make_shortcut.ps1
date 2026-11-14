# Creates "Boltsmith" shortcuts (Desktop + Start menu) with the icon
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ws = New-Object -ComObject WScript.Shell
foreach ($dir in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {
  $lnk = $ws.CreateShortcut((Join-Path $dir 'Boltsmith.lnk'))
  $lnk.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
  $lnk.Arguments = '"' + (Join-Path $here 'Boltsmith.vbs') + '"'
  $lnk.WorkingDirectory = $here
  $lnk.IconLocation = (Join-Path $here 'boltsmith.ico') + ',0'
  $lnk.Description = 'Boltsmith - fastener generator (STEP)'
  $lnk.Save()
  Write-Host ('Created: ' + (Join-Path $dir 'Boltsmith.lnk'))
}
