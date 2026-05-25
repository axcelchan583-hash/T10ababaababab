# IDC 覆盖范围口径正式主表小闭环

日期：2026-05-25  
主 X：`ln(1 + IDC_scope_city_stock_{c,t-1})`  
口径：发明专利申请，按申请年份归年  
样本：2008-2023 年，291 个 IDC 可合并城市，4647 个城市-年份  
工具：Stata MCP

## 1. 本轮新增文件

数据：

- `data/processed/idc_scope_formal_application_year_panel_2008_2023.csv`
- `data/processed/idc_scope_formal_application_year_panel_2008_2023.dta`

脚本：

- `scripts/build_idc_scope_formal_application_year_panel.py`
- `scripts/run_idc_scope_formal_main_stata.do`
- `scripts/run_idc_scope_sample_robustness_stata.do`
- `scripts/run_idc_scope_event_study_stata.do`

结果：

- `results/tables/idc_scope_formal_results_20260525.csv`
- `results/tables/idc_scope_sample_robustness_20260525.csv`
- `results/tables/idc_scope_event_study_20260525.csv`

## 2. 主表结果

主 X 为 `ln1p_idc_scope_stock_l1`。核心结果如下：

| Y | 城市+年份 FE | 省份×年份 FE | 省份×年份 + 基期能力×年份 FE | 城市趋势 |
|---|---:|---:|---:|---:|
| `ln1p_total_patents` | -0.006 | -0.021 | 0.085* | 0.013 |
| `ln1p_new_applicants` | -0.006 | 0.025 | 0.118*** | 0.105* |
| `new_applicant_share` | 0.023*** | 0.043*** | 0.023** | 0.032** |
| `hhi` | 0.016*** | 0.011* | 0.001 | -0.001 |
| `top10_share` | 0.038*** | 0.031** | -0.011 | -0.025* |
| `base_top_share` | 0.036*** | 0.026** | -0.015 | -0.020* |
| `base_mid_inc_share` | -0.021*** | -0.033*** | -0.006 | -0.015 |

判断：

```text
最稳的是新进入申请人份额上升。
集中度和基期 Top 份额在省份×年份 FE 下成立，
但被基期能力/集中度差异趋势吸收。
中腰部既有主体份额下降在省份×年份 FE 下很清楚，但强规格下不稳。
```

## 3. X 稳健性

### 3.1 当年新增 IDC

`ln1p_idc_scope_new_l1` 不支持主结果。  
在省份×年份 FE 下，甚至对总专利为负。

判断：

```text
新增许可证冲击不是好 X，可能噪声大，或新增许可不等于当年实际可用算力。
```

### 3.2 最近 5 年 IDC stock

`ln1p_idc_scope_pre5_l1`：

- 在省份×年份 FE 下，`new_applicant_share` 为正且显著；
- 加基期能力×年份 FE 后，`ln1p_new_applicants` 和 `new_applicant_share` 仍显著为正；
- 但 `top10_share`、`base_top_share` 转为负或边际负。

判断：

```text
最近 5 年口径更支持“进入扩容”，不支持“头部再集中”。
```

### 3.3 注册地址 / combined 口径

在省份×年份 FE 下：

- `IDC_registered_stock` 和 `IDC_combined_stock` 都支持 `new_applicant_share` 上升、`hhi/top10/base_top` 上升、`base_mid_inc_share` 下降；
- 但加基期能力×年份 FE 后，主要只剩总量和新进入数量，集中度消失。

判断：

```text
注册地和 combined 口径可作为稳健性，但不能当主 X。
```

### 3.4 省份口径

省份 IDC stock 不能放入省份×年份 FE，会被吸收。  
在城市+年份 FE 或城市趋势下：

- `hhi`、`base_top_share` 较稳为正；
- `base_mid_inc_share` 多数为负；
- `new_applicant_share` 不稳。

判断：

```text
省份口径更像“区域头部集中”信号，不适合作为进入扩容的主证据。
```

## 4. 样本稳健性

在省份×年份 FE 下：

- 剔除北上广深杭后，`new_applicant_share`、`hhi`、`top10_share`、`base_top_share` 仍为正，`base_mid_inc_share` 仍为负；
- 剔除前十创新城市后，方向仍基本成立；
- 限制 `total_patents >= 20/50` 后，`new_applicant_share` 仍显著为正，`base_mid_inc_share` 仍为负，但 `hhi/top10/base_top` 明显变弱。

