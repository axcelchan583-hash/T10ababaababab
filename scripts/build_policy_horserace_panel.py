#!/usr/bin/env python3
"""Merge city policy horse-race controls into the main application-year panel.

This script intentionally does not create policy variables. It expects a
manually/audited city-year policy panel at:

    data/external_proxy/city_policy_horserace_panel_2008_2023.csv

Required keys: city, year. Policy columns should be 0/1 post-adoption dummies or
counts. The blank template is:

    data/external_proxy/city_policy_horserace_template_2008_2023.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23实证选题探索/T10")
PROCESSED = ROOT / "data/processed"
EXTERNAL = ROOT / "data/external_proxy"
MAIN = PROCESSED / "idc_scope_formal_application_year_panel_2008_2023.csv"
POLICY = EXTERNAL / "city_policy_horserace_panel_2008_2023.csv"
OUT_CSV = PROCESSED / "idc_scope_policy_horserace_panel_2008_2023.csv"
OUT_DTA = PROCESSED / "idc_scope_policy_horserace_panel_2008_2023.dta"

POLICY_COLS = [
    "broadband_china_pilot",
    "smart_city_pilot",
    "bigdata_comprehensive_pilot",
    "innovative_city_pilot",
    "national_hightech_zone",
    "ip_demo_city",
    "information_consumption_pilot",
    "ecommerce_demo_city",
]


def main() -> None:
    if not POLICY.exists():
        raise FileNotFoundError(
            f"Missing audited policy panel: {POLICY}\n"
            "Fill/copy the template first: "
            f"{EXTERNAL / 'city_policy_horserace_template_2008_2023.csv'}"
        )

    main = pd.read_csv(MAIN, encoding="utf-8-sig", low_memory=False)
    policy = pd.read_csv(POLICY, encoding="utf-8-sig", low_memory=False)
    required = {"city", "year"}
    if not required.issubset(policy.columns):
        raise ValueError(f"Policy panel must contain columns: {sorted(required)}")

    available = [c for c in POLICY_COLS if c in policy.columns]
    if not available:
        raise ValueError(f"No recognized policy columns found. Expected any of: {POLICY_COLS}")

    policy = policy[["city", "year", *available]].copy()
    for col in available:
        policy[col] = pd.to_numeric(policy[col], errors="coerce")
    nonmissing = policy[available].notna().sum().sum()
    if nonmissing == 0:
        raise ValueError("Policy columns are all missing; refusing to create a fake horse-race panel.")

    out = main.merge(policy, on=["city", "year"], how="left", validate="m:1")
    for col in available:
        out[col] = out[col].fillna(0).astype("int8")
    if "new_patents" in out.columns and "ln1p_new_patents" not in out.columns:
        out["ln1p_new_patents"] = np.log1p(pd.to_numeric(out["new_patents"], errors="coerce").fillna(0))
    if "incumbent_patents" not in out.columns and {"total_patents", "new_patents"}.issubset(out.columns):
        out["incumbent_patents"] = (
            pd.to_numeric(out["total_patents"], errors="coerce").fillna(0)
            - pd.to_numeric(out["new_patents"], errors="coerce").fillna(0)
        )
    if "incumbent_patents" in out.columns and "ln1p_incumbent_patents" not in out.columns:
        out["ln1p_incumbent_patents"] = np.log1p(pd.to_numeric(out["incumbent_patents"], errors="coerce").clip(lower=0).fillna(0))
    out["policy_horserace_controls"] = ",".join(available)
    out["merge_policy_horserace"] = np.where(out[available].notna().any(axis=1), "both_or_zero", "left_only")

    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    out.to_stata(OUT_DTA, write_index=False, version=118)
    print(f"wrote {OUT_CSV} rows={len(out):,} policy_cols={available}")


if __name__ == "__main__":
    main()
