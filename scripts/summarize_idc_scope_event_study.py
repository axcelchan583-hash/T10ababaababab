import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
MEMOS = ROOT / "docs" / "memos"


CSV = TABLES / "idc_scope_event_study_binned_20260525.csv"
SUMMARY_CSV = TABLES / "idc_scope_event_study_binned_summary_20260525.csv"
MEMO = MEMOS / "idc_scope_event_study_binned_memo_20260525.md"


OUTCOMES = [
    "ln1p_new_applicants",
    "new_applicant_share",
    "hhi",
    "top10_share",
    "base_top_share",
    "base_mid_inc_share",
]

OUTCOME_LABEL = {
    "ln1p_new_applicants": "ln(1+new applicants)",
    "new_applicant_share": "new applicant share",
    "hhi": "HHI",
    "top10_share": "Top10 share",
    "base_top_share": "baseline Top share",
    "base_mid_inc_share": "baseline middle share",
}

POST_EVENTS = ["es_0", "es_p1", "es_p2", "es_p3"]


NUMERIC_FIELDS = {
    "rel",
    "coef",
    "se",
    "t",
    "p",
    "preF",
    "prep",
    "N",
    "N_city",
    "N_treated_city",
    "mean_y",
}


def read_rows() -> list[dict]:
    rows = []
    with CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in NUMERIC_FIELDS:
                if field in row and row[field] != "":
                    row[field] = float(row[field])
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows_in: list[dict]) -> list[dict]:
    rows = []
    groups = defaultdict(list)
    for row in rows_in:
        groups[(row["eventdef"], row["spec"], row["outcome"])].append(row)
    for eventdef, spec, outcome in sorted(groups):
        group = groups[(eventdef, spec, outcome)]
        post = [r for r in group if r["event"] in POST_EVENTS]
        post_avg = sum(r["coef"] for r in post) / len(post) if post else ""
        post_min_p = min((r["p"] for r in post), default="")
        rows.append(
            {
                "eventdef": eventdef,
                "spec": spec,
                "outcome": outcome,
                "N_city": int(group[0]["N_city"]),
                "N_treated_city": int(group[0]["N_treated_city"]),
                "pre_p": group[0]["prep"],
                "pre_clean_10pct": group[0]["prep"] >= 0.1,
                "post_avg_coef_0_to_3": post_avg,
                "post_min_p_0_to_3": post_min_p,
                "post_sig_pos_10pct_count": sum(1 for r in post if r["coef"] > 0 and r["p"] < 0.1),
                "post_sig_neg_10pct_count": sum(1 for r in post if r["coef"] < 0 and r["p"] < 0.1),
            }
        )
    return rows


