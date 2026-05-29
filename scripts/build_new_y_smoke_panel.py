#!/usr/bin/env python3
"""Build city-year smoke-test outcomes for alternative T10 Y choices.

Outcomes covered:
1. Sustained entrants: applicants first observed in a city-year who reappear in
   the same city within 2 or 3 years.
2. Top-applicant mobility: turnover of Top10/Top20 applicant lists against
   previous year and 2008-2010 baseline.
3. Quality entrant shares: new-entrant quality patents relative to main
   invention-application totals.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
COUNTS = PROCESSED / "city_applicant_counts_application_year/city_applicant_counts_inv_app_appyear_1985_2023.csv.gz"
BASE = PROCESSED / "idc_scope_policy_horserace_panel_2008_2023.csv"
TOP = PROCESSED / "top_applicants/city_year_top20_applicants_clean_inv_app_appyear_2008_2023.csv"
BASE_TOP = PROCESSED / "top_applicants/baseline_2008_2010_top20_applicants_clean_inv_app_appyear.csv"
QUALITY = PROCESSED / "idc_scope_appyear_quality_panel_2008_2023.csv"
OUT_CSV = PROCESSED / "new_y_smoke_panel_2008_2023.csv"
OUT_DTA = PROCESSED / "new_y_smoke_panel_2008_2023.dta"

START_YEAR = 2008
END_YEAR = 2023


def norm_name(name: object) -> str:
    text = "" if pd.isna(name) else str(name)
    text = text.strip().replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[;；,，]+$", "", text)
    return text


def build_sustained() -> pd.DataFrame:
    usecols = ["year", "city", "applicant", "patents"]
    detail = pd.read_csv(COUNTS, usecols=usecols, low_memory=False, encoding="utf-8-sig")
    detail = detail[detail["year"].between(1985, END_YEAR, inclusive="both")].copy()
    detail["applicant_norm"] = detail["applicant"].map(norm_name)
    detail = detail[detail["applicant_norm"] != ""].copy()
    detail["patents"] = pd.to_numeric(detail["patents"], errors="coerce").fillna(0)
    detail = (
        detail.groupby(["city", "applicant_norm", "year"], as_index=False)["patents"]
        .sum()
        .astype({"year": "int16"})
    )

    first = detail.groupby(["city", "applicant_norm"], as_index=False)["year"].min()
    first = first.rename(columns={"year": "first_year"})
    entry_patents = detail.rename(columns={"year": "first_year", "patents": "entry_patents"})
    first = first.merge(entry_patents, on=["city", "applicant_norm", "first_year"], how="left")

    entity_years = detail[["city", "applicant_norm", "year", "patents"]].drop_duplicates()
    future_flags = []
    future_pat_parts = []
    for lag in [1, 2, 3]:
        tmp = entity_years.copy()
        tmp["first_year"] = tmp["year"] - lag
        tmp["lag"] = lag
        future_flags.append(tmp[["city", "applicant_norm", "first_year", "lag"]])
        future_pat_parts.append(
            tmp[["city", "applicant_norm", "first_year", "lag", "patents"]].rename(
                columns={"patents": "future_patents"}
            )
        )

    flags = pd.concat(future_flags, ignore_index=True)
    flags = flags[flags["first_year"].between(START_YEAR, END_YEAR, inclusive="both")]
    flags["future2"] = flags["lag"].le(2)
    flags["future3"] = flags["lag"].le(3)
    flags = (
        flags.groupby(["city", "applicant_norm", "first_year"], as_index=False)
        .agg(has_future2=("future2", "max"), has_future3=("future3", "max"))
    )
    first = first.merge(flags, on=["city", "applicant_norm", "first_year"], how="left")
    first[["has_future2", "has_future3"]] = first[["has_future2", "has_future3"]].fillna(False)

    future_pat = pd.concat(future_pat_parts, ignore_index=True)
    future_pat = future_pat[future_pat["first_year"].between(START_YEAR, END_YEAR, inclusive="both")]
    future_pat2 = (
        future_pat[future_pat["lag"].le(2)]
        .groupby(["city", "applicant_norm", "first_year"], as_index=False)["future_patents"]
        .sum()
        .rename(columns={"future_patents": "future2_patents"})
    )
    future_pat3 = (
        future_pat[future_pat["lag"].le(3)]
        .groupby(["city", "applicant_norm", "first_year"], as_index=False)["future_patents"]
        .sum()
        .rename(columns={"future_patents": "future3_patents"})
    )
    first = first.merge(future_pat2, on=["city", "applicant_norm", "first_year"], how="left")
    first = first.merge(future_pat3, on=["city", "applicant_norm", "first_year"], how="left")
    first[["future2_patents", "future3_patents"]] = first[["future2_patents", "future3_patents"]].fillna(0)

    entrants = first[first["first_year"].between(START_YEAR, END_YEAR, inclusive="both")].copy()
    entrants["surv2_entry_patents"] = np.where(entrants["has_future2"], entrants["entry_patents"], 0)
    entrants["surv3_entry_patents"] = np.where(entrants["has_future3"], entrants["entry_patents"], 0)

    out = (
        entrants.groupby(["city", "first_year"], as_index=False)
        .agg(
            entrant_count=("applicant_norm", "nunique"),
            entrant_patents=("entry_patents", "sum"),
            surv2_applicants=("has_future2", "sum"),
            surv3_applicants=("has_future3", "sum"),
            surv2_entry_patents=("surv2_entry_patents", "sum"),
            surv3_entry_patents=("surv3_entry_patents", "sum"),
            surv2_future_patents=("future2_patents", "sum"),
            surv3_future_patents=("future3_patents", "sum"),
        )
        .rename(columns={"first_year": "year"})
    )
    out["surv2_applicant_rate"] = out["surv2_applicants"] / out["entrant_count"].where(out["entrant_count"] > 0)
    out["surv3_applicant_rate"] = out["surv3_applicants"] / out["entrant_count"].where(out["entrant_count"] > 0)
    out["surv2_entry_pat_share_new"] = out["surv2_entry_patents"] / out["entrant_patents"].where(out["entrant_patents"] > 0)
    out["surv3_entry_pat_share_new"] = out["surv3_entry_patents"] / out["entrant_patents"].where(out["entrant_patents"] > 0)

    # Avoid pretending we observe future behavior after the available window.
    for col in ["surv2_applicants", "surv2_entry_patents", "surv2_future_patents", "surv2_applicant_rate", "surv2_entry_pat_share_new"]:
        out.loc[out["year"] > END_YEAR - 2, col] = np.nan
    for col in ["surv3_applicants", "surv3_entry_patents", "surv3_future_patents", "surv3_applicant_rate", "surv3_entry_pat_share_new"]:
        out.loc[out["year"] > END_YEAR - 3, col] = np.nan
    return out


def top_metrics_for_n(top: pd.DataFrame, base_top: pd.DataFrame, n: int) -> pd.DataFrame:
    t = top[top["rank_city_year"] <= n].copy()
    b = base_top[base_top["rank_baseline"] <= n].copy()
    base_sets = b.groupby("city")["applicant_norm"].apply(set).to_dict()

    rows = []
    city_year_sets: dict[tuple[str, int], set[str]] = {}
    for (city, year), g in t.groupby(["city", "year"]):
        names = set(g["applicant_norm"])
        city_year_sets[(city, int(year))] = names

    for (city, year), g in t.groupby(["city", "year"]):
        year = int(year)
        names = set(g["applicant_norm"])
        prev = city_year_sets.get((city, year - 1), set())
        base = base_sets.get(city, set())
        current_n = len(names)
        top_patents = g["patents"].sum()

        prev_new = ~g["applicant_norm"].isin(prev)
        base_new = ~g["applicant_norm"].isin(base)
        rows.append(
            {
                "city": city,
                "year": year,
                f"top{n}_n": current_n,
                f"top{n}_turnover_prev_share": float(prev_new.sum() / current_n) if current_n else np.nan,
                f"top{n}_turnover_base_share": float(base_new.sum() / current_n) if current_n else np.nan,
                f"top{n}_turnover_prev_pat_share": float(g.loc[prev_new, "patents"].sum() / top_patents)
                if top_patents > 0
                else np.nan,
                f"top{n}_turnover_base_pat_share": float(g.loc[base_new, "patents"].sum() / top_patents)
                if top_patents > 0
                else np.nan,
                f"top{n}_persistence_prev_share": float((~prev_new).sum() / current_n) if current_n else np.nan,
                f"top{n}_persistence_base_share": float((~base_new).sum() / current_n) if current_n else np.nan,
            }
        )
    out = pd.DataFrame(rows)
    out.loc[out["year"] == START_YEAR, [f"top{n}_turnover_prev_share", f"top{n}_turnover_prev_pat_share", f"top{n}_persistence_prev_share"]] = np.nan
    return out


def build_top_mobility() -> pd.DataFrame:
    top = pd.read_csv(TOP, low_memory=False, encoding="utf-8-sig")
    base_top = pd.read_csv(BASE_TOP, low_memory=False, encoding="utf-8-sig")
    top["applicant_norm"] = top["applicant_norm"].map(norm_name)
    base_top["applicant_norm"] = base_top["applicant_norm"].map(norm_name)
    top["patents"] = pd.to_numeric(top["patents"], errors="coerce").fillna(0)
    parts = [top_metrics_for_n(top, base_top, 10), top_metrics_for_n(top, base_top, 20)]
    out = parts[0].merge(parts[1], on=["city", "year"], how="outer")
    return out


def build_quality_wide(base: pd.DataFrame) -> pd.DataFrame:
    q = pd.read_csv(QUALITY, low_memory=False, encoding="utf-8-sig")
    q = q[q["year"].between(START_YEAR, END_YEAR, inclusive="both")].copy()
    scope_short = {
        "inv_grant_appyear": "qgrant",
        "inv_grant_grantyear": "qgrantyr",
        "inv_grant_cited_appyear": "qcited",
        "inv_grant_familycited_appyear": "qfcited",
    }
    keep_scopes = list(scope_short)
    q = q[q["scope"].isin(keep_scopes)].copy()
    cols = ["total_patents", "active_applicants", "new_applicants", "new_patents", "new_applicant_share"]
    pieces = []
    for scope, g in q.groupby("scope"):
        sub = g[["city", "year"] + cols].copy()
        prefix = scope_short[scope]
        sub = sub.rename(
            columns={
                "total_patents": f"{prefix}_total",
                "active_applicants": f"{prefix}_active",
                "new_applicants": f"{prefix}_new_n",
                "new_patents": f"{prefix}_new_pat",
                "new_applicant_share": f"{prefix}_new_share",
            }
        )
        pieces.append(sub)
    out = pieces[0]
    for p in pieces[1:]:
        out = out.merge(p, on=["city", "year"], how="outer")

    main_cols = base[["city", "year", "total_patents", "new_patents"]].rename(
        columns={"total_patents": "main_total_patents", "new_patents": "main_new_patents"}
    )
    out = out.merge(main_cols, on=["city", "year"], how="left")
    for scope in keep_scopes:
        prefix = scope_short[scope]
        out[f"{prefix}_share_total"] = out[f"{prefix}_new_pat"] / out["main_total_patents"].where(
            out["main_total_patents"] > 0
        )
        out[f"{prefix}_share_new"] = out[f"{prefix}_new_pat"] / out["main_new_patents"].where(
            out["main_new_patents"] > 0
        )
        out[f"ln_{prefix}_new_n"] = np.log1p(out[f"{prefix}_new_n"].fillna(0))
        out[f"ln_{prefix}_new_pat"] = np.log1p(out[f"{prefix}_new_pat"].fillna(0))
    return out


def main() -> None:
    base = pd.read_csv(BASE, low_memory=False, encoding="utf-8-sig")
    base = base[
        (base["scope"] == "inv_app_appyear")
        & (base["year"].between(START_YEAR, END_YEAR, inclusive="both"))
        & (base["merge_idc_split"] == "both")
    ].copy()
    base = base.drop_duplicates(["city", "year"])

    sustained = build_sustained()
    top = build_top_mobility()
    quality = build_quality_wide(base)

    out = base.merge(sustained, on=["city", "year"], how="left")
    out = out.merge(top, on=["city", "year"], how="left")
    out = out.merge(quality, on=["city", "year"], how="left")

    for col in [
        "surv2_applicants",
        "surv3_applicants",
        "surv2_entry_patents",
        "surv3_entry_patents",
        "surv2_future_patents",
        "surv3_future_patents",
    ]:
        out[f"ln1p_{col}"] = np.log1p(out[col])
    out["surv2_entry_pat_share_total"] = out["surv2_entry_patents"] / out["total_patents"].where(out["total_patents"] > 0)
    out["surv3_entry_pat_share_total"] = out["surv3_entry_patents"] / out["total_patents"].where(out["total_patents"] > 0)

    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    out.to_stata(OUT_DTA, write_index=False, version=118)
    print(f"wrote {OUT_CSV} rows={len(out):,} cols={len(out.columns):,}")
    print("nonmissing key outcomes:")
    for col in [
        "surv2_applicant_rate",
        "surv2_entry_pat_share_total",
        "top10_turnover_prev_share",
        "top10_turnover_base_share",
        "qgrant_share_total",
        "qfcited_share_total",
    ]:
        print(col, int(out[col].notna().sum()) if col in out.columns else "MISSING")


if __name__ == "__main__":
    main()
