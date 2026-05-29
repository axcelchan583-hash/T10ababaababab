# T10 城市数据/算力基础设施与企业创新

本项目记录“城市数据/算力基础设施、企业创新韧性、上市公司创新相对地位”这一组选题的文献、数据构造、试跑和阶段性判断。

## 当前定位

当前不再把主线写成：

> 城市数据/算力基础设施提升企业创新韧性。

已有试跑显示，这一路线的正向主效应不稳，且创新韧性 Y 本身含有城市创新增长基准，容易与城市层面的 X 发生机械错配。

ChatGPT Pro 诊断后，当前主线曾改为：

> 城市数字/算力基础设施是否改变城市创新主体结构：创新扩散还是创新再集中？

截至 2026-05-23，第一轮低配数据不支持“上市公司创新优势被削弱”：IDC 代理口径下，城市整体创新和非 A 股近似创新增加，但 A 股上市公司合计创新响应更强，上市公司创新份额没有显著下降。因此后续不再围绕 `B/T` 或 `ln(C)-ln(B)` 硬救，而是转向全量专利申请人层面的城市创新集中度、Top 申请人份额、活跃申请人和新进入申请人。

截至 2026-05-25，进一步正式收窄为：

> 城市算力基础设施是否扩大城市创新进入边界？

当前写作口径进一步修正为：理论对象写“城市算力基础设施”，经验测度写“IDC 经营许可覆盖强度 / IDC 服务覆盖强度”。截至 2026-05-28，主识别已转为城市×技术领域 DDD，主 Y 优先放 `ln1p_new_applicants` 和 `ln1p_new_patents`，`new_applicant_share` 作为配套结构变量。HHI、Top share、中腰部挤压和企业技术领域结果都只作为结构性补充或异质性，不再作为最硬主线。

## 项目结构

- `docs/`：研究设计、变量构造、文献综述和阶段性判断。
- `docs/memos/`：每轮试跑的解释备忘录。
- `docs/literature/`：文献综述表和文献整理文件。
- `data/raw/`：本项目专属小型原始数据索引；大型原始数据仍保留在第三方资料目录，不复制进项目。
- `data/processed/`：本项目生成的中间面板和清洗数据。
- `data/external_proxy/`：外部代理数据，如 51miit IDC 许可证爬取结果。
- `results/tables/`：回归结果表。
- `results/reports/`：构建报告和数据质量报告。
- `results/logs/`：Stata 日志。
- `scripts/`：数据处理和 Stata 回归脚本。
- `chat/`：给 ChatGPT Pro / Claude / Deep Research 的 prompt。
- `notes/`：临时想法、老师反馈和待办。
- `outputs/`：兼容旧路径的软链接目录。真实文件已经归入 `data/` 和 `results/`。

## 关键文档

- [企业创新韧性 Y 构造](docs/01_innovation_resilience_y_construction_20260523.md)
- [城市算力基础设施与上市公司创新优势重塑：实验设计](docs/02_city_compute_infra_innovation_position_design_20260523.md)
- [创新韧性文献综述表](docs/literature/innovation_resilience_literature_review_T10_20260523.csv)
- [给 ChatGPT Pro 的诊断 prompt](chat/chatgpt_pro_prompt_创新相对地位诊断_20260523.md)
- [ChatGPT Pro 反馈整理](docs/memos/chatgpt_pro_feedback_digest_20260523.md)
- [全量专利申请人集中度第一轮结果](docs/memos/full_patent_applicant_concentration_first_round_20260524.md)
- [组会简报：当前设计与待判断问题](docs/design/group_meeting_brief_20260525.md)
- [新进入机制与异质性第一轮结果](docs/memos/entry_mechanism_heterogeneity_first_round_20260525.md)
- [政策 horse-race 与授权/高价值口径补充结果](docs/memos/policy_horserace_and_appyear_quality_20260526.md)
- [政策名单源头第一轮](docs/memos/policy_list_source_scan_20260527.md)
- [政策 horse-race 第一版结果](docs/memos/policy_horserace_preliminary_results_20260527.md)
- [当前结果外部评审 brief](docs/memos/current_results_external_review_brief_20260527.md)
- [审稿人防守补强第一轮：Y 清洗、X 拆分与质量口径](docs/memos/reviewer_round_y_cleaning_and_x_validation_20260528.md)
- [城市×技术领域 DDD 主效应重跑：1985 预热期口径](docs/memos/overall_tech_ddd_main_effect_20260528.md)
- [城市×技术领域 DDD 防守包：定义替换、政策交互、事件 DDD 与清洗样本](docs/memos/overall_tech_ddd_robustness_round_20260528.md)
- [给网页版深度评审的 prompt](chat/web_deep_review_prompt_current_results_20260527.md)

