# 事件研究与吸收能力异质性小闭环

日期：2026-05-24  
口径：发明专利申请，按 `申请年份` 归年  
工具：Stata MCP

## 1. 本轮做了什么

本轮在前一版“公开/公告年份口径”之后，改为更合理的申请年份口径，并补了三组检验：

1. 连续 IDC 强度主回归；
2. 大城市剔除、最小专利数阈值样本稳健性；
3. 事件研究 / 预趋势；
4. 基期吸收能力异质性。

主要输出：

- `data/processed/patent_applicant_concentration_application_year_2008_2023.csv`
- `data/processed/idc_applicant_concentration_application_year_panel_2008_2023.dta`
- `results/tables/idc_applicant_concentration_application_year_results_20260524.csv`
- `results/tables/idc_applicant_concentration_application_year_sample_robustness_20260524.csv`
- `results/tables/idc_applicant_concentration_application_year_event_study_20260524.csv`
- `results/tables/idc_applicant_concentration_application_year_event_thresholds_20260524.csv`
- `results/tables/idc_applicant_concentration_application_year_absorptive_heterogeneity_20260524.csv`

## 2. 连续强度主结果

样本：IDC 合并成功城市，2008-2023 年，291 个城市，4647 个城市-年份。

在 `city FE + province × year FE` 下，`ln(1 + IDC_stock_{t-1})` 的主要结果是：

| Y | 系数 | p 值 | 解释 |
|---|---:|---:|---|
| `new_applicant_share` | 0.021 | 0.002 | 新进入申请人份额上升 |
| `hhi` | 0.011 | 0.006 | 申请人集中度上升 |
| `top10_share` | 0.029 | 0.002 | 当年 Top10 份额上升 |
| `base_top_share` | 0.025 | 0.005 | 基期 Top 主体份额上升 |
| `base_mid_inc_share` | -0.019 | 0.008 | 中腰部既有主体份额下降 |

这组结果支持“进入扩容 + 头部再集中 + 中腰部挤压”的初步叙事。

但加入 `province × year FE + baseline innovation capacity × year FE` 后，集中度和杠铃分解大多不再显著，只有 `ln1p_total_patents`、`ln1p_new_applicants` 仍较稳。

这说明：当前集中度结果很可能与基期创新能力 / 基期集中度的差异趋势纠缠在一起，不能直接写成强因果。

## 3. 样本稳健性

在 `province × year FE` 下，剔除大城市后方向仍然基本成立：

- 剔除北上广深杭后，`new_applicant_share`、`hhi`、`top10_share`、`base_top_share` 为正，`base_mid_inc_share` 为负；
- 剔除北京、深圳、上海、杭州、广州、苏州、南京、武汉、成都、西安后，方向仍基本一致；
- 但在 `total_patents >= 50` 的样本中，`hhi` 和 `base_top_share` 明显变弱。

判断：不是完全由几个超级城市驱动，但集中度在高专利量城市样本中不够稳。

## 4. 事件研究 / 预趋势

### 4.1 首次 `IDC_stock > 0`

事件定义：首次 `idc_stock > 0`，仅保留首次事件在 2012-2020 年的城市，并保留从未出现 IDC 的城市作对照。

结果不理想：

- 处理后 1-3 年没有清楚的正向集中轨迹；
- `ln1p_new_applicants` 在 `province × year FE` 下处理后反而偏负；
- 对 `ln1p_new_applicants`，处理前联合检验偏危险：
  - `province × year FE`：pre joint p = 0.059；
  - 加基期能力组 × 年份 FE：pre joint p = 0.035。

这说明“首次有许可证”不是一个干净事件，不能作为主识别。

### 4.2 阈值事件

又试了首次达到：

- `idc_stock >= 3`
- `idc_stock >= 5`
- `idc_stock >= 10`

结果：

