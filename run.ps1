param([Parameter(ValueFromRemainingArguments=$true)][string[]]$RunArgs)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$runtimePython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) {
    throw 'Bundled Python not found. Install a working Python 3.11+ and run: python run_experiment.py --check'
}
& $runtimePython (Join-Path $PSScriptRoot 'run_experiment.py') @RunArgs
exit $LASTEXITCODE
