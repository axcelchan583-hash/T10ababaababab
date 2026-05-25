# IDC 覆盖范围口径事件研究：尾部合并版

日期：2026-05-25

## 1. 设置

- 事件定义：城市 IDC 覆盖范围存量首次达到 `>=1/2/3/5`。
- 事件窗口：`<=-4, -3, -2, -1, 0, +1, +2, +3, >=+4`，其中 `-1` 为遗漏基准期。
- 处理组：首次达到阈值年份位于 2012-2020 年的城市；对照组为从未达到阈值的城市。
- 规格一：城市固定效应 + 省份×年份固定效应。
- 规格二：城市固定效应 + 省份×年份固定效应 + 基期专利规模分组×年份固定效应 + 基期 Top10 分组×年份固定效应。
- 标准误按城市聚类。

## 2. 诊断表

`pre_p` 是 `<=-4, -3, -2` 三个前导项的联合检验 p 值；`post_avg` 是事件后 0 到 +3 年系数均值；`sig+/-` 是事件后 0 到 +3 年在 10% 水平显著为正/负的年份数。

| spec | event | outcome | treated cities | pre_p | post_avg | min post p | sig+ | sig- |
|---|---|---|---:|---:|---:|---:|---:|---:|
| province_year_fe | scope_ge_1 | base_mid_inc_share | 79 | 0.771 | -0.014 | 0.267 | 0 | 0 |
| province_year_fe | scope_ge_1 | base_top_share | 79 | 0.040 | -0.008 | 0.386 | 0 | 0 |
| province_year_fe | scope_ge_1 | hhi | 79 | 0.329 | 0.010 | 0.200 | 0 | 0 |
| province_year_fe | scope_ge_1 | ln1p_new_applicants | 79 | 0.507 | -0.020 | 0.337 | 0 | 0 |
| province_year_fe | scope_ge_1 | new_applicant_share | 79 | 0.952 | 0.024 | 0.023 | 2 | 0 |
| province_year_fe | scope_ge_1 | top10_share | 79 | 0.985 | 0.004 | 0.627 | 0 | 0 |
| province_year_fe | scope_ge_2 | base_mid_inc_share | 66 | 0.052 | -0.022 | 0.072 | 0 | 2 |
| province_year_fe | scope_ge_2 | base_top_share | 66 | 0.000 | -0.000 | 0.576 | 0 | 0 |
| province_year_fe | scope_ge_2 | hhi | 66 | 0.720 | 0.009 | 0.057 | 3 | 0 |
| province_year_fe | scope_ge_2 | ln1p_new_applicants | 66 | 0.237 | 0.045 | 0.185 | 0 | 0 |
| province_year_fe | scope_ge_2 | new_applicant_share | 66 | 0.338 | 0.025 | 0.038 | 2 | 0 |
| province_year_fe | scope_ge_2 | top10_share | 66 | 0.136 | 0.013 | 0.123 | 0 | 0 |
| province_year_fe | scope_ge_3 | base_mid_inc_share | 46 | 0.008 | -0.004 | 0.274 | 0 | 0 |
| province_year_fe | scope_ge_3 | base_top_share | 46 | 0.087 | 0.001 | 0.235 | 0 | 0 |
| province_year_fe | scope_ge_3 | hhi | 46 | 0.965 | 0.003 | 0.207 | 0 | 0 |
| province_year_fe | scope_ge_3 | ln1p_new_applicants | 46 | 0.654 | 0.050 | 0.311 | 0 | 0 |
| province_year_fe | scope_ge_3 | new_applicant_share | 46 | 0.024 | 0.004 | 0.367 | 0 | 0 |
| province_year_fe | scope_ge_3 | top10_share | 46 | 0.428 | 0.016 | 0.197 | 0 | 0 |
| province_year_fe | scope_ge_5 | base_mid_inc_share | 32 | 0.222 | 0.003 | 0.462 | 0 | 0 |
| province_year_fe | scope_ge_5 | base_top_share | 32 | 0.016 | -0.001 | 0.271 | 0 | 0 |
| province_year_fe | scope_ge_5 | hhi | 32 | 0.218 | -0.000 | 0.364 | 0 | 0 |
| province_year_fe | scope_ge_5 | ln1p_new_applicants | 32 | 0.233 | 0.037 | 0.226 | 0 | 0 |
| province_year_fe | scope_ge_5 | new_applicant_share | 32 | 0.035 | -0.002 | 0.498 | 0 | 0 |
| province_year_fe | scope_ge_5 | top10_share | 32 | 0.264 | 0.028 | 0.056 | 1 | 0 |
| provyr_baseyr_fe | scope_ge_1 | base_mid_inc_share | 79 | 0.811 | -0.005 | 0.599 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_1 | base_top_share | 79 | 0.335 | -0.010 | 0.279 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_1 | hhi | 79 | 0.434 | 0.006 | 0.459 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_1 | ln1p_new_applicants | 79 | 0.421 | 0.003 | 0.620 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_1 | new_applicant_share | 79 | 0.264 | 0.015 | 0.090 | 1 | 0 |
| provyr_baseyr_fe | scope_ge_1 | top10_share | 79 | 0.970 | -0.008 | 0.431 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_2 | base_mid_inc_share | 66 | 0.470 | -0.018 | 0.119 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_2 | base_top_share | 66 | 0.251 | -0.007 | 0.319 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_2 | hhi | 66 | 0.738 | 0.006 | 0.191 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_2 | ln1p_new_applicants | 66 | 0.953 | 0.068 | 0.078 | 1 | 0 |
| provyr_baseyr_fe | scope_ge_2 | new_applicant_share | 66 | 0.765 | 0.025 | 0.033 | 2 | 0 |
| provyr_baseyr_fe | scope_ge_2 | top10_share | 66 | 0.684 | 0.001 | 0.492 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_3 | base_mid_inc_share | 46 | 0.189 | 0.005 | 0.397 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_3 | base_top_share | 46 | 0.876 | -0.007 | 0.358 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_3 | hhi | 46 | 0.542 | -0.001 | 0.337 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_3 | ln1p_new_applicants | 46 | 0.613 | 0.093 | 0.105 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_3 | new_applicant_share | 46 | 0.214 | 0.003 | 0.358 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_3 | top10_share | 46 | 0.651 | -0.003 | 0.574 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_5 | base_mid_inc_share | 32 | 0.959 | 0.011 | 0.259 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_5 | base_top_share | 32 | 0.397 | -0.003 | 0.256 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_5 | hhi | 32 | 0.355 | -0.002 | 0.466 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_5 | ln1p_new_applicants | 32 | 0.495 | 0.052 | 0.164 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_5 | new_applicant_share | 32 | 0.461 | -0.008 | 0.314 | 0 | 0 |
| provyr_baseyr_fe | scope_ge_5 | top10_share | 32 | 0.207 | 0.015 | 0.177 | 0 | 0 |