## 阶段性结论

### 1. 企业创新韧性主线

主 Y：

- `企业创新韧性1`：企业发明专利授权变化相对城市发明授权增长基准。
- `企业创新韧性2`：企业专利申请相对城市申请增长基准。
- `企业创新韧性3`：企业专利授权相对城市授权增长基准。
- `企业创新韧性4`：企业专利申请相对行业申请变化。

判断：

- `企业创新韧性1` 与城市层面 X 存在机械错配。
- IDC 代理、2016 大数据试验区这两类 X 对 `企业创新韧性1` 的结果多为负或不稳。
- 这一主线不宜继续硬写成正向贡献。

### 2. IDC -> 数字创新 / AI 创新

结果：

- `IDC -> 企业数字发明专利` 有一定正向信号。
- `IDC -> AI/算力相关发明专利` 有少量正向信号。

判断：

- 这一路线与 Hui Jiang (2025) Finance Research Letters 的“computing infrastructure -> corporate digital technology innovation”高度接近。
- 如果只缩小到 AI/算力创新，贡献空间反而可能更窄。

### 3. 创新相对地位 / 上市公司创新优势

现有低配分解：

```text
城市总创新 T = 城市内 A 股上市公司创新合计 B + 非 A 股/其他主体创新近似 C
```

第一轮结果：

- IDC stock 提高城市发明授权总量。
- IDC stock 提高非 A 股近似发明授权。
- 但 IDC stock 对 A 股上市公司发明授权合计的系数更大。
- `B/T` 没有显著下降。
- `ln(1+C)-ln(1+B)` 在 IDC 代理口径下显著为负。

判断：

- 低配数据不支持“上市公司创新优势被削弱”。
- 现有 Y 的切法太粗，B 是所有 A 股上市公司合计，C 混合了非上市企业、高校、科研机构、个人和口径误差。
- 该路线降级为历史试跑和反证材料，不再作为主线。

### 4. 创新主体结构：扩散还是再集中

新主线：

```text
城市数字/算力基础设施建设
-> 城市创新总量变化
-> 城市内部申请人结构变化
-> 创新扩散 / 创新再集中
```

第一轮候选 Y 包括：

- 城市专利申请人 HHI；
- Top1/Top5/Top10 申请人份额；
- 有效申请人数 `1/HHI`；
- 活跃申请人数量；
- 新进入申请人数量和份额；
- A 股上市公司在 Top 申请人中的占比，作为第二层结果。

截至 2026-05-25，城市年模型曾把 `new_applicant_share` 作为最稳主 Y；2026-05-28 城市×技术领域 DDD 修正后，主 Y 降级为数量型新进入变量优先，份额变量作为配套结构结果。

这个方向不再预设上市公司一定输。若 HHI 下降，解释为创新扩散；若 HHI 上升，解释为头部主体吸收能力更强、创新再集中。

2026-05-24 已用“中国全量专利数据库1985-2025.11”的分年份文件完成第一轮构造。结果不是单纯扩散：

- IDC 滞后存量提高发明申请/发明授权口径的城市创新总量；
- `active_applicants`、`new_applicants` 或 `new_applicant_share` 上升；
- 但 `hhi`、`top5_share`、`top10_share` 也同步上升。

第一轮曾更适合写成：

```text
城市算力基础设施是否同时促进创新进入与创新集中？
```

2026-05-25 之后进一步收窄为“城市算力基础设施是否扩大城市创新进入边界”，实证上用 IDC 服务覆盖强度测度，不再把“创新集中”作为主因果结论。