- 阈值提高后，前导项整体比 `stock > 0` 干净；
- `stock >= 5` 在 `province × year FE` 下对 `base_top_share` 有较强正向结果，且 `top10_share` 有边际正向；
- 但加基期能力组 × 年份 FE 后，这些结果明显变弱。

判断：强度型 IDC 存量比“首次出现”更像有效 X，但仍不够支撑正式事件研究。

## 5. 吸收能力异质性

异质性变量：

- `high_base_patents`：基期专利能力较高；
- `high_base_top10`：基期 Top10 份额较高；
- `high_base_hhi`：基期 HHI 较高。

### 5.1 高基期专利能力

在 `province × year FE` 下：

- 高基期专利城市：`new_applicant_share`、`hhi`、`top10_share`、`base_top_share` 为正，`base_mid_inc_share` 为负；
- 这看起来支持“高吸收能力城市更容易出现杠铃化”。

但加入 `high_base_patents × year FE` 后：

- 高能力组的集中效应消失；
- 低能力组反而在 `hhi/top10/base_top` 上更明显。

### 5.2 高基期集中度

在 `province × year FE` 下：

- 低基期 Top10 / 低基期 HHI 城市反而更容易出现 `top10_share` 和 `base_top_share` 上升；
- 高基期集中城市更多体现为新进入或新进入份额。

加入组别 × 年份 FE 后，结果整体更弱，只剩部分集中度变量边际显著。

判断：吸收能力机制还没有被干净识别。现在不能写成“高能力城市必然头部再集中、低能力城市创新进入扩容”。

## 6. 当前 verdict

当前状态：**黄灯偏绿，但不能直接写论文。**

可以保留的结论：

```text
申请年份口径下，连续 IDC 存量与新进入申请人增加、申请人集中度上升、基期头部份额上升和中腰部份额下降相关。
```

必须降调的结论：

```text
事件研究没有支持一个干净的“首次 IDC 出现”冲击；
吸收能力异质性不够稳定；
因此当前不能把结果写成强因果或顶刊级识别。
```

## 7. 下一步优先级

第一优先级：补强 X。

- 机房地址；
- 机柜数 / MW；
- 智算中心；
- 国家算力枢纽 / 数据中心集群；
- 至少证明 IDC stock 与真实本地算力供给正相关。

第二优先级：导出并识别 Top 申请人。

- 当年 Top20；
- 基期 Top20；
- 处理后新晋 Top20；
- 类型：企业、高校、科研院所、个人、A 股集团/子公司。

第三优先级：重做事件研究。

不要再用“首次 `stock > 0`”作为主事件。优先使用：

- 首次达到较高 IDC 存量阈值；
- 首次大幅增长；
- 智算中心/东数西算/国家算力节点；
- 真实机房容量上线。

第四优先级：若 Top 身份可解释，再做高价值 / 数字技术专利。

当前不建议马上做：

- 全量集团合并；
- A 股集团全量匹配；
- 合作创新网络；
- IV。

这些只有在 X 和预趋势更清楚后才值得投入。

## 8. Top 申请人初步导出

已先导出一版 Top 申请人名单，供人工检查集中度来源：

- `data/processed/top_applicants/city_year_top20_applicants_inv_app_appyear_2008_2023.csv`
- `data/processed/top_applicants/baseline_2008_2010_top20_applicants_inv_app_appyear.csv`
- `data/processed/top_applicants/city_year_top20_type_summary_inv_app_appyear_2008_2023.csv`

这只是名称规则粗分，不是正式集团合并或主体类型识别。

2008-2023 年城市-年份 Top20 申请人中的专利量粗分类占比大致为：

- 企业：约 50.0%；
- 高校：约 40.4%；
- 科研机构：约 4.7%；
- 个人：约 3.5%；
- 医院及其他：约 1.3%。

初步直觉：

```text
Top 集中并不只是企业平台，也大量来自高校和科研机构。
所以后续不能只写“上市公司/企业吸收能力”，必须区分企业型头部和高校科研型头部。
```
