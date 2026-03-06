param(
    [string]$ProjectRoot = $PSScriptRoot,
    [switch]$PromptForProjectRoot
)

$ErrorActionPreference = 'Stop'

if ($PromptForProjectRoot) {
    $enteredRoot = Read-Host "Project root directory [$ProjectRoot]"
    if (-not [string]::IsNullOrWhiteSpace($enteredRoot)) {
        $ProjectRoot = $enteredRoot.Trim()
    }
}

$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$targetScript = Join-Path $ProjectRoot 'LEXA_SWITCHER_850k.ahk'

if (-not (Test-Path $targetScript)) {
    throw "Script not found: $targetScript"
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

    $searchRoots = @(
        "$env:ProgramFiles\AutoHotkey\v2",
        "$env:ProgramW6432\AutoHotkey\v2",
        "$env:LOCALAPPDATA\Programs\AutoHotkey\v2",
        "$env:ProgramFiles\AutoHotkey",
        "$env:ProgramW6432\AutoHotkey",
        "$env:ProgramFiles(x86)\AutoHotkey",
        "$env:ChocolateyInstall\lib\autohotkey\tools"
    ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

    foreach ($root in $searchRoots) {
        $found = Get-ChildItem -Path $root -Recurse -Filter AutoHotkey*.exe -File -ErrorAction SilentlyContinue |
            Sort-Object FullName |
            Select-Object -ExpandProperty FullName -First 1
        if ($found) {
            return $found
        }
    }

    return $null
}

$ahk = Find-AutoHotkey
if (-not $ahk) {
    if (-not (Get-Command choco.exe -ErrorAction SilentlyContinue)) {
        throw 'Chocolatey is not installed. Automatic AutoHotkey installation is unavailable.'
    }

    Write-Host 'AutoHotkey v2 not found. Installing via Chocolatey...'
    choco install autohotkey -y --no-progress
    $ahk = Find-AutoHotkey
}

if (-not $ahk) {
    throw 'AutoHotkey v2 installation finished, but executable was not found.'
}

Write-Host "Starting LEXA_SWITCHER_850k from: $ProjectRoot"
Write-Host "Interpreter: $ahk"
Start-Process -FilePath $ahk -ArgumentList ('"{0}"' -f $targetScript)
