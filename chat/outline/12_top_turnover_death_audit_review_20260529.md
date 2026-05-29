# 给网页版评审：T10 Top 榜单流动性死亡审计

## 1. 背景

T10 原主线“IDC 服务覆盖扩大城市专利系统进入边界”已经多次降级：

- 企业创新韧性不稳；
- 上市公司相对优势削弱被结果反驳；
- 城市×技术领域 DDD 的 `ln(1+Y)` 正结果被 PPML 打掉；
- 持续进入和高质量进入两个新 Y 没有救出主线。

上一轮唯一还有生命力的是：

```text
top10_turnover_prev_pat_share / top20_turnover_prev_pat_share
= 当年城市 Top10/Top20 专利申请人中，
  上一年未入榜主体贡献的专利份额。
```

本轮做死亡审计，只看这个新方向是否值得继续。

## 2. 三项死亡审计

### A. 事件研究

事件定义：首次 `idc_scope_stock >= threshold`。  
主要关注 `threshold = 2`。

强 FE：

```text
城市 FE + 省份×年份 FE
+ 基期专利规模分组×年份 FE
+ 基期 Top10 share 分组×年份 FE
```

`scope >= 2` 结果：

| outcome | event | coef | p |
|---|---:|---:|---:|
| `top10_turnover_prev_pat_share` | -4 | 0.0375 | 0.2071 |
| `top10_turnover_prev_pat_share` | -3 | -0.0171 | 0.6024 |
| `top10_turnover_prev_pat_share` | -2 | 0.0262 | 0.3654 |
| `top10_turnover_prev_pat_share` | +1 | 0.0684 | 0.0383 |
| `top10_turnover_prev_pat_share` | +2 | 0.0668 | 0.0531 |
| `top10_turnover_prev_pat_share` | +3 | 0.0904 | 0.0130 |
| `top20_turnover_prev_pat_share` | +1 | 0.0438 | 0.0990 |
| `top20_turnover_prev_pat_share` | +2 | 0.0486 | 0.0914 |
| `top20_turnover_prev_pat_share` | +3 | 0.0570 | 0.0538 |

前趋势：

- Top10 pre-trend joint p = 0.128；
- Top20 pre-trend joint p = 0.252。

边界：

- `scope >= 1` 没有处理后正效应；
- `scope >= 3/5` 不够稳。

初步判断：

```text
事件动态黄灯：scope>=2 有苗头，但阈值依赖明显。
```

### B. 新晋 Top 主体类型

问题：

> 新晋 Top 专利份额到底来自个人，还是组织/企业/高校科研机构？

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

初步判断：

```text
不是个人驱动，这是好消息；
但企业单项、高校科研单项都不稳，只能写“非个人组织”。
```

### C. 质量口径 Top 流动

重新从 20G 全量专利包里抽申请人级质量专利，构造质量口径 Top10/Top20 流动：

- 发明授权；
- 发明授权且被引；
- 发明授权且家族被引。

申请人级质量计数规模：

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

初步判断：

```text
质量口径红灯。
普通授权和家族被引授权都不显著；
被引授权 Top 流动反而显著下降。
```

## 3. 当前 verdict

我自己的判断是：

```text
T10 不建议继续作为主力论文。
```

如果硬写，只能非常收缩：

```text
IDC 服务覆盖与城市 Top 专利申请人榜单的数量型产出流动性提高相关。
```

但这个结论太窄：

- 阈值依赖 `scope>=2`；
- 质量口径撑不住；
- 企业/高校科研单项不稳；
- 很难支撑中文顶刊或 AJG3。

## 4. 请重点评审

1. 是否同意暂停/归档 T10？
2. `Top applicant turnover` 作为主 Y 是否有足够文献锚点？
3. 质量口径失败是否已经足以判 No-Go？
4. 如果不归档，是否还有一个更好的重写角度？
5. 是否值得继续补名称清洗、集团合并、事件 DID，还是已经边际收益过低？

## 5. 文件

- memo：`docs/memos/top_turnover_death_audit_20260529.md`
- event：`results/tables/top_turnover_event_study_20260529.csv`
- type：`results/tables/top_turnover_type_results_20260529.csv`
- quality：`results/tables/quality_top_turnover_results_20260529.csv`
- key summary：`results/tables/top_turnover_death_audit_key_summary_20260529.csv`
