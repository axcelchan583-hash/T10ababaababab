# 冲 AJG3 的补充实验设计

日期：2026-05-25
对应主线：城市 IDC 算力服务覆盖与城市创新进入边界扩展
当前主 X：`ln(1 + IDC_scope_city_stock_{c,t-1})`
当前主 Y：`new_applicant_share`

本文档只回答一件事：

```text
如果目标是 AJG 3 星（Research Policy / JEBO / SBE / RDE / WD 这一档），
现有的"FE + 阈值事件研究 + 类型/质量稳健性"还差什么？
按"必须补"和"加分项"两层列出补充实验。
```

不重复组会简报和已有 memo 已经覆盖的内容，只列出额外要做的事。

---

## 0. 当前差距诊断

AJG 3 期刊的审稿底线，按 2023 年后的实际过稿标准：

```text
1. 识别策略不能只是 TWFE 事件研究，必须有现代 staggered DiD 估计量或 IV/RDD/外生冲击；
2. 主结果必须能挡掉至少 3-4 类替代解释（其他政策、其他基础设施、需求侧、人口流入）；
3. 机制必须有可观测的中介变量，不能只在 reduced form 层面讲故事；
4. 异质性必须有理论锚，不能只是分组跑回归；
5. 政策含义必须能映射到 USD 价值或可测量的福利量纲，不能只说"促进了创新"。
```

当前项目按这五条评分：

| 维度 | 当前位置 | AJG3 底线 | 差距 |
|---|---|---|---|
| 识别 | TWFE + 阈值事件研究 | CS-DID/Borusyak + 外生冲击 IV | 大 |
| 替代解释 | 未做政策 horse-race | 至少 4 个政策 horse-race | 大 |
| 机制 | 只有 reduced form 分解 | 至少 1 个直接中介变量 | 大 |
| 异质性 | 基期能力/集中度，无理论锚 | 理论锚 + 至少 2 维异质性 | 中 |
| 政策含义 | 含糊"扩大进入边界" | 福利或经济价值估算 | 中 |
| 数据规模 | 291 城市 × 16 年 | 充足 | 无 |
| 主 Y 学理 | 份额变量，无主流理论引用 | 锚到 entrant-incumbent 框架 | 中 |

下面按"必须补"和"加分项"逐条列出补充实验。

---

## 1. 必须补：识别策略升级

### 1.1 现代 staggered DiD 估计量

现有事件研究是 TWFE，处理时点交错的情况下系数有 negative weighting bias。AJG3 第一轮一定会被打回。

补充实验：

```text
对"首次 IDC_scope_stock >= 2"事件，分别用下列估计量重跑事件研究：

1. Callaway-Sant'Anna (2021)：csdid 包，以 never-treated 为控制；
2. de Chaisemartin-D'Haultfœuille (2020)：did_multiplegt_dyn 包；
3. Borusyak-Jaravel-Spiess (2024)：did_imputation 包；
4. Sun-Abraham (2021)：eventstudyinteract 包，作为半参基线。

报告对比表：TWFE vs 上述 4 个估计量，前后 3 期事件系数和前趋势 p 值。
如果四个估计量方向一致，正文用 CS-DID，附录放对比表。
```

主结果一旦在 CS-DID 下仍显著，AJG3 的识别底线就过了。

新增脚本：

- `scripts/run_idc_scope_event_study_modern_did_stata.do`
- 输出：`results/tables/idc_scope_event_study_modern_did_comparison_20260526.csv`

### 1.2 工具变量或外生冲击

事件研究本身不是因果识别，只是动态描述。AJG3 还要求至少一个外生冲击或 IV。可选三条，按可行性排序：

**选项 A（最可行）：地理 IV—海底光缆登陆点 / 国家骨干网节点距离**

```text
Z_c = 1 / 距离(城市 c, 最近的国家级骨干网汇聚节点)
或   = 1 / 距离(城市 c, 最近的海底光缆登陆点)

逻辑：IDC 必须接入骨干网才有商业价值，骨干网节点是 1990s 末期工信部规划，
与 2008 年后城市创新进入边界几乎无直接关联。
Bartik 风格交互：Z_c × 全国 IDC 牌照发放浪潮_t。
```

**选项 B：工信部牌照政策窗口**