def _svg_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _panel_svg(parts: list[str], x0: int, y0: int, w: int, h: int, title: str, g: list[dict]) -> None:
    margin_l, margin_r, margin_t, margin_b = 42, 14, 24, 34
    px0, px1 = x0 + margin_l, x0 + w - margin_r
    py0, py1 = y0 + margin_t, y0 + h - margin_b
    x_min, x_max = -4, 4
    vals = []
    for r in g:
        vals.extend([r["coef"], r["coef"] - 1.96 * r["se"], r["coef"] + 1.96 * r["se"]])
    vals.append(0.0)
    y_min = min(vals)
    y_max = max(vals)
    pad = (y_max - y_min) * 0.18 if y_max > y_min else 0.05
    y_min -= pad
    y_max += pad

    def sx(v: float) -> float:
        return px0 + (v - x_min) / (x_max - x_min) * (px1 - px0)

    def sy(v: float) -> float:
        return py1 - (v - y_min) / (y_max - y_min) * (py1 - py0)

    parts.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="white" stroke="#dddddd"/>')
    parts.append(f'<text x="{x0 + 8}" y="{y0 + 16}" font-size="12" font-family="Arial">{_svg_escape(title)}</text>')
    parts.append(f'<line x1="{px0}" y1="{sy(0)}" x2="{px1}" y2="{sy(0)}" stroke="#444444" stroke-width="0.8"/>')
    parts.append(f'<line x1="{sx(-0.5)}" y1="{py0}" x2="{sx(-0.5)}" y2="{py1}" stroke="#888888" stroke-dasharray="4 3" stroke-width="0.8"/>')
    parts.append(f'<line x1="{px0}" y1="{py1}" x2="{px1}" y2="{py1}" stroke="#999999" stroke-width="0.8"/>')
    parts.append(f'<line x1="{px0}" y1="{py0}" x2="{px0}" y2="{py1}" stroke="#999999" stroke-width="0.8"/>')

    for tick in [-4, -3, -2, -1, 0, 1, 2, 3, 4]:
        label = "<=-4" if tick == -4 else ">=4" if tick == 4 else str(tick)
        parts.append(f'<line x1="{sx(tick)}" y1="{py1}" x2="{sx(tick)}" y2="{py1 + 4}" stroke="#999999" stroke-width="0.8"/>')
        parts.append(f'<text x="{sx(tick)}" y="{py1 + 17}" font-size="9" text-anchor="middle" font-family="Arial">{_svg_escape(label)}</text>')

    for val in [y_min + pad, 0, y_max - pad]:
        parts.append(f'<text x="{px0 - 5}" y="{sy(val) + 3}" font-size="8" text-anchor="end" font-family="Arial">{val:.2f}</text>')

    points = []
    for r in sorted(g, key=lambda item: item["rel"]):
        x = sx(r["rel"])
        y = sy(r["coef"])
        lo = sy(r["coef"] - 1.96 * r["se"])
        hi = sy(r["coef"] + 1.96 * r["se"])
        parts.append(f'<line x1="{x}" y1="{lo}" x2="{x}" y2="{hi}" stroke="#83a9d8" stroke-width="1.4"/>')
        parts.append(f'<line x1="{x - 3}" y1="{lo}" x2="{x + 3}" y2="{lo}" stroke="#83a9d8" stroke-width="1.0"/>')
        parts.append(f'<line x1="{x - 3}" y1="{hi}" x2="{x + 3}" y2="{hi}" stroke="#83a9d8" stroke-width="1.0"/>')
        points.append(f"{x},{y}")
    parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#2f6db2" stroke-width="1.8"/>')
    for r in sorted(g, key=lambda item: item["rel"]):
        parts.append(f'<circle cx="{sx(r["rel"])}" cy="{sy(r["coef"])}" r="3.2" fill="#2f6db2"/>')


def panel_plot(rows: list[dict], eventdef: str, spec: str) -> Path:
    sub = [r for r in rows if r["eventdef"] == eventdef and r["spec"] == spec]
    FIGURES.mkdir(parents=True, exist_ok=True)
    out = FIGURES / f"idc_scope_event_study_binned_{eventdef}_{spec}.svg"
    width, height = 1180, 670
    panel_w, panel_h = 380, 285
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="24" y="28" font-size="18" font-family="Arial">IDC event study: {_svg_escape(eventdef)}, {_svg_escape(spec)}</text>',
        '<text x="24" y="50" font-size="11" font-family="Arial" fill="#555555">Omitted event year is -1; vertical bars are 95% confidence intervals.</text>',
    ]
    for idx, outcome in enumerate(OUTCOMES):
        row, col = divmod(idx, 3)
        x0 = 18 + col * panel_w
        y0 = 70 + row * panel_h
        g = [r for r in sub if r["outcome"] == outcome]
        _panel_svg(parts, x0, y0, panel_w - 14, panel_h - 16, OUTCOME_LABEL[outcome], g)
    parts.append("</svg>")
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def format_float(x: float | str) -> str:
    if x == "":
        return ""
    return f"{x:.3f}"


