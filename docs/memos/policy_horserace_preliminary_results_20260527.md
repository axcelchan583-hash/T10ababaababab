# 政策 horse-race 第一版结果

日期：2026-05-27  
项目：T10 城市 IDC 服务覆盖与创新进入边界

## 1. 本轮做了什么

基于 `policy_seed_lists_20260527.csv`，先生成第一版城市-年份政策控制面板：

- `data/external_proxy/city_policy_horserace_panel_2008_2023.csv`
- `data/external_proxy/policy_seed_city_match_report_20260527.csv`
- `data/processed/idc_scope_policy_horserace_panel_2008_2023.csv`

并运行：

- `scripts/build_policy_horserace_panel_from_seed.py`
- `scripts/build_policy_horserace_panel.py`
- `scripts/run_policy_horserace_stata.do`

结果输出：

- `results/tables/policy_horserace_results_20260527.csv`
- `results/tables/policy_horserace_key_summary_20260527.csv`

## 2. 当前政策控制覆盖

本轮进入 horse-race 的政策：

| policy | city-year post observations | 说明 |
|---|---:|---|
| `broadband_china_pilot` | 1,020 | 2014/2015/2016 三批宽带中国示范城市 |
| `bigdata_comprehensive_pilot` | 256 | 省/区域/城市 broad coding |
| `innovative_city_pilot` | 582 | 2016 创新型城市试点建设名单 + 2018 新批次 |
| `ip_demo_city` | 452 | 2012 首批 + 2013 第二批国家知识产权示范城市 |

尚未真正进入：

- `smart_city_pilot`：三批国家智慧城市试点名单尚未完全结构化；
- `national_hightech_zone`：高新区名单需要抽批准年月和所属城市；
- `information_consumption_pilot`、`ecommerce_demo_city`：暂缓。

因此本轮是 preliminary horse-race，不是最终政策控制表。

## 3. 模型

基础规格：

```text
Y_ct = beta IDC_scope_stock_{c,t-1}
     + city FE
     + province × year FE
     + error_ct
```

政策 horse-race：

```text
Y_ct = beta IDC_scope_stock_{c,t-1}
     + broadband_china_pilot
     + bigdata_comprehensive_pilot
     + innovative_city_pilot
     + ip_demo_city
     + city FE
     + province × year FE
     + error_ct
```

强规格：

```text
在上式基础上加入
base_ln_patents_q × year FE
base_top10_q × year FE
```

样本：

```text
2008-2023 年
291 个城市
4,647 个城市-年份
城市聚类标准误
```

## 4. 核心结果

### 4.1 主 Y：`new_applicant_share`

| spec | coef | p |
|---|---:|---:|
| province × year FE | 0.0430 | 0.000006 |
| + policy horse-race | 0.0318 | 0.0037 |
| + policy + baseline × year FE | 0.0206 | 0.0652 |

解释：

```text
控制宽带中国、大数据试验区、创新型城市、知识产权示范城市后，
IDC_scope 对 new_applicant_share 的正向结果仍保留。
```

这是本轮最重要的结果。

### 4.2 分子变量

| Y | province × year FE | + policy | + policy + baseline × year FE |
|---|---:|---:|---:|
| `ln1p_new_applicants` | 0.0246 | 0.0768 | 0.0995** |
| `ln1p_new_patents` | -0.0100 | 0.0600 | 0.0934* |

解释：

```text
在政策控制和基期能力趋势控制后，新进入申请人数和新进入专利数为正，
说明主结果不是单纯分母效应。
```

### 4.3 集中度结果

| Y | province × year FE | + policy | + policy + baseline × year FE |
|---|---:|---:|---:|
| `hhi` | 0.0106* | 0.0079 | 0.0031 |
| `top10_share` | 0.0307** | 0.0048 | -0.0073 |

解释：

```text
集中度结果在加入政策控制后明显消失。
```

这进一步说明，当前论文不应把“头部再集中”当作主因果结论。可防守主线仍是“创新进入边界扩展”。

## 5. 当前可写结论

可以写：

```text
在控制若干重要数字与创新政策后，城市 IDC 服务覆盖对新进入申请人份额的正向影响仍然存在。
```

更谨慎写：

```text
第一版政策 horse-race 显示，主结果不完全由宽带中国、国家大数据综合试验区、
创新型城市建设和知识产权示范城市等政策叠加解释。
```

不能写：

```text
已经完全排除其他数字政策干扰。
```

原因：

- 智慧城市三批名单尚未补齐；
- 国家高新区数量尚未进入；
- 知识产权示范城市后续批次尚未补齐；
- 大数据综合试验区目前是 broad coding，省级/区域政策映射需要更细说明。

## 6. 下一步

优先级：

1. 补三批国家智慧城市试点名单；
2. 补国家高新区批准年月和所属城市，构造 `national_hightech_zone_count`；
3. 补知识产权示范城市后续批次；
4. 做 policy horse-race 第二版；
5. 若第二版仍保留 `new_applicant_share`，可把这张表放稳健性主文或附录前排。
