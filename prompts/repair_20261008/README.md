# 两批失败记录的专属修复提示词

本包包含26份逐题提示词：deepseek批25项，legacy批最终未通过1项。每份均附规格、该批候选和历史评估，不需要手动补齐上下文。

仅整理提示词与诊断，未调用LLM、未改原始实验、未验证新修复代码；不能承诺仅凭提示词全部通过。

## 重要发现

- deepseek批有5项API失败、8项编译失败、10项功能失配、2项超时。legacy的154同时有功能失配与Reviewer截断。
- 034/053/104的参考实现规定了规格未写出的初值；153参考PHT复位01，文字未指定。
- 062选择方向、093的K-map第2路、149补水方向存在文字与参考冲突。相应提示词提供分开的处理目标，不能同时声称符合两者。
- 099的参考和DUT都是Y1/Y3，测试平台却连接Y2/Y4；只改DUT不能修复整个编译。
- 082/141实际日志各有200000样本零失配，但命中固定仿真截止时间。不能将其误报为已通过，也不能根据旧摘要零样本就判定没运行。
- legacy有5个题目录，其中4个最终成功；133早期失败已在第2轮恢复，不再列为最终未通过项。历史失败阶段仍可用于研究，但不应覆盖已有成功结果。

## 使用方式

打开对应文件，把“可整体复制的任务”及后续内容整体交给模型。先解决编译兼容、明确的时序问题；冲突项先选定规格目标或本地基准兼容目标。API项先恢复完整生成，超时和接口项先修评测条件。

每轮保留原始文件，在新的实验目录保存候选、编译日志、仿真日志和结果。必须正常退出、有实际检查样本且零失配，才能记录通过；测试接口修正后的成绩单列，不能替代原始基准成绩。保留修复前/后与API异常的独立计数。

本包为基准辅助调试：诊断已查看部分参考实现以确认初态与规格冲突，未将完整参考RTL粘入提示词。任何使用这些补充约定得到的成绩均不应宣称spec-only或盲测结果。有限仿真通过不等同于形式化等价或所有输入正确。

## 逐题索引

| 批次 | 题目 | 分类 | 提示词 |
|---|---|---|---|
| deepseek | Prob034_dff8 | 初态约定缺失 | [打开](deepseek_full_20260920__Prob034_dff8.md) |
| deepseek | Prob053_m2014_q4d | 初态约定缺失 | [打开](deepseek_full_20260920__Prob053_m2014_q4d.md) |
| deepseek | Prob062_bugs_mux2 | 规格与基准冲突 | [打开](deepseek_full_20260920__Prob062_bugs_mux2.md) |
| deepseek | Prob082_lfsr32 | 测试超时待诊断 | [打开](deepseek_full_20260920__Prob082_lfsr32.md) |
| deepseek | Prob089_ece241_2014_q5a | API生成中断 | [打开](deepseek_full_20260920__Prob089_ece241_2014_q5a.md) |
| deepseek | Prob093_ece241_2014_q3 | 规格与基准冲突 | [打开](deepseek_full_20260920__Prob093_ece241_2014_q3.md) |
| deepseek | Prob098_circuit7 | 时序延迟疑点 | [打开](deepseek_full_20260920__Prob098_circuit7.md) |
| deepseek | Prob099_m2014_q6c | 测试接口冲突 | [打开](deepseek_full_20260920__Prob099_m2014_q6c.md) |
| deepseek | Prob104_mt2015_muxdff | 初态约定缺失 | [打开](deepseek_full_20260920__Prob104_mt2015_muxdff.md) |
| deepseek | Prob107_fsm1s | 枚举类型编译错误 | [打开](deepseek_full_20260920__Prob107_fsm1s.md) |
| deepseek | Prob117_circuit9 | 多余历史输入状态 | [打开](deepseek_full_20260920__Prob117_circuit9.md) |
| deepseek | Prob119_fsm3 | 枚举类型编译错误 | [打开](deepseek_full_20260920__Prob119_fsm3.md) |
| deepseek | Prob127_lemmings1 | 枚举类型编译错误 | [打开](deepseek_full_20260920__Prob127_lemmings1.md) |
| deepseek | Prob133_2014_q3fsm | API生成中断 | [打开](deepseek_full_20260920__Prob133_2014_q3fsm.md) |
| deepseek | Prob136_m2014_q6 | 枚举类型编译错误 | [打开](deepseek_full_20260920__Prob136_m2014_q6.md) |
| deepseek | Prob137_fsm_serial | 完成信号提前及组合依赖 | [打开](deepseek_full_20260920__Prob137_fsm_serial.md) |
| deepseek | Prob138_2012_q2fsm | 枚举类型编译错误 | [打开](deepseek_full_20260920__Prob138_2012_q2fsm.md) |
| deepseek | Prob139_2013_q2bfsm | API生成中断 | [打开](deepseek_full_20260920__Prob139_2013_q2bfsm.md) |
| deepseek | Prob140_fsm_hdlc | API连接中断 | [打开](deepseek_full_20260920__Prob140_fsm_hdlc.md) |
| deepseek | Prob141_count_clock | 测试超时待诊断 | [打开](deepseek_full_20260920__Prob141_count_clock.md) |
| deepseek | Prob146_fsm_serialdata | 枚举类型编译错误 | [打开](deepseek_full_20260920__Prob146_fsm_serialdata.md) |
| deepseek | Prob149_ece241_2013_q4 | 规格与基准冲突 | [打开](deepseek_full_20260920__Prob149_ece241_2013_q4.md) |
| deepseek | Prob153_gshare | 复位约定缺失 | [打开](deepseek_full_20260920__Prob153_gshare.md) |
| deepseek | Prob155_lemmings4 | 枚举编译及边界检查 | [打开](deepseek_full_20260920__Prob155_lemmings4.md) |
| deepseek | Prob156_review2015_fancytimer | API生成中断 | [打开](deepseek_full_20260920__Prob156_review2015_fancytimer.md) |
| legacy | Prob154_fsm_ps2data | 功能错位且Reviewer中断 | [打开](legacy_v2_20260922_103933_419294__Prob154_fsm_ps2data.md) |