### 5. 新型数字基础设施词频指数

X 来自城市政府工作报告中 52 个新型数字基础设施关键词。

判断：

- 这个 X 更像“政府政策关注度”，不是硬件基础设施存量。
- 每万字关键词总词频在局部窗口里让非 A 股相对上市公司变正，但同时城市总创新、上市公司创新、非 A 股近似创新都显著下降。
- 熵值法和 PCA 指数没有稳定支持“上市公司份额下降”。
- 不建议作为主 X。

## 重要数据

- `data/processed/public_innovation_resilience_rebuild_stata_2000_2024.dta`：公开创新韧性数据的 Stata 复刻版。
- `data/processed/city_listed_nonlisted_patent_decomposition_full_2000_2024.csv`：城市总创新、A 股上市公司合计、非 A 股近似量。
- `data/processed/city_innovation_position_panel_2000_2024.dta`：城市创新相对地位主面板。
- `data/processed/idc_proxy_city_year_2000_2024.csv`：51miit 代理 IDC 城市-年份 X。
- `data/processed/city_innovation_position_with_ndi_textindex_2003_2024.dta`：合并政府工作报告词频指数后的城市面板。
- `data/processed/patent_applicant_concentration_city_year_2008_2024.csv`：全量专利申请人城市-年份集中度面板。
- `data/processed/idc_applicant_concentration_panel_2008_2024.dta`：合并 IDC 后的城市创新主体结构面板。

## 重要结果

- `results/tables/city_innovation_position_first_round_results_20260523.csv`：IDC 代理 X 与创新相对地位。
- `results/tables/data_infra_city_position_first_round_results_20260523.csv`：2016 大数据试验区 X 与创新相对地位。
- `results/tables/ndi_textindex_city_position_results_20260523.csv`：新型数字基础设施词频指数 X 与创新相对地位。
- `results/tables/idc_resilience_with_controls_results_20260523.csv`：IDC 代理 X 与企业创新韧性，含控制变量。
- `results/tables/data_infra_resilience_with_controls_results_20260523.csv`：大数据试验区 X 与企业创新韧性，含控制变量。
- `results/tables/idc_applicant_concentration_results_20260524.csv`：IDC 代理 X 与全量专利申请人集中度、新进入申请人。
- `results/tables/appyear_quality_robustness_results_20260526.csv`：申请年份授权/高价值口径稳健性。

## 下一步

如果继续这个选题，不建议继续换粗 X，也不建议回到 `B/T` 或 `ln(C)-ln(B)`。优先围绕“进入扩容 + 头部集中”这组结果做更细分解：

1. 城市创新集中度 / 去中心化：
   - 城市专利申请人 HHI；
   - Top1/Top5 申请人专利份额；
   - A 股上市公司是否仍占据城市 Top 申请人。
2. 企业层面相对地位：
   - 单个上市公司专利 / 城市总专利；
   - 企业在本城市创新分布中的排名或 percentile。
3. 高价值或数字创新份额：
   - A 股上市公司高价值发明专利份额；
   - 数字技术、AI、数据、云计算专利份额。
4. 使用大型专利微观数据拆分申请人类型：
   - 非上市企业；
   - 高校；
   - 科研机构；
   - 个人；
   - 新创企业。

## 已完成的全量申请人 smoke test

2026-05-24 已完成：

1. 从 20GB RAR 中流式读取 2000-2024 年全量专利数据。
2. 以 2000-2007 年作为新进入申请人预热期。
3. 输出 2008-2024 年城市-年份 HHI、Top1/Top5/Top10 share、active applicants、new applicants。
4. 合并 IDC `stock/new`。
5. 跑城市固定效应 + 年份固定效应。

第一轮结果进入 Pivot，而不是 No-Go：

- `IDC -> HHI / Top5 / Top10` 为正；
- `IDC -> active applicants / new applicants / new applicant_share` 也为正；
- 因此第一轮表面上不是“创新民主化”或“上市公司优势削弱”，而是呈现“进入扩容与创新再集中并存”。后续强固定效应和事件研究显示，真正能防守的是进入扩容，头部再集中降为结构性补充。

