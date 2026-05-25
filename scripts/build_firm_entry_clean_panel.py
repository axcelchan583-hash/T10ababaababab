#!/usr/bin/env python3
"""Build firm-only innovation entry outcomes for T10.

The panel tests whether IDC service coverage expands the enterprise side of
the innovation-entry margin, rather than only raising entry by individuals.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from build_top_applicant_type_clean_panel import infer_type, norm_name


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
PROCESSED = ROOT / "data/processed"
DETAIL = PROCESSED / "city_applicant_counts_application_year/city_applicant_counts_inv_app_appyear_2000_2023.csv.gz"
Y = PROCESSED / "patent_applicant_concentration_application_year_2008_2023.csv"

START_YEAR = 2008
END_YEAR = 2023
WARMUP_YEAR = 2000


def main() -> None:
    detail = pd.read_csv(DETAIL, low_memory=False)
    detail = detail[(detail["year"] >= WARMUP_YEAR) & (detail["year"] <= END_YEAR)].copy()
    detail["applicant_norm"] = detail["applicant"].map(norm_name)
    detail = detail[detail["applicant_norm"] != ""].copy()
    detail["clean_type"] = detail["applicant_norm"].map(infer_type)
    firm = detail[detail["clean_type"] == "firm"].copy()

    firm = (
        firm.groupby(["city", "year", "applicant_norm"], as_index=False)
        .agg(patents=("patents", "sum"), applicant=("applicant", "first"))
    )
    firm["key"] = firm["city"] + "||" + firm["applicant_norm"]
    first_year = firm.groupby("key")["year"].min()
    firm["first_year"] = firm["key"].map(first_year)
    firm["is_new_firm"] = firm["year"].eq(firm["first_year"])
    firm["new_firm_patents_part"] = np.where(firm["is_new_firm"], firm["patents"], 0)

    sample = firm[(firm["year"] >= START_YEAR) & (firm["year"] <= END_YEAR)].copy()
    metrics = (
        sample.groupby(["city", "year"], as_index=False)
        .agg(
            firm_total_patents=("patents", "sum"),
            firm_active_applicants=("applicant_norm", "nunique"),
            new_firm_applicants=("is_new_firm", "sum"),
            new_firm_patents=("new_firm_patents_part", "sum"),
        )
    )
    metrics["firm_incumbent_patents"] = metrics["firm_total_patents"] - metrics["new_firm_patents"]
    metrics["firm_incumbent_applicants"] = metrics["firm_active_applicants"] - metrics["new_firm_applicants"]

    y = pd.read_csv(Y, low_memory=False, encoding="utf-8-sig")
    y = y[y["scope"] == "inv_app_appyear"][
        ["city", "year", "total_patents", "active_applicants", "new_applicants", "new_patents", "new_applicant_share"]
    ].copy()
    out = y.merge(metrics, on=["city", "year"], how="left")

    firm_cols = [
        "firm_total_patents",
        "firm_active_applicants",
        "new_firm_applicants",
        "new_firm_patents",
        "firm_incumbent_patents",
        "firm_incumbent_applicants",
    ]
    out[firm_cols] = out[firm_cols].fillna(0)

    out["firm_new_share_firm"] = out["new_firm_patents"] / out["firm_total_patents"].where(
        out["firm_total_patents"] > 0
    )
    out["firm_new_share_total"] = out["new_firm_patents"] / out["total_patents"].where(out["total_patents"] > 0)
    out["firm_patent_share_total"] = out["firm_total_patents"] / out["total_patents"].where(out["total_patents"] > 0)
    out["firm_incumbent_share_total"] = out["firm_incumbent_patents"] / out["total_patents"].where(
        out["total_patents"] > 0
    )
    out["new_firm_share_all_new_patents"] = out["new_firm_patents"] / out["new_patents"].where(
        out["new_patents"] > 0
    )

    for col in firm_cols:
        out[f"ln1p_{col}"] = np.log1p(out[col])
    out = out.fillna(0)

    out_csv = PROCESSED / f"firm_entry_clean_panel_{START_YEAR}_{END_YEAR}.csv"
    out_dta = PROCESSED / f"firm_entry_clean_panel_{START_YEAR}_{END_YEAR}.dta"
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    out.to_stata(out_dta, write_index=False, version=118)

    print(f"wrote {out_csv} rows={len(out):,} cities={out['city'].nunique():,}")
    print(f"wrote {out_dta}")
    print(
        out[
            [
                "firm_total_patents",
                "new_firm_patents",
                "firm_incumbent_patents",
                "firm_active_applicants",
                "new_firm_applicants",
                "firm_new_share_firm",
                "firm_new_share_total",
            ]
        ].describe().to_string()
    )


if __name__ == "__main__":
    main()
