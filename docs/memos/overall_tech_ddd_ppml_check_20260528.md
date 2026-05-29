# 城市×技术领域 DDD：PPML 函数形式复核

日期：2026-05-28

## 一句话结论

这轮 PPML 不支持把 `ln1p` DDD 的正向数量结果直接作为主因果结论。

```text
ln(1+Y) OLS 中，高算力领域的新进入数量相对上升；
但使用高维固定效应 PPML 后，count-level 结果转为显著为负。
```

这说明当前结果对函数形式和隐含权重敏感。论文不能再写成“高算力技术领域新进入数量稳健扩张”。更稳妥的处理是：

```text
PPML 作为函数形式压力测试；
ln1p OLS 作为小格子/比例变化意义下的描述性结果；
主线需要重新判断，或转回城市年进入边界/份额口径并承认 DDD 证据不稳。
```

## 为什么补 PPML

外部评审指出，`ln(1+Y)` 处理计数型结果有明确文献风险：

- Cohn, Liu and Wardlaw (2022, JFE) 讨论 count/count-like data 中 `log(1+x)` 的解释问题，并建议使用固定效应 Poisson；
- Chen and Roth (2024, QJE) 指出 `log(1+Y)` / asinh 在有 0 且处理影响 extensive margin 时对单位敏感；
- Santos Silva and Tenreyro (2006, REStat) 是 PPML 的经典计量来源。

我们的 Y 是城市×技术领域×年份的新进入申请人数/专利数，零值较多，且核心机制正是 extensive margin，因此必须补 PPML。

## 估计设定

PPML 不能跑在高算力减低算力后的差分 Y 上，因为差分后可能为负。正确做法是回到完整城市×技术领域×年份面板：

```text
E[Y_cft] = exp(
    beta * ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_f
    + city × year FE
    + city × HighCompute FE
    + HighCompute × year FE
)
```

标准误按城市聚类。

Stata 命令使用 `ppmlhdfe`：

```text
ppmlhdfe y x_high, absorb(city_id#year city_id#high_compute year#high_compute) vce(cluster city_id)
```

政策控制版加入：

```text
policy_ct × HighCompute_f
```

当前可用政策仍为：

- 宽带中国；
- 国家大数据综合试验区；
- 创新型城市；
- 知识产权示范城市。

## 输出

- 脚本：`scripts/run_overall_tech_ddd_ppml_stata.do`
- 结果：`results/tables/overall_tech_ddd_ppml_results_20260528.csv`
- 日志：`results/logs/overall_tech_ddd_ppml_20260528.log`

## 关键结果

全样本、未加政策交互：

| HighCompute 定义 | Y | PPML 系数 | p 值 |
|---|---|---:|---:|
| `broad` | 新进入申请人数 | -0.1544 | <0.001 |
| `broad` | 新进入专利数 | -0.1270 | 0.0245 |
| `no_h04` | 新进入申请人数 | -0.1088 | <0.001 |
| `no_h04` | 新进入专利数 | -0.1092 | 0.0332 |
| `g06_g16_g10l` | 新进入申请人数 | -0.1280 | <0.001 |
| `g06_g16_g10l` | 新进入专利数 | -0.1394 | 0.0145 |
| `g06_only` | 新进入申请人数 | -0.1336 | <0.001 |
| `g06_only` | 新进入专利数 | -0.1468 | 0.0100 |

加入政策 × HighCompute 后：

| HighCompute 定义 | Y | PPML 系数 | p 值 |
|---|---|---:|---:|
| `broad` | 新进入申请人数 | -0.0499 | 0.1742 |
| `broad` | 新进入专利数 | -0.1086 | 0.0722 |
| `no_h04` | 新进入申请人数 | -0.0273 | 0.4920 |
| `no_h04` | 新进入专利数 | -0.0987 | 0.0805 |
| `g06_g16_g10l` | 新进入申请人数 | -0.0445 | 0.3141 |
| `g06_g16_g10l` | 新进入专利数 | -0.1377 | 0.0376 |
| `g06_only` | 新进入申请人数 | -0.0501 | 0.2591 |
| `g06_only` | 新进入专利数 | -0.1437 | 0.0300 |

剔除个人和 one-shot 后，`broad` 定义下仍为负：

| 样本 | Y | PPML 系数 | p 值 |
|---|---|---:|---:|
| `all` | 新进入申请人数 | -0.1544 | <0.001 |
| `no_individual` | 新进入申请人数 | -0.1613 | <0.001 |
| `no_oneshot` | 新进入申请人数 | -0.1482 | <0.001 |
| `no_individual_no_oneshot` | 新进入申请人数 | -0.1553 | <0.001 |

## 如何解释

`ln1p` OLS 和 PPML 的差异不是小问题，而是对研究结论有实质影响：

```text
ln1p OLS 更像是在比较比例变化，并对小城市、小格子、低基数变化给了更多权重；
PPML 估计的是 count-level 条件均值的比例变化，大计数城市/格子权重更高。
```

当前 sign flip 说明：

```text
高算力领域可能在小基数或比例意义上扩张更快；
但按 count-level PPML 看，IDC 覆盖提升后，新进入数量并没有相对更多流向高算力领域，甚至相对低算力领域更弱。
```

## 写作边界

不能再写：

```text
城市×技术领域 DDD 稳健证明 IDC 服务覆盖使高算力领域新进入数量相对扩张。
```

可以写：

```text
城市×技术领域 DDD 的 ln1p OLS 显示高算力领域存在相对扩张迹象，但 PPML 函数形式复核不支持该结论。技术领域 DDD 不能作为当前最硬主识别，只能作为机制探索或未过关的压力测试。
```

## 下一步建议

1. 不要把 DDD 作为主效应直接写进论文主表。
2. 回到城市年进入边界结果，或重新寻找更细颗粒、但在 PPML 下也成立的 Y。
3. 若继续保留技术领域 DDD，应把主 Y 改为份额/率类变量，而不是 count；但这需要重新处理 share 的样本选择和分母问题。
4. 可追加 `fractional logit` / `PPML with exposure` 作为份额型结果压力测试，但这已经是下一轮设计，不应掩盖当前 PPML sign flip。
