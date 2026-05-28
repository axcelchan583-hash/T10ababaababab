# 2026-05-28 研究设计更新：从“创新生态重塑”收窄到“专利系统进入边界”

## 当前最稳研究问题

```text
IDC 服务覆盖强度提升是否扩大城市专利系统的进入边界？
```

更防守的中英文题目：

```text
算力服务可得性与城市专利系统进入边界：
基于 IDC 经营许可覆盖和全量专利申请人数据的证据

Compute-Service Availability and the Patent-System Entry Margin:
Evidence from Licensed IDC Coverage in China
```

## X 的写法

理论对象可以写：

```text
城市算力基础设施 / 算力服务可得性
```

经验测度必须写：

```text
IDC 经营许可覆盖强度 / IDC 服务覆盖强度
```

主变量：

```text
ln(1 + IDC_scope_city_stock_{c,t-1})
```

解释边界：

```text
它是制度化服务可得性的代理，不是机柜数、MW、FLOPS 或真实算力使用量。
```

新增内部验证：

```text
云/计算相关 IDC 许可覆盖对 new_applicant_share、ln1p_new_applicants、ln1p_new_patents 的解释力强于非云/计算相关许可。
```

这可以作为机制一致性证据，但还不是外部容量验证。

## Y 的写法

主 Y 继续使用：

```text
new_applicant_share
```

但主表必须同时报告分子变量：

```text
ln1p_new_applicants
ln1p_new_patents
```

原因：

```text
份额上升可能来自分母变化。当前结果显示新进入申请人数和新进入专利数同步上升，
所以“进入边界扩展”比“份额机械变化”更可防守。
```

## 识别口径

主估计仍是连续强度模型：

```text
Y_ct = beta ln(1 + IDC_scope_city_stock_{c,t-1})
     + city FE
     + province × year FE
     + baseline capacity × year FE
     + error_ct
```

现代 DID 和事件研究继续作为识别支撑：

```text
IDC_scope_stock >= 2
```

不能把二元事件 DID 直接替代连续强度主效应，除非后续重新定义论文 estimand。

## 当前证据等级

可以写：

```text
IDC 服务覆盖提升后，城市专利系统的新进入申请人份额、新进入申请人数、
新进入申请人专利数均呈正向响应。
```

可以谨慎写：

```text
在授权和家族被引授权等质量口径下，新进入申请人数量和新进入专利数量仍为正，
说明结果不完全来自低质量申请堆量。
```

不能写：

```text
IDC 稳健提高高质量新进入者份额。
IDC 明确导致城市创新头部再集中。
IDC 稳健促进企业/组织申请人进入。
```

## 机制与异质性安排

主机制：

```text
compute-enabled experimentation cost reduction
```

中文写法：

```text
算力服务可得性降低了边缘主体从技术想法、数据处理、原型验证到正式专利申请的实验与验证成本，
使此前未出现在本城市专利系统中的申请人更容易跨过正式申请门槛。
```

机制表优先级：

1. 分子/分母分解：
   - `ln1p_new_applicants`
   - `ln1p_new_patents`
   - `ln1p_incumbent_patents`
   - `ln1p_total_patents`

2. X 机制一致性：
   - 云/计算相关 IDC 许可；
   - 非云/计算 IDC 许可；
   - 跨地区许可；
   - 省内许可。

3. 技术领域 DDD：
   - 高算力依赖 IPC 领域；
   - 低算力依赖领域；
   - 结论写“普遍扩容 + 高算力领域额外增强”。

4. 身份和质量清洗：
   - 剔除个人；
   - 企业/组织申请人口径；
   - 授权、被引、家族被引；
   - 新进入后持续申请。

## 目前最危险的审稿攻击

1. X 攻击：

```text
IDC 许可证覆盖不是实际算力容量。
```

防守：

```text
表述降级为 IDC 服务覆盖强度；补外部验证；报告云/计算许可拆分。
```

2. Y 攻击：

```text
new_applicant_share 可能只是个人低质量专利申请增加。
```

防守：

```text
报告分子变量；做授权/家族被引数量口径；剔除个人和 one-shot entrants；做进入后持续性。
```

3. 识别攻击：

```text
IDC 服务商进入城市是内生选择，反映本地数字经济需求和政策包。
```

防守：

```text
省份×年份 FE、基期能力趋势、政策 horse-race、事件研究、时间安慰剂、
大城市剔除、matched event study 或供给侧预测变量。
```

## 下一步 Go / No-Go 标准

继续写的最低条件：

```text
剔除个人或剔除 one-shot entrants 后，至少 new_applicants / new_patents 的方向仍为正；
云/计算许可拆分继续强于非云/计算许可；
新增智慧城市、高新区和 IP 政策后，主结果方向不反转；
事件研究和时间安慰剂不出现明显前趋势。
```

如果上述条件失败，论文应降级为：

```text
IDC 服务覆盖与城市专利申请参与，而不是创新进入边界。
```
