# Bruh Shell Integration for PowerShell
# Captures previous command outcomes without manual piping

if (-not (Test-Path "$HOME\.bruh")) {
    New-Item -ItemType Directory -Path "$HOME\.bruh" -Force | Out-Null
}

$global:__bruh_last_cmd = ""

function global:__bruh_clean_command {
    param([string]$Raw)
    if (-not $Raw) { return "" }
    $lines = $Raw.Trim() -split "`r?`n"
    $filtered = @()
    foreach ($line in $lines) {
        $t = $line.Trim().TrimEnd('`').Trim()
        if ($t -and -not ($t.StartsWith("bruh")) -and $t -ne "clear" -and $t -ne "cls") {
            $filtered += $t
        }
    }
    if ($filtered.Count -eq 0) { return "" }

    if ($filtered[0].StartsWith('@"') -or $filtered[0].StartsWith("@'")) {
        $closeTag = if ($filtered[0].StartsWith('@"')) { '"@' } else { "'@" }
        $closeIdx = -1
        for ($i = 0; $i -lt $filtered.Count; $i++) {
            if ($filtered[$i].StartsWith($closeTag)) {
                $closeIdx = $i
                break
            }
        }
        if ($closeIdx -ne -1 -and $closeIdx -lt ($filtered.Count - 1)) {
            return $filtered[-1]
        }
        return ($filtered -join "`n")
    }

    return $filtered[-1]
}

