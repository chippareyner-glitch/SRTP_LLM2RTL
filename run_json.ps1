param([Parameter(ValueFromRemainingArguments=$true)][string[]]$RunArgs)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$runtimePython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) { throw 'Python runtime not found. Use your Python with requirements-json.txt installed.' }
& $runtimePython (Join-Path $PSScriptRoot 'run_json_pipeline.py') @RunArgs
exit $LASTEXITCODE
