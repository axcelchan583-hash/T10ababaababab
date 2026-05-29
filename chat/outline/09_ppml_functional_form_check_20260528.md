# 给网页版评审：DDD 的 PPML 函数形式复核

请重点评估：`ln(1+Y)` OLS 与 PPML 符号相反时，论文是否还应把城市×技术领域 DDD 作为主识别。

## 背景

此前城市×技术领域 DDD 使用：

```text
ln(1+Y_cft) = beta ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_f
            + city × year FE
            + city × HighCompute FE
            + HighCompute × year FE
```

`ln1p` OLS 结果显示，高算力领域的新进入申请人数和新进入专利数相对低算力领域显著增加。

外部评审指出，Cohn-Liu-Wardlaw (2022, JFE) 与 Chen-Roth (2024, QJE) 都会攻击 `ln(1+Y)` 处理 count outcome，尤其当结果有大量 0 且研究对象正是 extensive margin。

因此我补了 PPML。

## PPML 设定

PPML 不能跑 high-minus-low 差分后的 Y，因为差分可能为负。因此回到完整城市×技术领域×年份面板：

```text
E[Y_cft] = exp(
    beta ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_f
    + city × year FE
    + city × HighCompute FE
    + HighCompute × year FE
)
```

用 Stata `ppmlhdfe`：

```text
ppmlhdfe y x_high, absorb(city_id#year city_id#high_compute year#high_compute) vce(cluster city_id)
```

其中：

```text
x_high = ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_f
```

## PPML 结果

### 1. 替换 HighCompute 定义

全样本、未加政策交互：

| HighCompute 定义 | 新进入申请人数 | 新进入专利数 |
|---|---:|---:|
| `broad` | -0.1544*** | -0.1270** |
| `no_h04` | -0.1088*** | -0.1092** |
| `g06_g16_g10l` | -0.1280*** | -0.1394** |
| `g06_only` | -0.1336*** | -0.1468*** |

### 2. 加政策 × HighCompute

| HighCompute 定义 | 新进入申请人数 | 新进入专利数 |
|---|---:|---:|
| `broad` | -0.0499 | -0.1086* |
| `no_h04` | -0.0273 | -0.0987* |
| `g06_g16_g10l` | -0.0445 | -0.1377** |
| `g06_only` | -0.0501 | -0.1437** |

### 3. 剔除个人 / one-shot

`broad` 定义、未加政策交互：

| 样本 | 新进入申请人数 | 新进入专利数 |
|---|---:|---:|
| `all` | -0.1544*** | -0.1270** |
| `no_individual` | -0.1613*** | -0.1552** |
| `no_oneshot` | -0.1482*** | -0.1240* |
| `no_individual_no_oneshot` | -0.1553*** | -0.1462** |

## 和 ln1p OLS 的冲突

`ln1p` OLS 的 broad 结果为：

```text
新进入申请人数：0.2184***
新进入专利数：0.2560***
```

PPML 的 broad 结果为：

```text
新进入申请人数：-0.1544***
新进入专利数：-0.1270**
```

这不是显著性变弱，而是方向相反。

## 当前内部判断

我倾向于认为：

```text
城市×技术领域 DDD 不能再作为当前最硬主识别。
```

更准确的说法是：

```text
ln1p OLS 支持高算力领域在小基数/比例变化意义上的相对扩张；
PPML 不支持 count-level 条件均值意义上的相对扩张。
```

这说明结果对函数形式和隐含权重敏感。

## 请评审的问题

1. 当 `ln1p` OLS 与 PPML 方向相反时，是否应直接放弃 DDD 主识别？
2. 如果保留 DDD，是否只能把它写成“比例变化/小基数扩张迹象”，而不能写 count-level 扩张？
3. 是否应改用份额型 Y，并用 fractional logit / PPML with exposure 做主规格？
4. PPML 是否应成为主表，`ln1p` OLS 退为附录？
5. 这个结果是否意味着项目应回到城市年进入边界主线，而不是城市×技术领域 DDD？
6. 如果目标是中文顶刊或 AJG3，当前 sign flip 是否已经构成 No-Go 信号？