# Hook PSReadLine Enter key to capture command on Enter
if (Get-Command -Name Set-PSReadLineKeyHandler -ErrorAction SilentlyContinue) {
    try {
        Set-PSReadLineKeyHandler -Key Enter -ScriptBlock {
            try {
                $line = [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState().line
                if (-not [string]::IsNullOrWhiteSpace($line)) {
                    $cleaned = __bruh_clean_command $line
                    if ($cleaned -and -not ($cleaned.StartsWith("bruh"))) {
                        $global:__bruh_last_cmd = $cleaned
                    }
                }
            } catch {}
            [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
        }
    } catch {}
}

function global:__bruh_reconstruct_multiline {
    param([string[]]$Lines, [int]$EndIdx)
    $target = $Lines[$EndIdx].Trim()
    if ($target.StartsWith('"@') -or $target.StartsWith("'@")) {
        $delim = if ($target.StartsWith('"@')) { '@"' } else { "@'" }
        $minIdx = [Math]::Max(0, $EndIdx - 50)
        for ($s = $EndIdx - 1; $s -ge $minIdx; $s--) {
            $t = $Lines[$s].Trim()
            if ($t.StartsWith($delim)) {
                $block = $Lines[$s..$EndIdx] -join "`n"
                return $block.Trim()
            }
        }
    }
    return $target
}

function global:__bruh_get_last_command {
    # 1. Try active PowerShell session Get-History (most accurate in current session)
    try {
        $hist = Get-History -Count 10 -ErrorAction SilentlyContinue
        if ($hist) {
            $histLines = @($hist | ForEach-Object { $_.CommandLine })
            for ($idx = $histLines.Count - 1; $idx -ge 0; $idx--) {
                $rawCmd = $histLines[$idx]
                if ($rawCmd) {
                    $trimmed = $rawCmd.Trim()
                    if ($trimmed -and -not ($trimmed.StartsWith("bruh"))) {
                        $fullCmd = __bruh_reconstruct_multiline $histLines $idx
                        $clean = __bruh_clean_command $fullCmd
                        if ($clean -and -not ($clean.StartsWith("bruh"))) { return $clean }
                    }
                }
            }
        }
    } catch {}

    # 2. Check in-memory command captured by PSReadLine Enter key
    if ($global:__bruh_last_cmd) {
        $clean = __bruh_clean_command $global:__bruh_last_cmd
        if ($clean -and -not ($clean.StartsWith("bruh"))) { return $clean }
    }

    # 3. Try PSReadLine history file (persisted on disk)
    try {
        if (Get-Command -Name Get-PSReadLineOption -ErrorAction SilentlyContinue) {
            $histPath = (Get-PSReadLineOption).HistorySavePath
            if ($histPath -and (Test-Path $histPath)) {
                $lines = @(Get-Content $histPath -Tail 50 -ErrorAction SilentlyContinue)
                if ($lines) {
                    for ($idx = $lines.Count - 1; $idx -ge 0; $idx--) {
                        $line = $lines[$idx]
                        if ($line) {
                            $trimmed = $line.Trim()
                            if ($trimmed -and -not ($trimmed.StartsWith("bruh"))) {
                                $fullCmd = __bruh_reconstruct_multiline $lines $idx
                                $clean = __bruh_clean_command $fullCmd
                                if ($clean -and -not ($clean.StartsWith("bruh"))) { return $clean }
                            }
                        }
                    }
                }
            }
        }
    } catch {}

    return ""
}

function global:__bruh_save_session {
    param([string]$ExplicitCmd = "")

    $raw = if ($ExplicitCmd) { $ExplicitCmd } else { __bruh_get_last_command }
    $cmd = __bruh_clean_command $raw
    if (-not $cmd -or $cmd.Trim().StartsWith("bruh")) {
        return
    }

    $lastExit = $LASTEXITCODE
    if ($lastExit -eq $null) {
        $lastExit = $global:LASTEXITCODE
    }
    $lastStatus = $?

    $isFailed = ($lastStatus -eq $false) -or ($lastExit -ne $null -and $lastExit -ne 0)
    $exitCodeVal = if ($isFailed) { if ($lastExit -ne $null -and $lastExit -ne 0) { [int]$lastExit } else { 1 } } else { 0 }

    $errOutput = ""
    if ($isFailed -and $global:Error.Count -gt 0) {
        $errOutput = ($global:Error[0] | Out-String).Trim()
    }

    $sessionData = @{
        command = $cmd
        exit_code = $exitCodeVal
        output = $errOutput
        cwd = (Get-Location).Path
        timestamp = [double]([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0)
        shell = "powershell"
    } | ConvertTo-Json

    $sessionFile = "$HOME\.bruh\last_session.json"
    try {
        [System.IO.File]::WriteAllText($sessionFile, $sessionData, [System.Text.Encoding]::UTF8)
    } catch {}
}

# The bruh function ensures instantaneous capture directly at invocation time
function global:bruh {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        $CliArgs
    )

    # Save session with active shell exit state if not direct command
    if (-not $CliArgs -or $CliArgs.Count -eq 0) {
        __bruh_save_session
    }

    # Execute standalone bruh.exe / CLI if available on PATH
    if (Get-Command bruh.exe -ErrorAction SilentlyContinue) {
        if ($CliArgs) { & bruh.exe @CliArgs } else { & bruh.exe }
        return
    }

    # Fallback to python module execution
    if (Get-Command python -ErrorAction SilentlyContinue) {
        if ($CliArgs) { & python -m bruh @CliArgs } else { & python -m bruh }
        return
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        if ($CliArgs) { & py -m bruh @CliArgs } else { & py -m bruh }
        return
    }

    Write-Error "bruh command not found. Ensure bruh is installed via pip or bruh.exe is on PATH."
}

# Also hook prompt for automatic background capture on every command
function global:__bruh_prompt_hook {
    try {
        __bruh_save_session
    } catch {}
}

if (Test-Path Function:\prompt) {
    $originalPrompt = Get-Content Function:\prompt
    if ($originalPrompt -notmatch "__bruh_prompt_hook") {
        $newPrompt = @"
__bruh_prompt_hook
$originalPrompt
"@
        Set-Item -Path Function:\prompt -Value ([ScriptBlock]::Create($newPrompt))
    }
} else {
    function global:prompt {
        __bruh_prompt_hook
        "PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) "
    }
}
