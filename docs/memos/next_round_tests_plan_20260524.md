# 下一轮检验计划：算力基础设施与城市创新主体结构

日期：2026-05-24

## 1. 总判断

Claude 和 ChatGPT Pro 的判断高度一致：

```text
Pivot and continue, but only after passing a stricter small-loop validation.
```

当前最优先的任务不是继续堆机制和异质性，而是先确认：

1. 申请年份口径下结果是否仍存在；
2. 省市匹配是否可靠；
3. “进入扩容 + 头部集中”是否能升级为“新进入者 + 预先 Top + 中腰部既有主体”的结构分解；
4. 强固定效应、预趋势、大城市剔除和其他政策控制后是否还站得住；
5. 当前 IDC 许可证 X 是否能被解释为本地算力供给代理。

## 2. 第一批必须跑的检验：48 小时小闭环

### 检验 1：改用申请年份重构主 Y

当前第一轮使用公开公告年份所属文件作为年份。下一轮要改为：

- 发明申请：以 `申请年份` 作为主年份；
- 发明授权：以 `授权公告年份` 作为稳健性 / 质量口径；
- 主样本先截到 2022 或 2023，避免 2024 右截尾；
- 授权口径建议更保守，截到 2020 或 2021。

需要输出：

- `patent_applicant_concentration_city_year_application_2008_2023.csv`
- `idc_applicant_concentration_panel_application_2008_2023.dta`

主看：

- `ln1p_new_applicants`
- `new_applicant_share`
- `hhi`
- `top10_share`
- `ln1p_total_patents`

判定：

- 如果申请年份后新进入和集中度方向全部消失，当前题直接降级。

### 检验 2：省市映射修正

当前只按城市名去“市”合并，正式检验至少要纳入：

- 专利数据里的 `申请人地区` / 省份字段；
- 规范化省份 + 城市；
- 行政区划代码或自建省市映射表；
- 直辖市、自治州、地区、盟、县级市的处理规则。

主目标：

```text
province_city_year panel, not city-name-only panel.
```

判定：

- 如果省市修正后 IDC 匹配样本大幅变化，需要重跑所有第一轮结果。

### 检验 3：pre-top / new / middle 三分解

这是下一轮最重要的 Y 升级。

构造互斥份额：

```text
share_pre_top10_ct
share_new_ct
share_middle_incumbent_ct
```

建议两种 Top 定义都跑：

1. rolling pre-top：城市 c 在 t-3 至 t-1 年 Top10 申请人；
2. baseline pre-top：城市 c 在首次 IDC 进入前 3 年，或统一基期 2008-2010 年 Top10 申请人。

定义：

```text
share_pre_top10 = pre-top10 applicants' patents in year t / total patents in city-year
share_new = first-time applicants' patents / total patents
share_middle_incumbent = 1 - share_pre_top10 - share_new
```

判定：

- 最理想：`IDC -> share_new > 0`，`IDC -> share_pre_top10 > 0`，`IDC -> share_middle_incumbent < 0`。
- 这将支持“创新生态杠铃化”。

### 检验 4：强固定效应主规格

基准：

```stata
Y_ct = beta ln1p_idc_stock_l1 + city FE + year FE
```

升级主规格：

```stata
Y_ct = beta ln1p_idc_stock_l1 + city FE + province × year FE
```

再升级：

```stata
Y_ct = beta ln1p_idc_stock_l1
     + city FE
     + province × year FE
     + baseline_innovation × year FE
     + baseline_concentration × year FE
```

其中 baseline 可用 2008-2010：

- 基期发明专利数；
- 基期 HHI / Top10 share；
- 基期 active applicants。

判定：

- 强 FE 下方向不能乱；
- 显著性可以变弱，但经济量级不能完全消失。

### 检验 5：事件研究 / 预趋势

先定义事件：

1. 首次 `idc_stock > 0`；
2. 或首次进入 IDC stock 增长较高分位；
3. 或后续使用智算中心 / 东数西算节点作为清晰事件。

事件窗口：

```text
-5 to +5
```

核心 Y：

- `share_new`
- `share_pre_top10`
- `share_middle_incumbent`
- `hhi`
- `top10_share`

判定：

- pre-period joint F-test 不显著；
- 处理前不能已经出现新进入和集中度同步上升。

### 检验 6：剔除大城市和强创新中心

至少跑：

1. 剔除北上广深；
2. 剔除北上广深 + 杭州；
3. 剔除直辖市；
4. 剔除所有省会 / 副省级城市；
5. 剔除 Top10 专利城市；
6. 剔除高校极强城市或央企极强城市。

判定：

- 如果结果只剩北京、深圳、杭州驱动，就不能写一般城市效应；
- 可以 pivot 为“头部创新城市生态重组”。

### 检验 7：其他政策 horse-race

至少整理并控制：

