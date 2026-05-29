# 给网页版评审：T10 新 Y 烟测结果

## 1. 背景

本项目原来尝试写：

> IDC 服务覆盖 / 算力服务可得性是否扩大城市专利系统进入边界。

随后把城市×技术领域 DDD 作为主识别：

```text
Y_cft = beta ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_f
      + city × year FE
      + city × HighCompute FE
      + HighCompute × year FE
      + error_cft
```

但 DDD 的 `ln(1+Y)` OLS 正结果在 Stata `ppmlhdfe` 中转为显著为负，offset/rate/share 救法也没有救回来。因此暂时不能把城市×技术领域 DDD 作为主识别。

现在尝试寻找新的 Y。

## 2. 数据与规格

面板：

- 中国全量专利申请人，发明申请，按申请年份；
- 历史预热期从 1985 年起；
- 回归样本 2008-2023 年；
- 城市年面板 4,647 个观测。

X：

```text
ln1p_idc_scope_stock_l1
= 滞后一期 IDC 经营许可覆盖存量的 log(1+x)
```

回归规格：

1. 城市 FE + 年份 FE；
2. 城市 FE + 省份×年份 FE + 基期专利规模分组×年份 FE + 基期 Top10 share 分组×年份 FE；
3. 在 2 基础上加入政策 horse-race 控制。

计数型 Y 用 `ppmlhdfe`；份额/率类 Y 用 `reghdfe`；标准误按城市聚类。

## 3. 三组新 Y 的结果

### A. 持续进入

想法：

> 如果 IDC 服务覆盖真的扩大创新进入边界，那么新进入申请人不应只是一次性出现，而应在未来 2-3 年继续申请。

Y：

- `surv2_applicants`
- `surv3_applicants`
- `surv2_entry_pat_share_new`
- `surv3_entry_pat_share_new`
- `surv2_entry_pat_share_total`
- `surv3_entry_pat_share_total`

结果：

| Y | 强 FE + 政策 coef | p |
|---|---:|---:|
| `surv2_applicants` | 0.0546 | 0.2598 |
| `surv3_applicants` | 0.0299 | 0.5065 |
| `surv2_entry_pat_share_new` | -0.0165 | 0.0737 |
| `surv3_entry_pat_share_new` | -0.0210 | 0.0397 |
| `surv2_entry_pat_share_total` | 0.0015 | 0.7855 |
| `surv3_entry_pat_share_total` | 0.0005 | 0.9275 |

初步判断：

```text
持续进入不能救主线。
新进入扩容如果存在，也不像是稳定申请人的成长。
```

### B. 高质量进入

想法：

> 如果新进入是真正创新进入，至少应在授权、被引授权或家族被引授权口径上有一定支持。

Y：

- 发明授权新进入数量/专利数；
- 被引授权新进入数量/专利数；
- 家族被引授权新进入数量/专利数；
- 对应的新进入质量专利份额。

结果：

| Y | 强 FE + 政策 coef | p |
|---|---:|---:|
| `qgrant_new_n` | 0.0271 | 0.5278 |
| `qgrant_new_pat` | 0.0467 | 0.4258 |
| `qfcited_new_n` | 0.0193 | 0.6644 |
| `qfcited_new_pat` | 0.0277 | 0.6292 |
| `qgrant_share_total` | 0.0044 | 0.5387 |
| `qfcited_share_total` | 0.0057 | 0.3815 |

初步判断：

```text
高质量进入也不能作为主 Y。
```

### C. 头部榜单流动性

想法：

> IDC 服务覆盖可能没有稳定扩大长尾进入，也没有提升高质量进入份额；但它可能改变城市头部创新位置的竞争格局。

核心 Y：

```text
top10_turnover_prev_pat_share
= 当年城市 Top10 专利申请人中，由上一年未进入 Top10 的申请人贡献的专利份额

top20_turnover_prev_pat_share
= 当年城市 Top20 专利申请人中，由上一年未进入 Top20 的申请人贡献的专利份额
```

结果：

| Y | sample | 城市+年份 FE | 强 FE | 强 FE + 政策 |
|---|---|---:|---:|---:|
| `top10_turnover_prev_pat_share` | all | 0.0503*** | 0.0355** | 0.0348** |
| `top10_turnover_prev_pat_share` | min20 | 0.0531*** | 0.0362** | 0.0353** |
| `top10_turnover_prev_pat_share` | min50 | 0.0525*** | 0.0348** | 0.0338** |
| `top20_turnover_prev_pat_share` | all | 0.0331*** | 0.0272** | 0.0284** |
| `top20_turnover_prev_pat_share` | min20 | 0.0359*** | 0.0280** | 0.0282** |
| `top20_turnover_prev_pat_share` | min50 | 0.0329*** | 0.0273** | 0.0274** |

边界：

- 稳的是“上一年未入榜主体贡献的 Top 专利份额”；
- `top10_turnover_prev_share`，即未入榜主体数量占比，不稳。

初步判断：

```text
这是当前唯一有明显生命力的新 Y。
它更像“城市头部创新位置重组 / 榜单流动性增强”，不是“长尾创新进入边界扩大”。
```

## 4. 现在需要你重点评审的问题

1. 这个题能不能从“创新进入边界”改成“头部创新位置重组”？
2. `top10_turnover_prev_pat_share` 这种 Y 是否足够学术、是否有成熟文献可锚定？
3. 这个结果是否只是 Top 榜单机械波动，而不是真正的创新主体结构变化？
4. 如果主线改成“头部榜单流动性”，理论机制应写成什么：
   - 算力服务降低追赶者原型验证成本；
   - 算力服务加快新技术窗口期的头部重排；
   - 还是算力服务提高城市创新竞争强度？
5. 下一步最关键的防守检验应该是什么：
   - 事件研究；
   - Top 新晋主体类型；
   - 高质量/数字专利 Top 流动；
   - 名称清洗和集团合并；
   - placebo；
   - 还是另找更微观数据？

## 5. 我自己的当前判断

不要再硬救 DDD，也不要继续写高质量进入。

如果继续 T10，最可能的新方向是：

```text
城市算力服务可得性与头部创新位置重组：
来自中国城市 Top 专利申请人榜单流动性的证据
```

但这个方向还只是“有苗头”，不是已经能投稿：

- 必须先做 `top10_turnover_prev_pat_share` 的事件研究和前趋势；
- 必须识别新晋 Top 主体类型；
- 必须做质量口径 Top 流动性；
- 必须对 Top 申请人做更严格名称清洗。
