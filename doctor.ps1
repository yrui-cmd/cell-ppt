#requires -Version 5.1

[CmdletBinding()]
param([switch]$Json, [switch]$CheckVectorizer)

$ErrorActionPreference = 'Stop'
$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
$arguments = @('-3', '-X', 'utf8', (Join-Path $PSScriptRoot 'doctor.py'))
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    $arguments = @('-X', 'utf8', (Join-Path $PSScriptRoot 'doctor.py'))
}
if (-not $pythonCommand) { throw 'Python 3.10-3.14 was not found.' }
if ($Json) { $arguments += '--json' }
if ($CheckVectorizer) { $arguments += '--check-vectorizer' }
& $pythonCommand.Source @arguments
if ($LASTEXITCODE -ne 0) { throw 'Nature PPT diagnostics failed.' }
