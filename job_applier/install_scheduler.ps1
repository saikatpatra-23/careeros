# CareerOS -- Windows Task Scheduler Setup
# =========================================
# Registers TWO scheduled tasks: 9:30 AM and 2:00 PM daily.
# Key feature: "Wake the computer to run this task" is ENABLED.
# So even if laptop is in sleep, it wakes up, runs the bot, and goes back to sleep.
#
# Run as Administrator:
#   Right-click PowerShell -> "Run as Administrator"
#   cd to the job_applier folder
#   .\install_scheduler.ps1
#
# To remove tasks:
#   .\install_scheduler.ps1 -Uninstall

param(
    [string]$RunScript  = "$PSScriptRoot\run.py",
    [string]$PythonExe  = "",
    [switch]$Uninstall  = $false
)

$TaskNames = @("CareerOS-Morning", "CareerOS-Afternoon")

# -- Require admin -------------------------------------------------------------
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: Run this script as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell -> 'Run as Administrator', then try again."
    exit 1
}

# -- Uninstall mode ------------------------------------------------------------
if ($Uninstall) {
    Write-Host "Removing CareerOS scheduled tasks..." -ForegroundColor Yellow
    foreach ($name in $TaskNames) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "  Removed: $name"
    }
    Write-Host "Done." -ForegroundColor Green
    exit 0
}

# -- Find Python ---------------------------------------------------------------
if (-not $PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Host "ERROR: Python not found in PATH." -ForegroundColor Red
    exit 1
}
Write-Host "Python found: $PythonExe" -ForegroundColor Cyan

# -- Validate run.py -----------------------------------------------------------
if (-not (Test-Path $RunScript)) {
    Write-Host "ERROR: run.py not found at $RunScript" -ForegroundColor Red
    exit 1
}

# -- Create logs folder --------------------------------------------------------
$LogDir = "$PSScriptRoot\logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# -- Helper: register one task -------------------------------------------------
function Register-CareerOSTask {
    param(
        [string]$TaskName,
        [string]$Hour,
        [string]$Minute,
        [string]$Description
    )

    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

    $action = New-ScheduledTaskAction `
        -Execute $PythonExe `
        -Argument "-u `"$RunScript`"" `
        -WorkingDirectory $PSScriptRoot

    $trigger = New-ScheduledTaskTrigger -Daily -At "$($Hour):$($Minute)"

    $settings = New-ScheduledTaskSettingsSet `
        -WakeToRun `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
        -MultipleInstances IgnoreNew

    $principal = New-ScheduledTaskPrincipal `
        -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
        -LogonType Interactive `
        -RunLevel Highest

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description $Description `
        -Force | Out-Null

    Write-Host "  Registered: $TaskName at $($Hour):$($Minute)" -ForegroundColor Green
}

# -- Register both tasks -------------------------------------------------------
Write-Host ""
Write-Host "Registering CareerOS scheduled tasks..." -ForegroundColor Cyan

Register-CareerOSTask `
    -TaskName "CareerOS-Morning" `
    -Hour "09" -Minute "30" `
    -Description "CareerOS 9:30 AM daily run. Logs into Naukri, checks NVites, applies to jobs."

Register-CareerOSTask `
    -TaskName "CareerOS-Afternoon" `
    -Hour "14" -Minute "00" `
    -Description "CareerOS 2:00 PM daily run. Logs into Naukri, checks NVites, applies to jobs."

# -- Verify --------------------------------------------------------------------
Write-Host ""
$allOk = $true
foreach ($name in $TaskNames) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "  $name : $($task.State)" -ForegroundColor Green
    } else {
        Write-Host "  $name : NOT FOUND (error)" -ForegroundColor Red
        $allOk = $false
    }
}

if ($allOk) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  CareerOS Task Scheduler setup COMPLETE" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Runs at: 9:30 AM and 2:00 PM daily"
    Write-Host "  Wakes laptop from sleep automatically"
    Write-Host "  Runs on battery (no charger needed)"
    Write-Host "  If a run is missed, starts when laptop wakes"
    Write-Host ""
    Write-Host "  Useful commands:" -ForegroundColor Cyan
    Write-Host "    View tasks   : Get-ScheduledTask -TaskName 'CareerOS*'"
    Write-Host "    Run now      : Start-ScheduledTask -TaskName 'CareerOS-Morning'"
    Write-Host "    View history : Open Task Scheduler -> Task Scheduler Library"
    Write-Host "    Uninstall    : .\install_scheduler.ps1 -Uninstall"
    Write-Host ""

    $logName = "Microsoft-Windows-TaskScheduler/Operational"
    try {
        $log = [System.Diagnostics.Eventing.Reader.EventLogConfiguration]::new($logName)
        if (-not $log.IsEnabled) {
            $log.IsEnabled = $true
            $log.SaveChanges()
            Write-Host "  Task history logging enabled." -ForegroundColor Cyan
        }
    } catch {}
} else {
    Write-Host ""
    Write-Host "WARNING: Some tasks may not have registered correctly." -ForegroundColor Yellow
}
