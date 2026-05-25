# IDC/算力基础设施 × 数字创新/AI创新：Stata MCP 试跑备忘

## 1. 本次口径

X 仍使用 IDC 代理变量：

- `idc_new`：城市当年新增 IDC 许可数；
- `idc_stock`：城市累计 IDC 许可数；
- 均取 `ln(1+x)`；
- 滞后项按“省份-城市”重算，避免使用脏城市代码。

Y 分三组：

- A：企业数字创新  
  `ln1p_digital_invpat` = `ln(1 + 供应商年度数字发明专利授权数)`，2011-2024。
- B1：标题宽口径数字/AI 专利  
  `ln1p_ai_title_patent` = `ln(1 + 专利标题数字/AI关键词授权数)`，这个口径较粗。
- B2：严格 AI / 算力发明专利  
  从 CSMAR 专利明细原始表重构，按“公司-申请号”去重，只保留授权日期。  
  - 严格 AI 发明专利总量：161 件；
  - AI/算力相关发明专利总量：688 件；
  - 因为很稀疏，更适合做拓展结果或机制，不适合一开始就硬做主 Y。

回归设定：企业固定效应 + 年份固定效应，标准误按城市聚类；样本排除 ST 和金融业。当前未加财务控制变量，是第一轮方向性试跑。

## 2. A：企业数字创新

主结果更像是“新增 IDC 许可”有效，而不是“累计 IDC 存量”有效。

| Y | X | 样本 | 系数 | p 值 | 判断 |
|---|---|---:|---:|---:|---|
| `ln1p_digital_invpat` | `ln1p_idc_new` | 2012-2022 | 0.0061 | 0.025 | 正向显著 |
| `ln1p_digital_invpat` | `ln1p_idc_new` | 2011-2024 | 0.0068 | 0.032 | 正向显著 |
| `ln1p_digital_invpat` | `ln1p_idc_stock` | 2012-2022 | 0.0050 | 0.098 | 弱显著 |
| `ln1p_digital_invpat` | `ln1p_idc_stock` | 2011-2024 | 0.0002 | 0.947 | 消失 |

扩展边际也支持新增 IDC：

| Y | X | 样本 | 系数 | p 值 |
|---|---|---:|---:|---:|
| `has_digital_invpat` | `ln1p_idc_new` | 2012-2022 | 0.0048 | 0.011 |
| `has_digital_invpat` | `ln1p_idc_new` | 2011-2024 | 0.0058 | 0.002 |
| `has_digital_invpat` | `ln1p_idc_new_l1` | 2012-2022 | 0.0039 | 0.017 |
| `has_digital_invpat` | `ln1p_idc_new_l1` | 2011-2024 | 0.0035 | 0.042 |

## 3. B：AI / 算力创新

宽口径标题数字/AI 专利没有跑出来：

| Y | X | 样本 | 系数 | p 值 |
|---|---|---:|---:|---:|
| `ln1p_ai_title_patent` | `ln1p_idc_stock` | 2012-2022 | 0.0003 | 0.765 |
| `ln1p_ai_title_patent` | `ln1p_idc_new` | 2012-2022 | -0.0003 | 0.803 |
| `ln1p_ai_title_patent` | `ln1p_idc_stock` | 2011-2024 | -0.0002 | 0.845 |
| `ln1p_ai_title_patent` | `ln1p_idc_new` | 2011-2024 | -0.0013 | 0.260 |

严格 AI 发明专利有一点累计存量信号，但太稀疏：

| Y | X | 样本 | 系数 | p 值 |
|---|---|---:|---:|---:|
| `ln1p_strict_ai_inv` | `ln1p_idc_stock` | 2011-2024 | 0.0008 | 0.017 |
| `ln1p_strict_ai_inv` | `ln1p_idc_stock_l1` | 2011-2024 | 0.0008 | 0.023 |
| `ln1p_strict_ai_inv` | `ln1p_idc_stock` | 2012-2022 | 0.0003 | 0.218 |
| `ln1p_strict_ai_inv` | `ln1p_idc_new` | 2012-2022 | 0.0002 | 0.396 |

AI/算力相关发明专利的累计存量信号更清楚：

| Y | X | 样本 | 系数 | p 值 |
|---|---|---:|---:|---:|
| `ln1p_ai_compute_inv` | `ln1p_idc_stock` | 2011-2024 | 0.0016 | 0.023 |
| `ln1p_ai_compute_inv` | `ln1p_idc_stock_l1` | 2012-2022 | 0.0014 | 0.011 |
| `ln1p_ai_compute_inv` | `ln1p_idc_stock_l1` | 2011-2024 | 0.0020 | 0.008 |
| `ln1p_ai_compute_inv` | `ln1p_idc_new` | 2011-2024 | -0.0005 | 0.490 |

## 4. 判断

这次结果比“创新韧性”好很多。

更稳的主线不是“算力基础设施提升企业创新韧性”，而是：

> 城市算力基础设施建设促进企业数字技术创新。

其中，主 Y 建议用供应商年度数字发明专利授权数；AI/算力发明专利可以作为更贴近机制的拓展结果，但不适合直接做唯一主 Y。因为严格 AI 专利总量太少，容易被质疑为低基数、关键词噪声和偶然显著。

目前最值得继续的是：

- 主模型：`ln1p_digital_invpat` 对 `ln1p_idc_new`；
- 补充：是否产生数字发明专利 `has_digital_invpat`；
- 拓展：AI/算力相关发明专利对 `idc_stock` 或 `idc_stock_l1`；
- 不建议继续用一般创新韧性作为主 Y。

## 5. 输出

- Stata do 文件：`/Users/mac/computerscience/23选题探索/T10/scripts/run_idc_digital_ai_innovation_stata.do`
- 严格 AI/算力专利构造脚本：`/Users/mac/computerscience/23选题探索/T10/scripts/build_strict_ai_compute_patent_titles.py`
- 回归结果：`/Users/mac/computerscience/23选题探索/T10/outputs/idc_proxy_digital_ai_innovation_results_20260523.csv`
- 回归面板：`/Users/mac/computerscience/23选题探索/T10/outputs/idc_proxy_digital_ai_innovation_panel_2000_2024.csv`
- 严格 AI/算力专利年度表：`/Users/mac/computerscience/23选题探索/T10/outputs/strict_ai_compute_patent_title_annual.csv`

