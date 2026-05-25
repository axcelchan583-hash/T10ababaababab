# 申请年份口径小闭环第一轮结果

日期：2026-05-24

## 1. 本轮做了什么

根据 Claude 和 ChatGPT Pro 的评审意见，本轮先跑“小闭环”，不做全量集团合并。

已完成：

1. 从全量专利 RAR 中按字段 `申请年份` 重构发明申请口径；
2. 2000-2007 年作为新进入申请人预热期；
3. 输出 2008-2023 年城市-申请人-申请年份明细；
4. 构造城市-年份 HHI、Top10、新进入申请人、rolling pre-top、baseline top、中腰部既有主体份额；
5. 合并 IDC 城市年变量和省份信息；
6. 跑城市 FE、年份 FE、省份×年份 FE、基期能力×年份 FE、城市趋势；
7. 补跑剔除大城市和小样本城市阈值稳健性。

## 2. 新数据输出

申请人明细：

`data/processed/city_applicant_counts_application_year/city_applicant_counts_inv_app_appyear_2000_2023.csv.gz`

规模：

- 2,850,367 个申请人-城市-申请年份记录；
- 发明申请；
- 2000-2023 年。

城市年指标：

`data/processed/patent_applicant_concentration_application_year_2008_2023.csv`

规模：

- 6,149 行；
- 443 个城市；
- 2008-2023 年。

IDC 合并面板：

`data/processed/idc_applicant_concentration_application_year_panel_2008_2023.dta`

规模：

- 6,149 行；
- 4,647 行匹配 IDC 城市年面板；
- 291 个匹配城市；
- 207 个城市有过 IDC stock。

回归结果：

- `results/tables/idc_applicant_concentration_application_year_results_20260524.csv`
- `results/tables/idc_applicant_concentration_application_year_sample_robustness_20260524.csv`

## 3. 核心变量

主口径：

```text
scope = inv_app_appyear
```

即：

```text
发明申请 × 申请年份
```

新增结构变量：

| 变量 | 含义 |
|---|---|
| `new_applicant_share` | 新进入申请人的专利份额 |
| `top10_share` | 当年 Top10 申请人份额 |
| `roll_top_share` | t-3 至 t-1 年 rolling Top10 申请人在 t 年的份额 |
| `roll_mid_inc_share` | 非新进入、非 rolling Top10 的既有中腰部份额 |
| `base_top_share` | 2008-2010 年 baseline Top10 申请人在 t 年的份额 |
| `base_mid_inc_share` | 非新进入、非 baseline Top10 的既有中腰部份额 |

## 4. 主结果：申请年份后发生了什么

核心 X：

```text
ln1p_idc_stock_l1
```

### 4.1 城市 FE + 年份 FE

| Y | 系数 | p 值 | 结论 |
|---|---:|---:|---|
| `new_applicant_share` | 0.015 | 0.010 | 新进入份额上升 |
| `hhi` | 0.015 | 0.000 | 集中度上升 |
| `top10_share` | 0.032 | 0.000 | 当年 Top10 份额上升 |
| `roll_top_share` | -0.024 | 0.000 | rolling pre-top 份额下降 |
| `base_top_share` | 0.037 | 0.000 | baseline top 份额上升 |
| `base_mid_inc_share` | -0.019 | 0.003 | baseline 中腰部份额下降 |

读法：

- 简单 FE 下支持“新进入 + 当年集中 + baseline 头部强化 + 中腰部挤压”；
- 但 rolling pre-top 为负，说明“最近三年头部持续吸收”并不成立。

### 4.2 省份 × 年份 FE

| Y | 系数 | p 值 | 结论 |
|---|---:|---:|---|
| `new_applicant_share` | 0.021 | 0.002 | 新进入份额上升 |
| `hhi` | 0.011 | 0.006 | 集中度上升 |
| `top10_share` | 0.029 | 0.002 | 当年 Top10 份额上升 |
| `roll_top_share` | -0.022 | 0.008 | rolling pre-top 份额下降 |
| `base_top_share` | 0.025 | 0.005 | baseline top 份额上升 |
| `base_mid_inc_share` | -0.019 | 0.008 | baseline 中腰部份额下降 |

读法：

- 省份×年份 FE 后，核心“杠铃化”仍有支持；
- 这说明结果不是纯省级政策或省级趋势；
- 但 rolling pre-top 仍为负，说明头部强化更像“长期基准头部 / 基础强主体”而非“短期持续 Top”。

### 4.3 省份 × 年份 FE + 基期能力/集中度 × 年份 FE

| Y | 系数 | p 值 | 结论 |
|---|---:|---:|---|
| `ln1p_new_applicants` | 0.069 | 0.006 | 新进入数量上升 |
| `new_applicant_share` | 0.005 | 0.482 | 不显著 |
| `hhi` | 0.003 | 0.503 | 不显著 |
| `top10_share` | -0.002 | 0.778 | 不显著 |
| `base_top_share` | -0.006 | 0.512 | 不显著 |
| `base_mid_inc_share` | 0.003 | 0.719 | 不显著 |

