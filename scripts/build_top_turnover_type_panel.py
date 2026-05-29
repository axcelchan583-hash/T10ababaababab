#!/usr/bin/env python3
"""Build city-year Top applicant turnover type decomposition.

The dependent variable that survived the new-Y smoke test was the patent share
of current Top10/Top20 applicants who were not in the previous year's Top list.
This script decomposes that turnover by applicant type.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
TOP = PROCESSED / "top_applicants/city_year_top20_applicants_clean_inv_app_appyear_2008_2023.csv"
BASE = PROCESSED / "new_y_smoke_panel_2008_2023.csv"
OUT_CSV = PROCESSED / "top_turnover_type_panel_2008_2023.csv"
OUT_DTA = PROCESSED / "top_turnover_type_panel_2008_2023.dta"

START_YEAR = 2008
END_YEAR = 2023
TYPES = ["firm", "univ", "research", "hospital", "individual", "government", "other"]
TYPE_SHORT = {
    "firm": "firm",
    "univ": "univ",
    "research": "res",
    "hospital": "hosp",
    "individual": "ind",
    "government": "gov",
    "other": "oth",
}


def norm_name(name: object) -> str:
    text = "" if pd.isna(name) else str(name)
    text = text.strip().replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[;；,，]+$", "", text)
    return text


def metrics_for_n(top: pd.DataFrame, n: int) -> pd.DataFrame:
    t = top[top["rank_city_year"] <= n].copy()
    city_year_sets: dict[tuple[str, int], set[str]] = {
        (city, int(year)): set(g["applicant_norm"])
        for (city, year), g in t.groupby(["city", "year"], sort=False)
    }
    rows: list[dict] = []
    for (city, year), g in t.groupby(["city", "year"], sort=False):
        year = int(year)
        prev = city_year_sets.get((city, year - 1), set())
        top_patents = float(g["patents"].sum())
        new = ~g["applicant_norm"].isin(prev)
        turnover = g.loc[new].copy()
        turnover_patents = float(turnover["patents"].sum())
        row: dict[str, object] = {
            "city": city,
            "year": year,
            f"top{n}_patents": top_patents,
            f"top{n}_turnover_prev_patents": turnover_patents,
            f"top{n}_turnover_prev_pat_share": turnover_patents / top_patents if top_patents > 0 else np.nan,
        }
        for typ in TYPES:
            val = float(turnover.loc[turnover["clean_type"].eq(typ), "patents"].sum())
            short = TYPE_SHORT[typ]
            row[f"t{n}_new_{short}_pat"] = val
            row[f"t{n}_new_{short}_top"] = val / top_patents if top_patents > 0 else np.nan
            row[f"t{n}_new_{short}_turn"] = val / turnover_patents if turnover_patents > 0 else np.nan
        org_patents = float(turnover.loc[~turnover["clean_type"].eq("individual"), "patents"].sum())
        knowledge_patents = float(
            turnover.loc[turnover["clean_type"].isin(["univ", "research", "hospital"]), "patents"].sum()
        )
        row[f"t{n}_new_org_pat"] = org_patents
        row[f"t{n}_new_org_top"] = org_patents / top_patents if top_patents > 0 else np.nan
        row[f"t{n}_new_org_turn"] = org_patents / turnover_patents if turnover_patents > 0 else np.nan
        row[f"t{n}_new_kn_pat"] = knowledge_patents
        row[f"t{n}_new_kn_top"] = knowledge_patents / top_patents if top_patents > 0 else np.nan
        row[f"t{n}_new_kn_turn"] = knowledge_patents / turnover_patents if turnover_patents > 0 else np.nan
        rows.append(row)
    out = pd.DataFrame(rows)
    share_cols = [c for c in out.columns if c.startswith(f"t{n}_new_") and (c.endswith("_top") or c.endswith("_turn"))]
    out.loc[out["year"].eq(START_YEAR), share_cols] = np.nan
    return out


def main() -> None:
    top = pd.read_csv(TOP, low_memory=False, encoding="utf-8-sig")
    top = top[top["year"].between(START_YEAR, END_YEAR, inclusive="both")].copy()
    top["applicant_norm"] = top["applicant_norm"].map(norm_name)
    top["clean_type"] = top["clean_type"].fillna("other")
    top.loc[~top["clean_type"].isin(TYPES), "clean_type"] = "other"
    top["patents"] = pd.to_numeric(top["patents"], errors="coerce").fillna(0)

    parts = [metrics_for_n(top, 10), metrics_for_n(top, 20)]
    metrics = parts[0].merge(parts[1], on=["city", "year"], how="outer")

    base = pd.read_csv(BASE, low_memory=False, encoding="utf-8-sig")
    base = base[
        (base["scope"].eq("inv_app_appyear"))
        & (base["year"].between(START_YEAR, END_YEAR, inclusive="both"))
        & (base["merge_idc_split"].eq("both"))
    ].drop_duplicates(["city", "year"])
    out = base.merge(metrics, on=["city", "year"], how="left", suffixes=("", "_type"))
    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    out.to_stata(OUT_DTA, write_index=False, version=118)
    print(f"wrote {OUT_CSV} rows={len(out):,} cols={len(out.columns):,}")


if __name__ == "__main__":
    main()
