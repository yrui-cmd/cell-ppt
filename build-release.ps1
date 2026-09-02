#requires -Version 5.1

[CmdletBinding()]
param([string]$Version, [switch]$SkipTests)

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$manifestPath = Join-Path $repoRoot 'plugins\nature-ppt\.codex-plugin\plugin.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($Version)) { $Version = [string]$manifest.version }
if ($manifest.name -ne 'nature-ppt' -or $manifest.version -ne $Version) { throw 'Plugin identity or release version is invalid.' }
if (-not $SkipTests) {
    & (Join-Path $repoRoot 'tests\test-package.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Package tests failed.' }
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    $prefix = @('-3', '-X', 'utf8')
    if (-not $pythonCommand) { $pythonCommand = Get-Command python -ErrorAction Stop; $prefix = @('-X', 'utf8') }
    & $pythonCommand.Source @prefix (Join-Path $repoRoot 'tests\test_nature_ppt.py')
    if ($LASTEXITCODE -ne 0) { throw 'Nature PPT tests failed.' }
    & $pythonCommand.Source @prefix (Join-Path $repoRoot 'tests\test_cross_platform.py')
    if ($LASTEXITCODE -ne 0) { throw 'Cross-platform tests failed.' }
}
$distRoot = Join-Path $repoRoot 'dist'
$tempRoot = Join-Path $repoRoot '.release-tmp'
$stageRoot = Join-Path $tempRoot "nature-ppt-v$Version"
$zipPath = Join-Path $distRoot "nature-ppt-v$Version.zip"
$hashPath = "$zipPath.sha256"
if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stageRoot, $distRoot | Out-Null
$excluded = @('.git', '.tmp', '.tmp-cache', '.test-tmp', '.release-tmp', 'dist', 'work')
Get-ChildItem -LiteralPath $repoRoot -Force | Where-Object { $excluded -notcontains $_.Name } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $stageRoot -Recurse -Force
}
Get-ChildItem -LiteralPath $stageRoot -Recurse -Directory -Filter '__pycache__' | ForEach-Object {
    $checked = [IO.Path]::GetFullPath($_.FullName)
    if (-not $checked.StartsWith($stageRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe release cleanup target.' }
    Remove-Item -LiteralPath $checked -Recurse -Force
}
$releaseManifest = [ordered]@{
    product = 'Nature PPT'
    version = $Version
    tag = "v$Version"
    createdUtc = [DateTime]::UtcNow.ToString('o')
    credentialsIncluded = $false
    localApiKeyRequired = $false
    dependencyLock = 'requirements.lock'
    runtimeLock = 'runtime-lock.json'
}
$releaseManifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $stageRoot 'RELEASE-MANIFEST.json') -Encoding UTF8
if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
Compress-Archive -LiteralPath $stageRoot -DestinationPath $zipPath -CompressionLevel Optimal
$hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText($hashPath, "$hash  $([IO.Path]::GetFileName($zipPath))`r`n", [Text.UTF8Encoding]::new($false))
Remove-Item -LiteralPath $tempRoot -Recurse -Force
Write-Output "RELEASE_OK|version=$Version|zip=$zipPath|sha256=$hash"