下一轮最重要的是识别 Top 申请人是谁，以及这种集中到底来自企业、高校/科研院所，还是 A 股集团。

## 申请年份口径与事件研究更新

2026-05-24 已进一步完成申请年份口径的小闭环：

- 从 20GB RAR 中按 `申请年份` 重构 2008-2023 年发明专利申请的城市-申请人面板；
- 构造 `HHI`、`Top10 share`、`new applicant share`、基期 Top 份额、基期中腰部既有主体份额；
- 合并 IDC stock/new；
- 用 Stata MCP 跑连续强度主回归、样本稳健性、事件研究、阈值事件、吸收能力异质性。

关键结论：

- 连续 `ln(1 + IDC_stock_{t-1})` 在 `city FE + province × year FE` 下支持“新进入份额上升、HHI/Top10 上升、基期 Top 份额上升、中腰部既有主体份额下降”；
- 剔除北上广深杭和前十创新城市后，方向基本保留；
- 但加入基期能力/基期集中度 × 年份固定效应后，集中度与杠铃化结果明显变弱；
- 用“首次 `IDC_stock > 0`”做事件研究不理想，处理后轨迹不清楚，且新进入变量有危险前趋势；
- `IDC_stock >= 5` 等阈值事件比首次出现更像有效 X，但仍不足以作为正式识别；
- 吸收能力异质性不够干净，不能直接写成“高能力城市必然头部再集中、低能力城市必然创新进入扩容”。

当前判断：**黄灯偏绿**。题可以继续，但不能马上写成强因果论文。下一步必须先补强 X，并导出 Top 申请人身份。

新增结果备忘录：

- `docs/memos/application_year_small_loop_results_20260524.md`
- `docs/memos/event_and_heterogeneity_results_20260524.md`
- `docs/memos/computing_x_data_source_assessment_20260524.md`
- `docs/memos/sun_boyue_idc_measurement_and_trial_20260524.md`
- `docs/memos/formal_idc_scope_results_20260525.md`

同时已导出第一版 Top 申请人名单：

- `data/processed/top_applicants/city_year_top20_applicants_inv_app_appyear_2008_2023.csv`
- `data/processed/top_applicants/baseline_2008_2010_top20_applicants_inv_app_appyear.csv`
- `data/processed/top_applicants/city_year_top20_type_summary_inv_app_appyear_2008_2023.csv`

## 2026-05-26 补充：政策 horse-race 与授权/高价值口径

已补申请年份质量口径：

- 发明授权按申请年份；
- 发明授权按授权公告年份；
- 发明授权且被引按申请年份；
- 发明授权且家族被引按申请年份。

核心结论：

- `new_applicant_share` 在质量口径下方向多为正，但强固定效应下不显著；
- `ln1p_new_applicants` 和 `ln1p_new_patents` 在发明授权申请年、家族被引授权申请年口径下显著为正；
- 因此可以写“新进入授权/高价值相关专利数量扩张”，但不能写“高质量新进入份额稳健提升”。

政策 horse-race 尚未正式跑出结果，因为本地没有已清洗的城市-年份政策面板。已生成模板和脚本：

- `data/external_proxy/city_policy_horserace_template_2008_2023.csv`
- `scripts/build_policy_horserace_panel.py`
- `scripts/run_policy_horserace_stata.do`

待补政策变量包括宽带中国、智慧城市、大数据综合试验区、创新型城市、国家高新区、知识产权示范城市、信息消费试点、电子商务示范城市。

2026-05-27 已进一步补出第一版政策 seed list：

- `data/external_proxy/policy_seed_lists_20260527.csv`
- `data/external_proxy/policy_source_inventory_20260527.csv`
- `data/external_proxy/city_policy_horserace_panel_2008_2023.csv`
- `results/tables/policy_horserace_results_20260527.csv`

第一版 horse-race 控制了宽带中国、大数据综合试验区、创新型城市、知识产权示范城市。结果显示：

- `new_applicant_share` 在政策控制后仍显著为正；
- 加入政策控制和基期能力趋势控制后仍边际显著为正；
- `hhi/top10_share` 在加入政策控制后不再稳。