在省份×年份 + 基期能力×年份 FE 下：

- `ln1p_new_applicants` 稳健为正；
- `new_applicant_share` 在 all、min20、min50 中仍为正，剔除大城市后变弱；
- 集中度指标基本不显著。

判断：

```text
结果不是北上广深杭或前十创新城市单独驱动。
但“头部再集中”主要来自中小专利量城市或基期差异趋势；
在高专利量城市和强 FE 下不稳。
```

## 5. 事件研究

事件定义：首次达到 `idc_scope_stock >= 1/2/3/5`，保留首次事件在 2012-2020 年的城市和从未处理城市。

### 5.1 前趋势

在 `provyr_baseyr_fe` 下，前导项整体比旧混合口径更干净：

- `scope >= 1/2/3/5` 的大多数 Y 联合前趋势不显著；
- `scope >= 5` 样本只有 32 个处理城市，信息量有限。

在 `province_year_fe` 下：

- `scope >= 2/3` 的 `base_top_share` / `base_mid_inc_share` 有一定前趋势风险；
- 加基期能力×年份 FE 后明显缓和。

### 5.2 处理后

处理后 1-3 年平均：

- `scope >= 2/3` 对 `new_applicant_share` 为正，且在多个事件后年份显著；
- `base_mid_inc_share` 在 `scope >= 2/3` 下多为负；
- `base_top_share` 在 `province_year_fe` 下为正，但在强 FE 下不稳；
- `hhi/top10_share` 的动态轨迹不够清楚。

判断：

```text
事件研究支持“进入扩容”多于支持“头部再集中”。
集中度/头部化更适合作为相关性和结构分解发现，而不是强事件因果发现。
```

## 6. 当前 verdict

当前结果比昨天更稳，但叙事要收窄。

可以作为主发现写的：

```text
城市 IDC 覆盖范围存量提升后，城市创新生态的进入边界扩大：
新进入申请人份额稳健上升。
```

可以作为第二层发现写的：

```text
在较常规的省份×年份固定效应下，IDC 同时伴随当年 Top10/HHI 和基期 Top 份额上升、
中腰部既有主体份额下降，呈现“杠铃化”迹象。
```

必须降调的：

```text
“头部再集中”对基期能力差异趋势、样本专利量阈值和事件研究口径较敏感，
暂时不能作为最硬的因果主结论。
```

## 7. 下一步

## 7. Top20 粗分类探索

已构造：

- `data/processed/top20_type_share_panel_2008_2023.csv`
- `results/tables/top20_type_share_idc_scope_results_20260525.csv`

粗分类类型包括：

- 企业；
- 高校；
- 科研机构；
- 医院；
- 个人；
- 政府；
- 其他/不明。

结果比较意外：

在省份×年份 FE 下：

- `top20_firm_share_total` 不显著；
- `top20_univ_share_total` 显著为负；
- `top20_individual_share_total` 显著为正；
- Top20 内部份额中，企业份额下降，个人份额上升。

但在加入基期能力/集中度 × 年份 FE 后，这些类型份额基本不显著。

判断：

```text
当前不能写成“IDC 强化企业/上市公司头部吸收能力”。
Top20 粗分类结果更像提示：头部结构可能受到小城市、低专利量城市和个人申请人噪声影响。
后续必须先清洗 Top 申请人身份，并在高专利量城市、发明授权、高价值专利中重做类型分解。
```

这也解释了为什么 HHI/Top10 在强规格下不稳：集中度可能并不完全来自大型企业或高校科研头部，而是包含大量小城市中少数个人/小主体的机械集中。

## 8. 下一步

最优先：

1. **Top 申请人身份识别**  
   看进入扩容和头部集中分别来自企业、高校、科研院所还是个人。

2. **重新设计主标题和摘要**  
   不要把“再集中”写死在标题里。更稳的标题应突出“创新进入与主体结构重塑”。

3. **补机制分解**
   - 新进入者份额；
   - 基期 Top 份额；
   - 中腰部既有主体份额；
   - Top 主体类型分解。

4. **暂缓 IV**
   现在先不做光缆骨干网距离 IV。等 Top 身份和事件研究图能讲清楚后再考虑。
