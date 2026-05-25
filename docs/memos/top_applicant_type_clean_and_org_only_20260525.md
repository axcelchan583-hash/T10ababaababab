# Top 申请人类型清洗与组织申请人口径检验

日期：2026-05-25  
主 X：`ln(1 + IDC_scope_city_stock_{c,t-1})`  
口径：发明专利申请，申请年份归年，2008-2023 年  

## 1. 本轮目的

上一轮结果显示，IDC 与 `HHI/Top10/base_top_share` 在常规固定效应下为正，但强固定效应和事件研究下不稳。

本轮检验两个问题：

1. Top 申请人到底是企业、高校/学校、科研机构、医院、个人还是政府/其他？
2. 如果剔除个人申请人，组织申请人的 HHI、Top10 和新进入是否仍支持“头部再集中”？

## 2. 新增文件

脚本：

- `scripts/build_top_applicant_type_clean_panel.py`
- `scripts/run_top_applicant_type_clean_idc_scope_stata.do`
- `scripts/build_org_applicant_concentration_clean_panel.py`
- `scripts/run_org_applicant_concentration_clean_idc_scope_stata.do`

数据：

- `data/processed/top_applicant_type_clean_panel_2008_2023.csv`
- `data/processed/top_applicant_type_clean_panel_2008_2023.dta`
- `data/processed/org_applicant_concentration_clean_panel_2008_2023.csv`
- `data/processed/org_applicant_concentration_clean_panel_2008_2023.dta`
- `data/processed/top_applicants/city_year_top20_applicants_clean_inv_app_appyear_2008_2023.csv`
- `data/processed/top_applicants/baseline_2008_2010_top20_applicants_clean_inv_app_appyear.csv`
- `data/processed/top_applicants/top_applicant_type_clean_audit_top500_20260525.csv`
- `data/processed/top_applicants/top_applicant_type_clean_review_sample_20260525.csv`

结果：

- `results/tables/top_applicant_type_clean_idc_scope_results_20260525.csv`
- `results/tables/org_applicant_concentration_clean_idc_scope_results_20260525.csv`

## 3. 类型清洗规则

本轮对申请人名称做了基本标准化：

- 去除空格；
- 统一中英文括号；
- 用标准化申请人名聚合轻微格式差异。

类型分为：

- `firm`：公司、集团、厂、合作社、银行等市场主体；
- `univ`：大学、学院、学校、中学、小学、幼儿园等教育机构；
- `research`：研究院、研究所、研究中心、实验室、设计院等；
- `hospital`：医院、卫生院、疾控中心等；
- `individual`：2-4 字且不含组织关键词的中文姓名；
- `government`：政府、委员会、管理局、公安局、法院、管委会等；
- `other`：无法规则判定的其他主体。

注意：`univ` 在变量名中沿用旧名，但解释时应写成“高校/学校/教育机构”，不应只说大学。

## 4. Top20 构成概况

2008-2023 年城市-年份 Top20 申请人中，按 Top20 专利量汇总：

- 企业：2,903,745 件；
- 高校/学校：2,414,867 件；
- 个人：195,801 件；
- 科研机构：84,885 件；
- 医院：38,774 件；
- 其他：17,263 件；
- 政府：552 件。

这说明城市 Top 申请人并非只有企业。高校/学校也是非常重要的头部主体。

## 5. IDC 与 Top 类型份额

### 5.1 当年 Top20 类型

在 `province × year FE` 下：

- `cur_top_individual_share_total` 显著为正；
- `cur_top_univ_share_total` 显著为负；
- `cur_top_knowledge_share_total` 显著为负；
- `cur_top_org_share_total` 显著为负；
- `cur_top_firm_share_total` 不显著。

在加入基期专利规模分组 × 年份、基期 Top10 分组 × 年份固定效应后：

- 全样本中上述结果基本消失；
- 高专利量城市 `total_patents >= 50` 中，`cur_top_univ_share_total` 和 `cur_top_knowledge_share_total` 仍为负；
- `cur_top_individual_share_total` 不再显著。

判断：

```text
当前不能写成“IDC 强化企业或高校头部吸收能力”。
当年 Top20 的类型变化更像个人/非组织主体份额上升、教育科研组织份额下降的迹象，
但该迹象对强固定效应较敏感。
```

### 5.2 基期 Top20 类型

基期 Top20 指 2008-2010 年各城市 Top20 申请人，后续追踪这些既有头部主体的专利份额。

在 `province × year FE` 下：

- `base_top_individual_share_total` 显著为正；
- `base_top_firm_share_total` 不显著；
- `base_top_univ_share_total` 不显著；
- `base_top_knowledge_share_total` 不显著；
- `base_top_org_share_total` 不显著。

在强固定效应下：

- 上述基期 Top 类型份额均不稳。

判断：

```text
没有证据表明 IDC 后由基期企业头部或高校科研头部系统性吸收更多城市专利份额。
```

## 6. 组织申请人口径

剔除 `individual` 后，重新构造：

- `org_hhi`
- `org_top10_share`
- `ln1p_org_new_applicants`
- `org_new_share`
- `org_patent_share_total`

结果：

### 6.1 新进入

`org_new_share` 在 `province × year FE` 下显著为正，但强固定效应下不显著。  
在高专利量城市 `total_patents >= 50` 中，`ln1p_org_new_applicants` 在两类规格下均为边际正：

- `province_year_fe`：0.052，p=0.096；
- `provyr_baseyr_fe`：0.067，p=0.083。

判断：

```text
组织申请人进入有一定正向信号，但弱于全体申请人口径的新进入份额。
```

### 6.2 集中度

`org_hhi` 和 `org_top10_share` 在 `province × year FE` 下为正，但强固定效应下消失。

高专利量城市中：

- `org_hhi` 不显著；
- `org_top10_share` 在常规规格为正，但强规格不显著。

判断：

```text
剔除个人后，“组织申请人头部再集中”不够稳。
```

### 6.3 组织专利占比

`org_patent_share_total` 在 `province × year FE` 下显著为负；强固定效应下全样本仍边际为负。

这意味着：

```text
IDC 后城市专利中组织申请人占比没有上升，反而有下降迹象。
```

这进一步削弱了“企业/高校组织吸收算力红利”的解释。

## 7. 当前可写性判断

本轮结果把论文叙事进一步压窄。

可以继续写的主线：

```text
城市 IDC 算力基础设施扩张扩大了城市创新进入边界，
尤其体现为新进入申请人份额上升。
```

可以作为探索性结构发现：

```text
常规固定效应下存在 Top/HHI 上升和中腰部份额下降，
但这并不能稳定解释为企业或高校科研头部吸收能力增强。
```

暂时不能写：

```text
算力基础设施导致企业/高校/上市公司头部再集中。
```

原因：

1. Top 类型分解没有显示企业或高校头部份额上升；
2. 基期 Top 企业/高校份额没有稳健上升；
3. 剔除个人后的组织申请人集中度不稳；
4. 组织专利占比反而有下降迹象。

## 8. 下一步 gate

如果继续冲中文顶刊/AJG3，需要补一个更能解释“进入扩容”的机制，而不是继续硬救“头部再集中”：

1. 按申请人类型重新定义主 Y：新进入企业、新进入高校/科研、新进入个人分别怎么变；
2. 做高价值/发明授权/授权后维持年限口径，排除低质量个人申请；
3. 做“非个人、非学校”的企业组织进入；
4. 如果企业进入也不稳，就把论文收窄为“算力基础设施与创新参与边界扩展”，不要再写“创新再集中”。
