# 城市×技术领域 DDD：救法复核

日期：2026-05-28

## 一句话结论

DDD 基本救不回来。

```text
PPML + exposure 后，raw count 的显著负向有所缓和，但没有稳健转正；
进入率 / 份额结果只在 broad 定义下有局部支持；
真正 extensive margin，即是否出现新进入者，显著为负。
```

因此不能把城市×技术领域 DDD 作为论文主识别。它最多作为一个失败的压力测试或机制探索结果。

## 为什么做这一轮

上一轮 PPML 检验显示：

```text
ln1p OLS 为正；
count-level PPML 为负。
```

这说明 DDD 结果对函数形式和隐含权重敏感。为了确认是否只是 raw count 口径不合适，本轮继续试三种救法：

1. PPML + `offset(log(total_patents_field))`：检验给定技术领域专利规模后的新进入率；
2. PPML + `offset(log(active_applicants_field))`：检验给定活跃申请人规模后的新进入率；
3. 份额/率/是否有新进入者的 DDD：检验比例和真正 extensive margin。

## 设定

完整 DDD 面板：

```text
Y_cft = beta ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_f
      + city × year FE
      + city × HighCompute FE
      + HighCompute × year FE
```

PPML exposure 规格：

```text
ppmlhdfe y x_high, absorb(city_id#year city_id#high_compute year#high_compute)
    vce(cluster city_id) offset(log_exposure)
```

OLS 份额/二元变量规格：

```text
reghdfe y x_high, absorb(city_id#year city_id#high_compute year#high_compute)
    vce(cluster city_id)
```

输出：

- 脚本：`scripts/run_overall_tech_ddd_rescue_stata.do`
- 结果：`results/tables/overall_tech_ddd_rescue_results_20260528.csv`
- 日志：`results/logs/overall_tech_ddd_rescue_20260528.log`

## 1. PPML + 总专利 exposure

全样本、未加政策交互：

| HighCompute 定义 | 新进入申请人数 | 新进入专利数 |
|---|---:|---:|
| `broad` | 0.0270 | 0.0381 |
| `no_h04` | -0.0019 | 0.0045 |
| `g06_g16_g10l` | 0.0186 | 0.0169 |
| `g06_only` | 0.0113 | 0.0098 |

解释：

```text
给定技术领域专利规模后，符号不再显著为负，但也不显著为正。
```

加入政策 × HighCompute 后：

| HighCompute 定义 | 新进入申请人数 | 新进入专利数 |
|---|---:|---:|
| `broad` | 0.0796** | 0.0195 |
| `no_h04` | 0.0858* | 0.0271 |
| `g06_g16_g10l` | 0.1064** | 0.0340 |
| `g06_only` | 0.0994* | 0.0284 |

解释：

```text
申请人数的 rate 口径在加政策交互后有弱正结果；
但新进入专利数不显著。
这个结果可以作为探索线索，不能单独支撑主结论。
```

## 2. PPML + 活跃申请人 exposure

`broad` 定义、全样本：

| Y | 不加政策 | 加政策×HighCompute |
|---|---:|---:|
| 新进入申请人数 | -0.0296*** | -0.0199 |
| 新进入专利数 | -0.0346 | -0.0976* |
| 技术领域首次进入申请人数 | -0.0457*** | -0.0439*** |
| 技术领域首次进入专利数 | -0.0557 | -0.1069** |

解释：

```text
给定活跃申请人规模后，高算力领域的新进入率没有上升，反而更弱。
```

## 3. OLS 份额/进入率

全样本、未加政策交互：

| HighCompute 定义 | 新进入申请人率 | 新进入专利份额 |
|---|---:|---:|
| `broad` | 0.0108 | 0.0308** |
| `no_h04` | 0.0109 | 0.0128 |
| `g06_g16_g10l` | 0.0258 | 0.0207 |
| `g06_only` | 0.0262 | 0.0190 |

解释：

```text
申请人率不显著；
专利份额只在 broad 定义下显著，换定义后不稳。
```

剔除个人和 one-shot 后，`broad` 份额也不稳：

| 样本 | 新进入申请人率 | 新进入专利份额 |
|---|---:|---:|
| `all` | 0.0108 | 0.0308** |
| `no_individual` | 0.0020 | 0.0148 |
| `no_oneshot` | 0.0036 | 0.0190 |
| `no_individual_no_oneshot` | -0.0051 | 0.0081 |

## 4. 是否有新进入者

全样本、LPM：

| HighCompute 定义 | 是否有新进入申请人 | 是否有新进入专利 |
|---|---:|---:|
| `broad` | -0.1329*** | -0.1329*** |
| `no_h04` | -0.1585*** | -0.1585*** |
| `g06_g16_g10l` | -0.1547*** | -0.1547*** |
| `g06_only` | -0.1500*** | -0.1500*** |

解释：

```text
如果把“进入边界”理解为某个城市-技术领域-年份是否出现新进入者，
高算力领域并没有更容易出现进入，反而相对更弱。
```

这对 DDD 叙事伤害最大。

## 当前判断

三条救法都没有把 DDD 救成可防守主识别：

1. `PPML + total patent exposure`：不再负，但基本不显著；
2. `PPML + active applicant exposure`：多为负；
3. `share/rate/any-entry`：份额只在 broad 下局部显著，真正 extensive margin 为负。

因此：

```text
城市×技术领域 DDD 不适合作为主效应。
```

## 写作建议

不要写：

```text
IDC 服务覆盖显著推动高算力领域创新进入。
```

可以在内部讨论或附录中写：

```text
城市×技术领域 DDD 作为机制检验并不稳健。
ln1p OLS 显示高算力领域存在相对扩张迹象，
但 PPML、进入率和是否进入等压力测试不支持该结果。
```

如果论文继续推进，建议回到城市年进入边界主线，而不是继续救技术领域 DDD。