```text
工信部 2013-2014、2018 两次 IDC 业务许可政策调整，
可作为时间维度的外生冲击。
拿到具体政策发布日期，做事件窗口 ±1 年的 DiD：
高暴露城市 vs 低暴露城市在政策窗口前后的对比。
```

**选项 C（次选）：电力价格 / 用电成本工具变量**

```text
IDC 选址对电价敏感（西部、内蒙、贵州的算力枢纽就是这个原因）。
用历史工业电价（1990s 末期、2000 年代初）作为 IDC 选址的外生冲击。
但创新对电价也可能直接敏感，排他性受质疑，列为最后备选。
```

推荐主用 A，备 B。新增脚本：

- `scripts/build_backbone_node_distance_iv.py`
- `scripts/run_iv_idc_scope_new_applicant_share_stata.do`
- 输出：`results/tables/iv_idc_new_applicant_share_20260526.csv`

### 1.3 安慰剂检验

AJG3 现在标配。补两类：

```text
1. 时间安慰剂：把 IDC_scope_stock 时间平移 -5 年（提前发放），重跑主回归。
   预期：系数应不显著或显著为负。
2. Y 安慰剂：用与算力无关的传统创新 Y，比如纺织/食品/服装相关 IPC 的新进入份额。
   预期：系数应不显著。
```

新增脚本：

- `scripts/run_placebo_time_y_stata.do`
- 输出：`results/tables/placebo_idc_new_applicant_share_20260526.csv`

---

## 2. 必须补：替代解释排除

### 2.1 政策 horse-race（已在 README 列出，必须真跑）

把以下政策的城市-年份处理变量同时放入主回归：

```text
- 宽带中国（2014）；
- 智慧城市试点（2012-2015，三批）；
- 大数据综合试验区（2016-2017）；
- 国家新一代 AI 创新发展试验区（2019-2021）；
- 创新型城市（2008-）；
- 高新区扩区/新批；
- 知识产权示范城市；
- 国家算力枢纽节点（2021-2022，作为后期排除变量）。
```

模型：

```text
new_applicant_share_{c,t} = beta * ln(1 + IDC_scope_stock_{c,t-1})
                         + sum_p gamma_p * Policy_{p,c,t}
                         + city FE + prov × year FE
                         + e
```

如果 beta 在加入所有政策控制后仍显著，主线挡得住。

新增脚本：

- `scripts/build_city_policy_horserace_panel.py`
- `scripts/run_idc_scope_policy_horserace_stata.do`
- 输出：`results/tables/idc_policy_horserace_20260526.csv`

### 2.2 其他基础设施控制

读者会怀疑 IDC 只是和其他基础设施同向增长。补：

```text
- 高铁开通；
- 5G 基站数（2019-）；
- 移动宽带渗透率；
- 互联网宽带接入用户数；
- 城市电力装机容量。
```

把这些加入主回归作为时变控制，主系数应保持显著。

### 2.3 需求侧 / 人口流入控制

可能的混淆：算力扩张吸引人口流入 → 个人申请人增加。补：

```text
- 城市年末常住人口；
- 城市新增市场主体注册数；
- 城市高校在校生数；
- 城市规模以上工业企业数。
```

最关键：如果加入人口控制后，个人新进入系数大幅下降而组织新进入不变，可以反过来说"IDC 通过吸引人才促进创新参与"，这是机制而不是混淆。

新增脚本：

- `scripts/build_demand_side_controls_panel.py`
- `scripts/run_idc_scope_demand_controls_stata.do`
- 输出：`results/tables/idc_demand_controls_20260526.csv`

---

## 3. 必须补：机制中介

当前主线写"算力降低创新参与门槛"是叙事，没有可观测的中介。AJG3 至少要 1 个直接证据。

按数据可得性排序的候选中介：

### 3.1 城市公有云使用强度（最优但难拿）

```text
M_{c,t} = 城市公有云用户数 / 城市企业总数
       或 = 城市企业上云比例

数据来源候选：
- 阿里云、腾讯云的开发者地理分布（公开 API 或行业报告）；
- 工信部"企业上云"专项数据；
- 中国信通院《云计算白皮书》分省/分城市数据；
- 国家工业互联网平台用户数据。

中介回归：
IDC -> M -> new_applicant_share
报告间接效应 Sobel / bootstrap CI。
```

如果拿不到城市级，用省级降级。

### 3.2 城市数字服务/互联网企业新注册数

