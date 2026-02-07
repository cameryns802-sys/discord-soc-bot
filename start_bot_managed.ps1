#!/usr/bin/env powershell
<#
.DESCRIPTION
Discord SOC Bot - PowerShell Process Manager for 24/7 Operation
Handles automatic restarts, logging, and graceful shutdown
#>

param(
    [int]$RestartDelaySeconds = 5,
    [int]$MaxRestarts = -1  # -1 = infinite restarts
)

$ErrorActionPreference = "Continue"
$BotDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$RestartCount = 0
$StartTime = Get-Date

function Write-BotLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = @{
        "INFO"    = "Green"
        "WARNING" = "Yellow"
        "ERROR"   = "Red"
        "START"   = "Cyan"
        "STOP"    = "Magenta"
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color[$Level]
}

function Start-BotProcess {
    param([int]$AttemptNumber)
    
    Write-BotLog "Starting bot process (attempt #$AttemptNumber)" -Level "START"
    
    try {
        $process = Start-Process `
            -FilePath "python.exe" `
            -ArgumentList "bot.py" `
            -WorkingDirectory $BotDirectory `
            -NoNewWindow `
            -PassThru `
            -ErrorAction Stop
        
        return $process
    }
    catch {
        Write-BotLog "Failed to start bot: $_" -Level "ERROR"
        return $null
    }
}

function Stop-BotProcess {
    param([System.Diagnostics.Process]$Process)
    
    if ($null -eq $Process) { return }
    
    Write-BotLog "Stopping bot process (PID: $($Process.Id))" -Level "STOP"
    
    try {
        $Process.CloseMainWindow() | Out-Null
        
        if (!$Process.WaitForExit(10000)) {
            Write-BotLog "Force killing bot process" -Level "WARNING"
            $Process.Kill()
        }
    }
    catch {
        Write-BotLog "Error stopping process: $_" -Level "ERROR"
    }
}

function Get-Uptime {
    $elapsed = (Get-Date) - $StartTime
    return "{0:D2}:{1:D2}:{2:D2}" -f $elapsed.Hours, $elapsed.Minutes, $elapsed.Seconds
}

# Main loop
Write-BotLog "╔═══════════════════════════════════════════════════════════════════╗" -Level "START"
Write-BotLog "║ Discord SOC Bot - 24/7 Process Manager (PowerShell)              ║" -Level "START"
Write-BotLog "║ Auto-restart on crash: ENABLED                                   ║" -Level "START"
Write-BotLog "║ Stop with: Ctrl+C                                                ║" -Level "START"
Write-BotLog "╚═══════════════════════════════════════════════════════════════════╝" -Level "START"
Write-BotLog "Working Directory: $BotDirectory" -Level "INFO"
Write-BotLog ""

$shouldRun = $true

# Handle Ctrl+C
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-BotLog "Shutdown signal received. Cleaning up..." -Level "STOP"
    if ($null -ne $script:botProcess) {
        Stop-BotProcess $script:botProcess
    }
}

try {
    while ($shouldRun) {
        $RestartCount++
        
        if ($MaxRestarts -gt 0 -and $RestartCount -gt $MaxRestarts) {
            Write-BotLog "Max restart attempts ($MaxRestarts) reached. Exiting." -Level "ERROR"
            break
        }
        
        # Start bot
        $script:botProcess = Start-BotProcess $RestartCount
        
        if ($null -eq $script:botProcess) {
            Write-BotLog "Failed to start bot. Retrying in ${RestartDelaySeconds}s..." -Level "ERROR"
            Start-Sleep -Seconds $RestartDelaySeconds
            continue
        }
        
        # Wait for bot to exit
        $script:botProcess.WaitForExit()
        $exitCode = $script:botProcess.ExitCode
        
        $uptime = Get-Uptime
        
        if ($exitCode -eq 0) {
            Write-BotLog "Bot exited cleanly (uptime: $uptime)" -Level "INFO"
            break
        }
        else {
            Write-BotLog "Bot crashed with exit code $exitCode (uptime: $uptime)" -Level "ERROR"
        }
        
        # Calculate backoff delay
        $delay = [Math]::Min($RestartDelaySeconds * [Math]::Pow(2, ($RestartCount - 1)), 120)
        Write-BotLog "Restarting in $([Math]::Round($delay, 0)) seconds..." -Level "WARNING"
        Write-BotLog ""
        
        Start-Sleep -Seconds $delay
    }
}
catch {
    Write-BotLog "Fatal error: $_" -Level "ERROR"
}
finally {
    if ($null -ne $script:botProcess) {
        Stop-BotProcess $script:botProcess
    }
    Write-BotLog "Process Manager Stopped (Total uptime: $(Get-Uptime))" -Level "STOP"
}
