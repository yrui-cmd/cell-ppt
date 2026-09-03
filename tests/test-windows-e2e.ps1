#requires -Version 5.1

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
$prefix = @('-3', '-X', 'utf8')
if (-not $pythonCommand) { $pythonCommand = Get-Command python -ErrorAction Stop; $prefix = @('-X', 'utf8') }
& $pythonCommand.Source @prefix (Join-Path $repoRoot 'tests\test_nature_ppt.py')
if ($LASTEXITCODE -ne 0) { throw 'Nature PPT tests failed.' }
& $pythonCommand.Source @prefix (Join-Path $repoRoot 'tests\test_cross_platform.py')
if ($LASTEXITCODE -ne 0) { throw 'Cross-platform output tests failed.' }
Write-Output 'WINDOWS_E2E_OK|native=true|light_native=true|remote_contract=true'
