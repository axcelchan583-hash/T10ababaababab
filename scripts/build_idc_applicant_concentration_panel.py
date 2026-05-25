from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "results" / "reports"


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def norm_city(s: pd.Series) -> pd.Series:
    city = (
        s.astype("string")
        .str.strip()
        .str.replace("\u3000", "", regex=False)
        .str.replace(r"\s+", "", regex=True)
        .str.replace(r"^中国", "", regex=True)
        .str.replace(r"市$", "", regex=True)
    )
    return city


def main() -> None:
    concentration_path = PROCESSED / "patent_applicant_concentration_city_year_2008_2024.csv"
    idc_path = PROCESSED / "idc_proxy_city_year_2000_2024.csv"
    out_csv = PROCESSED / "idc_applicant_concentration_panel_2008_2024.csv"
    out_dta = PROCESSED / "idc_applicant_concentration_panel_2008_2024.dta"
    report_path = REPORTS / "idc_applicant_concentration_panel_report_20260523.json"

    y = read_csv(concentration_path)
    idc = read_csv(idc_path)

    y["city"] = norm_city(y["city"])
    y["year"] = pd.to_numeric(y["year"], errors="coerce")

    idc = idc.rename(columns={"城市": "city", "年份": "year", "省份": "province"})
    idc["city"] = norm_city(idc["city"])
    idc["year"] = pd.to_numeric(idc["year"], errors="coerce")
    for col in ["idc_new", "idc_stock", "ln1p_idc_new", "ln1p_idc_stock"]:
        idc[col] = pd.to_numeric(idc[col], errors="coerce").fillna(0)

    idc_city = (
        idc.groupby(["city", "year"], dropna=False, as_index=False)
        .agg(
            idc_new=("idc_new", "sum"),
            idc_stock=("idc_stock", "sum"),
        )
    )
    idc_city["ln1p_idc_new"] = np.log1p(idc_city["idc_new"])
    idc_city["ln1p_idc_stock"] = np.log1p(idc_city["idc_stock"])
    idc_city = idc_city.sort_values(["city", "year"]).reset_index(drop=True)
    idc_city["ln1p_idc_stock_l1"] = idc_city.groupby("city")["ln1p_idc_stock"].shift(1).fillna(0)
    idc_city["ln1p_idc_new_l1"] = idc_city.groupby("city")["ln1p_idc_new"].shift(1).fillna(0)

    panel = y.merge(idc_city, on=["city", "year"], how="left", indicator=True)
    panel["merge_idc"] = panel["_merge"].astype(str)
    panel = panel.drop(columns=["_merge"])
    for col in ["idc_new", "idc_stock", "ln1p_idc_new", "ln1p_idc_stock", "ln1p_idc_stock_l1", "ln1p_idc_new_l1"]:
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0)

    panel["ln1p_total_patents"] = np.log1p(panel["total_patents"])
    panel["ln1p_active_applicants"] = np.log1p(panel["active_applicants"])
    panel["ln1p_new_applicants"] = np.log1p(panel["new_applicants"])
    panel["ln_effective_applicants"] = np.log(panel["effective_applicants"].where(panel["effective_applicants"] > 0))

    panel["city_id"] = pd.factorize(panel["city"])[0] + 1
    panel["scope_id"] = pd.factorize(panel["scope"])[0] + 1
    panel = panel.sort_values(["scope", "city", "year"]).reset_index(drop=True)

    panel.to_csv(out_csv, index=False, encoding="utf-8-sig")
    panel.to_stata(out_dta, write_index=False, version=118)

    report = {
        "rows": int(len(panel)),
        "cities": int(panel["city"].nunique()),
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "scopes": sorted(panel["scope"].dropna().unique().tolist()),
        "idc_matched_rows": int((panel["merge_idc"] == "both").sum()),
        "idc_unmatched_rows_treated_as_zero": int((panel["merge_idc"] == "left_only").sum()),
        "cities_with_any_idc_stock": int(panel.loc[panel["idc_stock"] > 0, "city"].nunique()),
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
    }
    report_path.write_text(pd.Series(report).to_json(force_ascii=False, indent=2), encoding="utf-8")
    print(pd.Series(report).to_string())


if __name__ == "__main__":
    main()
