#!/usr/bin/env python3
"""Merge application-year applicant outcomes with split IDC proxies."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
PROCESSED = ROOT / "data/processed"
REPORTS = ROOT / "results/reports"


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def norm_city(s: pd.Series) -> pd.Series:
    return (
        s.astype("string")
        .str.strip()
        .str.replace("\u3000", "", regex=False)
        .str.replace(r"\s+", "", regex=True)
        .str.replace(r"^中国", "", regex=True)
        .str.replace(r"市$", "", regex=True)
    )


def main() -> None:
    y_path = PROCESSED / "patent_applicant_concentration_application_year_2008_2023.csv"
    x_path = PROCESSED / "idc_split_proxy_city_year_2000_2024.csv"
    out_csv = PROCESSED / "idc_split_applicant_concentration_application_year_panel_2008_2023.csv"
    out_dta = PROCESSED / "idc_split_applicant_concentration_application_year_panel_2008_2023.dta"
    report_path = REPORTS / "idc_split_applicant_concentration_application_year_panel_report_20260524.json"

    y = read_csv(y_path)
    x = read_csv(x_path)
    y["city"] = norm_city(y["city"])
    y["year"] = pd.to_numeric(y["year"], errors="coerce").astype("int16")
    x["city"] = norm_city(x["city"])
    x["province"] = norm_city(x["province"])
    x["year"] = pd.to_numeric(x["year"], errors="coerce").astype("int16")

    panel = y.merge(x, on=["city", "year"], how="left", indicator=True)
    panel["merge_idc_split"] = panel["_merge"].astype(str)
    panel = panel.drop(columns=["_merge"])
    panel["province"] = panel["province"].fillna("")
    prefixes = ["idc_scope", "idc_registered", "idc_combined"]
    for prefix in prefixes:
        for suffix in ["new", "stock", "ln1p_new", "ln1p_stock", "ln1p_stock_l1"]:
            col = f"{prefix}_{suffix}" if suffix in ["new", "stock"] else f"{suffix}_{prefix}"
            # Actual log columns are ln1p_idc_scope_new, etc.
        for col in [f"{prefix}_new", f"{prefix}_stock", f"ln1p_{prefix}_new", f"ln1p_{prefix}_stock", f"ln1p_{prefix}_stock_l1"]:
            panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0)

    panel["city_id"] = pd.factorize(panel["city"])[0] + 1
    panel["province_id"] = pd.factorize(panel["province"])[0] + 1

    base = (
        panel[panel["year"].between(2008, 2010, inclusive="both")]
        .groupby("city", as_index=False)
        .agg(
            base_ln_patents=("ln1p_total_patents", "mean"),
            base_hhi=("hhi", "mean"),
            base_top10=("top10_share", "mean"),
            base_active=("ln1p_active_applicants", "mean"),
        )
    )
    panel = panel.merge(base, on="city", how="left")
    for col in ["base_ln_patents", "base_hhi", "base_top10", "base_active"]:
        panel[col] = pd.to_numeric(panel[col], errors="coerce")
        panel[f"{col}_q"] = pd.qcut(panel[col], q=4, labels=False, duplicates="drop") + 1
        panel[f"{col}_q"] = panel[f"{col}_q"].fillna(0).astype("int8")

    panel = panel.sort_values(["city", "year"]).reset_index(drop=True)
    panel.to_csv(out_csv, index=False, encoding="utf-8-sig")
    panel.to_stata(out_dta, write_index=False, version=118)

    report = {
        "rows": int(len(panel)),
        "cities": int(panel["city"].nunique()),
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "matched_rows": int((panel["merge_idc_split"] == "both").sum()),
        "matched_cities": int(panel.loc[panel["merge_idc_split"] == "both", "city"].nunique()),
        "cities_with_scope_stock": int(panel.loc[panel["idc_scope_stock"] > 0, "city"].nunique()),
        "cities_with_registered_stock": int(panel.loc[panel["idc_registered_stock"] > 0, "city"].nunique()),
        "cities_with_combined_stock": int(panel.loc[panel["idc_combined_stock"] > 0, "city"].nunique()),
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path.write_text(pd.Series(report).to_json(force_ascii=False, indent=2), encoding="utf-8")
    print(pd.Series(report).to_string())


if __name__ == "__main__":
    main()