这进一步支持当前主线应收窄为“创新进入边界扩展”，不应主打“头部再集中”。

2026-05-28 按外部审稿意见补了 Y 清洗与 X 内部验证：

- 主申请年份口径的新进入申请人预热期已从 2000 年前移到 1985 年，主 Y 均值几乎不变；
- 在省份×年份 FE + 基期能力趋势 FE 下，`new_applicant_share` 边际显著为正，`ln1p_new_applicants` 和 `ln1p_new_patents` 显著为正；
- 政策 horse-race + 基期能力趋势 FE 下，`new_applicant_share` 仍边际显著为正；
- 申请人类型拆分显示，强规格下主要来自个人申请人，企业/组织进入不稳；
- 云/计算相关 IDC 许可的结果强于非云/计算许可，可作为机制一致性证据；
- HHI 和 Top10 在强规格下不显著，不能再作为主因果结果；
- 质量口径仍是 2000 预热期补充，支持新进入授权/家族被引授权数量扩张，但不支持高质量新进入份额稳健提升。

最新写作口径相应降级为：

```text
算力服务可得性与城市专利系统进入边界。
经验测度是 IDC 经营许可覆盖强度 / IDC 服务覆盖强度。
```

详见：

- `docs/memos/reviewer_round_y_cleaning_and_x_validation_20260528.md`
- `docs/design/reviewer_round_update_20260528.md`

粗分类显示，城市-年份 Top20 申请人中的专利量约一半来自企业，约四成来自高校，说明后续机制不能只按“企业/上市公司吸收能力”写，需要单独识别高校科研型头部。

国泰安补充数据判断：

- `全国数据资源调查统计表` 只有全国年度维度，不能作为城市主 X；
- `分地区大数据发展指数表` 是省级为主、少量重点城市的大数据发展指数，不是算力基础设施；
- 当前最接近已有文献的 X 仍是 IDC 许可证路线。下一步应完整重爬/重清洗工信部或 51miit 的 IDC 许可，优先使用许可证覆盖范围城市，注册地址只作为 fallback。

## 企业层面与技术领域 DDD 更新

2026-05-25 已尝试把 Y 收窄到企业申请人。

城市-年份企业 Y 第一轮结果较弱：

- `firm_new_share_total` 不显著；
- `ln1p_new_firm_patents` 不显著；
- `ln1p_new_firm_applicants` 只在高专利量城市中边际为正；
- 企业口径事件研究没有复现全体申请人口径的清晰动态。

因此，企业 Y 不适合直接替代全体申请人的新进入份额作为主 Y。

随后进一步做了城市 × 技术领域 × 年份 DDD：

```text
Y_{c,k,t} = beta * ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_k
          + city × year FE
          + city × HighCompute FE
          + HighCompute × year FE
          + error
```

高算力领域按 IPC 主分类识别，包含 G06/G16/H04 等计算、通信、自动化、机器人、语音识别相关类别。

第一轮结果：

- 高算力技术领域的企业新进入数量和新进入企业专利数量相对上升；
- 但企业新进入份额没有上升，连续强度 DDD 中反而为负；
- 既有企业专利和企业总专利在高算力领域增长更快；
- 事件 DDD 的数量变量有处理后正信号，但前趋势不干净。

当前判断：

```text
企业层面不是完全没信号，但只能作为补充。
更稳的主线仍是“城市算力基础设施扩大整体创新进入边界”，实证上由 IDC 服务覆盖强度刻画；
企业技术领域 DDD 可用于说明高算力领域存在企业进入数量扩张，
但新增创新份额更多被既有企业/既有能力主体吸收。
```

组会讨论时的最终口径：

```text
主 Y 不换成企业。
主线改为整体申请人城市×技术领域 DDD。
企业结果放在“技术领域异质性/补充机制”：
高算力领域企业进入数量增加，但份额没有增加。
```

2026-05-28 已进一步把整体申请人城市×技术领域×年份 DDD 升级为主效应/主识别：

- 用 1985 年作为新进入申请人预热期重建 DDD 面板；
- 样本为 2008-2023 年、291 个城市、城市×高算力/低算力×年份 9294 行；
- 模型吸收 `city × year`、`city × HighCompute`、`HighCompute × year`；
- 识别来自同一城市同一年中，高算力依赖技术领域相对低算力领域的新进入变化。

