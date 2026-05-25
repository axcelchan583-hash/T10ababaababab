# 企业 × 高算力技术领域 DDD 第一轮结果

日期：2026-05-25  
问题：城市年颗粒太粗以后，企业 Y 是否可以通过“城市 × 技术领域 × 年份”细分来救？

## 1. 本轮设计

把每个城市-年份拆成两类技术领域：

```text
高算力依赖技术领域 vs 其他技术领域
```

高算力领域第一版按 IPC 主分类识别：

```text
G06, G16, H04B/H04L/H04M/H04N/H04W, G05B, B25J, G10L 等
```

企业申请人沿用清洗规则：公司、集团、厂、合作社、银行、保险、证券、事务所、农场、矿等市场主体。

核心 DDD：

```text
Y_{c,k,t} = beta * ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_k
          + city × year FE
          + city × HighCompute FE
          + HighCompute × year FE
          + error
```

解释：同一城市同一年内，IDC 覆盖提高后，高算力技术领域的企业进入是否比其他技术领域增长更多。

## 2. 新增文件

脚本：

- `scripts/build_firm_tech_entry_ddd_panel.py`
- `scripts/run_firm_tech_entry_ddd_stata.do`
- `scripts/run_firm_tech_entry_ddd_event_stata.do`

数据：

- `data/processed/firm_tech_entry_ddd_panel_2008_2023.csv`
- `data/processed/firm_tech_entry_ddd_panel_2008_2023.dta`

结果：

- `results/tables/firm_tech_entry_ddd_results_20260525.csv`
- `results/tables/firm_tech_entry_ddd_event_results_20260525.csv`
- `results/reports/firm_tech_entry_ddd_build_report_2008_2023.csv`

## 3. 样本

正式样本：

- 291 个城市；
- 2008-2023 年；
- 每个城市-年份两格：高算力领域、其他领域；
- 共 9,294 个城市-技术领域-年份观测。

专利处理：

- 使用发明申请；
- 按申请年份归年；
- 从 2000 年开始作为新进入预热期；
- 扫描 2000-2025 年公开文件，以尽量补足 2023 申请年的公开滞后。

## 4. 连续强度 DDD 结果

核心 X：

```text
ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_k
```

在吸收 `city × year`、`city × HighCompute`、`HighCompute × year` 后：

### 4.1 企业进入数量

正向且显著：

- `ln_city_new_firm_n_f`：0.379，p < 0.01；
- `ln_city_new_firm_pat_f`：0.415，p < 0.01；
- `ln_field_new_firm_n_f`：0.324，p < 0.01；
- `ln_field_new_firm_pat_f`：0.338，p < 0.01。

含义：

```text
IDC 覆盖提高后，高算力技术领域相对其他领域出现更多企业新进入数量和新进入企业专利数量。
```

该方向在 `total_patents >= 20` 和 `total_patents >= 50` 样本中仍为正。

### 4.2 企业进入份额

份额变量为负：

- `city_new_share_tot_f`：-0.033，p < 0.01；
- `city_new_share_firm_f`：-0.115，p < 0.01；
- `field_new_share_tot_f`：-0.053，p < 0.01；
- `field_new_share_firm_f`：-0.159，p < 0.01。

含义：

```text
高算力领域的企业新进入数量确实增加，
但既有企业或整体高算力领域专利增长更快，
所以新进入企业的份额反而下降。
```

### 4.3 既有企业与总量

正向且显著：

- `ln_firm_pat_f`：0.341，p < 0.01；
- `ln_firm_inc_pat_f`：0.523，p < 0.01；
- `ln_firm_act_f`：0.329，p < 0.01；
- `ln_tot_pat_f`：0.166，p < 0.01。

这解释了为什么“数量进入”与“份额下降”可以同时发生：

```text
高算力领域内，既有企业增长更快，新进入企业虽然变多，但没有拿到更高份额。
```

## 5. 事件 DDD 结果

事件定义：

```text
IDC_scope_stock 首次达到 >= 2 或 >= 5
```

事件变量与 `HighCompute` 交互，并继续吸收：

- `city × year FE`；
- `city × HighCompute FE`；
- `HighCompute × year FE`。

### 5.1 `scope >= 2`

处理城市：66 个。

数量变量处理后长期窗口为正，但前趋势不干净：

- `ln_city_new_firm_n_f`：+4 期为正，p < 0.01；
- `ln_city_new_firm_pat_f`：+3 / +4 期为正；
- 但 pretrend joint test 的 p 值极小。

份额变量：

- 处理后不支持份额上升；
- 企业内部份额在 +2 / +4 期反而为负；
- 部分份额变量前趋势相对好，但没有正向处理效应。

### 5.2 `scope >= 5`

处理城市：32 个。

数量变量在 +2 期后较明显为正：

- `ln_city_new_firm_n_f`：+2、+3、+4 期为正；
- `ln_field_new_firm_n_f`：+2、+3、+4 期为正。

但问题是：

- 处理城市少；
- 多个数量变量仍有明显前趋势；
- 专利数量份额没有转正。

## 6. 阶段性判断

企业 Y 不是完全没戏，但不能写成：

```text
IDC 扩张提高企业新进入份额。
```

更准确的是：

```text
IDC 服务覆盖提高后，高算力技术领域相对其他领域出现企业进入数量扩张；
但高算力领域内既有企业扩张更快，新进入企业份额并未上升，甚至下降。
```

这与目前主线兼容：

```text
算力服务可得性扩大创新进入边界，但其创新增量仍更多被既有企业/既有能力主体吸收。
```

## 7. 对题目的含义

如果继续把主 Y 只放在企业层面，当前证据不足。

更稳的写法是：

1. 主文仍以全体申请人的新进入份额作为进入边界证据；
2. 企业层面作为技术领域 DDD 扩展：
   - 企业新进入数量在高算力领域更强；
   - 但企业新进入份额不升，说明企业内部仍存在既有主体吸收优势；
3. 不再把“企业新进入份额”作为主结论。

## 8. 下一步

如果要继续企业层面，需要做三件事：

1. 把高算力领域从二分改成更细的 IPC/CPC 技术组，避免只有两类技术导致解释过粗；
2. 按企业年龄、上市/非上市、民营/国企、基期专利能力分组，看新进入数量是否来自真正小企业；
3. 在事件 DDD 中处理前趋势问题：更换阈值、缩窄处理组、或改用连续强度为主并把事件研究降级为描述。

当前 verdict：

```text
企业层面可以做补充，不适合替代全体申请人进入边界作为主 Y。
```
