#!/usr/bin/env python3
"""Build cleaned top-applicant type panels for T10.

This script keeps two distinct objects:
1. Current city-year Top20 applicant composition.
2. Baseline 2008-2010 Top20 applicant composition followed over time.

The second object is the cleaner mechanism variable because it avoids defining
"head applicants" from the same year outcome.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
TOPDIR = PROCESSED / "top_applicants"

START_YEAR = 2008
END_YEAR = 2023
WARMUP_YEAR = 1985
BASE_START = 2008
BASE_END = 2010
TOP_N = 20
DETAIL = (
    PROCESSED
    / f"city_applicant_counts_application_year/city_applicant_counts_inv_app_appyear_{WARMUP_YEAR}_{END_YEAR}.csv.gz"
)
Y = PROCESSED / "patent_applicant_concentration_application_year_2008_2023.csv"


TYPE_ORDER = [
    "firm",
    "univ",
    "research",
    "hospital",
    "individual",
    "government",
    "other",
]

FIRM_MARKERS = [
    "有限公司",
    "有限责任公司",
    "股份有限公司",
    "集团",
    "公司",
    "总公司",
    "分公司",
    "厂",
    "企业",
    "合作社",
    "银行",
    "保险",
    "证券",
    "商行",
    "事务所",
    "农场",
    "牧场",
    "矿",
]

HOSPITAL_MARKERS = ["医院", "卫生院", "医学院附属", "疾控中心", "疾病预防控制中心"]
UNIV_MARKERS = [
    "大学",
    "学院",
    "高等专科学校",
    "职业技术学院",
    "职业学院",
    "专科学校",
    "学校",
    "中学",
    "小学",
    "幼儿园",
    "技校",
    "职校",
    "中等专业学校",
]
RESEARCH_MARKERS = [
    "研究院",
    "研究所",
    "研究中心",
    "研发中心",
    "科学院",
    "设计院",
    "勘察院",
    "实验室",
    "工程中心",
    "技术中心",
]
GOV_MARKERS = [
    "人民政府",
    "政府",
    "委员会",
    "管理局",
    "财政局",
    "科技局",
    "知识产权局",
    "公安局",
    "检察院",
    "法院",
    "管委会",
    "水利局",
    "农业局",
    "林业局",
    "税务局",
    "交通局",
    "公路管理",
    "气象局",
    "规划局",
    "自然资源局",
    "生态环境局",
]

ORG_HINTS = set("公司厂院所校学局部委会中心站社团馆场矿队室库店行")


def norm_name(name: object) -> str:
    text = "" if pd.isna(name) else str(name)
    text = text.strip()
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[;；,，]+$", "", text)
    return text


def contains_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)


def is_likely_person(text: str) -> bool:
    if not 2 <= len(text) <= 4:
        return False
    if contains_any(text, FIRM_MARKERS + HOSPITAL_MARKERS + UNIV_MARKERS + RESEARCH_MARKERS + GOV_MARKERS):
        return False
    if any(ch in ORG_HINTS for ch in text):
        return False
    return bool(re.fullmatch(r"[\u4e00-\u9fff·]+", text))


def infer_type(name: object) -> str:
    text = norm_name(name)
    if not text:
        return "other"

    if is_likely_person(text):
        return "individual"

    if contains_any(text, HOSPITAL_MARKERS):
        return "hospital"

    # Corporate suffix dominates institute-like branch names.
    if contains_any(text, FIRM_MARKERS):
        return "firm"

    if contains_any(text, UNIV_MARKERS):
        return "univ"

    if contains_any(text, RESEARCH_MARKERS):
        return "research"

    if contains_any(text, GOV_MARKERS):
        return "government"

    return "other"


def add_type_shares(panel: pd.DataFrame, prefix: str, denom_col: str) -> pd.DataFrame:
    for t in TYPE_ORDER:
        col = f"{prefix}_{t}_patents"
        if col not in panel.columns:
            panel[col] = 0
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0)
        panel[f"{prefix}_{t}_share_total"] = panel[col] / panel["total_patents"].where(panel["total_patents"] > 0)
        panel[f"{prefix}_{t}_share_{denom_col}"] = panel[col] / panel[f"{prefix}_patents"].where(panel[f"{prefix}_patents"] > 0)

    panel[f"{prefix}_knowledge_patents"] = (
        panel[f"{prefix}_univ_patents"] + panel[f"{prefix}_research_patents"] + panel[f"{prefix}_hospital_patents"]
    )
    panel[f"{prefix}_org_patents"] = panel[f"{prefix}_patents"] - panel[f"{prefix}_individual_patents"]
    for t in ["knowledge", "org"]:
        panel[f"{prefix}_{t}_share_total"] = panel[f"{prefix}_{t}_patents"] / panel["total_patents"].where(
            panel["total_patents"] > 0
        )
        panel[f"{prefix}_{t}_share_{denom_col}"] = panel[f"{prefix}_{t}_patents"] / panel[
            f"{prefix}_patents"
        ].where(panel[f"{prefix}_patents"] > 0)
    return panel


def wide_type_patents(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    wide = (
        df.pivot_table(
            index=["city", "year"],
            columns="clean_type",
            values="patents",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    rename = {t: f"{prefix}_{t}_patents" for t in TYPE_ORDER if t in wide.columns}
    wide = wide.rename(columns=rename)
    for t in TYPE_ORDER:
        col = f"{prefix}_{t}_patents"
        if col not in wide.columns:
            wide[col] = 0
    wide[f"{prefix}_patents"] = wide[[f"{prefix}_{t}_patents" for t in TYPE_ORDER]].sum(axis=1)
    return wide


def main() -> None:
    TOPDIR.mkdir(parents=True, exist_ok=True)

    detail = pd.read_csv(DETAIL, low_memory=False)
    detail = detail[(detail["year"] >= START_YEAR) & (detail["year"] <= END_YEAR)].copy()
    detail["applicant_norm"] = detail["applicant"].map(norm_name)
    detail = detail[detail["applicant_norm"] != ""].copy()
    detail["clean_type"] = detail["applicant_norm"].map(infer_type)
    detail = (
        detail.groupby(["city", "year", "applicant_norm", "clean_type"], as_index=False)
        .agg(patents=("patents", "sum"), applicant=("applicant", "first"))
        .sort_values(["city", "year", "patents", "applicant_norm"], ascending=[True, True, False, True])
    )

    y = pd.read_csv(Y, low_memory=False, encoding="utf-8-sig")
    y = y[y["scope"] == "inv_app_appyear"][["city", "year", "total_patents"]].copy()

    detail["rank_city_year"] = detail.groupby(["city", "year"]).cumcount() + 1
    cur_top = detail[detail["rank_city_year"] <= TOP_N].copy()
    cur_top_out = TOPDIR / f"city_year_top{TOP_N}_applicants_clean_inv_app_appyear_{START_YEAR}_{END_YEAR}.csv"
    cur_top.to_csv(cur_top_out, index=False, encoding="utf-8-sig")

    cur_wide = wide_type_patents(cur_top, "cur_top")

    base_source = detail[(detail["year"] >= BASE_START) & (detail["year"] <= BASE_END)]
    base = (
        base_source.groupby(["city", "applicant_norm", "clean_type"], as_index=False)
        .agg(patents=("patents", "sum"), applicant=("applicant", "first"))
        .sort_values(["city", "patents", "applicant_norm"], ascending=[True, False, True])
    )
    base["rank_baseline"] = base.groupby("city").cumcount() + 1
    base_top = base[base["rank_baseline"] <= TOP_N].copy()
    base_top_out = TOPDIR / f"baseline_{BASE_START}_{BASE_END}_top{TOP_N}_applicants_clean_inv_app_appyear.csv"
    base_top.to_csv(base_top_out, index=False, encoding="utf-8-sig")

    base_keys = base_top[["city", "applicant_norm", "clean_type", "rank_baseline"]].copy()
    base_follow = detail.merge(base_keys, on=["city", "applicant_norm", "clean_type"], how="inner")
    base_wide = wide_type_patents(base_follow, "base_top")

    panel = y.merge(cur_wide, on=["city", "year"], how="left").merge(base_wide, on=["city", "year"], how="left")
    for prefix in ["cur_top", "base_top"]:
        patent_cols = [f"{prefix}_{t}_patents" for t in TYPE_ORDER] + [f"{prefix}_patents"]
        for col in patent_cols:
            panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0)
        panel = add_type_shares(panel, prefix, "top" if prefix == "cur_top" else "base")

    share_cols = [c for c in panel.columns if "_share_" in c]
    panel[share_cols] = panel[share_cols].fillna(0)

    panel_out = PROCESSED / f"top_applicant_type_clean_panel_{START_YEAR}_{END_YEAR}.csv"
    dta_out = PROCESSED / f"top_applicant_type_clean_panel_{START_YEAR}_{END_YEAR}.dta"
    panel.to_csv(panel_out, index=False, encoding="utf-8-sig")
    panel.to_stata(dta_out, write_index=False, version=118)

    audit = (
        cur_top.groupby(["applicant_norm", "clean_type"], as_index=False)
        .agg(
            applicant=("applicant", "first"),
            top_patents=("patents", "sum"),
            top_rows=("patents", "size"),
            city_count=("city", "nunique"),
            max_city_year_patents=("patents", "max"),
        )
        .sort_values(["top_patents", "max_city_year_patents"], ascending=False)
    )
    audit_out = TOPDIR / "top_applicant_type_clean_audit_top500_20260525.csv"
    audit.head(500).to_csv(audit_out, index=False, encoding="utf-8-sig")

    review = audit[
        (audit["clean_type"].isin(["individual", "other", "government"]))
        | ((audit["clean_type"].isin(["research", "hospital"])) & (audit["top_patents"] >= 100))
    ].head(500)
    review_out = TOPDIR / "top_applicant_type_clean_review_sample_20260525.csv"
    review.to_csv(review_out, index=False, encoding="utf-8-sig")

    print(f"wrote {panel_out} rows={len(panel):,} cities={panel['city'].nunique():,}")
    print(f"wrote {dta_out}")
    print(f"wrote {cur_top_out} rows={len(cur_top):,}")
    print(f"wrote {base_top_out} rows={len(base_top):,}")
    print(f"wrote {audit_out} rows={min(500, len(audit)):,}")
    print(f"wrote {review_out} rows={len(review):,}")


if __name__ == "__main__":
    main()