主结果已按“显式常数项 + drop-first dummy”的标准固定效应实现重跑：

- `ln1p_city_new_applicants_field`：0.2184，p < 0.001；
- `ln1p_city_new_patents_field`：0.2560，p < 0.001；
- `city_new_share_total_field`：0.0310，p = 0.0270；
- 限制高专利量城市后，数量型新进入结果仍显著。

因此当前论文主线调整为：

```text
城市年回归作为背景事实；
城市×技术领域 DDD 作为主效应/主识别；
核心结论是 IDC 服务覆盖增强后，算力依赖型技术领域的新进入相对增加。
```

详见：

- `docs/memos/overall_tech_ddd_main_effect_20260528.md`
- `docs/design/ddd_main_effect_update_20260528.md`

随后已补 DDD 防守包：

- HighCompute 定义替换：数量型新进入结果在 `broad`、`no_h04`、`G06/G16/G10L`、`G06 only` 下均显著；
- 政策 × HighCompute 控制：加入宽带中国、大数据综合试验区、创新型城市、知识产权示范城市后，数量结果仍显著，份额降为边际显著；
- 剔除个人和 one-shot：数量结果仍显著，field-level entrant share 仍有支持，但 city-level entrant share 不稳；
- 事件 DDD：事件后长期数量变量转正，但远端前期显著为负，只能作为动态补充。

最新写作边界：

```text
主 Y 应优先放新进入申请人数和新进入专利数；
new applicant share 作为配套结构变量；
事件 DDD 不替代连续强度 DDD 主识别。
```

详见：

- `docs/memos/overall_tech_ddd_robustness_round_20260528.md`
- `chat/outline/08_ddd_robustness_round_20260528.md`

## 新进入机制与异质性更新

2026-05-25 已固定主 Y `new_applicant_share`，继续跑机制和异质性。

关键结果：

- 分子/分母分解支持主线：`ln1p_new_applicants` 和 `ln_new_patents` 均显著为正，既有主体专利数不显著，说明不是分母塌缩造成的新进入份额上升；
- 新进入类型拆分显示，强规格下最稳的是个人新进入份额和个人新进入申请人数；
- 企业、知识机构和组织申请人的新进入份额暂时不稳；
- 城市基础异质性中，基期创新能力、基期集中度、基期企业/知识机构/个人份额的交互项基本不显著；
- 发明申请公开口径支持主结果，全部公开口径较弱支持，发明授权公开口径为正但不显著。

当前写作口径：

```text
主线可以进入写作：城市算力基础设施扩大城市创新进入边界，IDC 服务覆盖强度是当前核心测度。
但必须承认：当前进入扩展更多体现在个人申请人，
企业/组织和授权质量口径还需要继续补强。
```

新增备忘录：

- `docs/memos/entry_mechanism_heterogeneity_first_round_20260525.md`
- `docs/memos/firm_entry_clean_first_round_20260525.md`
- `docs/memos/firm_tech_entry_ddd_first_round_20260525.md`

孙波约等中文顶刊文献确认了这一路线：其核心做法是抓取工信部电信业务经营许可证，筛选互联网数据中心业务，手工整理许可证业务覆盖范围中的机房所在地与颁发时间，加总到城市-年份层面。已按这个思路把现有 51miit 数据拆成三套 X：

- `IDC_scope_city_stock`：只用许可证覆盖范围明确出现的城市；
- `IDC_registered_city_stock`：只用注册地址/公司名推断城市；
- `IDC_combined_stock`：覆盖范围优先，缺失时用注册地址。

申请年份口径试跑显示，`IDC_scope_city_stock` 在省份×年份固定效应下仍支持新进入份额上升、Top10/HHI 上升、基期 Top 份额上升和中腰部份额下降；但加入基期能力×年份固定效应后，集中度结果变弱，主要只剩新进入更稳。

## 当前定稿口径

截至 2026-05-24，本文主 X 暂定为：

```text
城市 IDC 经营许可覆盖强度
```

