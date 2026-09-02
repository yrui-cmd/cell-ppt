#requires -Version 5.1

[CmdletBinding()]
param([switch]$ConfirmDisposablePresentation)

$ErrorActionPreference = 'Stop'
if (-not $ConfirmDisposablePresentation) { throw 'This test writes to the active presentation. Pass -ConfirmDisposablePresentation only for a disposable document.' }
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$scripts = Join-Path $repoRoot 'plugins\nature-ppt\skills\nature-ppt\scripts'
$temporary = Join-Path $repoRoot '.test-tmp\powerpoint-live'
New-Item -ItemType Directory -Force -Path $temporary | Out-Null
$cache = Join-Path $temporary 'cache'
$output = Join-Path $temporary 'nature-ppt-live-test.pptx'
$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
$prefix = @('-3', '-X', 'utf8')
if (-not $pythonCommand) { $pythonCommand = Get-Command python -ErrorAction Stop; $prefix = @('-X', 'utf8') }
& $pythonCommand.Source @prefix (Join-Path $scripts 'prepare_geometry_cache.py') --input (Join-Path $repoRoot 'tests\fixtures\editable.svg') --output-dir $cache --job-id natureppt1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Geometry preparation failed.' }
& (Join-Path $scripts 'draw_to_powerpoint.ps1') -GeometryCache (Join-Path $cache 'geometry-cache.json') -OutputPptx $output -HostApplication powerpoint -UseActivePresentation -StepDelayMs 0 -Overwrite | Out-Null
if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw 'PowerPoint did not save the test output.' }
Write-Output "POWERPOINT_E2E_OK|output=$output"
