<#
.SYNOPSIS
    Creates Desktop and Start Menu shortcuts for Worldweaver Multiverse Tabletop.

.DESCRIPTION
    Creates a shortcut to run_app.bat on:
      - The OneDrive-synced Desktop (if %OneDriveCommercial% or %OneDrive% is set)
      - The regular %USERPROFILE%\Desktop
      - The Start Menu (Programs folder)

    No admin rights required. Run once after installation or if you
    move the project folder.

.PARAMETER ProjectDir
    Path to the Worldweaver project folder. Defaults to the folder this
    script lives in.
#>
param(
    [string]$ProjectDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path -Path $ProjectDir).Path
$target     = Join-Path $ProjectDir "run_app.bat"
$iconPath   = Join-Path $ProjectDir "assets\worldweaver.ico"
$appName    = "Worldweaver"
$appDesc    = "Launch Worldweaver Multiverse Tabletop on http://localhost:8501"

if (-not (Test-Path $target)) {
    Write-Error "run_app.bat not found in $ProjectDir"
    exit 1
}

function New-Shortcut {
    param([Parameter(Mandatory)][string]$LnkPath)
    $dir = Split-Path -Parent $LnkPath
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $shell          = New-Object -ComObject WScript.Shell
    $sc             = $shell.CreateShortcut($LnkPath)
    $sc.TargetPath       = $target
    $sc.WorkingDirectory = $ProjectDir
    $sc.Description      = $appDesc
    if (Test-Path $iconPath) { $sc.IconLocation = $iconPath }
    $sc.Save()
    Write-Host "  Created: $LnkPath"
}

Write-Host ""
Write-Host "=== Worldweaver shortcut installer ==="
Write-Host "Project : $ProjectDir"
Write-Host "Launcher: $target"
Write-Host ""

# ── Desktop shortcuts ──────────────────────────────────────────────────────
# Detect OneDrive Desktop(s) first. Windows sets %OneDriveCommercial% and
# %OneDrive% to the actual synced root (may be on another drive or named
# "OneDrive - Company"), so we check those instead of assuming the path.
$normalDesktop = Join-Path $env:USERPROFILE "Desktop"

$oneDriveRoots = @($env:OneDriveCommercial, $env:OneDrive, (Join-Path $env:USERPROFILE "OneDrive")) |
    Where-Object { $_ } | Select-Object -Unique

$desktopDirs = New-Object System.Collections.Generic.List[string]
foreach ($root in $oneDriveRoots) {
    $candidate = Join-Path $root "Desktop"
    if ((Test-Path $candidate) -and -not $desktopDirs.Contains($candidate)) {
        $desktopDirs.Add($candidate)
        Write-Host "OneDrive Desktop: $candidate"
    }
}
if (-not $desktopDirs.Contains($normalDesktop)) {
    $desktopDirs.Add($normalDesktop)
    Write-Host "Normal Desktop  : $normalDesktop"
}

foreach ($d in $desktopDirs) {
    try   { New-Shortcut -LnkPath (Join-Path $d "$appName.lnk") }
    catch { Write-Warning "Could not create shortcut in $d : $_" }
}

# ── Start Menu shortcut ────────────────────────────────────────────────────
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
try   { New-Shortcut -LnkPath (Join-Path $startMenu "$appName.lnk") }
catch { Write-Warning "Could not create Start Menu shortcut: $_" }

Write-Host ""
Write-Host "Done. Double-click '$appName' on your Desktop to launch the game."
Write-Host "The game opens at http://localhost:8501 in your browser."
Write-Host ""
