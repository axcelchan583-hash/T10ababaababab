from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE = Path("/Users/mac/computerscience")
T07_INTERIM = BASE / "23选题探索/T07_public_data_ai_adoption/data/interim"
OUT_DIR = BASE / "23选题探索/T10/outputs"


def safe_growth(current: pd.Series, lagged: pd.Series) -> pd.Series:
    out = (current - lagged) / lagged
    return out.replace([np.inf, -np.inf], np.nan)


def safe_resilience(actual_change: pd.Series, benchmark_growth: pd.Series, current_count: pd.Series) -> pd.Series:
    expected = benchmark_growth * current_count
    out = (actual_change - expected) / expected.abs()
    return out.replace([np.inf, -np.inf], np.nan)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    panel_path = T07_INTERIM / "firm_month_hiring_patent_panel.csv"
    panel = pd.read_csv(
        panel_path,
        dtype={
            "symbol": "Int64",
            "provinceCode": "Int64",
            "cityCode": "Int64",
            "industryCodeC": "string",
            "industryCodeD": "string",
        },
    )
    panel["month_dt"] = pd.to_datetime(panel["month"], errors="coerce")
    panel["year"] = panel["month_dt"].dt.year

    for col in ["patent_grant_count", "invention_grant_count"]:
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0)

    id_cols = [
        "symbol",
        "shortname_latest",
        "fullname_latest",
        "provinceCode",
        "province",
        "cityCode",
        "city",
        "industryCodeC",
        "industryNameC",
        "industryCodeD",
        "industryNameD",
        "listingDate",
        "listingState",
    ]

    annual = (
        panel.dropna(subset=["symbol", "year"])
        .groupby(id_cols + ["year"], dropna=False, as_index=False)
        .agg(
            企业专利授权总量_现有库=("patent_grant_count", "sum"),
            企业发明专利授权量_现有库=("invention_grant_count", "sum"),
            月份数=("month", "nunique"),
        )
    )

    annual = annual.sort_values(["symbol", "year"]).copy()
    annual["企业专利授权量变化_现有库"] = annual.groupby("symbol")["企业专利授权总量_现有库"].diff()
    annual["企业发明专利授权量变化_现有库"] = annual.groupby("symbol")["企业发明专利授权量_现有库"].diff()

    city_annual = (
        annual.groupby(["cityCode", "city", "year"], dropna=False, as_index=False)
        .agg(
            市上市公司专利授权总量_现有库=("企业专利授权总量_现有库", "sum"),
            市上市公司发明专利授权量_现有库=("企业发明专利授权量_现有库", "sum"),
            市上市公司数=("symbol", "nunique"),
        )
        .sort_values(["cityCode", "city", "year"])
    )
    city_annual["城市专利授权量变化_现有库"] = city_annual.groupby(["cityCode", "city"], dropna=False)[
        "市上市公司专利授权总量_现有库"
    ].transform(lambda s: safe_growth(s, s.shift(1)))
    city_annual["城市发明专利授权量变化_现有库"] = city_annual.groupby(["cityCode", "city"], dropna=False)[
        "市上市公司发明专利授权量_现有库"
    ].transform(lambda s: safe_growth(s, s.shift(1)))

    out = annual.merge(
        city_annual[
            [
                "cityCode",
                "city",
                "year",
                "市上市公司专利授权总量_现有库",
                "市上市公司发明专利授权量_现有库",
                "市上市公司数",
                "城市专利授权量变化_现有库",
                "城市发明专利授权量变化_现有库",
            ]
        ],
        on=["cityCode", "city", "year"],
        how="left",
        validate="m:1",
    )

    out["企业创新韧性1_2025诊断版"] = safe_resilience(
        out["企业发明专利授权量变化_现有库"],
        out["城市发明专利授权量变化_现有库"],
        out["企业发明专利授权量_现有库"],
    )
    out["企业创新韧性3_2025诊断版"] = safe_resilience(
        out["企业专利授权量变化_现有库"],
        out["城市专利授权量变化_现有库"],
        out["企业专利授权总量_现有库"],
    )
    out["数据口径说明"] = (
        "诊断版：使用T07本地上市公司专利授权日期明细，城市基准为同库上市公司城市合计；"
        "不是公开包的全城市专利总量口径。"
    )

    keep_cols = [
        "symbol",
        "shortname_latest",
        "fullname_latest",
        "year",
        "provinceCode",
        "province",
        "cityCode",
        "city",
        "industryCodeC",
        "industryNameC",
        "industryCodeD",
        "industryNameD",
        "listingDate",
        "listingState",
        "月份数",
        "企业专利授权总量_现有库",
        "企业发明专利授权量_现有库",
        "企业专利授权量变化_现有库",
        "企业发明专利授权量变化_现有库",
        "市上市公司专利授权总量_现有库",
        "市上市公司发明专利授权量_现有库",
        "市上市公司数",
        "城市专利授权量变化_现有库",
        "城市发明专利授权量变化_现有库",
        "企业创新韧性1_2025诊断版",
        "企业创新韧性3_2025诊断版",
        "数据口径说明",
    ]

    out_2022_2025 = out[out["year"].between(2022, 2025)].copy()

    full_path = OUT_DIR / "innovation_resilience_2022_2025_pilot_existing_data.csv"
    y2025_path = OUT_DIR / "innovation_resilience_2025_pilot_existing_data.csv"
    out_2022_2025[keep_cols].to_csv(full_path, index=False, encoding="utf-8-sig")
    out_2022_2025.loc[out_2022_2025["year"] == 2025, keep_cols].to_csv(
        y2025_path, index=False, encoding="utf-8-sig"
    )

    summary: dict[str, object] = {
        "source_file": str(panel_path),
        "method": "public-formula-style diagnostic rebuild using available listed-firm patent grant data",
        "important_caveats": [
            "2025 patent grant records in the current local data are extremely sparse.",
            "The current data has patent_grant_count and invention_grant_count, but not patent application counts.",
            "City benchmark is listed-firm city aggregate from the same local data, not all-city patent totals in the public 2000-2024 package.",
            "Therefore only resilience 1 and 3 are constructed; resilience 2 and 4 are not constructed.",
        ],
        "annual_totals": {},
        "nonmissing_by_year": {},
        "output_full": str(full_path),
        "output_2025": str(y2025_path),
    }

    for year, g in out_2022_2025.groupby("year"):
        summary["annual_totals"][int(year)] = {
            "rows": int(len(g)),
            "firms": int(g["symbol"].nunique()),
            "months_min": int(g["月份数"].min()),
            "months_max": int(g["月份数"].max()),
            "patent_grant_count": float(g["企业专利授权总量_现有库"].sum()),
            "invention_grant_count": float(g["企业发明专利授权量_现有库"].sum()),
            "firms_with_any_grant": int((g["企业专利授权总量_现有库"] > 0).sum()),
            "firms_with_any_invention_grant": int((g["企业发明专利授权量_现有库"] > 0).sum()),
        }
        summary["nonmissing_by_year"][int(year)] = {
            "企业创新韧性1_2025诊断版": int(g["企业创新韧性1_2025诊断版"].notna().sum()),
            "企业创新韧性3_2025诊断版": int(g["企业创新韧性3_2025诊断版"].notna().sum()),
        }

    report_path = OUT_DIR / "innovation_resilience_2025_pilot_existing_data_report_20260523.json"
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
