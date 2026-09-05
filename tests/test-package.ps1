#requires -Version 5.1

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pluginRoot = Join-Path $repoRoot 'plugins\nature-ppt'
$skillRoot = Join-Path $pluginRoot 'skills\nature-ppt'
$required = @(
    '.codex-plugin\plugin.json',
    'skills\nature-ppt\SKILL.md',
    'skills\nature-ppt\references\architecture.md',
    'skills\nature-ppt\references\remote-backend.md',
    'skills\nature-ppt\scripts\preflight_image.py',
    'skills\nature-ppt\scripts\run_pipeline.py',
    'skills\nature-ppt\scripts\remote_vectorize.py',
    'skills\nature-ppt\scripts\vectorize_budgeted.py',
    'skills\nature-ppt\scripts\optimize_svg_paths.py',
    'skills\nature-ppt\scripts\draw_to_powerpoint.ps1',
    'skills\nature-ppt\scripts\render_pptx_ooxml.py'
)
foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $pluginRoot $relative) -PathType Leaf)) { throw "Missing package file: $relative" }
}
$plugin = Get-Content -LiteralPath (Join-Path $pluginRoot '.codex-plugin\plugin.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($plugin.name -ne 'nature-ppt' -or $plugin.version -ne '0.6.0' -or $plugin.interface.displayName -ne 'Nature PPT') { throw 'Plugin identity is invalid.' }
$runtime = Get-Content -LiteralPath (Join-Path $repoRoot 'runtime-lock.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($runtime.codex.skillId -ne 'nature-ppt' -or $runtime.runtimeContracts.defaultNativeObjectLimit -ne 50000) { throw 'Runtime contract is invalid.' }
$forbidden = ('ce' + 'll[_-]?ppt|shibie' + 'lujing|xiao' + 'miao')
$scanRoots = @(
    (Join-Path $repoRoot 'README.md'),
    (Join-Path $repoRoot 'README_EN.md'),
    (Join-Path $repoRoot 'CHANGELOG.md'),
    (Join-Path $repoRoot 'runtime-lock.json'),
    $pluginRoot,
    (Join-Path $repoRoot 'tests')
)
foreach ($root in $scanRoots) {
    $files = if (Test-Path -LiteralPath $root -PathType Container) { Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.Extension -notin @('.pyc', '.pyo') } } else { Get-Item -LiteralPath $root }
    foreach ($file in $files) {
        if ((Get-Content -LiteralPath $file.FullName -Raw -ErrorAction SilentlyContinue) -match $forbidden) { throw "Forbidden inherited branding remains in $($file.FullName)" }
    }
}
Write-Output 'PACKAGE_OK|skill=nature-ppt|version=0.6.0|branding=clean|remote=optional|native_limit=50000'
