# 政策 horse-race 与授权/高价值口径补充结果

日期：2026-05-26  
项目：T10 城市 IDC 服务覆盖与创新进入边界

## 1. 本轮补了什么

本轮补两个审稿风险点：

1. 政策 horse-race：检查是否可以直接控制宽带中国、智慧城市、大数据综合试验区、创新型城市、高新区、知识产权示范城市等政策。
2. 授权/高价值口径：用申请年份重新构造发明授权、授权且被引、授权且家族被引等质量口径，避免只依赖公开年份。

新增文件：

- `scripts/build_appyear_quality_panel.py`
- `scripts/build_idc_scope_appyear_quality_panel.py`
- `scripts/run_appyear_quality_robustness_stata.do`
- `scripts/build_policy_horserace_panel.py`
- `scripts/run_policy_horserace_stata.do`
- `data/processed/patent_applicant_quality_application_year_2008_2023.csv`
- `data/processed/idc_scope_appyear_quality_panel_2008_2023.csv`
- `results/tables/appyear_quality_robustness_results_20260526.csv`
- `results/tables/appyear_quality_key_summary_20260526.csv`
- `data/external_proxy/city_policy_horserace_template_2008_2023.csv`

## 2. 授权/高价值口径构造

原始数据来自“中国全量专利数据库 1985-2025.11”的分年份 RAR。使用字段包括：

- `专利类型`
- `申请人`
- `申请人城市`
- `申请号`
- `申请年份`
- `授权公告年份`
- `被引证次数`
- `家族被引证次数`

构造四个 scope：

| scope | 含义 |
|---|---|
| `inv_grant_appyear` | 发明授权，按申请年份归年 |
| `inv_grant_grantyear` | 发明授权，按授权公告年份归年 |
| `inv_grant_cited_appyear` | 发明授权且被引证次数 > 0，按申请年份归年 |
| `inv_grant_familycited_appyear` | 发明授权且家族被引证次数 > 0，按申请年份归年 |

输出面板：

```text
2008-2023 年
4 个授权/高价值 scope
22,509 个 scope-城市-年份观测
441 个城市
```

回归样本与主规格：

```text
Y_ct = beta * ln(1 + IDC_scope_stock_{c,t-1})
     + city FE
     + province × year FE
     + baseline patent scale × year FE
     + baseline top10 share × year FE
     + error_ct
```

标准误按城市聚类。

## 3. 授权/高价值结果

### 3.1 发明授权按申请年份

在最强规格 `provyr_baseyr_fe` 下：

| 截尾 | `new_applicant_share` | `ln1p_new_applicants` | `ln1p_new_patents` | `ln1p_total_patents` |
|---|---:|---:|---:|---:|
| ≤2020 | 0.0099 | 0.0534 | 0.0761 | 0.0652 |
| ≤2021 | 0.0107 | 0.0694* | 0.0929** | 0.0791 |
| ≤2022 | 0.0100 | 0.0768* | 0.0997** | 0.0919* |
| ≤2023 | 0.0123 | 0.0997** | 0.1245** | 0.1073** |

解释：

```text
授权申请年口径下，份额变量方向为正但不显著；
分子变量更强：新进入申请人数量和新进入申请人授权专利数显著上升。
```

这支持“进入扩容”不是纯低质量申请驱动，但还不能写成“新进入高质量专利份额稳健上升”。

### 3.2 发明授权按授权公告年份

在最强规格下，`new_applicant_share` 系数约为 0.018-0.019，但不显著；`ln1p_new_patents` 在 ≤2023 截尾下边际显著。

该口径不适合作为主口径，因为授权公告年份存在严重滞后和右截尾。2024、2025 年原始文件中的授权公告年份可用性已经明显塌缩。

### 3.3 授权且被引

`inv_grant_cited_appyear` 方向较弱：

- `new_applicant_share` 不显著；
- `ln1p_new_applicants` 和 `ln1p_new_patents` 在 ≤2023 截尾下边际显著；
- 被引数据明显存在引用窗口截尾，不适合作为当前主结果。

### 3.4 授权且家族被引

`inv_grant_familycited_appyear` 的分子变量较强：

| 截尾 | `new_applicant_share` | `ln1p_new_applicants` | `ln1p_new_patents` | `ln1p_total_patents` |
|---|---:|---:|---:|---:|
| ≤2020 | 0.0145 | 0.0681* | 0.0920** | 0.0815 |
| ≤2021 | 0.0153 | 0.0900** | 0.1146** | 0.0997* |
| ≤2022 | 0.0133 | 0.1022** | 0.1256*** | 0.1167** |
| ≤2023 | 0.0145 | 0.1162*** | 0.1407*** | 0.1274** |

解释：

```text
家族被引授权口径支持“高质量相关的新进入数量扩张”，
但份额变量仍未显著。
```

## 4. 当前质量口径结论

可以写：

```text
在发明授权、授权且家族被引等质量口径下，
IDC 服务覆盖提升后，新进入申请人数量和新进入申请人授权专利数仍呈正向响应。
```

谨慎写：

```text
质量口径下的份额变量方向为正，但在强固定效应下未达到常规显著性。
```

不能写：

```text
IDC 服务覆盖稳健提高新进入者的高价值专利份额。
```

质量口径更适合作为“不是低质量申请堆出来”的补充证据，而不是替代主结果。

## 5. 政策 horse-race 当前状态

本地没有发现可直接合并的城市-年份政策面板。现有国泰安/数据要素类文件包括：

- `分地区大数据发展指数表(2016-2020)`：城市/地区大数据发展指数，时间短，更像数字基础控制，不是政策 dummy；
- `全国数据资源调查统计表`：全国年度变量，不能做城市政策 horse-race；
- 未发现已清洗的宽带中国、智慧城市、大数据综合试验区、创新型城市、高新区、知识产权示范城市等城市-年份政策面板。

因此本轮没有运行政策 horse-race。原因不是模型不能跑，而是缺少可信政策变量。强行把空模板当政策控制会制造假结果。

## 6. 已落地的政策 horse-race 接口

已生成政策模板：

```text
data/external_proxy/city_policy_horserace_template_2008_2023.csv
```

规模：

```text
443 个城市
2008-2023 年
6,149 个城市-年份
```

待补变量：

| 变量 | 建议含义 |
|---|---|
| `broadband_china_pilot` | 宽带中国试点城市及后续年份 |
| `smart_city_pilot` | 国家智慧城市试点及后续年份 |
| `bigdata_comprehensive_pilot` | 国家大数据综合试验区覆盖城市/区域及后续年份 |
| `innovative_city_pilot` | 创新型城市试点及后续年份 |
| `national_hightech_zone` | 国家高新区城市，最好用数量，也可先用 dummy |
| `ip_demo_city` | 知识产权示范/强市相关政策 |
| `information_consumption_pilot` | 信息消费试点城市 |
| `ecommerce_demo_city` | 电子商务示范城市 |

补齐后将模板另存为：

```text
data/external_proxy/city_policy_horserace_panel_2008_2023.csv
```

再运行：

```text
scripts/build_policy_horserace_panel.py
scripts/run_policy_horserace_stata.do
```

即可输出：

```text
results/tables/policy_horserace_results_20260526.csv
```

## 7. 对当前论文的影响

本轮后，当前判断更新为：

```text
主线仍可继续：IDC 服务覆盖扩大创新进入边界。
质量口径提供有限支持：新进入授权/家族被引授权数量上升，但份额不显著。
政策 horse-race 还没完成：需要补城市政策面板，否则不能声称已经排除了其他数字政策。
```

下一步最该补的是政策面板，而不是继续堆更多专利口径。
