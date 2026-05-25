#!/usr/bin/env python3
"""Export city-year and baseline top patent applicants for manual inspection."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
DETAIL = ROOT / "data/processed/city_applicant_counts_application_year/city_applicant_counts_inv_app_appyear_2000_2023.csv.gz"
OUTDIR = ROOT / "data/processed/top_applicants"


def infer_type(name: str) -> str:
    text = str(name)
    if any(k in text for k in ["医院", "卫生院"]):
        return "hospital"
    if any(k in text for k in ["研究院", "研究所", "科学院", "实验室"]) and "有限公司" not in text:
        return "research_institute"
    if any(k in text for k in ["大学", "学院"]) and "有限公司" not in text:
        return "university_or_college"
    if any(k in text for k in ["有限公司", "股份有限公司", "集团", "公司", "厂", "企业"]):
        return "firm"
    if any(k in text for k in ["政府", "委员会", "管理局", "财政局", "科技局", "知识产权局", "管委会"]):
        return "government"
    if 2 <= len(text) <= 4 and not any(k in text for k in ["市", "县", "区", "省"]):
        return "likely_individual"
    return "other_org_or_unclear"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2008)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--baseline-start-year", type=int, default=2008)
    parser.add_argument("--baseline-end-year", type=int, default=2010)
    parser.add_argument("--top-n", type=int, default=20)
    args = parser.parse_args()

    OUTDIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DETAIL)
    df = df[(df["year"] >= args.start_year) & (df["year"] <= args.end_year)].copy()
    df["applicant_type_rough"] = df["applicant"].map(infer_type)

    df = df.sort_values(["city", "year", "patents", "applicant"], ascending=[True, True, False, True])
    df["rank_city_year"] = df.groupby(["city", "year"]).cumcount() + 1
    top = df[df["rank_city_year"] <= args.top_n].copy()
    top_out = OUTDIR / f"city_year_top{args.top_n}_applicants_inv_app_appyear_{args.start_year}_{args.end_year}.csv"
    top.to_csv(top_out, index=False)

    base = df[(df["year"] >= args.baseline_start_year) & (df["year"] <= args.baseline_end_year)]
    base = (
        base.groupby(["city", "applicant", "applicant_type_rough"], as_index=False)["patents"]
        .sum()
        .sort_values(["city", "patents", "applicant"], ascending=[True, False, True])
    )
    base["rank_baseline"] = base.groupby("city").cumcount() + 1
    base_top = base[base["rank_baseline"] <= args.top_n].copy()
    base_out = OUTDIR / f"baseline_{args.baseline_start_year}_{args.baseline_end_year}_top{args.top_n}_applicants_inv_app_appyear.csv"
    base_top.to_csv(base_out, index=False)

    summary = (
        top.groupby(["year", "applicant_type_rough"], as_index=False)
        .agg(top_rows=("applicant", "size"), top_patents=("patents", "sum"))
        .sort_values(["year", "top_patents"], ascending=[True, False])
    )
    summary_out = OUTDIR / f"city_year_top{args.top_n}_type_summary_inv_app_appyear_{args.start_year}_{args.end_year}.csv"
    summary.to_csv(summary_out, index=False)

    print(f"wrote {top_out} rows={len(top):,}")
    print(f"wrote {base_out} rows={len(base_top):,}")
    print(f"wrote {summary_out} rows={len(summary):,}")


if __name__ == "__main__":
    main()