```text
M_{c,t} = 城市当年新注册互联网/软件/信息服务业企业数
       （工商注册数据按行业代码筛 I 大类、F 大类的子类）

逻辑：IDC 覆盖增强 → 数字服务供给增加 → 创新参与门槛下降 → 新进入增加。

数据来源：
- 启信宝、企查查的工商注册数据；
- 国家市场监督管理总局公开数据。
```

这条比公有云更可行，强烈推荐做。

新增脚本：

- `scripts/build_digital_service_registration_panel.py`
- `scripts/run_idc_digital_service_mechanism_stata.do`

### 3.3 城市风险投资活跃度

```text
M_{c,t} = 城市当年 VC/PE 投资笔数（早期轮次）
       或 = 城市当年早期投资金额

逻辑：IDC 降低初创门槛 → 早期投资活跃 → 新申请人进入。

数据来源：CVSource、清科、IT 桔子城市层面数据。
```

### 3.4 城市数字技术专利的知识扩散

```text
M_{c,t} = 城市内已有数字技术专利对新进入申请人的被引次数
       或 = 城市数字技术专利的本地引用比例

逻辑：IDC 平台增加了既有知识的可获取性 → 新进入者更容易站在巨人肩膀上。

数据来源：你已有的全量专利数据 + 引文数据库。
```

---

## 4. 必须补：异质性的理论锚

当前异质性是按基期能力/集中度分组，没有理论锚。AJG3 要求：

```text
异质性必须能回答"为什么是这个维度，理论上预期方向是什么"。
```

补两组：

### 4.1 城市初始数字技能存量 × IDC

```text
理论锚：Acemoglu-Restrepo (2022) 技术-技能互补框架。
预测：高数字技能城市，IDC 对新进入的吸纳效应更弱（既有主体已经能用算力），
     低数字技能城市，IDC 对新进入的吸纳效应更强（突破了原有技能瓶颈）。

异质性变量：
- 基期城市计算机/软件相关本科及以上人口比例（普查数据）；
- 基期城市信息传输/软件/信息技术服务业从业人员占比。
```

### 4.2 城市基期创新参与不平等 × IDC

```text
理论锚：Bell-Chetty-Jaravel-Petkova-Van Reenen (2019) Lost Einsteins。
预测：基期创新参与高度集中的城市（少数主体垄断专利），
     IDC 带来的进入扩张效应应更强（解锁了被排除的潜在创新者）。

异质性变量：
- 基期城市发明人 HHI；
- 基期城市发明人户籍 vs 非户籍比例；
- 基期城市百万人口发明人数低于全国中位数（dummy）。
```

把"个人新进入主导"的现象，包装成 lost Einsteins 框架的实证证据，这是把弱点翻成卖点的关键。

新增脚本：

- `scripts/build_theory_anchored_heterogeneity_panel.py`
- `scripts/run_lost_einsteins_heterogeneity_stata.do`

---

## 5. 必须补：质量稳健性（命门）

第 1 题里已经讲过，这里只列具体实验：

### 5.1 剔除个人申请人的组织新进入

```text
new_org_applicant_share_{c,t} = 仅组织申请人中新进入者的专利数 / 组织申请人总专利数
```

主回归 + 事件研究，必须做。

### 5.2 高价值发明专利新进入

```text
high_value_invention_new_share_{c,t} 定义为以下任一标准下的新进入份额：

- 维持年限 >= 6 年的发明专利；
- 5 年内被引 >= 1 次的发明专利；
- 同族 >= 2 的发明专利；
- 授权时长 < 3 年的发明专利（快速授权代理质量）。
```

### 5.3 数字 / AI / 算力相关 IPC 的新进入

```text
limit 到 G06、G16、H04、B25J、G10L 等高算力相关 IPC，重跑主回归。
预期：在算力相关领域，新进入效应更强；在传统领域，效应弱或消失。
```

这同时是异质性也是质量稳健性。

新增脚本：

- `scripts/build_quality_filtered_new_entry_panel.py`
- `scripts/run_quality_filtered_main_stata.do`
- 输出：`results/tables/quality_filtered_new_entry_20260526.csv`

---

## 6. 必须补：政策含义量化

AJG3 不接受"促进了创新进入边界扩展"这种含糊表述。需要至少一个量纲化的政策含义。

候选量化口径：

