#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "results" / "reports"


def topn_flags_from_scores(scores: pd.DataFrame, score_col: str, top_n: int, flag_col: str) -> pd.DataFrame:
    if scores.empty:
        return pd.DataFrame(columns=["city", "year", "applicant", flag_col])
    scores = scores.sort_values(["city", "year", score_col, "applicant"], ascending=[True, True, False, True])
    scores["_rank"] = scores.groupby(["city", "year"]).cumcount() + 1
    out = scores.loc[scores["_rank"] <= top_n, ["city", "year", "applicant"]].copy()
    out[flag_col] = True
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", default="inv_app_appyear")
    parser.add_argument("--warmup-start-year", type=int, default=1985)
    parser.add_argument("--start-year", type=int, default=2008)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--baseline-start-year", type=int, default=2008)
    parser.add_argument("--baseline-end-year", type=int, default=2010)
    parser.add_argument("--rolling-window", type=int, default=3)
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()

    detail_path = (
        PROCESSED
        / "city_applicant_counts_application_year"
        / f"city_applicant_counts_{args.scope}_{args.warmup_start_year}_{args.end_year}.csv.gz"
    )
    out_csv = PROCESSED / f"patent_applicant_concentration_application_year_{args.start_year}_{args.end_year}.csv"
    out_dta = PROCESSED / f"patent_applicant_concentration_application_year_{args.start_year}_{args.end_year}.dta"
    report_path = REPORTS / f"patent_applicant_concentration_application_year_metrics_report_{args.start_year}_{args.end_year}.json"

    df = pd.read_csv(detail_path, encoding="utf-8-sig")
    df = df[df["scope"].eq(args.scope)].copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("int16")
    df["patents"] = pd.to_numeric(df["patents"], errors="coerce").fillna(0).astype("int32")
    df = df[(df["year"] <= args.end_year) & (df["patents"] > 0)]

    df["key"] = df["city"] + "\t" + df["applicant"]
    df["first_year"] = df.groupby("key")["year"].transform("min")
    df["is_new"] = df["year"].eq(df["first_year"])
    df["patents_sq"] = df["patents"].astype("float64") ** 2
    df["new_patents_part"] = np.where(df["is_new"], df["patents"], 0)

    current = df[df["year"].between(args.start_year, args.end_year, inclusive="both")].copy()

    base = (
        current.groupby(["city", "year"], as_index=False)
        .agg(
            total_patents=("patents", "sum"),
            active_applicants=("applicant", "nunique"),
            patent_sq_sum=("patents_sq", "sum"),
            new_applicants=("is_new", "sum"),
            new_patents=("new_patents_part", "sum"),
        )
    )

    ranked_current = current.sort_values(["city", "year", "patents", "applicant"], ascending=[True, True, False, True]).copy()
    ranked_current["_rank"] = ranked_current.groupby(["city", "year"]).cumcount() + 1
    top_sums = []
    for n in [1, 5, 10]:
        part = (
            ranked_current[ranked_current["_rank"] <= n]
            .groupby(["city", "year"], as_index=False)["patents"]
            .sum()
            .rename(columns={"patents": f"top{n}_patents"})
        )
        top_sums.append(part)

    out = base
    for part in top_sums:
        out = out.merge(part, on=["city", "year"], how="left")
    for col in ["top1_patents", "top5_patents", "top10_patents"]:
        out[col] = out[col].fillna(0)

    shifted = []
    for lag in range(1, args.rolling_window + 1):
        tmp = df[["city", "applicant", "year", "patents"]].copy()
        tmp["year"] = tmp["year"] + lag
        tmp = tmp[tmp["year"].between(args.start_year, args.end_year, inclusive="both")]
        shifted.append(tmp)
    rolling_scores = (
        pd.concat(shifted, ignore_index=True)
        .groupby(["city", "year", "applicant"], as_index=False)["patents"]
        .sum()
        .rename(columns={"patents": "rolling_prev_patents"})
    )
    roll_flags = topn_flags_from_scores(rolling_scores, "rolling_prev_patents", args.top_n, "is_roll_top")

    base_scores = (
        df[df["year"].between(args.baseline_start_year, args.baseline_end_year, inclusive="both")]
        .groupby(["city", "applicant"], as_index=False)["patents"]
        .sum()
        .rename(columns={"patents": "base_patents"})
    )
    base_scores["year"] = args.start_year
    base_flags = []
    for city, g in base_scores.groupby("city", sort=False):
        top = g.sort_values(["base_patents", "applicant"], ascending=[False, True]).head(args.top_n)
        if top.empty:
            continue
        tmp = pd.DataFrame(
            {
                "city": city,
                "applicant": top["applicant"].tolist(),
            }
        )
        tmp["is_base_top"] = True
        base_flags.append(tmp)
    base_flags = pd.concat(base_flags, ignore_index=True) if base_flags else pd.DataFrame(columns=["city", "applicant", "is_base_top"])

    detail_flags = current[["city", "year", "applicant", "patents", "is_new"]].copy()
    detail_flags = detail_flags.merge(roll_flags, on=["city", "year", "applicant"], how="left")
    detail_flags = detail_flags.merge(base_flags, on=["city", "applicant"], how="left")
    detail_flags["is_roll_top"] = detail_flags["is_roll_top"].fillna(False)
    detail_flags["is_base_top"] = detail_flags["is_base_top"].fillna(False)
    detail_flags["roll_top_part"] = np.where(detail_flags["is_roll_top"], detail_flags["patents"], 0)
    detail_flags["base_top_part"] = np.where(detail_flags["is_base_top"], detail_flags["patents"], 0)
    detail_flags["roll_mid_part"] = np.where((~detail_flags["is_new"]) & (~detail_flags["is_roll_top"]), detail_flags["patents"], 0)
    detail_flags["base_mid_part"] = np.where((~detail_flags["is_new"]) & (~detail_flags["is_base_top"]), detail_flags["patents"], 0)

    decomp = (
        detail_flags.groupby(["city", "year"], as_index=False)
        .agg(
            roll_top_patents=("roll_top_part", "sum"),
            base_top_patents=("base_top_part", "sum"),
            roll_mid_inc_patents=("roll_mid_part", "sum"),
            base_mid_inc_patents=("base_mid_part", "sum"),
        )
    )
    out = out.merge(decomp, on=["city", "year"], how="left")
    for col in ["roll_top_patents", "base_top_patents", "roll_mid_inc_patents", "base_mid_inc_patents"]:
        out[col] = out[col].fillna(0)

    out["scope"] = args.scope
    out["hhi"] = out["patent_sq_sum"] / (out["total_patents"].astype("float64") ** 2)
    out["effective_applicants"] = 1.0 / out["hhi"]
    out["new_applicant_share"] = out["new_patents"] / out["total_patents"]
    out["top1_share"] = out["top1_patents"] / out["total_patents"]
    out["top5_share"] = out["top5_patents"] / out["total_patents"]
    out["top10_share"] = out["top10_patents"] / out["total_patents"]
    out["roll_top_share"] = out["roll_top_patents"] / out["total_patents"]
    out["base_top_share"] = out["base_top_patents"] / out["total_patents"]
    out["roll_mid_inc_share"] = out["roll_mid_inc_patents"] / out["total_patents"]
    out["base_mid_inc_share"] = out["base_mid_inc_patents"] / out["total_patents"]
    out["ln1p_total_patents"] = np.log1p(out["total_patents"])
    out["ln1p_active_applicants"] = np.log1p(out["active_applicants"])
    out["ln1p_new_applicants"] = np.log1p(out["new_applicants"])
    out["ln_effective_applicants"] = np.log(out["effective_applicants"])
    out["roll_top_n"] = args.top_n
    out["base_top_n"] = args.top_n

    keep = [
        "city",
        "year",
        "scope",
        "total_patents",
        "active_applicants",
        "hhi",
        "top1_share",
        "top5_share",
        "top10_share",
        "effective_applicants",
        "new_applicants",
        "new_patents",
        "new_applicant_share",
        "roll_top_patents",
        "roll_top_share",
        "roll_mid_inc_patents",
        "roll_mid_inc_share",
        "base_top_patents",
        "base_top_share",
        "base_mid_inc_patents",
        "base_mid_inc_share",
        "ln1p_total_patents",
        "ln1p_active_applicants",
        "ln1p_new_applicants",
        "ln_effective_applicants",
        "roll_top_n",
        "base_top_n",
    ]
    out = out[keep].sort_values(["city", "year"]).reset_index(drop=True)
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    out.to_stata(out_dta, write_index=False, version=118)

    report = {
        "detail_path": str(detail_path),
        "detail_rows": int(len(df)),
        "output_rows": int(len(out)),
        "cities": int(out["city"].nunique()),
        "years": [int(out["year"].min()), int(out["year"].max())],
        "scope": args.scope,
        "warmup_start_year": args.warmup_start_year,
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
