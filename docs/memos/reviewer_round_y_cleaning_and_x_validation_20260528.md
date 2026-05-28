# 审稿人防守补强第一轮：Y 清洗、X 拆分与质量口径

日期：2026-05-28

## 一句话结论

这一轮补强后，最能防守的结论仍然是：

```text
IDC 服务覆盖强度提升后，城市专利系统的新进入边界扩大。
```

但结论需要继续收窄：

```text
不能写成企业/组织进入稳健增加；
不能写成高质量新进入份额稳健提升；
不能写成城市创新头部再集中具有强因果证据。
```

更适合的论文定位是：

```text
算力服务可得性与城市专利系统进入边界：
基于 IDC 经营许可覆盖和全量专利申请人数据的证据。
```

## 本轮做了什么

1. 将主申请年份口径的新进入申请人面板预热期从 2000 年扩展到 1985 年：
   - 输入：`data/processed/city_applicant_counts_application_year/city_applicant_counts_inv_app_appyear_1985_2023.csv.gz`
   - 输出：`data/processed/patent_applicant_concentration_application_year_2008_2023.csv`
   - 行数：6149
   - 城市数：443

2. 重建合并 IDC scope 的正式主面板、政策 horse-race 面板、申请人类型面板、企业口径面板和组织口径面板。

3. 新增 IDC 许可证特征拆分：
   - `idc_scope_cloud`：公司名、许可证号或覆盖范围文本中包含云、计算、数据、算力等关键词；
   - `idc_scope_noncloud`：其他 IDC scope 记录；
   - `idc_scope_cross` / `idc_scope_provlic`：跨地区许可证与省内许可证；
   - `idc_scope_carrier` / `idc_scope_noncarrier`：基础运营商与非基础运营商。

4. 用 Python 跑了审稿人防守诊断表：
   - 本机当前没有可调用 Stata binary；
   - Python 表使用显式 dummy fixed effects 和城市聚类标准误；
   - 该表用于快速诊断，正式投稿表仍应回到 Stata / reghdfe / csdid / did_imputation。

5. 质量口径说明：
   - 1985 预热期质量口径重建任务运行约 19.5 小时仍未落盘，已停止；
   - 本轮质量诊断仍使用现有 2000 预热期质量面板；
   - 因此质量结论只能作为临时补充，不能和 1985 主口径混写。

## 关键输出

- `scripts/build_idc_scope_license_feature_panel.py`
- `scripts/run_reviewer_round_python.py`
- `data/processed/idc_scope_license_feature_city_year_2000_2024.csv`
- `results/tables/reviewer_round_y_cleaning_results_20260527.csv`
- `results/tables/warmup_1985_vs_2000_comparison_20260527.csv`
- `results/reports/reviewer_round_y_cleaning_report_20260527.json`

## 1985 预热期是否改变主 Y

与旧 2000 预热期相比，主 Y 变化很小：

| 变量 | 旧均值 | 新均值 | 均值差 |
|---|---:|---:|---:|
| `new_applicant_share` | 0.4717 | 0.4693 | -0.0024 |
| `new_applicants` | 174.92 | 174.28 | -0.64 |
| `new_patents` | 239.49 | 238.72 | -0.77 |

解释：

```text
将历史预热期前移到 1985 年不会推翻主结果。
主 Y 不是由 2000 年左截断机械制造出来的。
```

## 主结果：进入边界仍能防守

核心 X：

```text
ln(1 + IDC_scope_city_stock_{c,t-1})
```

样本为申请年份发明申请口径，2008-2023，城市聚类标准误。

| 结果变量 | 规格 | 系数 | p 值 | 判断 |
|---|---|---:|---:|---|
| `new_applicant_share` | 省份×年份 FE + 基期能力趋势 FE | 0.0222 | 0.0539 | 边际显著 |
| `new_applicant_share` | 政策 horse-race + 基期能力趋势 FE | 0.0200 | 0.0764 | 边际显著 |
| `ln1p_new_applicants` | 省份×年份 FE + 基期能力趋势 FE | 0.1179 | 0.0086 | 显著 |
| `ln1p_new_applicants` | 政策 horse-race + 基期能力趋势 FE | 0.0988 | 0.0336 | 显著 |
| `ln1p_new_patents` | 省份×年份 FE + 基期能力趋势 FE | 0.1152 | 0.0294 | 显著 |
| `ln1p_new_patents` | 政策 horse-race + 基期能力趋势 FE | 0.0931 | 0.0980 | 边际显著 |

解释：

```text
份额变量不是唯一证据。
新进入申请人数和新进入专利数同步上升，说明不是老申请人专利下降造成的机械份额变化。
```

## 集中度结果：不能再作为主因果

| 结果变量 | 规格 | 系数 | p 值 |
|---|---|---:|---:|
| `hhi` | 省份×年份 FE + 基期能力趋势 FE | 0.0009 | 0.9099 |
| `hhi` | 政策 horse-race + 基期能力趋势 FE | 0.0031 | 0.7152 |
| `top10_share` | 省份×年份 FE + 基期能力趋势 FE | -0.0106 | 0.3817 |
| `top10_share` | 政策 horse-race + 基期能力趋势 FE | -0.0073 | 0.5521 |

解释：

