# 新 Y 烟测：持续进入、质量进入与头部榜单流动性

日期：2026-05-28  
目的：在城市×技术领域 DDD 经 PPML 与 rate 检验后无法作为主识别的情况下，尝试寻找新的、更能防守的 Y。

## 一、数据与规格

面板：

- `data/processed/new_y_smoke_panel_2008_2023.csv`
- 样本：`inv_app_appyear`，2008-2023 年，4,647 个城市年观测；
- 新进入申请人历史预热期：1985 年起；
- X：`ln1p_idc_scope_stock_l1`，即滞后一期 IDC 经营许可覆盖存量。

规格：

1. `city_year`：城市 FE + 年份 FE；
2. `provyr_base`：城市 FE + 省份×年份 FE + 基期专利规模分组×年份 FE + 基期 Top10 share 分组×年份 FE；
3. `provyr_base_policy`：在 2 的基础上加入政策 horse-race 控制。

计数型 Y 用 `ppmlhdfe`；份额/率类 Y 用 `reghdfe`。标准误按城市聚类。

## 二、尝试的三组新 Y

### 1. 持续进入

定义：申请人在某城市首次出现后，未来 2 年或 3 年内是否继续在同一城市申请专利。

变量包括：

- `surv2_applicants`、`surv3_applicants`；
- `surv2_entry_patents`、`surv3_entry_patents`；
- `surv2_future_patents`、`surv3_future_patents`；
- `surv2_applicant_rate`、`surv3_applicant_rate`；
- `surv2_entry_pat_share_new`、`surv3_entry_pat_share_new`；
- `surv2_entry_pat_share_total`、`surv3_entry_pat_share_total`。

结果：

- 计数型变量多数为正，但在强规格下不显著；
- `surv2_entry_pat_share_new` 和 `surv3_entry_pat_share_new` 在强规格下显著为负；
- 说明 IDC 服务覆盖后，新进入主体里“能持续留下来的主体”并没有更高占比。

强规格示例：

| Y | coef | p |
|---|---:|---:|
| `surv2_applicants` | 0.0546 | 0.2598 |
| `surv3_applicants` | 0.0299 | 0.5065 |
| `surv2_entry_pat_share_new` | -0.0165 | 0.0737 |
| `surv3_entry_pat_share_new` | -0.0210 | 0.0397 |

判断：

```text
持续进入不能救主线。
它反而提示：此前的“新进入扩容”更像一次性或低持续性进入，不能强写为稳定创新主体成长。
```

### 2. 高质量进入

定义：把新进入专利换成授权、被引授权、家族被引授权口径。

变量包括：

- `qgrant_new_n`、`qgrant_new_pat`；
- `qcited_new_n`、`qcited_new_pat`；
- `qfcited_new_n`、`qfcited_new_pat`；
- `qgrant_share_total`、`qcited_share_total`、`qfcited_share_total`；
- 对应的 `share_new`。

结果：

- 强规格下，发明授权、被引授权、家族被引授权的新进入数量均不显著；
- 质量份额也不显著；
- 方向大多为正，但不能作为主 Y。

强规格示例：

| Y | coef | p |
|---|---:|---:|
| `qgrant_new_n` | 0.0271 | 0.5278 |
| `qgrant_new_pat` | 0.0467 | 0.4258 |
| `qfcited_new_n` | 0.0193 | 0.6644 |
| `qfcited_new_pat` | 0.0277 | 0.6292 |
| `qgrant_share_total` | 0.0044 | 0.5387 |
| `qfcited_share_total` | 0.0057 | 0.3815 |

判断：

```text
高质量进入不能作为主线。
最多只能在附录里说明：方向没有明显反证，但质量闭环没有打赢。
```

### 3. 头部榜单流动性

定义：城市年度 Top10/Top20 专利申请人中，有多少专利来自“上一年不在 Top10/Top20 榜单”的申请人。

核心变量：

- `top10_turnover_prev_pat_share`；
- `top20_turnover_prev_pat_share`。

解释：

```text
不是问“有没有更多长尾进入”，而是问：
IDC 服务覆盖增强后，城市头部创新位置是否更容易被上一年未入榜主体重新争夺？
```

结果最稳：

| Y | sample | city+year FE | 强 FE | 强 FE + 政策 |
|---|---|---:|---:|---:|
| `top10_turnover_prev_pat_share` | all | 0.0503*** | 0.0355** | 0.0348** |
| `top10_turnover_prev_pat_share` | min20 | 0.0531*** | 0.0362** | 0.0353** |
| `top10_turnover_prev_pat_share` | min50 | 0.0525*** | 0.0348** | 0.0338** |
| `top20_turnover_prev_pat_share` | all | 0.0331*** | 0.0272** | 0.0284** |
| `top20_turnover_prev_pat_share` | min20 | 0.0359*** | 0.0280** | 0.0282** |
| `top20_turnover_prev_pat_share` | min50 | 0.0329*** | 0.0273** | 0.0274** |

但有一个边界：

- `top10_turnover_prev_share`，即“未入榜主体数量占比”，不稳；
- 稳的是“未入榜主体贡献的 Top 专利份额”。

判断：

```text
这是当前唯一有明显生命力的新 Y。
可改写为：IDC 服务覆盖并没有稳定扩大可持续新进入，也没有稳定提高高质量新进入份额；
但它显著提高了城市头部创新榜单的产出流动性，即上一年未入榜主体在当年 Top10/Top20 专利中的份额上升。
```

## 三、当前 Go / Pivot 判断

这一轮结果不支持继续写：

```text
IDC 服务覆盖扩大稳定创新进入边界；
IDC 服务覆盖提高高质量新进入；
城市×技术领域 DDD 是最硬主识别。
```

更可能救得住的方向是：

```text
城市算力服务可得性与头部创新位置重组：
来自城市 Top 专利申请人榜单流动性的证据
```

它的核心贡献不再是“长尾扩容”，而是：

```text
算力服务覆盖提高后，城市创新头部位置更容易发生重新排序；
创新资源并未简单向长尾扩散，但头部榜单内部的竞争和更替增强。
```

## 四、下一步必须补的检验

如果继续这个新方向，下一步不是立刻写论文，而是先补四个防守检验：

1. 事件研究：`top10_turnover_prev_pat_share` 和 `top20_turnover_prev_pat_share` 的动态效应与前趋势；
2. 主体类型：新增进入 Top 榜单的主体是企业、高校、科研院所、个人，还是上市公司集团；
3. 质量口径：Top 榜单流动是否也出现在发明授权、家族被引授权、数字/AI 专利；
4. 名称清洗压力测试：Top 申请人必须做更强的名称标准化和重点主体人工核验。

## 五、对应文件

- 构造脚本：`scripts/build_new_y_smoke_panel.py`
- 回归脚本：`scripts/run_new_y_smoke_tests_stata.do`
- 完整结果：`results/tables/new_y_smoke_results_20260528.csv`
- 精简结果：`results/tables/new_y_smoke_key_summary_20260528.csv`
