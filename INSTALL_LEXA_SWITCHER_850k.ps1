param(
    [string]$InstallDir = "$env:LOCALAPPDATA\LEXA_SWITCHER_850k"
)

$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$entered = Read-Host "Install directory [$InstallDir]"
if (-not [string]::IsNullOrWhiteSpace($entered)) {
    $InstallDir = $entered.Trim()
}

$InstallDir = [System.IO.Path]::GetFullPath($InstallDir)
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

$items = @('LEXA_SWITCHER_850k.ahk', 'START_LEXA_SWITCHER_850k.ps1', 'START_LEXA_SWITCHER_850k.cmd', 'config.ini', 'README.md', 'data')
foreach ($item in $items) {
    $from = Join-Path $sourceRoot $item
    $to = Join-Path $InstallDir $item
    if (Test-Path $from) {
        Copy-Item -Path $from -Destination $to -Recurse -Force
    }
}

Write-Host "Installed project to: $InstallDir"
powershell -ExecutionPolicy Bypass -File (Join-Path $InstallDir 'START_LEXA_SWITCHER_850k.ps1') -ProjectRoot $InstallDir
