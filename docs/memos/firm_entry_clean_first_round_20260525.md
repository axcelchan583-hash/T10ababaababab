# 企业新进入口径第一轮结果

日期：2026-05-25  
主 X：`ln(1 + IDC_scope_city_stock_{c,t-1})`  
口径：发明专利申请，申请年份归年，2008-2023 年  

## 1. 本轮问题

由于全体申请人口径的新进入可能混入个人申请人和低质量申请，本轮把 Y 收窄到企业申请人：

```text
城市 IDC 服务覆盖是否促进企业创新进入？
```

重点检验网页版 GPT 提醒的 numerator / denominator 分解：

1. 新进入企业专利份额；
2. 新进入企业专利数量；
3. 新进入企业数量；
4. 既有企业专利数量；
5. 企业总专利数量。

## 2. 新增文件

脚本：

- `scripts/build_firm_entry_clean_panel.py`
- `scripts/run_firm_entry_clean_idc_scope_stata.do`
- `scripts/run_firm_entry_clean_event_study_stata.do`

数据：

- `data/processed/firm_entry_clean_panel_2008_2023.csv`
- `data/processed/firm_entry_clean_panel_2008_2023.dta`

结果：

- `results/tables/firm_entry_clean_idc_scope_results_20260525.csv`
- `results/tables/firm_entry_clean_event_study_20260525.csv`

## 3. 企业定义

沿用清洗版申请人类型规则：

```text
firm = 公司、集团、厂、合作社、银行、保险、证券、商行、事务所、农场、牧场、矿等市场主体
```

新进入企业定义：

```text
某企业申请人首次出现在该城市专利申请人历史中的年份。
```

预热期从 2000 年开始，主样本为 2008-2023 年。

## 4. 变量

主变量：

- `firm_new_share_total`：新进入企业专利 / 城市总专利；
- `firm_new_share_firm`：新进入企业专利 / 城市企业专利；
- `ln1p_new_firm_patents`：新进入企业专利数；
- `ln1p_new_firm_applicants`：新进入企业申请人数；
- `ln1p_firm_incumbent_patents`：既有企业专利数；
- `ln1p_firm_total_patents`：企业总专利数；
- `firm_patent_share_total`：企业专利 / 城市总专利。

## 5. 主回归结果

样本为 291 个城市、4,647 个城市-年份。

### 5.1 新进入企业专利占城市总专利份额

`firm_new_share_total` 在所有主要规格下不显著：

- 城市+年份 FE：不显著；
- 省份×年份 FE：不显著；
- 省份×年份 + 基期能力/集中度×年份 FE：不显著；
- 城市趋势：不显著。

判断：

```text
IDC 没有稳健提高“新进入企业专利占城市总专利的份额”。
```

### 5.2 新进入企业专利占企业专利份额

`firm_new_share_firm` 在城市+年份 FE、省份×年份 FE 和城市趋势下为正，但在强固定效应下消失。

这说明：

```text
企业内部的新进入份额有表面正相关，
但它不能通过基期能力/集中度差异趋势控制。
```

### 5.3 numerator / denominator 分解

核心 numerator：

- `ln1p_new_firm_patents`：不显著；
- `ln1p_new_firm_applicants`：全样本不显著，高专利量城市中边际为正；
- `ln1p_firm_incumbent_patents`：在常规 FE 下为负，强固定效应下不显著；
- `ln1p_firm_total_patents`：整体不稳。

因此，不能说：

```text
IDC 稳健提高了新进入企业数量或新进入企业专利数。
```

更可能是：

```text
企业内部的新进入份额上升主要来自企业内部结构变化，
但 numerator 不够强，denominator 也不稳定。
```

## 6. 企业口径事件研究

事件定义沿用：

```text
IDC_scope_stock 首次达到 >= 1/2/3/5
```

尾部合并窗口：

```text
<= -4, -3, -2, -1, 0, +1, +2, +3, >= +4
```

核心判断：

- `scope >= 2` 下，企业新进入相关 Y 没有清晰事件后上升；
- `firm_new_share_total` 在 `scope >= 2` 下不显著；
- `ln1p_new_firm_patents` 和 `ln1p_new_firm_applicants` 在 `scope >= 2` 下不显著；
- `scope >= 5` 下有一些企业进入正向信号，但处理城市只有 32 个，且不是最适合的主事件阈值。

判断：

```text
企业口径事件研究不能支持“IDC 扩张显著促进企业创新进入”。
```

## 7. 当前 verdict

企业 Y 可以作为补充，但不适合替代全体申请人口径作为主线。

原因：

1. `firm_new_share_total` 不显著；
2. `ln1p_new_firm_patents` 不显著；
3. `ln1p_new_firm_applicants` 只在高专利量城市中边际为正；
4. 企业口径事件研究没有复现全体申请人口径的清晰动态；
5. `firm_new_share_firm` 的正结果在强固定效应下消失。

当前更稳的写法仍是：

```text
城市 IDC 服务覆盖扩大整体创新进入边界。
```

企业口径应作为限制性检验：

```text
这一进入扩展不主要由企业新进入驱动；
后续需要进一步区分个人、企业、高校/科研和高价值专利进入。
```

## 8. 下一步

不要继续只在城市-年份企业 Y 上硬救。更值得推进的是：

1. **新进入类型分解**
   - 企业；
   - 高校/科研；
   - 个人；
   - 组织申请人。

2. **高价值专利口径**
   - 发明授权；
   - 授权后维持；
   - 被引；
   - 高价值发明。

3. **城市-技术领域-年份 DDD**
   - 只看企业申请人；
   - 构造高算力依赖技术领域；
   - 使用 `IDC_ct × HighComputeTech_k`；
   - 吸收城市×年份、技术领域×年份、城市×技术领域固定效应。

如果企业进入在高算力依赖技术领域显著增强，企业 Y 才有机会成为主线。
