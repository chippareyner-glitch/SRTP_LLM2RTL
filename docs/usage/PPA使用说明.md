# 最终 RTL 的通用综合评估

主流程现在按“生成 / 修复 → 验证 / 冻结选择 → 最终 RTL 综合 → 保存报告”运行。
`run.py direct`（含 `--closed-loop`）、`json`、`generate`、`rtllm`、`reselect`、`select-contract`
及旧入口 `run_experiment.py` 默认启用 `--ppa generic`。可用 `--ppa off` 关闭。
直接生成评估每个实验分支的 `module_final.sv`；JSON 评估通过契约验证的 `final.sv`；
候选流程只评估冻结选择后的 `selected.sv`；RTLLM 评估最后生成的 `module.sv`。
没有最终输出时记录 `skipped`；RTLLM 的 `--check` 只做参考预检，跳过生成代码的 PPA。
存在最终 RTL 时，即使功能测试失败，也可以记录综合指标，同时保留 `functional_passed=false`。

## 本阶段的指标边界

| 指标 | 当前结果 | 单位 / 含义 |
|---|---|---|
| 综合 | `synthesis_passed` | 独立于功能正确性 |
| 面积代理 | 单元总数、组合单元、触发器、锁存器及单元类型分布 | 通用门级单元数，不是 μm² 或 FPGA LUT 数 |
| 时序代理 | `logic_depth` | 排除时序单元后的最长组合路径层数，不是 ns 或 MHz |
| 实际面积 / 时延 / Fmax | `null` | 等待器件或标准单元库及约束 |
| 功耗 | `not_evaluated`，数值 `null` | 等待器件 / 工艺、工作条件、开关活动率 |

`status=ok` 表示这次综合和报告提取成功，不表示完整物理 PPA 达标。
当前不设置 PPA 阈值、不按 PPA 改变候选排序、不向生成器提供 PPA 修复反馈。
功能测试结论及原有退出码语义保留；PPA 缺工具、综合失败、报告错误或超时均单独记状态。
Yosys 对 SystemVerilog 的支持有限：仿真通过但综合不支持的语法会记录 `synthesis_failed`。

## 安装与参数

后端按显式 `--ppa-yosys`、环境变量 `PPA_YOSYS`、PATH 中的 `yosys` / `yowasp-yosys`、
项目专用 `tools/ppa/.venv` / `.venv312` 的顺序发现。显式指定的工具不存在时不会偷偷换用其他工具。
可使用已安装的原生 Yosys。Windows 也可以安装固定版本的 YoWASP 包：

```powershell
cd E:\SRTP\SRTP_LLM2RTL
python -m venv tools\ppa\.venv
tools\ppa\.venv\Scripts\python.exe -m pip install -r tools\ppa\requirements.txt
```

`--ppa-top` 默认 `TopModule`；RTLLM 默认自动发现顶层，可显式指定以避免多顶层选择歧义。
`--ppa-timeout` 默认 120 秒，必须是正整数。YoWASP 首次运行需要编译 WebAssembly 缓存。
所有输入按原始字节记录 SHA-256，并用固定文件名复制到新报告目录；不读取参考 RTL 或测试平台。
输入必须是独立 RTL，辅助模块可一起提供；外部 include 文件和目标 IP 库尚未接入。

## 使用

原有生成命令自动附加综合步骤，例如下面的生成命令会调用已配置的 LLM：

```powershell
python run.py direct --dataset .\dataset_spec-to-rtl_gcc --case Prob005 --ppa generic
python run.py generate --dataset .\dataset_spec-to-rtl_gcc --case Prob005 --ppa generic
python run.py json --dataset .\dataset_spec-to-rtl_gcc --cases Prob005 --ppa generic
```

对已有 RTL 单独离线检测，不调用 LLM，不改动原始实验：

```powershell
python run.py ppa --rtl "已有实验目录\selected.sv" --output "experiments\ppa_saved_case"
python run.py ppa --rtl "设计\main.sv" "设计\helper.sv" --ppa-top MyTop --output "experiments\ppa_my_top"
```

输出目录必须不存在，防止旧网表或旧指标被当成当前结果。独立命令检测失败返回非零退出码。
批次恢复会保留已完成条目；需要给旧条目补指标时使用独立 `ppa` 命令。

## 报告

每个最终 RTL 对应一个 `ppa/` 目录，包含 `report.json`、输入快照、`synthesis.ys`、
`synthesis.log`、`launcher.log`、`logic_depth.log`、`stats.json`、`netlist.json`、`netlist.v`
（工具失败时可能只有部分文件）。YoWASP 默认缓存放在 `tools/ppa/cache`，可用 `YOWASP_CACHE_DIR` 覆盖。
每题与批次 JSON 中增加 `ppa` 字段；实验根目录新增 `ppa_results.csv`，
兼容 Excel，缺失的数值留空。原有功能结果 CSV 不改列结构。
独立 `ppa` 命令直接将这些文件保存在其 `--output` 目录。

后端使用 `hierarchy -check`、`flatten -noscopeinfo`、`synth -flatten`、`check -assert`、`stat -json`、
`write_json` 和 `ltp -noff`。通过条件要求工具正常退出、单一且无黑盒的扁平顶层、
统计与网表单元数一致，以及有效的组合路径报告；常量输出的零单元设计允许成功。

参考：[Yosys 综合文档](https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/synthesis/synth.html)、
[ltp 源码与命令说明](https://github.com/YosysHQ/yosys/blob/main/passes/cmds/ltp.cc)、
[YoWASP 安装说明](https://yowasp.org/)。