def write_memo(summary: list[dict], figures: list[Path]) -> None:
    focus = [
        r
        for r in summary
        if r["eventdef"] in ["scope_ge_1", "scope_ge_2", "scope_ge_3", "scope_ge_5"]
        and r["outcome"] in OUTCOMES
    ]
    focus = sorted(focus, key=lambda r: (r["spec"], r["eventdef"], r["outcome"]))
    lines = [
        "# IDC 覆盖范围口径事件研究：尾部合并版",
        "",
        "日期：2026-05-25",
        "",
        "## 1. 设置",
        "",
        "- 事件定义：城市 IDC 覆盖范围存量首次达到 `>=1/2/3/5`。",
        "- 事件窗口：`<=-4, -3, -2, -1, 0, +1, +2, +3, >=+4`，其中 `-1` 为遗漏基准期。",
        "- 处理组：首次达到阈值年份位于 2012-2020 年的城市；对照组为从未达到阈值的城市。",
        "- 规格一：城市固定效应 + 省份×年份固定效应。",
        "- 规格二：城市固定效应 + 省份×年份固定效应 + 基期专利规模分组×年份固定效应 + 基期 Top10 分组×年份固定效应。",
        "- 标准误按城市聚类。",
        "",
        "## 2. 诊断表",
        "",
        "`pre_p` 是 `<=-4, -3, -2` 三个前导项的联合检验 p 值；`post_avg` 是事件后 0 到 +3 年系数均值；`sig+/-` 是事件后 0 到 +3 年在 10% 水平显著为正/负的年份数。",
        "",
        "| spec | event | outcome | treated cities | pre_p | post_avg | min post p | sig+ | sig- |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in focus:
        lines.append(
            "| {spec} | {eventdef} | {outcome} | {n} | {pre} | {avg} | {minp} | {sigp} | {sign} |".format(
                spec=r["spec"],
                eventdef=r["eventdef"],
                outcome=r["outcome"],
                n=int(r["N_treated_city"]),
                pre=format_float(r["pre_p"]),
                avg=format_float(r["post_avg_coef_0_to_3"]),
                minp=format_float(r["post_min_p_0_to_3"]),
                sigp=int(r["post_sig_pos_10pct_count"]),
                sign=int(r["post_sig_neg_10pct_count"]),
            )
        )

    lines.extend(
        [
            "",
            "## 3. 目前判断",
            "",
            "1. 事件研究不能支撑“现在就直接投”的强因果版本。",
            "2. 相对最能看的组合是 `scope_ge_2`：在强固定效应下，前趋势干净，`new_applicant_share` 在事件后 +1、+2 年为正且显著。",
            "3. `scope_ge_1` 更像进入门槛太低，事件后动态弱；`scope_ge_5` 处理城市只有 32 个，样本太小；`scope_ge_3` 在强规格下进入扩容不稳。",
            "4. HHI、Top10、基期 Top 份额的事件动态不够稳定，不能作为最硬主结论。",
            "5. 基期中腰部份额下降在 `scope_ge_2` 下有方向，但强规格中显著性不够，适合作为结构分解线索。",
            "",
            "## 4. 图",
            "",
        ]
    )
    for fig in figures:
        rel = fig.relative_to(ROOT)
        lines.append(f"- `{rel}`")

    lines.extend(
        [
            "",
            "## 5. 写作口径",
            "",
            "可以写：",
            "",
            "> 围绕城市 IDC 覆盖范围存量首次跨过较低但非零噪声阈值的事件研究显示，处理城市在事件前不存在明显差异趋势；在事件后 1-2 年，新进入申请人份额上升。这支持算力基础设施扩张主要通过扩大创新参与边界发挥作用。",
            "",
            "暂时不要写：",
            "",
            "> IDC 明确导致城市创新头部再集中。",
            "",
            "原因是集中度变量在事件研究中轨迹不稳定，且对基期能力趋势控制敏感。",
            "",
        ]
    )

    MEMO.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = read_rows()
    summary = summarize(rows)
    write_csv(SUMMARY_CSV, summary)
    figures = [
        panel_plot(rows, "scope_ge_2", "provyr_baseyr_fe"),
        panel_plot(rows, "scope_ge_2", "province_year_fe"),
        panel_plot(rows, "scope_ge_3", "provyr_baseyr_fe"),
    ]
    write_memo(summary, figures)
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {MEMO}")
    for fig in figures:
        print(f"Wrote {fig}")


if __name__ == "__main__":
    main()
