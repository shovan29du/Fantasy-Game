<#
.SYNOPSIS
    Creates Desktop and Start Menu shortcuts for Ark_AI.

.DESCRIPTION
    Targets run_ark_ai.bat with the project folder as the working
    directory. Detects the real OneDrive-synced Desktop via the
    %OneDriveCommercial%/%OneDrive% environment variables (Windows sets
    these to the actual synced path, which is not always
    %USERPROFILE%\OneDrive - it can live on another drive or be named
    "OneDrive - <Company>" for a work/school account) and creates a
    shortcut there if found. It also always creates a shortcut on the
    regular %USERPROFILE%\Desktop and in the Start Menu.
    Requires no admin rights - everything is written under the current
    user's profile.

.PARAMETER ProjectDir
    Path to the Ark_AI project folder. Defaults to the folder this
    script lives in.
#>
param(
    [string]$ProjectDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path -Path $ProjectDir).Path
$target = Join-Path $ProjectDir "run_ark_ai.bat"

if (-not (Test-Path $target)) {
    Write-Error "run_ark_ai.bat not found in $ProjectDir"
    exit 1
}

$iconPath = Join-Path $ProjectDir "relay.ico"

function New-ArkAiShortcut {
    param(
        [Parameter(Mandatory)] [string]$Path
    )
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($Path)
    $shortcut.TargetPath = $target
    $shortcut.WorkingDirectory = $ProjectDir
    $shortcut.Description = "Launch Ark_AI"
    if (Test-Path $iconPath) {
        $shortcut.IconLocation = $iconPath
    }
    $shortcut.Save()
    Write-Host "Created shortcut: $Path"
}

# ---- Desktop shortcut(s): OneDrive Desktop (if redirected there) and/or
# the regular Desktop. Windows sets %OneDrive%/%OneDriveCommercial% to the
# *actual* synced folder, which is not always %USERPROFILE%\OneDrive (it can
# be on another drive, or named "OneDrive - <Company>" for work accounts),
# so check those env vars first instead of assuming the default path.
$normalDesktop = Join-Path $env:USERPROFILE "Desktop"

$oneDriveRoots = @($env:OneDriveCommercial, $env:OneDrive, (Join-Path $env:USERPROFILE "OneDrive")) |
    Where-Object { $_ } | Select-Object -Unique

$desktopTargets = New-Object System.Collections.Generic.List[string]
foreach ($root in $oneDriveRoots) {
    $candidate = Join-Path $root "Desktop"
    if ((Test-Path $candidate) -and -not $desktopTargets.Contains($candidate)) {
        $desktopTargets.Add($candidate)
        Write-Host "OneDrive Desktop detected - using $candidate"
    }
}
if (-not $desktopTargets.Contains($normalDesktop)) {
    $desktopTargets.Add($normalDesktop)
    Write-Host "Normal Desktop - using $normalDesktop"
}

foreach ($desktopDir in $desktopTargets) {
    try {
        New-ArkAiShortcut -Path (Join-Path $desktopDir "Ark_AI.lnk")
    } catch {
        Write-Warning "Could not create Desktop shortcut in $desktopDir : $_"
    }
}

# ---- Start Menu shortcut ----
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$startMenuShortcut = Join-Path $startMenu "Ark_AI.lnk"

try {
    New-ArkAiShortcut -Path $startMenuShortcut
} catch {
    Write-Warning "Could not create Start Menu shortcut: $_"
}

Write-Host "Done."
