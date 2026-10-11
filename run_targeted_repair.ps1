param([Parameter(ValueFromRemainingArguments=$true)][string[]]$RunArgs)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$repairPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (-not (Test-Path -LiteralPath $repairPython)) { throw 'Python runtime missing; use python run_targeted_repair.py instead.' }
& $repairPython (Join-Path $PSScriptRoot 'run_targeted_repair.py') @RunArgs
exit $LASTEXITCODE
