# Use the verified Python runtime instead of an unrelated Python on PATH.
$projectPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw "Verified Python runtime is missing: $projectPython"
}
& $projectPython (Join-Path $PSScriptRoot 'run.py') @args
exit $LASTEXITCODE