```text
1. 每增加 1 单位 IDC_scope_stock，对应多少个新进入申请人 / 新增多少专利；
2. 把这些新增专利按平均维持年限和经济价值（Kogan et al. 2017 / 国内类似工作）折算为 RMB；
3. 反推 IDC 牌照发放的隐含创新弹性，与已有的"宽带中国—创新"弹性对比；
4. 用样本期前后差异估算反事实：如果 IDC 覆盖维持 2008 年水平，
   2023 年新进入申请人会少多少。
```

新增 1 张表 `results/tables/policy_implications_magnitude_20260526.csv`。

---

## 7. 加分项：让审稿人记住

### 7.1 LLM/生成式 AI 时代的算力溢价

```text
分子样本：2018-2023 vs 2008-2017
检验 IDC 效应是否在 2018 年后显著放大。
预期：是。这给文章贴上"AI 时代政策含义"的标签。
```

### 7.2 与全球文献对话

```text
拉一组国际可比数据：
- 美国 FCC broadband data + USPTO 申请人新进入；
- 欧盟 EPO 申请人新进入 + ENISA broadband data；
做一个 5 年子样本对比，证明结论不是中国特殊。
（如果做不到，至少在文献综述里讨论 Goldfarb-Tucker、Andrews-Nicoletti-Timiliotis 那条线。）
```

这条不是必须，但 AJG3 现在很吃"全球比较视角"。

### 7.3 网络外溢效应

```text
Y_{c,t} = beta1 * IDC_{c,t-1} + beta2 * sum_{c' != c} w_{c,c'} * IDC_{c',t-1} + ...

w_{c,c'}：城市间地理距离倒数，或城市间专利合作强度。
预期：beta2 显著为正说明算力外溢。
```

这是"城市间溢出"标准做法，做了就在方法贡献上加一分。

---

## 8. 实施优先级

按"必须做才能投 AJG3"和"做了能加分"分层：

### 第一优先（不做就不能投 AJG3）

```text
[识别]    1.1 CS-DID / Borusyak 重跑事件研究
[识别]    1.2 选项 A 地理 IV
[识别]    1.3 双安慰剂检验
[替代]    2.1 政策 horse-race（至少 5 个政策）
[替代]    2.2 其他基础设施控制
[机制]    3.2 数字服务企业新注册数中介
[质量]    5.1 剔除个人后的组织新进入
[质量]    5.2 高价值发明专利新进入
[政策]    6   政策含义量化
```

按这九项做完，目标期刊画一条线：

- **稳冲**：Research Policy（borderline）、Economics of Innovation and New Technology、Information Economics and Policy、Telecommunications Policy（AJG3 边缘）；
- **够呛**：JEBO、Small Business Economics、Regional Studies；
- **天花板**：AJG3 顶部。

### 第二优先（做了上限再抬一档）

```text
[识别]    1.2 选项 B 工信部政策窗口 DiD
[替代]    2.3 需求侧/人口流入控制
[机制]    3.1 公有云使用强度（如能拿到数据）
[机制]    3.3 风险投资活跃度
[机制]    3.4 知识扩散中介
[异质]    4.1 数字技能 × IDC（Acemoglu-Restrepo 锚）
[异质]    4.2 Lost Einsteins 异质性
[质量]    5.3 数字/AI/算力 IPC 限定子样本
```

按这八项做完：

- **稳冲**：Research Policy、JEBO、Regional Studies；
- **够呛**：World Development、Journal of Urban Economics；
- **天花板**：摸到 AJG4 边缘（视故事完整性）。

### 第三优先（讲故事加分）

```text
[加分]    7.1 LLM 时代子样本
[加分]    7.2 全球文献对话子样本
[加分]    7.3 网络外溢
```

---

## 9. 数据获取分项清单

下面列出本设计需要补但本项目尚未具备的数据。按获取难度分。

### 容易（开放或公开 API）

```text
- 国家骨干网节点 / 海底光缆登陆点地理坐标（公开学术资料 + 工信部公告）；
- 工信部 IDC 业务许可政策发布日期（工信部公告）；
- 历史工业电价（中经网、wind）；
- 高铁开通时点（已有公开数据库）；
- 创新型城市/智慧城市/宽带中国/大数据综合试验区时点（公开政策文件）；
- 国家算力枢纽节点时点（国家发改委 2021-2022 公告）。
```

