#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$Version,
    [switch]$SkipTests
)

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$manifest = Get-Content -LiteralPath (Join-Path $repoRoot 'plugins\cell-ppt\.codex-plugin\plugin.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($Version)) { $Version = [string]$manifest.version }
if ($manifest.version -ne $Version) { throw "Plugin version $($manifest.version) does not match release $Version." }
if (Test-Path -LiteralPath (Join-Path $repoRoot '.agents\plugins\marketplace.json')) { throw 'Marketplace metadata is forbidden in this release.' }

if (-not $SkipTests) {
    & (Join-Path $repoRoot 'tests\test-package.ps1')
    & (Join-Path $repoRoot 'tests\test-windows-e2e.ps1')
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    $pythonPrefix = @('-3', '-X', 'utf8')
    if (-not $pythonCommand) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        $pythonPrefix = @('-X', 'utf8')
    }
    if (-not $pythonCommand) { throw 'Python 3.11-3.14 was not found.' }
    & $pythonCommand.Source @pythonPrefix (Join-Path $repoRoot 'tests\test_fidelity_skill.py')
    if ($LASTEXITCODE -ne 0) { throw 'Cell_ppt Fidelity tests failed.' }
}

$distRoot = Join-Path $repoRoot 'dist'
$tempRoot = Join-Path $repoRoot '.release-tmp'
$stageRoot = Join-Path $tempRoot "cell-ppt-v$Version"
$zipPath = Join-Path $distRoot "cell-ppt-v$Version.zip"
$hashPath = "$zipPath.sha256"
if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stageRoot, $distRoot | Out-Null

$excludedTop = @('.git', '.tmp', '.tmp-cache', '.test-tmp', '.visibility-test', '.visibility-test-v2', '.release-tmp', 'dist', 'work')
Get-ChildItem -LiteralPath $repoRoot -Force | Where-Object { $excludedTop -notcontains $_.Name } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $stageRoot -Recurse -Force
}
Get-ChildItem -LiteralPath $stageRoot -Recurse -Directory -Filter '__pycache__' | ForEach-Object {
    $checked = [IO.Path]::GetFullPath($_.FullName)
    if (-not $checked.StartsWith($stageRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Refusing to clean outside the release stage.' }
    Remove-Item -LiteralPath $checked -Recurse -Force
}
$forbiddenExtensions = @('.pyc', '.pyo', '.dpapi', '.pptx', '.png', '.jpg', '.jpeg', '.webp', '.pdf')
Get-ChildItem -LiteralPath $stageRoot -Recurse -File | Where-Object {
    $forbiddenExtensions -contains $_.Extension.ToLowerInvariant()
} | ForEach-Object {
    $checked = [IO.Path]::GetFullPath($_.FullName)
    if (-not $checked.StartsWith($stageRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Refusing to clean outside the release stage.' }
    Remove-Item -LiteralPath $checked -Force
}

$releaseManifest = [ordered]@{
    product = 'Cell_ppt'
    version = $Version
    tag = "v$Version"
    createdUtc = [DateTime]::UtcNow.ToString('o')
    marketplaceEntry = $false
    credentialsIncluded = $false
    dependencyLock = 'requirements.lock'
    runtimeLock = 'runtime-lock.json'
    platformContract = 'plugins/cell-ppt/skills/cell-ppt/references/platform-contract.json'
}
$releaseManifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $stageRoot 'RELEASE-MANIFEST.json') -Encoding UTF8
foreach ($required in @(
    'README.md',
    'install.py',
    'plugins\cell-ppt\skills\cell-ppt\SKILL.md',
    'plugins\cell-ppt\skills\cell-ppt-fidelity\SKILL.md',
    'plugins\cell-ppt\skills\cell-ppt-fidelity\scripts\vectorize.py'
)) {
    if (-not (Test-Path -LiteralPath (Join-Path $stageRoot $required) -PathType Leaf)) {
        throw "Release stage is incomplete: $required"
    }
}

if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
Compress-Archive -LiteralPath $stageRoot -DestinationPath $zipPath -CompressionLevel Optimal
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $entryNames = @($archive.Entries | ForEach-Object { $_.FullName.Replace('\', '/') })
    if ($entryNames.Count -lt 30 -or -not ($entryNames -match 'cell-ppt-fidelity/scripts/vectorize.py$')) {
        throw 'Release archive validation failed: required Skill files are missing.'
    }
}
finally { $archive.Dispose() }
$hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText($hashPath, "$hash  $([IO.Path]::GetFileName($zipPath))`r`n", [Text.UTF8Encoding]::new($false))
Remove-Item -LiteralPath $tempRoot -Recurse -Force
Write-Output "RELEASE_OK|version=$Version|zip=$zipPath|sha256=$hash"
