# 城市×技术领域 DDD 主效应重跑：1985 预热期口径

日期：2026-05-28

## 一句话结论

可以把主识别从城市年层面的连续强度回归，调整为：

```text
城市 × 技术领域 × 年份 DDD
```

重跑 1985 预热期后，结果仍然显著，而且比城市年主效应更适合作为主识别：

```text
IDC 服务覆盖增强后，同一城市同一年中，高算力依赖技术领域的新进入申请人和新进入专利相对低算力领域显著增加。
```

## 为什么要改成 DDD 主识别

原城市年模型是：

```text
Y_ct = beta ln(1 + IDC_scope_stock_{c,t-1})
     + city FE
     + province × year FE
     + baseline capacity × year FE
     + error_ct
```

它的问题是粒度偏粗，容易被质疑为：

```text
城市数字经济需求、地方创新政策、专利资助、营商环境、产业趋势同时推动 IDC 覆盖和新进入申请人。
```

DDD 改成：

```text
Y_cft = beta ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_f
      + city × year FE
      + city × HighCompute FE
      + HighCompute × year FE
      + error_cft
```

此时识别来自：

```text
同一个城市、同一年，高算力领域相对低算力领域的新进入变化。
```

`city × year FE` 吸收了城市当年全部共同冲击，包括政策包、城市创新景气、地方专利激励、经济周期、财政科技支出等。

## 本轮数据构造

已将整体申请人 DDD 面板从旧 2000 预热期改为 1985 预热期：

- 脚本：`scripts/build_overall_tech_entry_ddd_panel.py`
- 输入：`分年份保存数据.rar` 中 1985-2025 年全量专利 CSV
- 样本：2008-2023
- 输出：`data/processed/overall_tech_entry_ddd_panel_2008_2023.csv`
- 城市数：291
- 面板行数：9294
- detail 行数：3,070,093

高算力领域按 IPC 子类识别，包含：

```text
B25J, G05B, G06*, G10L, G16*, H04*
```

即机器人、自动控制、计算、数据处理、AI、软件、语音识别、数字通信等领域。

## 估计方式

为了避免生成大规模 dummy，本轮 Python 诊断使用等价差分形式：

```text
Delta Y_ct = Y_high_compute,ct - Y_other,ct

Delta Y_ct = beta ln(1 + IDC_scope_stock_{c,t-1})
           + city FE
           + year FE
           + error_ct
```

这个差分形式等价于原来的：

```text
city × year FE + city × HighCompute FE + HighCompute × year FE
```

标准误按城市聚类。

输出：

- `scripts/run_overall_tech_ddd_python.py`
- `results/tables/overall_tech_ddd_main_results_20260528.csv`
- `results/reports/overall_tech_ddd_main_results_20260528.json`

2026-05-28 晚修正：根据外部评审提醒，原 Python 虚拟变量实现使用 `drop_first=True` 但未显式加入常数项。现已修正为“常数项 + drop-first dummy”的标准等价实现，并重跑下列表格。修正后系数略小，但方向和显著性结论不变。

## 主结果

全样本结果：

| Y | 系数 | p 值 | 判断 |
|---|---:|---:|---|
| `ln1p_city_new_applicants_field` | 0.2184 | <0.001 | 显著 |
| `ln1p_city_new_patents_field` | 0.2560 | <0.001 | 显著 |
| `city_new_share_total_field` | 0.0310 | 0.0270 | 显著 |
| `ln1p_field_new_applicants_field` | 0.1729 | <0.001 | 显著 |
| `ln1p_field_new_patents_field` | 0.1928 | <0.001 | 显著 |
| `field_new_share_total_field` | 0.0317 | 0.0369 | 显著 |
| `ln1p_total_patents_field` | 0.1665 | 0.0003 | 显著 |
| `ln1p_incumbent_patents_field` | 0.2973 | <0.001 | 显著 |

解释：

```text
IDC 服务覆盖提升后，高算力技术领域相对低算力领域出现更多新进入申请人和新进入专利，
新进入份额在 broad 主定义下也正向显著。
```

但也要注意：

```text
既有主体专利在高算力领域也上升。
因此这不是纯粹“新进入者替代既有主体”，而是高算力领域整体扩张，其中新进入边界同步扩展。
后续定义替换和清洗样本显示，份额变量不如数量变量稳，不能让份额单独扛主结论。
```

## 样本稳健性

限制高专利量城市后，结果仍稳：

| 样本 | Y | 系数 | p 值 |
|---|---|---:|---:|
| `min20` | `ln1p_city_new_applicants_field` | 0.1530 | <0.001 |
| `min20` | `ln1p_city_new_patents_field` | 0.1797 | <0.001 |
| `min20` | `city_new_share_total_field` | 0.0366 | 0.0073 |
| `min20` | `field_new_share_total_field` | 0.0415 | 0.0039 |
| `min50` | `ln1p_city_new_applicants_field` | 0.0942 | 0.0019 |
| `min50` | `ln1p_city_new_patents_field` | 0.1150 | 0.0025 |
| `min50` | `city_new_share_total_field` | 0.0351 | 0.0113 |
| `min50` | `field_new_share_total_field` | 0.0492 | 0.0006 |

解释：

```text
结果不是小城市、低专利量城市的份额噪声驱动。
```

## 对论文主线的影响

建议把论文主识别改成：

```text
城市 × 技术领域 × 年份 DDD
```

城市年主效应降为背景事实：

```text
城市 IDC 服务覆盖增强后，城市整体新进入申请人上升。
```

DDD 主结论改为：

```text
IDC 服务覆盖增强后，城市专利系统的新进入更多发生在算力依赖型技术领域。
```

相应题目建议改成：

```text
算力服务可得性与算力依赖型创新进入：
来自中国城市全量专利申请人数据的证据
```

或更保守：

```text
IDC 服务覆盖与算力依赖型专利进入：
基于中国全量专利申请人数据的证据
```

## 当前仍不能写什么

不能写：

```text
IDC 明确导致城市整体创新进入增加。
```

因为 DDD 主识别吸收了 city × year FE，识别的是高算力领域相对低算力领域的变化。

不能写：

```text
IDC 只影响高算力领域。
```

因为城市年主效应和低算力领域也可能有正向变化。更准确是：

```text
普遍扩容 + 高算力领域额外增强。
```

不能写：

```text
新进入者替代既有主体。
```

因为既有主体在高算力领域也增长更快。

## 下一轮必须补

1. 换 HighCompute 定义：
   - 只保留 G06/G16/H04；
   - 剔除 H04 通信；
   - 只看 AI/软件/数据处理；
   - 按 IPC 更细子类或关键词重构。

2. 做事件 DDD：
   - `IDC_scope_stock >= 2` × `HighCompute`；
   - 继续吸收 city × year、city × field、field × year；
   - 检查处理前高算力领域是否已经相对上升。

3. 加政策 × HighCompute 控制：
   - 宽带中国 × HighCompute；
   - 智慧城市 × HighCompute；
   - 大数据试验区 × HighCompute；
   - 创新型城市 × HighCompute；
   - 高新区 × HighCompute。

4. 做质量和身份版本 DDD：
   - 发明授权；
   - 家族被引授权；
   - 剔除个人；
   - 剔除 one-shot entrants。