### 中等（需要购买或申请）

```text
- 工商注册新增企业按行业（启信宝/企查查 API、付费）；
- VC/PE 投资笔数（清科/IT 桔子，付费或申请）；
- 城市常住人口 / 高校在校生（中经网，付费）；
- 国家数据资源调查统计表（国泰安已有但是全国维度，城市维度需另购）。
```

### 难（可能拿不到）

```text
- 城市公有云用户数 / 上云比例（阿里云/腾讯云不公开）；
- 工信部 IDC 实际机柜数 / MW 数据（保密）；
- 5G 基站城市分布历年数据（部分省份公开，全国不全）。
```

数据策略：

```text
1. 先把"容易"全做完，覆盖第一优先；
2. 中等优先做工商注册数据（机制 3.2）和 VC 数据（机制 3.3）；
3. 难的不强求，能拿一两个就在正文写，拿不到放讨论部分坦白。
```

---

## 10. 一句话总结

```text
冲 AJG3 不在于换主线，而在于：
- 把当前 reduced form 升级成 CS-DID + 地理 IV；
- 把"个人申请人"从瑕疵翻成 Lost Einsteins 卖点；
- 用数字服务企业注册数和 VC 活跃度作为中介把机制坐实；
- 把"扩大进入边界"量化为可比的弹性和反事实。

这五件事做完，主线不动，论文就从中文 B 类直接抬到 AJG3 区间。
```

---

## 附：本轮新增脚本与输出清单

```text
scripts/
  run_idc_scope_event_study_modern_did_stata.do        # 1.1 现代 DiD
  build_backbone_node_distance_iv.py                   # 1.2 地理 IV 构造
  run_iv_idc_scope_new_applicant_share_stata.do        # 1.2 IV 主回归
  run_placebo_time_y_stata.do                          # 1.3 安慰剂
  build_city_policy_horserace_panel.py                 # 2.1 政策 horse-race 面板
  run_idc_scope_policy_horserace_stata.do              # 2.1 horse-race 回归
  build_other_infra_controls_panel.py                  # 2.2 其他基础设施
  run_idc_scope_other_infra_stata.do                   # 2.2 其他基础设施回归
  build_demand_side_controls_panel.py                  # 2.3 需求侧
  run_idc_scope_demand_controls_stata.do               # 2.3 需求侧回归
  build_digital_service_registration_panel.py          # 3.2 中介构造
  run_idc_digital_service_mechanism_stata.do           # 3.2 中介回归
  build_vc_activity_panel.py                           # 3.3 VC 中介
  run_idc_vc_mechanism_stata.do                        # 3.3 VC 回归
  build_theory_anchored_heterogeneity_panel.py         # 4.x 异质性面板
  run_lost_einsteins_heterogeneity_stata.do            # 4.2 Lost Einsteins
  run_skill_complementarity_heterogeneity_stata.do     # 4.1 技能互补
  build_quality_filtered_new_entry_panel.py            # 5.x 质量面板
  run_quality_filtered_main_stata.do                   # 5.1-5.2 质量稳健性
  run_digital_ai_ipc_subsample_stata.do                # 5.3 数字 IPC 子样本
  compute_policy_implications_magnitude.py             # 6   政策含义量化
  run_post_2018_llm_era_subsample_stata.do             # 7.1 LLM 时代
  build_spatial_spillover_panel.py                     # 7.3 空间外溢
  run_spatial_spillover_stata.do                       # 7.3 空间回归

results/tables/
  idc_scope_event_study_modern_did_comparison_20260526.csv
  iv_idc_new_applicant_share_20260526.csv
  placebo_idc_new_applicant_share_20260526.csv
  idc_policy_horserace_20260526.csv
  idc_other_infra_controls_20260526.csv
  idc_demand_controls_20260526.csv
  idc_digital_service_mechanism_20260526.csv
  idc_vc_mechanism_20260526.csv
  lost_einsteins_heterogeneity_20260526.csv
  skill_complementarity_heterogeneity_20260526.csv
  quality_filtered_new_entry_20260526.csv
  digital_ai_ipc_subsample_20260526.csv
  policy_implications_magnitude_20260526.csv
  post_2018_llm_era_subsample_20260526.csv
  spatial_spillover_20260526.csv

docs/memos/
  ajg3_upgrade_round_results_20260526.md   # 跑完一轮后写
```