读法：

- 一旦吸收基期创新能力和基期集中度的差异趋势，“集中度 / 杠铃化”线明显变弱；
- 新进入数量仍为正，但新进入份额不稳；
- 这说明当前集中度结果可能部分来自高基期创新能力城市的差异趋势。

## 5. 剔除大城市和小样本稳健性

使用省份×年份 FE 规格：

### 剔除北上广深杭

- `new_applicant_share`：0.017，p=0.009；
- `hhi`：0.012，p=0.002；
- `top10_share`：0.033，p=0.000；
- `base_top_share`：0.030，p=0.001；
- `base_mid_inc_share`：-0.019，p=0.009。

### 剔除 Top10 专利城市

- `new_applicant_share`：0.014，p=0.033；
- `hhi`：0.012，p=0.002；
- `top10_share`：0.033，p=0.000；
- `base_top_share`：0.028，p=0.002；
- `base_mid_inc_share`：-0.016，p=0.030。

### 剔除小样本城市年

`total_patents >= 20`：

- `new_applicant_share`：0.019，p=0.004；
- `hhi`：0.005，p=0.090；
- `top10_share`：0.022，p=0.013；
- `base_top_share`：0.018，p=0.032；
- `base_mid_inc_share`：-0.018，p=0.014。

`total_patents >= 50`：

- `new_applicant_share`：0.019，p=0.004；
- `hhi`：0.004，p=0.224；
- `top10_share`：0.015，p=0.077；
- `base_top_share`：0.009，p=0.297；
- `base_mid_inc_share`：-0.016，p=0.041。

读法：

- 剔除大城市后，省份×年份 FE 下结果没有消失，这是好消息；
- 但剔除小样本后 HHI 和 baseline top 变弱，Top10 和中腰部下降仍有一定信号；
- 加基期能力×年份 FE 后，大部分集中度结果消失，这是最大黄灯。

## 6. 当前判断

这一轮不是红灯，但也不是绿灯。

更准确是：

```text
黄灯偏绿：申请年份口径支持“进入扩容 + 当年集中 + baseline 中腰部挤压”，
但集中度结果对基期能力差异趋势非常敏感。
```

可以继续，但下一步不能直接写论文。

## 7. 对理论叙事的影响

原先预期：

```text
新进入者份额上升 + 预先 Top 份额上升 + 中腰部份额下降
```

现在更细的结果是：

1. `new_applicant_share` 在省份×年份 FE 下稳健为正；
2. 当年 `top10_share` 和 `hhi` 也为正；
3. `base_top_share` 为正，`base_mid_inc_share` 为负；
4. 但 `roll_top_share` 为负；
5. 加基期能力×年份 FE 后，集中度和杠铃化不稳。

因此，当前不宜直接写“既有头部吸收能力强化”。

更谨慎的说法是：

```text
算力基础设施扩张伴随更多新申请人进入，也伴随城市年度创新产出向当年头部申请人集中。
这种集中并非简单由最近几年头部持续垄断推动，
更可能反映长期基础强主体、头部重排或新晋头部的共同作用。
```

如果后续要写“头部吸收能力”，必须补：

- Top 申请人身份识别；
- baseline Top 与 rolling Top 的差异解释；
- 基期能力异质性，而不是只看平均效应。

## 8. 下一步必须做

### 8.1 事件研究 / 预趋势

这是下一步第一优先级。  
如果 HHI / Top10 / new applicant share 在 IDC 前已经上升，则当前结果不能写因果。

建议事件定义：

1. 首次 `idc_stock > 0`；
2. 或首次进入 `idc_stock` 增长高分位；
3. 若补到智算中心 / 东数西算节点，再用更清晰事件。

### 8.2 解释 baseline top 与 rolling top 的差异

当前 `base_top_share` 为正，`roll_top_share` 为负。必须检查：

- rolling top 是否被新进入者或短期波动污染；
- baseline top 是否主要是高校 / 大企业 / 科研机构；
- 当年 Top10 上升是否来自新晋头部。

建议导出：

```text
city-year Top20 applicants
baseline Top20 applicants
rolling Top20 applicants
new Top20 applicants
```

### 8.3 基期吸收能力异质性

既然加 `baseline × year FE` 会吸收结果，说明必须把它写成机制/异质性：

```text
IDC × high_baseline_AC
```

看：

- 高 AC 城市是否更集中；
- 低 AC 城市是否更多新进入；
- 如果二者可分离，理论才稳。

### 8.4 X 外部验证

当前仍需证明 IDC stock 不是注册地噪声。至少找一个外部指标验证：

- 机房地址；
- 数据中心数量；
- 机柜数 / MW；
- 智算中心；
- 国家算力枢纽 / 数据中心集群。

## 9. 暂缓事项

暂时不要做：

- 全量集团合并；
- 全量 A 股子公司匹配；
- 合作创新网络；
- IV；
- 过多城市异质性。

这些都应等事件研究和 X 验证之后再做。

