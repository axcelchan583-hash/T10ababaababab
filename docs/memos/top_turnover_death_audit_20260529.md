# Top 榜单流动性死亡审计

日期：2026-05-29  
目的：上一轮新 Y 烟测中，唯一还显著的是 `top10/top20_turnover_prev_pat_share`。本轮只做三个生死检验：

1. Top 榜单流动性的事件研究和前趋势；
2. 新晋 Top 主体类型；
3. 授权/被引/家族被引授权口径下的 Top 流动性。

结论先行：

```text
不建议继续把 T10 写成强论文。
Top 榜单流动性只有“数量口径 + scope>=2 阈值”有一定动态支持；
主体类型不由个人驱动，这一点稍微加分；
但质量口径没有撑住，被引授权口径甚至显著为负。
如果没有新的 X 或新的更微观 Y，T10 应暂停或归档。
```

## 一、事件研究

脚本：

- `scripts/run_top_turnover_event_study_stata.do`

结果：

- `scope >= 2` 是唯一较能看的事件定义；
- `top10_turnover_prev_pat_share` 在事件后 +1、+2、+3 年为正，其中 +1、+3 在 5% 显著，+2 在 10% 显著；
- `top20_turnover_prev_pat_share` 在事件后 +1、+2、+3 年为正，均在 10% 左右显著；
- 强 FE 下前趋势联合检验不显著：Top10 `p=0.128`，Top20 `p=0.252`；
- 但 `scope >= 1` 没有处理后正效应，`scope >= 3/5` 稳定性也弱。

`scope >= 2`，强 FE 结果：

| outcome | event | coef | p |
|---|---:|---:|---:|
| `top10_turnover_prev_pat_share` | -4 | 0.0375 | 0.2071 |
| `top10_turnover_prev_pat_share` | -3 | -0.0171 | 0.6024 |
| `top10_turnover_prev_pat_share` | -2 | 0.0262 | 0.3654 |
| `top10_turnover_prev_pat_share` | 0 | 0.0072 | 0.7973 |
| `top10_turnover_prev_pat_share` | +1 | 0.0684 | 0.0383 |
| `top10_turnover_prev_pat_share` | +2 | 0.0668 | 0.0531 |
| `top10_turnover_prev_pat_share` | +3 | 0.0904 | 0.0130 |
| `top10_turnover_prev_pat_share` | +4+ | 0.0451 | 0.1383 |
| `top20_turnover_prev_pat_share` | +1 | 0.0438 | 0.0990 |
| `top20_turnover_prev_pat_share` | +2 | 0.0486 | 0.0914 |
| `top20_turnover_prev_pat_share` | +3 | 0.0570 | 0.0538 |

判断：

```text
事件动态不是完全烂，但只在 scope>=2 阈值下成立。
这能支持“有苗头”，不能支持“强识别已经过关”。
```

## 二、新晋 Top 主体类型

脚本：

- `scripts/build_top_turnover_type_panel.py`
- `scripts/run_top_turnover_type_stata.do`

结果：

强 FE + 政策控制、all 样本：

| outcome | coef | p |
|---|---:|---:|
| `t10_new_org_top` | 0.0320 | 0.0387 |
| `t10_new_firm_top` | 0.0221 | 0.1532 |
| `t10_new_ind_top` | 0.0028 | 0.8349 |
| `t10_new_kn_top` | 0.0053 | 0.3487 |
| `t20_new_org_top` | 0.0235 | 0.1035 |
| `t20_new_firm_top` | 0.0190 | 0.1916 |
| `t20_new_ind_top` | 0.0049 | 0.7039 |

解释：

- Top10 的新晋产出份额主要来自“非个人组织”合计；
- 不是个人申请人驱动，这比此前新进入主线要好；
- 但企业单项不显著，高校/科研机构也不显著；
- Top20 组织项只是边际接近，没到 10%。

判断：

```text
主体类型给了一点正面证据：不是个人专利噪声。
但它只支持“组织主体进入 Top10 榜单”，不支持更强的企业追赶或科研机构追赶叙事。
```

## 三、质量口径 Top 流动

脚本：

- `scripts/build_quality_top_turnover_panel.py`
- `scripts/run_quality_top_turnover_stata.do`

数据构造：

- 从 20G 全量专利压缩包重新流式抽取申请人级质量专利；
- `inv_grant_appyear`：发明授权，申请年份归年；
- `inv_grant_cited_appyear`：发明授权且被引，申请年份归年；
- `inv_grant_familycited_appyear`：发明授权且家族被引，申请年份归年。

构造出的申请人级质量计数：

- 发明授权：1,316,451 行；
- 被引授权：232,865 行；
- 家族被引授权：979,631 行。

强 FE + 政策控制、all 样本：

| outcome | coef | p |
|---|---:|---:|
| `qgrant_t10_new_pat_sh` | 0.0118 | 0.3808 |
| `qgrant_t20_new_pat_sh` | -0.0033 | 0.7774 |
| `qfcited_t10_new_pat_sh` | 0.0017 | 0.9042 |
| `qfcited_t20_new_pat_sh` | -0.0080 | 0.5279 |
| `qcited_t10_new_pat_sh` | -0.0373 | 0.0229 |
| `qcited_t20_new_pat_sh` | -0.0298 | 0.0707 |

判断：

```text
质量口径没有撑住。
普通授权 Top 流动不显著；
家族被引授权 Top 流动不显著；
被引授权 Top 流动反而显著为负。
```

这基本打掉了“头部创新位置重组”作为高质量创新结构变化的主线。

## 四、最终判断

三项死亡审计结果：

| 检验 | 结果 | 判断 |
|---|---|---|
| 事件研究 | scope>=2 下可看，+1 到 +3 年为正，前趋势尚可 | 黄灯 |
| 主体类型 | Top10 新晋组织主体显著，个人不显著 | 黄灯偏绿 |
| 质量口径 | 授权/家族被引不显著，被引授权为负 | 红灯 |

最终 verdict：

```text
T10 不建议继续作为主力论文推进。
若坚持写，只能写成非常收缩的数量口径发现：
“IDC 服务覆盖与城市 Top 专利申请人榜单产出流动性提高相关”。
但这不足以支撑中文顶刊或 AJG3。
```

建议：

1. 先暂停 T10；
2. 保留数据工程和文献整理；
3. 不再继续围绕 IDC 换 Y；
4. 除非后续拿到更强 X，例如真实机柜/MW/FLOPS/云节点，或能构造更微观的企业/申请人层面识别，否则不再投入主力时间。

## 五、对应文件

- 事件研究：`results/tables/top_turnover_event_study_20260529.csv`
- 类型分解：`results/tables/top_turnover_type_results_20260529.csv`
- 质量口径：`results/tables/quality_top_turnover_results_20260529.csv`
- 关键摘要：`results/tables/top_turnover_death_audit_key_summary_20260529.csv`