- 宽带中国；
- 智慧城市；
- 国家大数据综合试验区；
- 创新型城市；
- 高新区；
- 知识产权示范城市；
- 电子政务 / 信息化试点，如果已有数据。

第一步可以先做政策叠加指数：

```text
digital_policy_stack_ct
```

再逐项加入。

判定：

- 如果 IDC 系数完全被这些政策吸收，当前 X 不是独立算力效应；
- 可转为“数字政策组合与创新主体结构”或换更强 X。

### 检验 8：X 的外部验证

当前 IDC 许可证是最大软肋。至少要做一个验证：

1. IDC stock 与城市数据中心 / 机房地址数量是否正相关；
2. IDC stock 与智算中心、超算中心、国家算力枢纽城市是否正相关；
3. IDC stock 与公开报道的数据中心容量、机柜数、MW、算力规模是否正相关；
4. 城市 IDC 增量是否在东数西算 / 算力枢纽城市更明显。

判定：

- 如果无外部验证，论文只能谨慎写“IDC 服务经营主体 / 算力服务供给代理”；
- 如果验证强，才写“本地算力基础设施”。

## 3. 第二批检验：小闭环过后再做

### 检验 9：Top 申请人身份识别

先不要全量集团合并。下一步先导出：

```text
city-year Top20 applicants
pre-treatment Top20 applicants
```

识别：

- 企业；
- 高校；
- 科研院所；
- 医院；
- 个人；
- 机关团体；
- A 股集团 / 子公司；
- 央企 / 国企 / 民企。

主看：

- Top10 份额上升来自哪类主体；
- pre-top 是否持续留在榜单；
- 新进入者中是否有高校 / 企业 / 个人差异。

### 检验 10：基期吸收能力异质性

交互项：

```text
IDC_ct × High_Baseline_AC_c
```

基期 AC 可用：

- 基期发明专利数；
- 基期 Top10 share；
- 基期有效申请人数；
- 基期高校 / 科研资源；
- 基期数字专利占比。

预期：

- 高 AC 城市：`IDC -> pre_top_share / hhi` 更强；
- 低 AC 城市：`IDC -> new_applicants / share_new` 更强。

### 检验 11：专利类型和技术方向

优先顺序：

1. 发明申请；
2. 发明授权；
3. 实用新型；
4. 数字 / AI / 云 / 数据处理专利；
5. 高价值发明。

预期：

- 发明类比实用新型更能支持真实创新；
- 数字 / AI / 云专利中再集中更强；
- 若普通专利扩散、高价值专利集中，则可 pivot 为“数量扩散、质量集中”。

### 检验 12：小城市 HHI 噪声和权重稳健性

HHI 对小样本城市很敏感，必须做：

- 剔除 `total_patents < 10`；
- 剔除 `total_patents < 20`；
- 剔除 `total_patents < 50`；
- 按基期专利规模加权；
- winsorize HHI / share。

## 4. 暂时不要优先做的事

1. 全量申请人集团合并：太重，先做 Top 申请人；
2. 全量 A 股集团匹配：容易把题拉回上市公司旧题；
3. 合作创新网络：机制很有趣，但不是最小闭环；
4. IV：先不要强行做，坏 IV 会伤文章；
5. 过多城市异质性：容易显得为显著性服务；
6. 数字经济指数 / 政府工作报告词频：不适合作为主 X。

## 5. 推荐执行顺序

### 第 1 轮：生死检验

1. 申请年份重构；
2. 省市映射修正；
3. pre-top / new / middle 三分解；
4. 城市 FE + 年份 FE；
5. 省份 × 年份 FE；
6. 基期能力 × 年份 FE；
7. 剔除大城市；
8. 事件研究；
9. X 外部验证。

### 第 2 轮：机制检验

1. Top20 申请人导出；
2. Top 主体类型识别；
3. 基期 AC 异质性；
4. 专利类型异质性；
5. 数字 / AI / 云专利分类。

### 第 3 轮：投稿级补强

1. 更强 X：机柜数、MW、智算中心、东数西算；
2. Top 主体集团合并；
3. 高价值专利；
4. 其他数字政策 horse-race；
5. 稳健 staggered DID。

## 6. 当前最小 Go 标准

继续投入大工程前，至少需要满足：

1. 申请年份口径下，`IDC -> share_new` 为正；
2. 申请年份口径下，`IDC -> share_pre_top10` 为正；
3. `IDC -> share_middle_incumbent` 为负或不增长；
4. 省份×年份 FE 下方向不变；
5. 剔除北上广深 / Top10 城市后方向不变；
6. 事件研究没有明显预趋势；
7. IDC stock 至少能被一个外部算力 / 机房 / 智算中心指标验证。

如果这 7 条过 5 条以上，继续做。

如果只过 3-4 条，保留但降级为中文普通 CSSCI 或重写为单机制。

如果过 2 条以下，不再继续当前 framing。
