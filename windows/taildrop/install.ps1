# Copies tdsend.ps1 to %LOCALAPPDATA%\tdsend and adds a Start Menu shortcut on Ctrl+Alt+D.
# Windows only honours shortcut hotkeys for .lnk files in the Start Menu or on the desktop.
$dir = Join-Path $env:LOCALAPPDATA "tdsend"
New-Item -ItemType Directory -Force $dir | Out-Null
Copy-Item (Join-Path $PSScriptRoot "tdsend.ps1") $dir -Force

$lnk = Join-Path ([Environment]::GetFolderPath("Programs")) "Taildrop clipboard.lnk"
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
$s.TargetPath = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$s.Arguments = "-NoProfile -STA -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$dir\tdsend.ps1`""
$s.Hotkey = "CTRL+ALT+D"
$s.WindowStyle = 7
$s.IconLocation = "C:\Program Files\Tailscale\tailscale-ipn.exe,0"
$s.Description = "Taildrop the clipboard to a tailnet device"
$s.Save()
"installed: $lnk (Ctrl+Alt+D)"
