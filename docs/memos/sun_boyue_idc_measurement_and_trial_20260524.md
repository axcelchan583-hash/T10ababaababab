# 孙波约等文献 IDC 构造与本项目试跑

日期：2026-05-24  
文献：孙波约、于斌斌、胡雅静《算力基础设施建设是否抑制了企业“脱实向虚”？——来自中国地级及以上城市数据中心建设的经验证据》

## 1. 这篇文章怎么用 IDC

该文将数据中心视为算力基础设施的核心载体，用工信部电信业务经营许可数据构造城市算力基础设施变量。

核心步骤：

1. 登录工信部政务平台数据查询板块；
2. 用 Python 批量爬取历年电信业务经营许可证颁发信息；
3. 清洗许可证数据，筛选保留互联网数据中心业务相关条目；
4. 手工整理许可证业务覆盖范围中的互联网数据中心业务机房所在地信息与颁发时间；
5. 加总至城市-年份层面，得到各地级市当年获批的数据中心数量；
6. 以首批许可证获批时间为基期，对每年新增数据中心累计加总，得到数据中心存量，以此刻画当地算力基础设施建设水平 `idc`。

特别重要的处理：

- 少量许可证只披露机房所在地省份时，作者用天眼查中的企业注册地址作为机房所在地；
- 为避免这个处理带来偏误，作者还把核心解释变量加总到省份-年份层面做稳健性；
- 许可证有效期为 5 年，作者还用最近 5 年新建数据中心构造 `idc_pre5`；
- 替代 X 包括当年新增 `idc_new`、前一期存量 `l_idc`、注册资本修正的 `idc_modify`、省份-年份 `idc_province`。

样本：

- 2012-2022 年；
- 284 个地级市；
- 沪深 A 股非金融企业。

识别：

- 基准模型：企业固定效应 + 年份固定效应；
- 控制企业变量和城市变量；
- 部分规格加入省份固定效应；
- 稳健性中加入省份 × 年份、行业 × 年份固定效应；
- IV：城市与光缆骨干网距离对数 × 排除本市以外全国层面数据中心数量均值。

## 2. 对我们最有用的启发

这篇文章支持我们继续用 IDC 许可证路线。

但它不是简单用企业注册地，而是优先使用：

```text
许可证业务覆盖范围中的机房所在地城市
```

只有在披露到省份或信息不足时，才用注册地址兜底。

所以我们当前应该把 X 拆开，而不是混在一起：

- `IDC_scope_city_stock`：只用覆盖范围明确出现的城市；
- `IDC_registered_city_stock`：只用注册地址/公司名推断城市；
- `IDC_combined_stock`：覆盖范围优先，缺失时用注册地址 fallback。

## 3. 本项目已按这个口径试跑

新增脚本：

- `scripts/build_idc_scope_registered_city_year_panel.py`
- `scripts/build_idc_split_applicant_concentration_application_year_panel.py`
- `scripts/run_idc_split_x_application_year_stata.do`

新增数据：

- `data/processed/idc_split_proxy_city_year_2000_2024.csv`
- `data/processed/idc_split_applicant_concentration_application_year_panel_2008_2023.dta`
- `results/tables/idc_split_x_application_year_results_20260524.csv`

数据规模：

- 51miit 许可证明细：3277 条；
- 旧脚本识别到覆盖范围非空：306 条；
- 修正“因特网数据中心业务”等旧式写法后，覆盖范围非空：356 条；
- 覆盖范围明确落到城市的许可证-城市行：743 条，覆盖 137 个城市；
- 注册地址推断许可证-城市行：2462 条，覆盖 177 个城市；
- 合并口径许可证-城市行：2915 条，覆盖 213 个城市。

## 4. 申请年份口径试跑结果

Y：发明专利申请，按申请年份归年。  
样本：2008-2023 年，291 个城市。

### 4.1 覆盖范围城市 X

`ln(1 + IDC_scope_stock_{t-1})`

在 `city FE + province × year FE` 下：

| Y | 系数 | p 值 |
|---|---:|---:|
| `new_applicant_share` | 0.0430 | 0.000 |
| `hhi` | 0.0106 | 0.094 |
| `top10_share` | 0.0307 | 0.025 |
| `base_top_share` | 0.0259 | 0.039 |
| `base_mid_inc_share` | -0.0325 | 0.002 |

这说明：按孙波约等更接近的“覆盖范围城市”口径，结果方向仍支持“进入扩容 + 头部再集中 + 中腰部挤压”。

但在加入 `province × year FE + baseline capacity × year FE` 后：

- `ln1p_new_applicants` 正且显著；
- `new_applicant_share` 仍在 5% 水平显著为正；
- `hhi`、`top10_share`、`base_top_share`、`base_mid_inc_share` 均不显著。

### 4.2 注册地址 X

`ln(1 + IDC_registered_stock_{t-1})`

在 `province × year FE` 下方向类似，但加入基期能力 × 年份 FE 后，集中度结果同样消失。

### 4.3 合并 X

`ln(1 + IDC_combined_stock_{t-1})`

在 `province × year FE` 下：

- `new_applicant_share` 正；
- `hhi/top10/base_top` 正；
- `base_mid_inc_share` 负。

但加入基期能力 × 年份 FE 后，同样主要只剩 `ln1p_new_applicants`。

## 5. 当前判断

这篇文章让本项目的 X 路线更可行，但也提高了要求。

可以继续试：

```text
主 X 改为 IDC_scope_city_stock，而不是注册地混合口径。
```

但不能把当前结果写成已定论。更准确的判断是：

```text
覆盖范围口径下，IDC 与新进入申请人扩张最稳；
创新再集中和中腰部挤压在省份×年份固定效应下存在，
但对基期能力差异趋势较敏感。
```

如果要继续，下一步优先做：

1. 用 `IDC_scope_city_stock` 重做事件研究；
2. 用 `idc_new`、`l_idc`、最近 5 年 stock 重做稳健性；
3. 构造省份-年份 `idc_province` 稳健性；
4. 尝试复刻该文 IV：城市到光缆骨干网距离 × 全国其他城市 IDC 数量均值；
5. 继续完善许可证覆盖范围爬取，尽量减少注册地址 fallback。

暂时不要：

- 用国泰安全国智能算力规模作主 X；
- 把注册地址口径当成强主 X；
- 直接声称已识别“真实机房容量”或“智能算力规模”。