## 3. 目前判断

1. 事件研究不能支撑“现在就直接投”的强因果版本。
2. 相对最能看的组合是 `scope_ge_2`：在强固定效应下，前趋势干净，`new_applicant_share` 在事件后 +1、+2 年为正且显著。
3. `scope_ge_1` 更像进入门槛太低，事件后动态弱；`scope_ge_5` 处理城市只有 32 个，样本太小；`scope_ge_3` 在强规格下进入扩容不稳。
4. HHI、Top10、基期 Top 份额的事件动态不够稳定，不能作为最硬主结论。
5. 基期中腰部份额下降在 `scope_ge_2` 下有方向，但强规格中显著性不够，适合作为结构分解线索。

## 4. 图

- `results/figures/idc_scope_event_study_binned_scope_ge_2_provyr_baseyr_fe.svg`
- `results/figures/idc_scope_event_study_binned_scope_ge_2_province_year_fe.svg`
- `results/figures/idc_scope_event_study_binned_scope_ge_3_provyr_baseyr_fe.svg`

## 5. 写作口径

可以写：

> 围绕城市 IDC 覆盖范围存量首次跨过较低但非零噪声阈值的事件研究显示，处理城市在事件前不存在明显差异趋势；在事件后 1-2 年，新进入申请人份额上升。这支持算力基础设施扩张主要通过扩大创新参与边界发挥作用。

暂时不要写：

> IDC 明确导致城市创新头部再集中。

原因是集中度变量在事件研究中轨迹不稳定，且对基期能力趋势控制敏感。
