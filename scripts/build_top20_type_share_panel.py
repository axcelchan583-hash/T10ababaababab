#!/usr/bin/env python3
"""Build rough city-year Top20 applicant type share outcomes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
PROCESSED = ROOT / "data/processed"
TOP = PROCESSED / "top_applicants/city_year_top20_applicants_inv_app_appyear_2008_2023.csv"
Y = PROCESSED / "patent_applicant_concentration_application_year_2008_2023.csv"


TYPE_MAP = {
    "firm": "firm",
    "university_or_college": "univ",
    "research_institute": "research",
    "hospital": "hospital",
    "likely_individual": "individual",
    "government": "government",
    "other_org_or_unclear": "other",
}


def main() -> None:
    top = pd.read_csv(TOP, low_memory=False)
    y = pd.read_csv(Y, low_memory=False, encoding="utf-8-sig")
    y = y[y["scope"] == "inv_app_appyear"][["city", "year", "total_patents"]].copy()
    top["type_short"] = top["applicant_type_rough"].map(TYPE_MAP).fillna("other")

    pivot = (
        top.pivot_table(
            index=["city", "year"],
            columns="type_short",
            values="patents",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )
    for t in TYPE_MAP.values():
        if t not in pivot.columns:
            pivot[t] = 0
    type_cols = sorted(set(TYPE_MAP.values()))
    pivot["top20_patents"] = pivot[type_cols].sum(axis=1)
    out = y.merge(pivot, on=["city", "year"], how="left")
    for col in type_cols + ["top20_patents"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
        out[f"top20_{col}_share_total"] = out[col] / out["total_patents"].where(out["total_patents"] > 0)
        if col != "top20_patents":
            out[f"top20_{col}_share_top20"] = out[col] / out["top20_patents"].where(out["top20_patents"] > 0)

    keep = ["city", "year", "total_patents", "top20_patents"]
    for t in type_cols:
        keep += [f"top20_{t}_share_total", f"top20_{t}_share_top20"]
    out = out[keep].fillna(0)

    out_csv = PROCESSED / "top20_type_share_panel_2008_2023.csv"
    out_dta = PROCESSED / "top20_type_share_panel_2008_2023.dta"
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    out.to_stata(out_dta, write_index=False, version=118)
    print(f"wrote {out_csv} rows={len(out):,} cities={out['city'].nunique():,}")


if __name__ == "__main__":
    main()
