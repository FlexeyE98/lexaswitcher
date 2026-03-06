param(
    [string]$ProjectRoot,
    [switch]$PromptForProjectRoot
)

$ErrorActionPreference = 'Stop'

if (-not $ProjectRoot) {
    $ProjectRoot = Join-Path $PSScriptRoot '..'
}

if ($PromptForProjectRoot) {
    $enteredRoot = Read-Host "Project root directory [$ProjectRoot]"
    if (-not [string]::IsNullOrWhiteSpace($enteredRoot)) {
        $ProjectRoot = $enteredRoot.Trim()
    }
}

$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$pyScript = Join-Path $ProjectRoot 'app\lexa_switcher.py'
$requirements = Join-Path $ProjectRoot 'requirements.txt'
$ahkScript = Join-Path $ProjectRoot 'windows\LEXA_SWITCHER_850k.ahk'

function Find-Python {
    $candidates = @(
        (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
        (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    ) | Where-Object { $_ } | Select-Object -Unique

    if ($candidates) {
        return $candidates | Select-Object -First 1
    }

    return $null
}

function Find-AutoHotkey {
    $preferredCandidates = @(
        "$env:ProgramFiles\AutoHotkey\v2\AutoHotkey64.exe",
        "$env:ProgramW6432\AutoHotkey\v2\AutoHotkey64.exe",
        "$env:LOCALAPPDATA\Programs\AutoHotkey\v2\AutoHotkey64.exe",
        (Get-Command AutoHotkey64.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    ) | Where-Object { $_ -and (Test-Path $_) }

    if ($preferredCandidates) {
        return $preferredCandidates | Select-Object -First 1
    }

    return $null
}

$python = Find-Python
if ($python -and (Test-Path $pyScript)) {
    Write-Host "Starting cross-platform switcher (Python) from: $ProjectRoot"
    Write-Host "Interpreter: $python"

    if (Test-Path $requirements) {
        if ([System.IO.Path]::GetFileName($python).ToLowerInvariant() -eq 'py.exe') {
            & $python -3 -m pip install -r $requirements
            Start-Process -FilePath $python -ArgumentList '-3', ('"{0}"' -f $pyScript) -WorkingDirectory $ProjectRoot
        }
        else {
            & $python -m pip install -r $requirements
            Start-Process -FilePath $python -ArgumentList ('"{0}"' -f $pyScript) -WorkingDirectory $ProjectRoot
        }
    }
    else {
        if ([System.IO.Path]::GetFileName($python).ToLowerInvariant() -eq 'py.exe') {
            Start-Process -FilePath $python -ArgumentList '-3', ('"{0}"' -f $pyScript) -WorkingDirectory $ProjectRoot
        }
        else {
            Start-Process -FilePath $python -ArgumentList ('"{0}"' -f $pyScript) -WorkingDirectory $ProjectRoot
        }
    }

    return
}

if (-not (Test-Path $ahkScript)) {
    throw "No runnable script found in: $ProjectRoot"
}

$ahk = Find-AutoHotkey
if (-not $ahk) {
    throw 'Python is unavailable and AutoHotkey v2 was not found. Install Python 3 or AutoHotkey v2.'
}

Write-Host "Starting legacy AutoHotkey switcher from: $ProjectRoot"
Write-Host "Interpreter: $ahk"
Start-Process -FilePath $ahk -ArgumentList ('"{0}"' -f $ahkScript)