主变量：

```text
ln(1 + IDC_scope_city_stock_{c,t-1})
```

其中，`IDC_scope_city_stock` 只使用许可证业务覆盖范围中明确出现的互联网数据中心业务机房所在地城市，并按城市-年份累计。这个口径最接近孙波约等中文顶刊文献。

降级变量：

- `IDC_registered_city_stock`：注册地址推断城市，只作稳健性；
- `IDC_combined_stock`：覆盖范围优先、注册地址 fallback，只作稳健性；
- 国泰安全国算力规模、大数据发展指数：只作背景或控制，不作主 X。

当前主叙事不再是“企业创新韧性”或“上市公司创新优势削弱”，而是：

```text
城市算力基础设施是否扩大城市创新进入边界。
经验测度为城市 IDC 经营许可覆盖强度。
```

头部再集中和中腰部挤压只作为第二层结构性补充，不作为主因果结论。

## 2026-05-25 正式 IDC_scope 结果

已用主 X `ln(1 + IDC_scope_city_stock_{c,t-1})` 重跑正式主表、X 稳健性、样本稳健性和事件研究。

这部分是城市年层面的阶段性结果，现作为背景事实和补充，不再作为最硬主识别。关键结论：

- 最稳的是 **新进入申请人份额上升**。`new_applicant_share` 在城市+年份 FE、省份×年份 FE、基期能力×年份 FE、城市趋势四类规格下均显著为正；
- `ln1p_new_applicants` 在强规格和城市趋势下为正；
- `hhi/top10/base_top` 在省份×年份 FE 下为正，但加入基期能力/集中度×年份 FE 后消失；
- `base_mid_inc_share` 在省份×年份 FE 下显著为负，但强规格下不稳；
- 剔除北上广深杭、前十创新城市后，省份×年份 FE 下方向仍基本保留；
- 限制高专利量城市后，集中度变弱，但新进入份额和中腰部下降仍更稳；
- 事件研究比旧混合口径干净，`scope >= 2/3` 更支持新进入份额上升和中腰部下降，但 HHI/Top10 动态不强。

当前更稳的写法：

```text
城市算力基础设施提升扩大了城市创新生态的进入边界；
实证上由 IDC 经营许可覆盖强度刻画；
同时在常规固定效应下呈现头部再集中和中腰部挤压迹象，
但再集中结果对基期能力趋势较敏感，应作为第二层结构发现，而不是最硬因果主结论。
```

Top20 粗分类探索显示，当前不能直接写成“企业/上市公司头部吸收”。在省份×年份 FE 下，Top20 中个人申请人份额上升，企业和高校份额没有上升；强规格下类型结果基本消失。这说明后续必须清洗 Top 申请人身份，并在高专利量城市、发明授权或高价值专利中重做类型分解。

## 2026-05-25 尾部合并事件研究

已新增尾部合并版事件研究：

- 脚本：`scripts/run_idc_scope_event_study_binned_stata.do`
- 结果长表：`results/tables/idc_scope_event_study_binned_20260525.csv`
- 诊断表：`results/tables/idc_scope_event_study_binned_summary_20260525.csv`
- 备忘录：`docs/memos/idc_scope_event_study_binned_memo_20260525.md`
- 图：`results/figures/idc_scope_event_study_binned_scope_ge_2_provyr_baseyr_fe.svg`

设置：

- 事件定义为城市 IDC 覆盖范围存量首次达到 `>=1/2/3/5`；
- 事件窗口为 `<=-4, -3, -2, -1, 0, +1, +2, +3, >=+4`，以 `-1` 为遗漏基准期；
- 处理城市为首次达到阈值年份在 2012-2020 年的城市；
- 主规格为城市固定效应 + 省份×年份固定效应，以及再加入基期专利规模分组×年份和基期 Top10 分组×年份固定效应。

当前判断：

- 最能看的事件定义是 `scope >= 2`；
- 在强固定效应下，`scope >= 2` 的前趋势干净，`new_applicant_share` 在事件后 +1、+2 年显著为正；
- `ln1p_new_applicants` 在 `scope >= 2` 下为正，但显著性弱于 `new_applicant_share`；
- `HHI`、`Top10`、`base_top_share` 的事件动态不稳定；
- `base_mid_inc_share` 有下降方向，但强规格下不够硬。

