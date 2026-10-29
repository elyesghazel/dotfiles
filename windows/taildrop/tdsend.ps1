# Taildrop the clipboard from Windows, the counterpart of the zunder `send` plugin.
# Ctrl+Alt+D opens a device list (last device on top), Enter sends what's on the clipboard:
# a screenshot as PNG, copied files as themselves, text as a .txt. Esc closes.
# Received files land in Downloads. Installed by install.ps1 next to this file.
param([string]$To)

Add-Type -AssemblyName System.Windows.Forms, System.Drawing

$Tailscale = "C:\Program Files\Tailscale\tailscale.exe"
$State = Join-Path $env:LOCALAPPDATA "tdsend"
$LastFile = Join-Path $State "last"
$Out = Join-Path $env:TEMP "tdsend"
$Default = "elyes-laptop"
$Hide = @("u363359-wsl")  # WSL on this laptop, not another device
$Labels = @{
    "elyes-laptop"        = "Arch laptop"
    "elyes-arch"          = "PC"
    "elyes-iphone"        = "iPhone"
    "elyes-ghazel-server" = "VPS"
    "pi"                  = "Pi"
    "pixel-9"             = "Pixel"
}
New-Item -ItemType Directory -Force $State, $Out | Out-Null
$Clip = [System.Windows.Forms.Clipboard]

function Label($h) { if ($Labels.ContainsKey($h)) { $Labels[$h] } else { $h } }

function Notify($title, $body) {
    $n = New-Object System.Windows.Forms.NotifyIcon
    $n.Icon = [System.Drawing.SystemIcons]::Information
    $n.Visible = $true
    $n.ShowBalloonTip(4000, $title, $body, [System.Windows.Forms.ToolTipIcon]::None)
    Start-Sleep -Seconds 5
    $n.Dispose()
}

function Kind {
    if ($Clip::ContainsFileDropList()) { return "files" }
    if ($Clip::ContainsImage()) { return "image" }
    if ($Clip::ContainsText()) { return "text" }
    ""
}

# Write the clipboard to files for `tailscale file cp`.
function Materialise($kind) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    switch ($kind) {
        "files" { @($Clip::GetFileDropList()) }
        "image" {
            $f = Join-Path $Out "screenshot-$stamp.png"
            $img = $Clip::GetImage()
            $img.Save($f, [System.Drawing.Imaging.ImageFormat]::Png)
            $img.Dispose()
            $f
        }
        "text" {
            $f = Join-Path $Out "clip-$stamp.txt"
            [IO.File]::WriteAllText($f, $Clip::GetText())
            $f
        }
    }
}

function Send($target, $kind) {
    $files = @(Materialise $kind | Where-Object { $_ -and (Test-Path $_) })
    if (-not $files) { Notify "Nothing to send" "the clipboard is empty"; return }
    $err = & $Tailscale file cp @files "${target}:" 2>&1
    if ($LASTEXITCODE -ne 0) { Notify "Send to $(Label $target) failed" "$err".Trim(); return }
    Set-Content $LastFile $target
    $names = ($files | Select-Object -First 3 | ForEach-Object { Split-Path $_ -Leaf }) -join ", "
    Notify "Sent to $(Label $target)" $names
}

$kind = Kind
if (-not $kind) { Notify "Nothing to send" "copy a screenshot, files or text first"; exit }
$what = @{ files = "copied files"; image = "clipboard screenshot"; text = "clipboard text" }[$kind]
if ($To) { Send $To $kind; exit }

$prev = if (Test-Path $LastFile) { (Get-Content $LastFile -Raw).Trim() } else { $Default }
$hosts = @(& $Tailscale file cp --targets 2>$null | Where-Object { $_ -notmatch "offline" } |
    ForEach-Object { ($_ -split "`t")[1] } | Where-Object { $_ -and $Hide -notcontains $_ } |
    Sort-Object @{ E = { $_ -ne $prev } }, @{ E = { $_ -ne $Default } }, @{ E = { Label $_ } })
if (-not $hosts) { Notify "No devices online" "tailscale file cp --targets is empty"; exit }

$form = New-Object System.Windows.Forms.Form
$form.Text = "Send $what to"
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedToolWindow"
$form.TopMost = $true
$form.KeyPreview = $true
$form.Font = New-Object System.Drawing.Font("Segoe UI", 11)
$form.ClientSize = New-Object System.Drawing.Size(340, (16 + 28 * $hosts.Count))

$list = New-Object System.Windows.Forms.ListBox
$list.SetBounds(8, 8, 324, (8 + 28 * $hosts.Count))
$list.ItemHeight = 28
$list.BorderStyle = "None"
foreach ($h in $hosts) { [void]$list.Items.Add("$(Label $h)   ($h)") }
$list.SelectedIndex = 0
$form.Controls.Add($list)

$script:chosen = $null
$list.Add_DoubleClick({ $script:chosen = $hosts[$list.SelectedIndex]; $form.Close() })
$form.Add_KeyDown({
    if ($_.KeyCode -eq "Enter") { $script:chosen = $hosts[$list.SelectedIndex]; $form.Close() }
    elseif ($_.KeyCode -eq "Escape") { $form.Close() }
})
$form.Add_Shown({ $form.Activate(); $list.Focus() })
[void]$form.ShowDialog()
$form.Dispose()

if ($script:chosen) { Send $script:chosen $kind }
