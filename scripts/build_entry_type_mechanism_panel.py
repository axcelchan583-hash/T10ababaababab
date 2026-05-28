#!/usr/bin/env python3
"""Build city-year entrant-type mechanism variables for T10."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"

START_YEAR = 2008
END_YEAR = 2023
WARMUP_YEAR = 1985
BASE_START = 2008
BASE_END = 2010
DETAIL = (
    PROCESSED
    / f"city_applicant_counts_application_year/city_applicant_counts_inv_app_appyear_{WARMUP_YEAR}_{END_YEAR}.csv.gz"
)
Y = PROCESSED / "patent_applicant_concentration_application_year_2008_2023.csv"

TYPE_ORDER = ["firm", "knowledge", "individual", "government", "other", "org"]

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
KNOWLEDGE_MARKERS = [
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
    "医院",
    "卫生院",
    "疾控中心",
    "疾病预防控制中心",
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
    text = text.strip().replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[;；,，]+$", "", text)
    return text


def contains_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)


def is_likely_person(text: str) -> bool:
    if not 2 <= len(text) <= 4:
        return False
    if contains_any(text, FIRM_MARKERS + KNOWLEDGE_MARKERS + GOV_MARKERS):
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
    if contains_any(text, FIRM_MARKERS):
        return "firm"
    if contains_any(text, KNOWLEDGE_MARKERS):
        return "knowledge"
    if contains_any(text, GOV_MARKERS):
        return "government"
    return "other"


def add_type_metrics(panel: pd.DataFrame, typed: pd.DataFrame, city_year: pd.DataFrame) -> pd.DataFrame:
    sample = typed[typed["year"].between(START_YEAR, END_YEAR, inclusive="both")].copy()
    sample["new_pat_part"] = np.where(sample["is_new"], sample["patents"], 0)

    typed_metrics = (
        sample.groupby(["city", "year", "clean_type"], as_index=False)
        .agg(
            total_pat=("patents", "sum"),
            active_n=("applicant_norm", "nunique"),
            new_n=("is_new", "sum"),
            new_pat=("new_pat_part", "sum"),
        )
    )

    out = panel.copy()
    for t in ["firm", "knowledge", "individual", "government", "other"]:
        sub = typed_metrics[typed_metrics["clean_type"] == t][
            ["city", "year", "total_pat", "active_n", "new_n", "new_pat"]
        ].copy()
        sub = sub.rename(
            columns={
                "total_pat": f"{t}_pat",
                "active_n": f"{t}_active_n",
                "new_n": f"{t}_new_n",
                "new_pat": f"{t}_new_pat",
            }
        )
        out = out.merge(sub, on=["city", "year"], how="left")

    org = typed_metrics[typed_metrics["clean_type"] != "individual"].copy()
    org = (
        org.groupby(["city", "year"], as_index=False)
        .agg(
            org_pat=("total_pat", "sum"),
            org_active_n=("active_n", "sum"),
            org_new_n=("new_n", "sum"),
            org_new_pat=("new_pat", "sum"),
        )
    )
    out = out.merge(org, on=["city", "year"], how="left")

    count_cols = [c for c in out.columns if c.endswith(("_pat", "_new_pat", "_active_n", "_new_n"))]
    out[count_cols] = out[count_cols].fillna(0)

    for t in TYPE_ORDER:
        out[f"{t}_new_share_total"] = out[f"{t}_new_pat"] / out["total_patents"].where(out["total_patents"] > 0)
        out[f"{t}_new_share_new"] = out[f"{t}_new_pat"] / out["new_patents"].where(out["new_patents"] > 0)
        out[f"ln_{t}_new_n"] = np.log1p(out[f"{t}_new_n"])
        out[f"ln_{t}_new_pat"] = np.log1p(out[f"{t}_new_pat"])
        out[f"ln_{t}_pat"] = np.log1p(out[f"{t}_pat"])

    out["incumbent_patents"] = out["total_patents"] - out["new_patents"]
    out["incumbent_applicants"] = out["active_applicants"] - out["new_applicants"]
    out["incumbent_share"] = out["incumbent_patents"] / out["total_patents"].where(out["total_patents"] > 0)
    out["ln_new_patents"] = np.log1p(out["new_patents"])
    out["ln_incumbent_patents"] = np.log1p(out["incumbent_patents"])
    out["ln_incumbent_applicants"] = np.log1p(out["incumbent_applicants"])

    base = out[out["year"].between(BASE_START, BASE_END, inclusive="both")].copy()
    base_city = (
        base.groupby("city", as_index=False)
        .agg(
            base_firm_share=("firm_pat", "sum"),
            base_knowledge_share=("knowledge_pat", "sum"),
            base_individual_share=("individual_pat", "sum"),
            base_org_share=("org_pat", "sum"),
            base_total=("total_patents", "sum"),
        )
    )
    for col in ["base_firm_share", "base_knowledge_share", "base_individual_share", "base_org_share"]:
        base_city[col] = base_city[col] / base_city["base_total"].where(base_city["base_total"] > 0)
        qname = col.replace("base_", "high_base_")
        base_city[qname] = (base_city[col] >= base_city[col].median()).astype("int8")
    out = out.merge(
        base_city[
            [
                "city",
                "base_firm_share",
                "base_knowledge_share",
                "base_individual_share",
                "base_org_share",
                "high_base_firm_share",
                "high_base_knowledge_share",
                "high_base_individual_share",
                "high_base_org_share",
            ]
        ],
        on="city",
        how="left",
    )
    out = out.fillna(0)
    return out


def main() -> None:
    detail = pd.read_csv(DETAIL, low_memory=False)
    detail = detail[detail["year"].between(WARMUP_YEAR, END_YEAR, inclusive="both")].copy()
    detail["applicant_norm"] = detail["applicant"].map(norm_name)
    detail = detail[detail["applicant_norm"] != ""].copy()
    detail["clean_type"] = detail["applicant_norm"].map(infer_type)
    detail = (
        detail.groupby(["city", "year", "applicant_norm", "clean_type"], as_index=False)
        .agg(patents=("patents", "sum"), applicant=("applicant", "first"))
    )
    detail["key"] = detail["city"] + "||" + detail["applicant_norm"]
    first_year = detail.groupby("key")["year"].min()
    detail["first_year"] = detail["key"].map(first_year)
    detail["is_new"] = detail["year"].eq(detail["first_year"])

    y = pd.read_csv(Y, low_memory=False, encoding="utf-8-sig")
    y = y[y["scope"] == "inv_app_appyear"][
        [
            "city",
            "year",
            "total_patents",
            "active_applicants",
            "new_applicants",
            "new_patents",
            "new_applicant_share",
        ]
    ].copy()

    out = add_type_metrics(y, detail, y)

    out_csv = PROCESSED / f"entry_type_mechanism_panel_{START_YEAR}_{END_YEAR}.csv"
    out_dta = PROCESSED / f"entry_type_mechanism_panel_{START_YEAR}_{END_YEAR}.dta"
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    out.to_stata(out_dta, write_index=False, version=118)

    print(f"wrote {out_csv} rows={len(out):,} cities={out['city'].nunique():,}")
    print(f"wrote {out_dta}")
    cols = [
        "firm_new_pat",
        "knowledge_new_pat",
        "individual_new_pat",
        "org_new_pat",
        "firm_new_n",
        "knowledge_new_n",
        "individual_new_n",
        "org_new_n",
    ]
    print(out[cols].sum().to_string())


if __name__ == "__main__":
    main()
