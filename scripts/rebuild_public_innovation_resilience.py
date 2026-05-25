from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


SOURCE_DIR = Path(
    "/Users/mac/computerscience/第三方资料/90_临时下载待归档/"
    "上市公司创新韧性数据（2000-2024年）"
)
RAW_DIR = SOURCE_DIR / "原始数据"
OUT_DIR = Path("/Users/mac/computerscience/23选题探索/T10/outputs")


def safe_growth(current: pd.Series, lagged: pd.Series) -> pd.Series:
    out = (current - lagged) / lagged
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def safe_ratio(numer: pd.Series, denom: pd.Series) -> pd.Series:
    out = numer / denom.abs()
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    firm_path = RAW_DIR / "上市公司专利数据.xlsx"
    city_path = RAW_DIR / "地级市专利数据.xlsx"
    product_path = SOURCE_DIR / "企业创新韧性（2000-2024年）.dta"

    firm = pd.read_excel(firm_path, sheet_name="1949-2026")
    city = pd.read_excel(city_path, sheet_name="1949-2026")

    firm = firm[pd.to_numeric(firm["年份"], errors="coerce").notna()].copy()
    city = city[pd.to_numeric(city["年份"], errors="coerce").notna()].copy()

    firm["年份"] = pd.to_numeric(firm["年份"], errors="coerce").astype("int64")
    city["年份"] = pd.to_numeric(city["年份"], errors="coerce").astype("int64")
    firm["股票代码"] = pd.to_numeric(firm["股票代码"], errors="coerce").astype("int64")
    firm["城市代码"] = pd.to_numeric(firm["城市代码"], errors="coerce")
    city["城市代码"] = pd.to_numeric(city["城市代码"], errors="coerce")

    firm_cols = ["企业专利申请总量", "企业专利授权总量", "企业发明专利授权量"]
    city_rename = {
        "市-专利申请总量": "市专利申请总量",
        "市-专利授权总量": "市专利授权总量",
        "市-发明专利授权量": "市发明专利授权量",
    }
    city = city.rename(columns=city_rename)
    city_cols = ["市专利申请总量", "市专利授权总量", "市发明专利授权量"]

    for col in firm_cols:
        firm[col] = pd.to_numeric(firm[col], errors="coerce")
    for col in city_cols:
        city[col] = pd.to_numeric(city[col], errors="coerce")

    city = city.sort_values(["城市代码", "年份"]).copy()
    city["城市发明专利授权量变化"] = city.groupby("城市代码")["市发明专利授权量"].transform(
        lambda s: safe_growth(s, s.shift(1))
    )
    city["城市专利申请量变化"] = city.groupby("城市代码")["市专利申请总量"].transform(
        lambda s: safe_growth(s, s.shift(1))
    )
    city["城市专利授权量变化"] = city.groupby("城市代码")["市专利授权总量"].transform(
        lambda s: safe_growth(s, s.shift(1))
    )

    city_keep = [
        "年份",
        "城市",
        "城市代码",
        "市专利申请总量",
        "市专利授权总量",
        "市发明专利授权量",
        "城市发明专利授权量变化",
        "城市专利申请量变化",
        "城市专利授权量变化",
    ]

    # The source Stata code merges city data by 年份 and 城市, not by 城市代码.
    # Keeping the same key is necessary to reproduce the vendor-provided file.
    merged = firm.merge(
        city[city_keep],
        on=["年份", "城市"],
        how="left",
        validate="m:1",
        suffixes=("", "_cityref"),
    )

    industry = (
        merged.groupby(["行业代码", "年份"], dropna=False)["企业专利申请总量"]
        .sum()
        .reset_index(name="patent_industry")
        .sort_values(["行业代码", "年份"])
    )
    industry["行业专利申请量变化"] = industry.groupby(
        "行业代码", dropna=False
    )["patent_industry"].diff()
    merged = merged.merge(
        industry[["行业代码", "年份", "行业专利申请量变化"]],
        on=["行业代码", "年份"],
        how="left",
        validate="m:1",
    )

    merged = merged.sort_values(["股票代码", "年份"]).copy()
    merged["企业发明专利授权量变化"] = merged.groupby("股票代码")["企业发明专利授权量"].diff()
    merged["企业专利申请量变化"] = merged.groupby("股票代码")["企业专利申请总量"].diff()
    merged["企业专利授权量变化"] = merged.groupby("股票代码")["企业专利授权总量"].diff()

    denom1 = merged["城市发明专利授权量变化"] * merged["企业发明专利授权量"]
    denom2 = merged["城市专利申请量变化"] * merged["企业专利申请总量"]
    denom3 = merged["城市专利授权量变化"] * merged["企业专利授权总量"]
    denom4 = merged["行业专利申请量变化"] * merged["企业专利申请总量"]

    merged["企业创新韧性1_rebuild"] = safe_ratio(
        merged["企业发明专利授权量变化"] - denom1, denom1
    )
    merged["企业创新韧性2_rebuild"] = safe_ratio(
        merged["企业专利申请量变化"] - denom2, denom2
    )
    merged["企业创新韧性3_rebuild"] = safe_ratio(
        merged["企业专利授权量变化"] - denom3, denom3
    )
    merged["企业创新韧性4_rebuild"] = safe_ratio(
        merged["企业专利申请量变化"] - denom4, denom4
    )

    product = pd.read_stata(product_path, convert_categoricals=False)
    product["股票代码"] = pd.to_numeric(product["股票代码"], errors="coerce").astype("int64")
    product["年份"] = pd.to_numeric(product["年份"], errors="coerce").astype("int64")

    compare_cols = [
        ("企业创新韧性1", "企业创新韧性1_rebuild"),
        ("企业创新韧性2", "企业创新韧性2_rebuild"),
        ("企业创新韧性3", "企业创新韧性3_rebuild"),
        ("企业创新韧性4", "企业创新韧性4_rebuild"),
    ]

    compare = product[["股票代码", "年份"] + [a for a, _ in compare_cols]].merge(
        merged[["股票代码", "年份"] + [b for _, b in compare_cols]],
        on=["股票代码", "年份"],
        how="outer",
        indicator=True,
        validate="1:1",
    )

    metrics: dict[str, object] = {
        "raw_firm_rows": int(len(firm)),
        "raw_city_rows": int(len(city)),
        "rebuilt_rows": int(len(merged)),
        "product_rows": int(len(product)),
        "merge_status_counts": compare["_merge"].value_counts(dropna=False).to_dict(),
        "year_min": int(merged["年份"].min()),
        "year_max": int(merged["年份"].max()),
        "firm_count": int(merged["股票代码"].nunique()),
        "checks": {},
    }

    for old, new in compare_cols:
        diff = compare[old] - compare[new]
        both_missing = compare[old].isna() & compare[new].isna()
        both_present = compare[old].notna() & compare[new].notna()
        close = both_present & np.isclose(compare[old], compare[new], rtol=1e-5, atol=1e-5)
        mismatch = ~(both_missing | close)
        metrics["checks"][old] = {
            "product_nonmissing": int(compare[old].notna().sum()),
            "rebuilt_nonmissing": int(compare[new].notna().sum()),
            "matched_or_both_missing": int((~mismatch).sum()),
            "mismatch_count": int(mismatch.sum()),
            "max_abs_diff": None
            if not both_present.any()
            else float(diff[both_present].abs().max(skipna=True)),
            "mean_abs_diff": None
            if not both_present.any()
            else float(diff[both_present].abs().mean(skipna=True)),
        }

    out_cols = [
        "股票代码",
        "股票简称",
        "年份",
        "省份",
        "城市",
        "区县",
        "省份代码",
        "城市代码",
        "区县代码",
        "行业代码",
        "行业名称",
        "首次上市年份",
        "是否ST类",
        "企业创新韧性1_rebuild",
        "企业创新韧性2_rebuild",
        "企业创新韧性3_rebuild",
        "企业创新韧性4_rebuild",
        "企业专利申请总量",
        "企业专利授权总量",
        "企业发明专利授权量",
        "市专利申请总量",
        "市专利授权总量",
        "市发明专利授权量",
    ]
    rebuilt_csv = OUT_DIR / "public_innovation_resilience_rebuild_2000_2024.csv"
    merged[out_cols].to_csv(rebuilt_csv, index=False, encoding="utf-8-sig")

    report_path = OUT_DIR / "public_innovation_resilience_rebuild_report_20260523.json"
    report_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"CSV: {rebuilt_csv}")
    print(f"REPORT: {report_path}")


if __name__ == "__main__":
    main()