因此，事件研究可以支持“IDC 扩张扩大创新进入边界”，但暂时不能支持“IDC 明确导致头部再集中”的强因果结论。

## 2026-05-25 Top 类型清洗与组织申请人口径

已新增 Top 申请人类型清洗和组织申请人口径检验：

- 备忘录：`docs/memos/top_applicant_type_clean_and_org_only_20260525.md`
- Top 类型面板：`data/processed/top_applicant_type_clean_panel_2008_2023.csv`
- 组织申请人口径面板：`data/processed/org_applicant_concentration_clean_panel_2008_2023.csv`
- Top 类型结果：`results/tables/top_applicant_type_clean_idc_scope_results_20260525.csv`
- 组织申请人口径结果：`results/tables/org_applicant_concentration_clean_idc_scope_results_20260525.csv`

关键结论：

- Top20 专利量中，企业和高校/学校是主要头部主体，但 IDC 并没有稳定提高企业或高校/科研头部份额；
- 当年 Top20 中，个人申请人份额在普通省份×年份 FE 下上升，但强固定效应下不稳；
- 基期 Top20 追踪结果中，基期企业和高校/科研头部份额没有稳健上升；
- 剔除个人后，组织申请人 HHI/Top10 只在普通省份×年份 FE 下为正，强固定效应下消失；
- 组织专利占城市总专利的比例反而有下降迹象。

因此，当前不能再写“IDC 强化企业/高校/上市公司头部吸收能力”。更稳的论文口径应进一步收窄为：

```text
城市算力基础设施提升扩大创新进入边界；
实证测度为 IDC 服务覆盖强度；
头部再集中只作为常规固定效应下的结构性迹象，
不能作为强因果主结论。
```

## 2026-05-25 AJG3 升级检验第一轮

已按外部评审意见补一轮最小升级检验：

- 脚本：`scripts/build_overall_tech_entry_ddd_panel.py`
- 脚本：`scripts/run_ajg3_minimal_upgrade_stata.do`
- 脚本：`scripts/run_idc_scope_modern_did_stata.do`
- 结果：`results/tables/ajg3_minimal_upgrade_results_20260525.csv`
- 结果：`results/tables/idc_scope_modern_did_20260525.csv`
- 备忘录：`docs/memos/ajg3_minimal_upgrade_round_results_20260525.md`

关键更新：

- `scope >= 2` 的现代 DID 支持主结果。Borusyak-Jaravel-Spiess 和 Callaway-Sant'Anna 均显示事件后 +1 至 +4 年 `new_applicant_share` 显著上升，处理前三期不显著；
- BJS 规格中，`new_applicant_share` 前趋势联合检验 `p = 0.762`；
- `ln1p_new_applicants` 与 `ln1p_new_patents` 在两套现代 DID 中也显示事件后上升；
- 整体申请人城市 × 高算力技术领域 × 年份 DDD 显示，高算力领域的新进入申请人数、新进入专利数和新进入份额相对上升；
- 低算力领域单独回归也为正，因此不能写“IDC 只影响高算力领域”，更准确是“普遍扩容 + 高算力领域额外增强”；
- 时间安慰剂通过：未来 3 年、5 年 IDC 覆盖对主 Y 和分子变量均不显著；
- 组织申请人和发明授权口径仍不稳，不能升级成“企业/组织/高质量创新进入”。

当前主线因此从“黄灯偏绿”上调为：

```text
可以继续写，且主结果已经具备比普通 OLS+FE 更强的动态识别支撑。
但冲中文顶刊/AJG3 仍必须补政策 horse-race 和高价值专利质量口径。
```

## 兼容说明

早期脚本和备忘录大量引用 `outputs/`。现在 `outputs/` 保留为软链接兼容目录，真实文件分别位于：

- `data/processed/`
- `data/external_proxy/`
- `results/tables/`
- `results/reports/`
- `results/logs/`

新写脚本时优先使用新目录，不再往 `outputs/` 写新文件。
