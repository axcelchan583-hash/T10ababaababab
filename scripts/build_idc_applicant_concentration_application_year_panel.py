from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "results" / "reports"


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
    idc_path = PROCESSED / "idc_proxy_city_year_2000_2024.csv"
    out_csv = PROCESSED / "idc_applicant_concentration_application_year_panel_2008_2023.csv"
    out_dta = PROCESSED / "idc_applicant_concentration_application_year_panel_2008_2023.dta"
    report_path = REPORTS / "idc_applicant_concentration_application_year_panel_report_20260524.json"

    y = read_csv(y_path)
    idc = read_csv(idc_path)

    y["city"] = norm_city(y["city"])
    y["year"] = pd.to_numeric(y["year"], errors="coerce").astype("int16")

    idc = idc.rename(columns={"省份": "province", "城市": "city", "年份": "year"})
    idc["province"] = norm_city(idc["province"])
    idc["city"] = norm_city(idc["city"])
    idc["year"] = pd.to_numeric(idc["year"], errors="coerce")
    for col in ["idc_new", "idc_stock"]:
        idc[col] = pd.to_numeric(idc[col], errors="coerce").fillna(0)

    city_province = (
        idc[["city", "province"]]
        .dropna()
        .drop_duplicates()
        .sort_values(["city", "province"])
        .drop_duplicates("city")
    )
    idc_city = (
        idc.groupby(["city", "year"], as_index=False)
        .agg(idc_new=("idc_new", "sum"), idc_stock=("idc_stock", "sum"))
        .merge(city_province, on="city", how="left")
        .sort_values(["city", "year"])
    )
    idc_city["ln1p_idc_new"] = np.log1p(idc_city["idc_new"])
    idc_city["ln1p_idc_stock"] = np.log1p(idc_city["idc_stock"])
    idc_city["ln1p_idc_stock_l1"] = idc_city.groupby("city")["ln1p_idc_stock"].shift(1).fillna(0)
    idc_city["ln1p_idc_new_l1"] = idc_city.groupby("city")["ln1p_idc_new"].shift(1).fillna(0)

    panel = y.merge(idc_city, on=["city", "year"], how="left", indicator=True)
    panel["merge_idc"] = panel["_merge"].astype(str)
    panel = panel.drop(columns=["_merge"])
    for col in ["idc_new", "idc_stock", "ln1p_idc_new", "ln1p_idc_stock", "ln1p_idc_stock_l1", "ln1p_idc_new_l1"]:
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0)
    panel["province"] = panel["province"].fillna("")

    panel["city_id"] = pd.factorize(panel["city"])[0] + 1
    panel["province_id"] = pd.factorize(panel["province"])[0] + 1
    panel["city_cluster"] = panel["city_id"]

    # Baseline groups for FE interactions. Use 2008-2010 city averages.
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
        "idc_matched_rows": int((panel["merge_idc"] == "both").sum()),
        "idc_unmatched_rows_treated_as_zero": int((panel["merge_idc"] == "left_only").sum()),
        "matched_cities": int(panel.loc[panel["merge_idc"] == "both", "city"].nunique()),
        "cities_with_any_idc_stock": int(panel.loc[panel["idc_stock"] > 0, "city"].nunique()),
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
    }
    report_path.write_text(pd.Series(report).to_json(force_ascii=False, indent=2), encoding="utf-8")
    print(pd.Series(report).to_string())


if __name__ == "__main__":
    main()
