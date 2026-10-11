> 上游实验协议存档。当前集成入口默认改为可执行测试筛选；本机命令和行为请参阅 `代码整合说明_20260926.md`。

# Three-candidate blind-selection experiment

This experiment separates three questions:

1. `pass@1`: does the ordinary first candidate pass?
2. `oracle_pass@3`: does any of three independently prompted candidates pass?
3. `blind_select@3`: can a selector choose a passing candidate without seeing the reference or official testbench?

The candidates use three fixed perspectives: literal implementation, observable-contract implementation, and counterexample-driven implementation. Syntax compiler messages may be used for minimal repair. The selector receives only the original specification and syntax-clean candidates. Its decision is written to `selector/frozen_selection.json` before official evaluation begins.

Default model: `deepseek-flash`.

Example smoke run from the workspace root:

```powershell
$env:DEEPSEEK_API_KEY = Read-Host -MaskInput "DeepSeek API key"
python '.\script_gcc_test 3.14 12.32\run_three_candidate_select.py' `
  --case Prob062 --case Prob080 --case Prob154 --case Prob156 `
  --output '.\experiments\candidate_selection\three_candidate_select_smoke_YYYYMMDD'
```

The output directory must not already exist. This prevents accidental result overwrite.
