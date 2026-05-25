# AJG3 升级检验第一轮结果

日期：2026-05-25  
项目：T10 城市 IDC 算力服务覆盖与创新进入边界

## 1. 本轮做了什么

本轮按 Claude / ChatGPT Pro 建议，先做可由现有数据直接落地的最小升级包：

1. 整体申请人层面的城市 × 高算力技术领域 × 年份 DDD；
2. 低算力领域单独回归，检查效应是否只来自高算力领域；
3. 时间安慰剂：使用未来 3 年、5 年 IDC 覆盖作为伪处理；
4. 组织申请人口径复核，排查个人申请人驱动问题；
5. 公开年份质量口径：发明申请公开、发明授权公开、全部公开；
6. `scope >= 2` 阈值事件的现代 DID 复核：Callaway-Sant'Anna 和 Borusyak-Jaravel-Spiess。

新增脚本和结果：

- `scripts/build_overall_tech_entry_ddd_panel.py`
- `scripts/run_ajg3_minimal_upgrade_stata.do`
- `scripts/run_idc_scope_modern_did_stata.do`
- `data/processed/overall_tech_entry_ddd_panel_2008_2023.csv`
- `results/tables/ajg3_minimal_upgrade_results_20260525.csv`
- `results/tables/idc_scope_modern_did_20260525.csv`

## 2. 现代 DID 结果：主线明显增强

事件定义：

```text
城市 IDC_scope_stock 首次达到 >= 2
```

样本：

```text
2008-2023 年
291 个城市
4,647 个城市-年份
82 个 ever-treated 城市
```

### 2.1 `new_applicant_share`

Borusyak-Jaravel-Spiess，含城市 FE、省份 × 年份 FE、基期能力 × 年份控制：

| event time | coef | p |
|---:|---:|---:|
| -3 | -0.018 | 0.282 |
| -2 | -0.010 | 0.505 |
| -1 | -0.010 | 0.579 |
| 0 | -0.014 | 0.296 |
| +1 | 0.050 | 0.001 |
| +2 | 0.077 | 0.000 |
| +3 | 0.067 | 0.000 |
| +4 | 0.068 | 0.000 |

前趋势联合检验：

```text
p = 0.762
```

Callaway-Sant'Anna 结果方向一致：

| event time | coef | p |
|---:|---:|---:|
| -3 | -0.016 | 0.354 |
| -2 | 0.005 | 0.775 |
| -1 | -0.002 | 0.903 |
| 0 | -0.004 | 0.796 |
| +1 | 0.059 | 0.006 |
| +2 | 0.087 | 0.001 |
| +3 | 0.078 | 0.004 |
| +4 | 0.078 | 0.005 |

解释：

```text
现代 DID 支持主线：IDC 覆盖达到一定强度后，新进入申请人份额不是立即跳升，
而是在事件后 1-4 年持续上升，处理前三期没有明显预趋势。
```

### 2.2 分子变量

`ln1p_new_applicants` 和 `ln1p_new_patents` 在 BJS 与 CSDID 中同样显示事件后显著上升。

关键系数：

- BJS `ln1p_new_applicants`：+0 年 0.252，+1 年 0.323，+2 年 0.338，均 p < 0.01；
- CSDID `ln1p_new_applicants`：+0 年 0.221，+1 年 0.291，+2 年 0.318，均 p < 0.01；
- BJS `ln1p_new_patents`：+1 年 0.234，+2 年 0.343，+3 年 0.257，均 p < 0.01；
- CSDID `ln1p_new_patents`：+1 年 0.229，+2 年 0.346，+3 年 0.266，均 p < 0.01。

这说明主结果不是旧申请人下降导致的机械份额变化。

## 3. 技术领域 DDD：高算力领域额外更强

模型：

```text
Y_{c,k,t} = beta * ln(1 + IDC_scope_stock_{c,t-1}) × HighCompute_k
          + City × Year FE
          + City × HighCompute FE
          + HighCompute × Year FE
          + error
```

这里的 `HighCompute_k` 基于 IPC 子类识别 AI、计算、软件、数字通信、数据处理等高算力依赖领域。

整体申请人 DDD 结果：

