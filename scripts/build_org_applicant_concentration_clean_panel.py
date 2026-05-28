#!/usr/bin/env python3
"""Build organization-only applicant concentration outcomes.

This diagnostic removes likely individual applicants before computing HHI,
Top10 share, and new-entry outcomes. It tests whether the concentration signal
is driven by individual-applicant noise in small city-years.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from build_top_applicant_type_clean_panel import infer_type, norm_name


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"

START_YEAR = 2008
END_YEAR = 2023
WARMUP_YEAR = 1985
DETAIL = (
    PROCESSED
    / f"city_applicant_counts_application_year/city_applicant_counts_inv_app_appyear_{WARMUP_YEAR}_{END_YEAR}.csv.gz"
)
Y = PROCESSED / "patent_applicant_concentration_application_year_2008_2023.csv"


def top_share(values: pd.Series, n: int) -> float:
    total = values.sum()
    if total <= 0:
        return 0.0
    return values.nlargest(n).sum() / total


def hhi(values: pd.Series) -> float:
    total = values.sum()
    if total <= 0:
        return 0.0
    shares = values / total
    return float(np.square(shares).sum())


def main() -> None:
    detail = pd.read_csv(DETAIL, low_memory=False)
    detail = detail[(detail["year"] >= WARMUP_YEAR) & (detail["year"] <= END_YEAR)].copy()
    detail["applicant_norm"] = detail["applicant"].map(norm_name)
    detail = detail[detail["applicant_norm"] != ""].copy()
    detail["clean_type"] = detail["applicant_norm"].map(infer_type)
    detail = detail[detail["clean_type"] != "individual"].copy()

    detail = (
        detail.groupby(["city", "year", "applicant_norm", "clean_type"], as_index=False)
        .agg(patents=("patents", "sum"), applicant=("applicant", "first"))
    )
    detail["key"] = detail["city"] + "||" + detail["applicant_norm"]
    first_year = detail.groupby("key")["year"].min()
    detail["first_year"] = detail["key"].map(first_year)
    detail["is_new_org"] = detail["year"].eq(detail["first_year"])
    detail["new_org_patents_part"] = np.where(detail["is_new_org"], detail["patents"], 0)

    sample = detail[(detail["year"] >= START_YEAR) & (detail["year"] <= END_YEAR)].copy()
    metrics = (
        sample.groupby(["city", "year"], as_index=False)
        .agg(
            org_total_patents=("patents", "sum"),
            org_active_applicants=("applicant_norm", "nunique"),
            org_new_applicants=("is_new_org", "sum"),
            org_new_patents=("new_org_patents_part", "sum"),
        )
    )

    hhi_top = (
        sample.groupby(["city", "year"])["patents"]
        .agg(org_hhi=hhi, org_top1_share=lambda s: top_share(s, 1), org_top5_share=lambda s: top_share(s, 5), org_top10_share=lambda s: top_share(s, 10))
        .reset_index()
    )
    metrics = metrics.merge(hhi_top, on=["city", "year"], how="left")

    y = pd.read_csv(Y, low_memory=False, encoding="utf-8-sig")
    y = y[y["scope"] == "inv_app_appyear"][
        ["city", "year", "total_patents", "active_applicants", "new_applicants", "new_applicant_share", "hhi", "top10_share"]
    ].copy()
    out = y.merge(metrics, on=["city", "year"], how="left")
    fill_cols = [c for c in out.columns if c.startswith("org_")]
    out[fill_cols] = out[fill_cols].fillna(0)
    out["org_new_share"] = out["org_new_patents"] / out["org_total_patents"].where(out["org_total_patents"] > 0)
    out["org_patent_share_total"] = out["org_total_patents"] / out["total_patents"].where(out["total_patents"] > 0)
    out["ln1p_org_total_patents"] = np.log1p(out["org_total_patents"])
    out["ln1p_org_active_applicants"] = np.log1p(out["org_active_applicants"])
    out["ln1p_org_new_applicants"] = np.log1p(out["org_new_applicants"])
    out["ln_org_effective_applicants"] = np.log(1 / out["org_hhi"].where(out["org_hhi"] > 0))
    out = out.fillna(0)

    out_csv = PROCESSED / f"org_applicant_concentration_clean_panel_{START_YEAR}_{END_YEAR}.csv"
    out_dta = PROCESSED / f"org_applicant_concentration_clean_panel_{START_YEAR}_{END_YEAR}.dta"
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    out.to_stata(out_dta, write_index=False, version=118)
    print(f"wrote {out_csv} rows={len(out):,} cities={out['city'].nunique():,}")
    print(f"wrote {out_dta}")


if __name__ == "__main__":
    main()
