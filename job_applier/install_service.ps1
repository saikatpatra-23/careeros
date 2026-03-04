# CareerOS — Windows Service Installer
# Converts watcher.py into a proper Windows Service.
# Service starts on boot, runs even when you're logged off.
#
# Run as Administrator:
#   Right-click PowerShell → "Run as Administrator"
#   cd to the job_applier folder
#   .\install_service.ps1

param(
    [string]$WatcherScript  = "$PSScriptRoot\watcher.py",
    [string]$PythonExe      = "",
    [string]$ServiceName    = "CareerOSWatcher",
    [switch]$Uninstall      = $false
)

# ── Require admin ─────────────────────────────────────────────────────────────
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: Run this script as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell → 'Run as Administrator', then try again."
    exit 1
}

# ── Uninstall mode ────────────────────────────────────────────────────────────
if ($Uninstall) {
    Write-Host "Removing CareerOS Windows Service..." -ForegroundColor Yellow
    Stop-Service  -Name $ServiceName -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Write-Host "✅ Service removed." -ForegroundColor Green
    exit 0
}

# ── Find Python ───────────────────────────────────────────────────────────────
if (-not $PythonExe) {
    $PythonExe = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
    if (-not $PythonExe) {
        $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    }
}
if (-not $PythonExe) {
    Write-Host "ERROR: Python not found in PATH." -ForegroundColor Red
    Write-Host "Install Python and make sure it's added to PATH."
    exit 1
}
Write-Host "Python found: $PythonExe" -ForegroundColor Cyan

# ── Validate watcher script ───────────────────────────────────────────────────
if (-not (Test-Path $WatcherScript)) {
    Write-Host "ERROR: watcher.py not found at $WatcherScript" -ForegroundColor Red
    exit 1
}

# ── Download NSSM ─────────────────────────────────────────────────────────────
$NSSMVersion = "2.24"
$NSSMZip     = "$env:TEMP\nssm.zip"
$NSSMDir     = "$env:TEMP\nssm-$NSSMVersion"
$NSSMExe     = "$NSSMDir\win64\nssm.exe"

if (-not (Test-Path $NSSMExe)) {
    Write-Host "Downloading NSSM (service manager)..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-$NSSMVersion.zip" `
                          -OutFile $NSSMZip -UseBasicParsing
        Expand-Archive -Path $NSSMZip -DestinationPath "$env:TEMP" -Force
        Rename-Item "$env:TEMP\nssm-$NSSMVersion" $NSSMDir -ErrorAction SilentlyContinue
    } catch {
        Write-Host "ERROR: Could not download NSSM: $_" -ForegroundColor Red
        exit 1
    }
}

# ── Remove existing service if present ───────────────────────────────────────
$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing service..." -ForegroundColor Yellow
    & $NSSMExe stop    $ServiceName | Out-Null
    & $NSSMExe remove  $ServiceName confirm | Out-Null
    Start-Sleep -Seconds 2
}

# ── Create logs folder ────────────────────────────────────────────────────────
$LogDir = "$PSScriptRoot\logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# ── Install service via NSSM ─────────────────────────────────────────────────
Write-Host "Installing CareerOS Watcher as Windows Service..." -ForegroundColor Cyan

& $NSSMExe install     $ServiceName $PythonExe
& $NSSMExe set         $ServiceName AppParameters     $WatcherScript
& $NSSMExe set         $ServiceName AppDirectory      $PSScriptRoot
& $NSSMExe set         $ServiceName DisplayName       "CareerOS Watcher"
& $NSSMExe set         $ServiceName Description       "CareerOS automated job monitoring. Runs at 9:30 AM and 2 PM daily. HR invite detection runs on every check."
& $NSSMExe set         $ServiceName Start             SERVICE_AUTO_START
& $NSSMExe set         $ServiceName AppStdout         "$LogDir\service.log"
& $NSSMExe set         $ServiceName AppStderr         "$LogDir\service_error.log"
& $NSSMExe set         $ServiceName AppRotateFiles    1
& $NSSMExe set         $ServiceName AppRotateSeconds  86400   # rotate daily
& $NSSMExe set         $ServiceName AppRotateBytes    5242880 # 5 MB max per log
& $NSSMExe set         $ServiceName AppRestartDelay   10000   # restart after 10s on crash

# ── Start service ─────────────────────────────────────────────────────────────
Write-Host "Starting service..." -ForegroundColor Cyan
& $NSSMExe start $ServiceName | Out-Null
Start-Sleep -Seconds 3

$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -eq "Running") {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  CareerOS Watcher is LIVE as a Windows Service" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Starts automatically on Windows boot"
    Write-Host "  Runs even when you're logged off"
    Write-Host "  Survives reboots and crashes (auto-restarts)"
    Write-Host ""
    Write-Host "  Useful commands:" -ForegroundColor Cyan
    Write-Host "    Check status  : Get-Service CareerOSWatcher"
    Write-Host "    Stop          : Stop-Service CareerOSWatcher"
    Write-Host "    Restart       : Restart-Service CareerOSWatcher"
    Write-Host "    View logs     : notepad $LogDir\service.log"
    Write-Host "    Uninstall     : .\install_service.ps1 -Uninstall"
    Write-Host ""
} else {
    Write-Host "WARNING: Service installed but may not be running." -ForegroundColor Yellow
    Write-Host "Check logs at: $LogDir\service_error.log"
}
