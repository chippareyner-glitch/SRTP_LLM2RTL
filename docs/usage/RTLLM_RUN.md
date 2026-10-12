# RTLLM 50题运行入口

`python run.py rtllm --all`：使用现有G3提示词及DeepSeek客户端，每题生成一次，调用validator.validate_rtllm检查语法和原配Testbench功能。

`python run.py rtllm --all --max-repairs 5`：最多修复5次，原配Testbench诊断进入修复提示词。因此该模式不是独立留出测试，也不是之前的AI契约Testbench流程。

`python run.py rtllm --check --timeout 30`：只跑50题参考实现，不调用API。

`--cases accu adder_16bit` 可选择少量题；`--dataset`指定含dataset_manifest.json的目录；`--output`必须是新的输出目录；`--timeout`为每次仿真的墙钟秒数。

每题先做reference预检，参考RTL只用于本地验证，不发送模型。带verified_前缀的模块在临时副本中适配测试台名称，映射保存在reference_module_mapping.json。原数据集不变。

输出在experiments/rtllm_时间戳：每题module.sv是最新生成候选，iteration_NNN保留每轮代码、提示词、API日志及验证日志，summary.json和results.csv汇总。reference_failed表示原配基准未通过，功能结果为空；仍生成一版候选并保存其验证结果。超时和缺少通过标志不能通过。连续3题API失败停止批次。当前未实现断点续跑，重试可用--cases选择未完成题。

Windows仿真使用独立临时工作目录，保留随题数据路径。沙箱若限制Icarus子进程，可在正常PowerShell终端运行。RTLLM_SCRATCH环境变量可指定可写的ASCII临时父目录。

此评测反映原配测试覆盖范围，不能证明所有输入下的正确性。单次成功率以iterations[0]计，修复后以最后一轮计；参考基准失败需单列，不归因于模型。
