# 全量专利申请人集中度第一轮结果

日期：2026-05-24

## 1. 数据确认

主人截图中的 `分年份保存数据.rar` 确认为可用的中国全量专利数据库。

本机路径：

`/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/上市公司其他/分年份保存数据.rar`

压缩包内为 1985-2025 年逐年 CSV。2024 年文件包含约 656 万行记录。可用字段包括：

- 专利类型；
- 申请人；
- 申请人类型；
- 申请人城市；
- 申请号；
- 公开公告年份；
- 授权公告年份。

当前第一轮使用“公开公告年份所属文件”作为年份。后续若改用申请年份，需要单独处理公开滞后和右截尾。

## 2. 本轮构造

脚本：

`scripts/build_patent_applicant_concentration_from_rar.py`

构造逻辑：

1. 不整包解压，直接从 RAR 中逐年流式读取 CSV。
2. 提取第一申请人和第一申请人城市。
3. 城市名统一去掉末尾“市”，过滤 `CN`、未知等异常值。
4. 以 2000-2007 年作为既有申请人预热期。
5. 输出 2008-2024 年城市-年份-口径面板。

专利口径：

- `all_pub`：全部公开公告记录；
- `inv_app_pub`：发明申请公开；
- `inv_grant_pub`：发明授权公开。

主 Y：

- `hhi`：城市申请人专利份额 HHI；
- `top1_share`、`top5_share`、`top10_share`；
- `effective_applicants = 1 / HHI`；
- `active_applicants`；
- `new_applicants`；
- `new_applicant_share`；
- `total_patents`。

输出文件：

- `data/processed/patent_applicant_concentration_city_year_2008_2024.csv`
- `data/processed/patent_applicant_concentration_city_year_2008_2024.dta`
- `results/reports/patent_applicant_concentration_build_report_2008_2024.csv`

面板规模：

- 18,329 行；
- 444 个城市/地区；
- 2008-2024 年；
- 三个专利口径。

## 3. IDC 合并

脚本：

`scripts/build_idc_applicant_concentration_panel.py`

合并数据：

- `data/processed/idc_proxy_city_year_2000_2024.csv`
- `data/processed/patent_applicant_concentration_city_year_2008_2024.csv`

合并口径：

- 第一轮按规范化城市名合并；
- 现有 IDC 文件中的城市代码不可直接信任，本轮未用城市代码；
- 主回归只保留能匹配到 IDC 城市年面板的城市-年份记录。

合并后：

- 18,329 行；
- 14,790 行能匹配 IDC 城市年面板；
- 209 个城市曾经有 IDC 存量。

输出文件：

- `data/processed/idc_applicant_concentration_panel_2008_2024.csv`
- `data/processed/idc_applicant_concentration_panel_2008_2024.dta`

## 4. 回归设定

脚本：

`scripts/run_idc_applicant_concentration_stata.do`

第一轮设定：

```stata
areg Y ln1p_idc_stock_l1 i.year if scope == ... & merge_idc == "both", absorb(city_id) vce(cluster city)
```

固定效应：

- 城市固定效应；
- 年份固定效应。

标准误：

- 按城市聚类。

样本：

- `matched_2008_2024`；
- `matched_2012_2022`。

结果表：

- `results/tables/idc_applicant_concentration_results_20260524.csv`
- `results/tables/idc_applicant_concentration_results_20260524.dta`
- `results/logs/run_idc_applicant_concentration_stata_20260524.log`

## 5. 核心结果

### 发明申请公开口径

`matched_2008_2024`，核心 X 为 `ln1p_idc_stock_l1`：

| Y | 系数 | p 值 | 方向 |
|---|---:|---:|---|
| `ln1p_total_patents` | 0.056 | 0.095 | 总量弱正 |
| `hhi` | 0.012 | 0.004 | 集中度上升 |
| `top5_share` | 0.017 | 0.021 | Top5 份额上升 |
| `top10_share` | 0.029 | 0.000 | Top10 份额上升 |
| `ln1p_active_applicants` | 0.048 | 0.092 | 活跃申请人弱正 |
| `ln1p_new_applicants` | 0.039 | 0.162 | 不显著 |
| `new_applicant_share` | 0.026 | 0.000 | 新进入申请人份额上升 |

`matched_2012_2022` 中方向基本一致，`hhi`、`top10_share`、`new_applicant_share` 仍为正。

### 发明授权公开口径

`matched_2008_2024`，核心 X 为 `ln1p_idc_stock_l1`：

| Y | 系数 | p 值 | 方向 |
|---|---:|---:|---|
| `ln1p_total_patents` | 0.113 | 0.004 | 总量上升 |
| `hhi` | 0.027 | 0.000 | 集中度上升 |
| `top1_share` | 0.016 | 0.049 | Top1 份额上升 |
| `top5_share` | 0.039 | 0.000 | Top5 份额上升 |
| `top10_share` | 0.036 | 0.001 | Top10 份额上升 |
| `ln1p_active_applicants` | 0.093 | 0.009 | 活跃申请人上升 |
| `ln1p_new_applicants` | 0.103 | 0.004 | 新进入申请人上升 |
| `new_applicant_share` | 0.037 | 0.000 | 新进入申请人份额上升 |

## 6. 解释

当前结果不是简单的“创新扩散”，也不是简单的“只有头部拿走红利”。

更准确的读法是：

> IDC/算力基础设施提高了城市创新活跃度，也吸引或释放了更多新申请人，但新增创新并没有平均分散到长尾主体；头部申请人的相对份额同时上升。

这支持一个更有张力的题目：

> 城市算力基础设施建设与创新生态重构：进入扩容还是创新再集中？

可能机制：

1. 算力基础设施降低一部分创新主体进入门槛，所以 `new_applicants` 和 `new_applicant_share` 上升。
2. 但头部企业、高校、平台型机构和强研发组织具有更高吸收能力，所以 HHI、Top5、Top10 同时上升。
3. 结果可能是“主体数量扩散，创新产出集中”。

## 7. 当前判断

Go，但不走旧题。

不能写：

> 城市算力基础设施削弱上市公司创新优势。

更应该写：

> 城市算力基础设施是否同时促进创新进入与创新集中？

或者：

> 城市算力基础设施与创新生态的双重重构：新主体进入和头部集中并存。

## 8. 下一步

优先补三件事：

1. 申请人类型分解：
   - 企业；
   - 大专院校；
   - 科研单位；
   - 机关团体；
   - 个人。
2. Top 申请人身份识别：
   - Top5/Top10 中企业、高校、科研院所分别占比；
   - A 股上市公司及其集团是否进入 Top5/Top10。
3. 更严格识别：
   - 城市线性趋势；
   - 省份 × 年份固定效应；
   - 剔除北上广深、省会、直辖市；
   - `ln1p_idc_new`、`ln1p_idc_stock` 多滞后；
   - 事件研究或预趋势检查。

如果加入严格趋势后 HHI/Top share 仍为正，同时 new applicants 仍为正，这个题比原来的“上市公司份额下降”更值得继续。
