# Usage: .\run.ps1 <command> [arguments]   (commands: see run.py - json / generate / rtllm / experiment / ppa ...)
# The system Python on this machine is broken, so use the bundled Codex Python 3.12 and put .deps\json_pipeline (pyslang) on PYTHONPATH.
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$RunArgs)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = (Join-Path $PSScriptRoot '.deps\json_pipeline') + ';' + $env:PYTHONPATH
$runtimePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) {
    throw "Python runtime not found: $runtimePython. Use a working Python 3.11+ and run: python run.py <command>"
}
& $runtimePython (Join-Path $PSScriptRoot 'run.py') @RunArgs
exit $LASTEXITCODE
