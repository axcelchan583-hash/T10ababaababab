#!/usr/bin/env python3
"""Build publication/grant-year robustness panel with formal IDC scope X."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23实证选题探索/T10")
PROCESSED = ROOT / "data/processed"
Y = PROCESSED / "patent_applicant_concentration_city_year_2008_2024.csv"
IDC = PROCESSED / "idc_split_proxy_city_year_2000_2024.csv"
START_YEAR = 2008
END_YEAR = 2024


def qcut4(s: pd.Series) -> pd.Series:
    if s.notna().sum() < 4 or s.nunique(dropna=True) < 4:
        return pd.Series(1, index=s.index, dtype="int8")
    return pd.qcut(s.rank(method="first"), 4, labels=False).astype("int8") + 1


def main() -> None:
    y = pd.read_csv(Y, low_memory=False, encoding="utf-8-sig")
    y = y[y["year"].between(START_YEAR, END_YEAR, inclusive="both")].copy()
    idc = pd.read_csv(IDC, low_memory=False, encoding="utf-8-sig")
    out = y.merge(idc, on=["city", "year"], how="left", suffixes=("", "_idc"))
    if "province" not in out.columns and "province_idc" in out.columns:
        out["province"] = out["province_idc"]
    elif "province_idc" in out.columns:
        out["province"] = out["province"].fillna(out["province_idc"])
    out["province"] = out["province"].astype("string").fillna("")
    out["merge_idc_split"] = np.where(out["idc_scope_stock"].notna(), "both", "left_only")
    idc_cols = [c for c in out.columns if c.startswith("idc_") or c.startswith("ln1p_idc_")]
    out[idc_cols] = out[idc_cols].fillna(0)

    out["ln1p_total_patents"] = np.log1p(out["total_patents"])
    out["ln1p_active_applicants"] = np.log1p(out["active_applicants"])
    out["ln1p_new_applicants"] = np.log1p(out["new_applicants"])
    out["ln1p_new_patents"] = np.log1p(out["new_patents"])
    out["incumbent_patents"] = out["total_patents"] - out["new_patents"]
    out["ln1p_incumbent_patents"] = np.log1p(out["incumbent_patents"])
    out["incumbent_share"] = out["incumbent_patents"] / out["total_patents"].where(out["total_patents"] > 0)

    city_levels = sorted(out["city"].dropna().unique())
    prov_levels = sorted(out["province"].dropna().unique())
    out["city_id"] = out["city"].map({v: i + 1 for i, v in enumerate(city_levels)}).astype("int32")
    out["province_id"] = out["province"].map({v: i + 1 for i, v in enumerate(prov_levels)}).fillna(0).astype("int16")

    bases = []
    for scope, g in out[out["year"].between(2008, 2010, inclusive="both")].groupby("scope"):
        b = (
            g.groupby("city", as_index=False)
            .agg(
                base_ln_patents=("ln1p_total_patents", "mean"),
                base_hhi=("hhi", "mean"),
                base_top10=("top10_share", "mean"),
                base_active=("ln1p_active_applicants", "mean"),
            )
        )
        b["scope"] = scope
        for col in ["base_ln_patents", "base_hhi", "base_top10", "base_active"]:
            b[f"{col}_q"] = qcut4(b[col])
        bases.append(b)
    base = pd.concat(bases, ignore_index=True)
    out = out.merge(base, on=["scope", "city"], how="left")
    qcols = [c for c in out.columns if c.endswith("_q")]
    out[qcols] = out[qcols].fillna(1).astype("int8")
    out = out.fillna(0)

    out_csv = PROCESSED / f"idc_scope_pubyear_quality_panel_{START_YEAR}_{END_YEAR}.csv"
    out_dta = PROCESSED / f"idc_scope_pubyear_quality_panel_{START_YEAR}_{END_YEAR}.dta"
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    out.to_stata(out_dta, write_index=False, version=118)
    print(f"wrote {out_csv} rows={len(out):,} scopes={out['scope'].nunique()}")
    print(out["scope"].value_counts().to_string())


if __name__ == "__main__":
    main()