| Y | coef | p | 判断 |
|---|---:|---:|---|
| `ln1p_city_new_applicants_field` | 0.216 | 0.000 | 高算力领域新进入申请人数相对上升 |
| `ln1p_city_new_patents_field` | 0.254 | 0.000 | 高算力领域新进入申请人专利数相对上升 |
| `city_new_share_total_field` | 0.029 | 0.033 | 高算力领域新进入份额相对上升 |
| `ln1p_total_patents_field` | 0.166 | 0.000 | 高算力领域总专利也上升 |
| `ln1p_incumbent_patents_field` | 0.306 | 0.000 | 既有主体也更强受益 |

阈值样本稳健性：

- `total_patents >= 20` 和 `>= 50` 后，新进入数量和份额仍为正；
- 在 `>= 50` 后，总专利和既有主体专利不显著，但新进入份额仍显著。

解释：

```text
高算力领域确实是更敏感的响应场景。
这比企业 DDD 更适合作为机制/异质性：不是只看企业，而是全体申请人中，
高算力技术领域的新进入边界扩张更明显。
```

## 4. 低算力领域不是干净 placebo

低算力领域单独回归中，IDC 对新进入份额、新进入申请人数和新进入专利数仍为正且显著。

这意味着不能写：

```text
IDC 只影响 AI/云计算/软件等高算力领域。
```

更准确写法是：

```text
IDC 覆盖提升对城市创新进入有普遍扩容效应，
在高算力依赖技术领域存在额外增强。
```

## 5. 时间安慰剂：主 Y 通过

使用未来 3 年、未来 5 年 IDC 覆盖作为伪处理：

| fake X | Y | coef | p |
|---|---|---:|---:|
| `F3(IDC)` | `new_applicant_share` | 0.016 | 0.307 |
| `F5(IDC)` | `new_applicant_share` | 0.010 | 0.558 |
| `F3(IDC)` | `ln1p_new_applicants` | 0.073 | 0.190 |
| `F5(IDC)` | `ln1p_new_applicants` | 0.045 | 0.403 |
| `F3(IDC)` | `ln1p_new_patents` | 0.093 | 0.107 |
| `F5(IDC)` | `ln1p_new_patents` | 0.064 | 0.319 |

解释：

```text
主 Y 的未来处理安慰剂不显著，反向时间趋势风险下降。
```

## 6. 组织申请人与质量口径：仍需降调

组织申请人口径：

| Y | coef | p | 判断 |
|---|---:|---:|---|
| `org_new_share` | 0.014 | 0.182 | 不显著 |
| `org_new_share_org` | 0.012 | 0.234 | 不显著 |
| `ln1p_org_new_applicants` | 0.048 | 0.204 | 不显著 |
| `ln1p_org_new_patents` | 0.068 | 0.162 | 不显著 |
| `org_patent_share_total` | -0.024 | 0.094 | 组织专利占比边际下降 |

质量口径：

- 发明申请公开口径支持主结果；
- 全部公开口径方向一致但较弱；
- 发明授权公开口径方向为正，但份额和数量多数不显著，只有 `ln1p_new_patents` 在 2023 截尾下边际显著。

解释：

```text
当前最稳的是“全体申请人的进入边界扩展”。
不能升级成“组织/企业高质量创新进入已经稳健扩张”。
```

## 7. 当前可写结论

可以写：

```text
城市 IDC 服务覆盖达到一定强度后，城市创新进入边界扩展；
新进入申请人份额、新进入申请人数和新进入申请人专利数同步上升；
现代 DID、时间安慰剂和技术领域 DDD 均支持这一方向。
```

可以作为补充写：

```text
进入扩展在高算力依赖技术领域更明显；
但低算力领域也有正效应，说明 IDC 的作用不是狭窄的 AI/云计算专属效应。
```

必须降调：

```text
组织/企业新进入、高质量授权新进入、头部再集中目前都不能作为主因果结论。
```

## 8. 下一步优先级

最需要补的是两类：

1. 政策 horse-race：宽带中国、智慧城市、大数据综合试验区、创新型城市、高新区、知识产权示范城市等；
2. 新进入质量：发明授权申请年份口径、维持年限、被引、同族或高价值发明专利。

不建议近期优先做：

```text
地理 IV、Sobel 中介、全球样本、合作网络。
```

这些工程量大，且不解决当前最核心的审稿风险。
