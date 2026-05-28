#!/usr/bin/env python3
"""Build preliminary IDC license feature panels for X validation.

This is a diagnostic split of the existing scope-city IDC license rows. It does
not replace the main X. The purpose is to test whether licenses that look closer
to cloud / compute service supply have stronger relationships with the entry
margin.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
REPORTS = ROOT / "results/reports"
SCOPE_ROWS = PROCESSED / "idc_split_proxy/idc_scope_city_license_rows.csv"
CITY_YEAR = PROCESSED / "idc_split_proxy_city_year_2000_2024.csv"
OUT_CSV = PROCESSED / "idc_scope_license_feature_city_year_2000_2024.csv"
OUT_DTA = PROCESSED / "idc_scope_license_feature_city_year_2000_2024.dta"
REPORT = REPORTS / "idc_scope_license_feature_city_year_report_20260527.json"


PROVINCE_PREFIX = tuple("京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼")
CLOUD_PAT = re.compile(r"云|云计算|数据|数据中心|算力|计算|智能|人工智能|网络|互联网|信息")
CARRIER_PAT = re.compile(r"中国电信|中国移动|中国联通|铁塔|广电")


def is_cross_region_license(license_no: object) -> bool:
    text = str(license_no or "").strip()
    if not text:
        return False
    return not text.startswith(PROVINCE_PREFIX)


def has_cloud_compute_terms(row: pd.Series) -> bool:
    text = " ".join(str(row.get(c, "") or "") for c in ["company", "idc_scope_raw", "license_no"])
    return bool(CLOUD_PAT.search(text))


def is_carrier(row: pd.Series) -> bool:
    text = str(row.get("company", "") or "")
    return bool(CARRIER_PAT.search(text))


def add_stock(panel: pd.DataFrame, prefix: str) -> pd.DataFrame:
    panel = panel.sort_values(["city", "year"]).copy()
    panel[f"{prefix}_new"] = panel[f"{prefix}_new"].fillna(0).astype(int)
    panel[f"{prefix}_stock"] = panel.groupby("city")[f"{prefix}_new"].cumsum()
    panel[f"ln1p_{prefix}_new"] = panel[f"{prefix}_new"].map(lambda x: math.log1p(float(x)))
    panel[f"ln1p_{prefix}_stock"] = panel[f"{prefix}_stock"].map(lambda x: math.log1p(float(x)))
    panel[f"ln1p_{prefix}_stock_l1"] = panel.groupby("city")[f"ln1p_{prefix}_stock"].shift(1).fillna(0)
    return panel


def main() -> None:
    rows = pd.read_csv(SCOPE_ROWS, low_memory=False, encoding="utf-8-sig")
    base = pd.read_csv(CITY_YEAR, low_memory=False, encoding="utf-8-sig")[["province", "city", "year"]]
    base = base.drop_duplicates().sort_values(["city", "year"])

    rows["feature_cloud_compute"] = rows.apply(has_cloud_compute_terms, axis=1)
    rows["feature_carrier"] = rows.apply(is_carrier, axis=1)
    rows["feature_cross_region_license"] = rows["license_no"].map(is_cross_region_license)
    rows["feature_provincial_license"] = ~rows["feature_cross_region_license"]

    feature_defs = {
        "idc_scope_cloud": rows["feature_cloud_compute"],
        "idc_scope_noncloud": ~rows["feature_cloud_compute"],
        "idc_scope_cross": rows["feature_cross_region_license"],
        "idc_scope_provlic": rows["feature_provincial_license"],
        "idc_scope_carrier": rows["feature_carrier"],
        "idc_scope_noncarrier": ~rows["feature_carrier"],
    }

    out = base.copy()
    for prefix, mask in feature_defs.items():
        part = rows.loc[mask].copy()
        if part.empty:
            counts = pd.DataFrame(columns=["city", "year", f"{prefix}_new"])
        else:
            counts = (
                part.groupby(["city", "license_year"], as_index=False)
                .size()
                .rename(columns={"license_year": "year", "size": f"{prefix}_new"})
            )
        out = out.merge(counts, on=["city", "year"], how="left")
        out = add_stock(out, prefix)

    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    out.to_stata(OUT_DTA, write_index=False, version=118)

    report = {
        "scope_license_rows": int(len(rows)),
        "cloud_compute_rows": int(rows["feature_cloud_compute"].sum()),
        "cross_region_rows": int(rows["feature_cross_region_license"].sum()),
        "provincial_license_rows": int(rows["feature_provincial_license"].sum()),
        "carrier_rows": int(rows["feature_carrier"].sum()),
        "cities_with_cloud_compute_scope": int(rows.loc[rows["feature_cloud_compute"], "city"].nunique()),
        "cities_with_cross_region_scope": int(rows.loc[rows["feature_cross_region_license"], "city"].nunique()),
        "output_csv": str(OUT_CSV),
        "caveat": "Feature splits are keyword/license-number diagnostics, not audited MIIT capacity data.",
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
