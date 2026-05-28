#!/usr/bin/env python3
"""Add formal IDC-scope robustness variables to the applicant-concentration panel."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
REPORTS = ROOT / "results/reports"


def main() -> None:
    in_path = PROCESSED / "idc_split_applicant_concentration_application_year_panel_2008_2023.csv"
    out_csv = PROCESSED / "idc_scope_formal_application_year_panel_2008_2023.csv"
    out_dta = PROCESSED / "idc_scope_formal_application_year_panel_2008_2023.dta"
    report_path = REPORTS / "idc_scope_formal_application_year_panel_report_20260525.json"

    panel = pd.read_csv(in_path, low_memory=False, encoding="utf-8-sig")
    panel = panel.sort_values(["city", "year"]).reset_index(drop=True)

    for prefix in ["idc_scope", "idc_registered", "idc_combined"]:
        new_col = f"{prefix}_new"
        pre5_col = f"{prefix}_pre5"
        panel[pre5_col] = (
            panel.groupby("city", group_keys=False)[new_col]
            .apply(lambda s: s.rolling(window=5, min_periods=1).sum())
            .astype(float)
        )
        panel[f"ln1p_{pre5_col}"] = np.log1p(panel[pre5_col])
        panel[f"ln1p_{pre5_col}_l1"] = (
            panel.groupby("city")[f"ln1p_{pre5_col}"].shift(1).fillna(0)
        )
        panel[f"ln1p_{prefix}_new_l1"] = (
            panel.groupby("city")[f"ln1p_{prefix}_new"].shift(1).fillna(0)
        )

    province_year = (
        panel[["province", "year", "idc_scope_new", "idc_registered_new", "idc_combined_new"]]
        .drop_duplicates(["province", "year", "idc_scope_new", "idc_registered_new", "idc_combined_new"])
    )
    province_year = (
        panel.groupby(["province", "year"], as_index=False)
        .agg(
            idc_scope_prov_new=("idc_scope_new", "sum"),
            idc_registered_prov_new=("idc_registered_new", "sum"),
            idc_combined_prov_new=("idc_combined_new", "sum"),
        )
        .sort_values(["province", "year"])
    )
    for prefix in ["idc_scope_prov", "idc_registered_prov", "idc_combined_prov"]:
        province_year[f"{prefix}_stock"] = province_year.groupby("province")[f"{prefix}_new"].cumsum()
        province_year[f"{prefix}_pre5"] = (
            province_year.groupby("province", group_keys=False)[f"{prefix}_new"]
            .apply(lambda s: s.rolling(window=5, min_periods=1).sum())
            .astype(float)
        )
        for suffix in ["new", "stock", "pre5"]:
            province_year[f"ln1p_{prefix}_{suffix}"] = np.log1p(province_year[f"{prefix}_{suffix}"])
            province_year[f"ln1p_{prefix}_{suffix}_l1"] = (
                province_year.groupby("province")[f"ln1p_{prefix}_{suffix}"].shift(1).fillna(0)
            )

    keep_prov_cols = [
        c for c in province_year.columns if c not in {"idc_registered_prov_new", "idc_registered_prov_stock",
                                                      "idc_registered_prov_pre5", "idc_combined_prov_new",
                                                      "idc_combined_prov_stock", "idc_combined_prov_pre5"}
    ]
    panel = panel.merge(province_year[keep_prov_cols], on=["province", "year"], how="left")

    for col in panel.columns:
        if col.startswith(("idc_", "ln1p_idc_")):
            panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0)

    panel.to_csv(out_csv, index=False, encoding="utf-8-sig")
    panel.to_stata(out_dta, write_index=False, version=118)

    report = {
        "rows": int(len(panel)),
        "cities": int(panel["city"].nunique()),
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "cities_with_scope_stock": int(panel.loc[panel["idc_scope_stock"] > 0, "city"].nunique()),
        "cities_with_scope_pre5": int(panel.loc[panel["idc_scope_pre5"] > 0, "city"].nunique()),
        "provinces_with_scope_stock": int(panel.loc[panel["idc_scope_prov_stock"] > 0, "province"].nunique()),
        "main_x": "ln1p_idc_scope_stock_l1",
        "robustness_x": [
            "ln1p_idc_scope_new_l1",
            "ln1p_idc_scope_pre5_l1",
            "ln1p_idc_scope_prov_stock_l1",
            "ln1p_idc_registered_stock_l1",
            "ln1p_idc_combined_stock_l1",
        ],
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
