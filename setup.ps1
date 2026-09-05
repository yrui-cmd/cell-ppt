#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$Destination = "$env:USERPROFILE\.codex\skills",
    [switch]$Force,
    [switch]$SkipDependencies
)

$ErrorActionPreference = 'Stop'
$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
$prefix = @('-3', '-X', 'utf8')
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    $prefix = @('-X', 'utf8')
}
if (-not $pythonCommand) { throw 'Python 3.10-3.14 was not found.' }
$python = $pythonCommand.Source
& $python @prefix -c "import sys; assert (3,10) <= sys.version_info[:2] < (3,15)"
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10-3.14 is required.' }
if (-not $SkipDependencies) {
    & $python @prefix -m pip install --disable-pip-version-check --requirement (Join-Path $PSScriptRoot 'requirements.lock')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
$installArgs = @('--destination', ([IO.Path]::GetFullPath($Destination)))
if ($Force) { $installArgs += '--force' }
& $python @prefix (Join-Path $PSScriptRoot 'install.py') @installArgs
if ($LASTEXITCODE -ne 0) { throw 'Skill installation failed.' }
& $python @prefix (Join-Path $PSScriptRoot 'doctor.py')
if ($LASTEXITCODE -ne 0) { throw 'Diagnostics failed.' }
Write-Output 'SETUP_OK|skill=nature-ppt|local_vectorizer=true|remote_optional=true|restart_codex=true'