```text
头部再集中可以保留为早期现象或描述性结构结果，
但不能写成强因果主结论。
```

## 申请人类型：主要来自个人进入

强规格下：

| 结果变量 | 系数 | p 值 | 判断 |
|---|---:|---:|---|
| `individual_new_share_total` | 0.0264 | 0.0237 | 显著 |
| `ln_individual_new_n` | 0.1309 | 0.0385 | 显著 |
| `org_new_share_total` | -0.0043 | 0.5956 | 不显著 |
| `ln_org_new_n` | 0.0485 | 0.2054 | 不显著 |
| `firm_new_share_total` | -0.0070 | 0.4201 | 不显著 |
| `ln_firm_new_n` | 0.0495 | 0.2225 | 不显著 |

解释：

```text
不能把当前主结果直接解释为企业创新进入。
更防守的说法是：IDC 服务覆盖扩大了城市专利系统进入边界，
现阶段最明显体现在个人申请人和边缘申请人进入。
```

下一步必须做：

```text
剔除个人申请人；
剔除一次性申请人；
检查新进入者进入后 2-3 年是否继续申请；
识别疑似非正常申请和代理集中申请。
```

## X 拆分：云/计算相关 IDC 许可更贴近机制

强规格下，云/计算相关许可变量的系数更稳：

| X | Y | 系数 | p 值 |
|---|---|---:|---:|
| `ln1p_idc_scope_cloud_stock_l1` | `new_applicant_share` | 0.0320 | 0.0043 |
| `ln1p_idc_scope_cloud_stock_l1` | `ln1p_new_applicants` | 0.1363 | 0.0038 |
| `ln1p_idc_scope_cloud_stock_l1` | `ln1p_new_patents` | 0.1425 | 0.0117 |
| `ln1p_idc_scope_noncloud_stock_l1` | `new_applicant_share` | 0.0166 | 0.2961 |
| `ln1p_idc_scope_noncloud_stock_l1` | `ln1p_new_applicants` | 0.1248 | 0.0296 |
| `ln1p_idc_scope_noncloud_stock_l1` | `ln1p_new_patents` | 0.1080 | 0.1151 |

解释：

```text
这为“算力服务可得性”提供了初步内部验证。
但它只是关键词拆分，不等于外部容量验证。
```

论文中可以写：

```text
与机制更接近的云/计算相关 IDC 许可覆盖对新进入边界的解释力更强。
```

不能写：

```text
我们已经证明 IDC 许可证等于真实算力容量。
```

## 质量口径：支持数量扩张，不支持份额稳健

注意：本节仍是 2000 预热期质量补充。

强规格下：

| 质量口径 | Y | 系数 | p 值 |
|---|---|---:|---:|
| 发明授权申请年 | `new_applicant_share` | 0.0123 | 0.2461 |
| 发明授权申请年 | `ln1p_new_applicants` | 0.0997 | 0.0144 |
| 发明授权申请年 | `ln1p_new_patents` | 0.1245 | 0.0109 |
| 发明授权且被引 | `new_applicant_share` | 0.0036 | 0.8181 |
| 发明授权且被引 | `ln1p_new_applicants` | 0.0898 | 0.0748 |
| 发明授权且被引 | `ln1p_new_patents` | 0.0927 | 0.0857 |
| 发明授权且家族被引 | `new_applicant_share` | 0.0145 | 0.1916 |
| 发明授权且家族被引 | `ln1p_new_applicants` | 0.1162 | 0.0052 |
| 发明授权且家族被引 | `ln1p_new_patents` | 0.1407 | 0.0035 |

解释：

```text
质量口径下，新进入申请人数量和新进入授权专利数量仍有正向证据；
但新进入者份额不显著。
```

可写：

```text
结果不完全由低质量申请堆量解释，因为在授权和家族被引授权口径下，
新进入申请人数量和新进入专利数量仍呈正向响应。
```

不能写：

```text
IDC 稳健提高高质量新进入专利份额。
```

## 当前写作边界

最安全主线：

```text
IDC 服务覆盖强度提升与城市专利系统进入边界扩展相关，
并在 1985 预热期、政策 horse-race、现代 DID、时间安慰剂和高算力技术领域 DDD 下得到支持。
```

需要降级的地方：

```text
城市颗粒仍偏粗；
X 仍是 IDC 许可覆盖而非真实机柜/MW/FLOPS；
当前进入主要来自个人申请人；
质量口径只支持数量扩张；
集中度和企业/组织口径不能主打。
```

## 下一轮优先级

1. X 外部验证：
   - 数据中心项目数；
   - 机柜数、MW、PUE、智算中心；
   - 云服务节点、运营商云资源池；
   - 地方算力券或算力中心政策。

2. Y 清洗：
   - 剔除个人；
   - 剔除 one-shot entrants；
   - 进入后持续申请；
   - 申请人名称变体审计。

3. 政策混淆：
   - 智慧城市；
   - 国家高新区；
   - 知识产权示范/强市后续批次；
   - 信息消费、电商示范、AI 创新发展试验区；
   - 地方专利资助、知识产权保护中心/预审城市。

4. 正式表：
   - Python 诊断需要用 Stata / reghdfe / did_imputation / csdid 重跑；
   - 质量口径 1985 预热期需要另写快版，不再用当前低效脚本。
