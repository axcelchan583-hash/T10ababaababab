from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
OUT = ROOT / "outputs"


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def norm_city_name(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.strip()
        .str.replace("\u3000", "", regex=False)
        .str.replace(" ", "", regex=False)
    )


def main() -> None:
    decomp_path = OUT / "city_listed_nonlisted_patent_decomposition_full_2000_2024.csv"
    idc_path = OUT / "idc_proxy_city_year_2000_2024.csv"
    csv_out = OUT / "city_innovation_position_panel_2000_2024.csv"
    dta_out = OUT / "city_innovation_position_panel_2000_2024.dta"
    report_out = OUT / "city_innovation_position_panel_report_20260523.json"

    decomp = read_csv(decomp_path)
    idc = read_csv(idc_path)

    decomp = decomp.rename(columns={"省份": "province", "城市": "city", "年份": "year"})
    idc = idc.rename(
        columns={
            "省份": "province",
            "城市": "city",
            "年份": "year",
            "城市代码": "city_code_idc_dirty",
        }
    )

    for frame in (decomp, idc):
        frame["province"] = norm_city_name(frame["province"])
        frame["city"] = norm_city_name(frame["city"])
        frame["year"] = pd.to_numeric(frame["year"], errors="coerce").astype("Int64")

    keep_decomp = [
        "province",
        "city",
        "year",
        "省份代码",
        "城市代码",
        "city_apply",
        "city_grant",
        "city_invgrant",
        "listed_apply",
        "listed_grant",
        "listed_invgrant",
        "n_listed_firms",
        "nonlisted_apply_proxy",
        "nonlisted_grant_proxy",
        "nonlisted_invgrant_proxy",
        "listed_share_apply",
        "listed_share_grant",
        "listed_share_invgrant",
        "bad_negative_nonlisted_apply",
        "bad_negative_nonlisted_grant",
        "bad_negative_nonlisted_invgrant",
    ]
    keep_decomp = [c for c in keep_decomp if c in decomp.columns]
    decomp = decomp[keep_decomp].copy()
    decomp = decomp.rename(columns={"省份代码": "province_code", "城市代码": "city_code"})

    idc_keep = [
        "province",
        "city",
        "year",
        "idc_new",
        "idc_stock",
        "ln1p_idc_new",
        "ln1p_idc_stock",
    ]
    idc = idc[idc_keep].drop_duplicates(["province", "city", "year"]).copy()

    panel = decomp.merge(idc, on=["province", "city", "year"], how="left", indicator=True)
    for col in ["idc_new", "idc_stock", "ln1p_idc_new", "ln1p_idc_stock"]:
        panel[col] = pd.to_numeric(panel[col], errors="coerce").fillna(0.0)

    panel["merge_idc"] = panel["_merge"].astype(str)
    panel = panel.drop(columns=["_merge"])

    for stem in ["apply", "grant", "invgrant"]:
        for prefix in ["city", "listed", "nonlisted"]:
            source = f"{prefix}_{stem}" if prefix != "nonlisted" else f"nonlisted_{stem}_proxy"
            if source in panel:
                panel[f"ln1p_{source}"] = np.log1p(panel[source].clip(lower=0))

        share_col = f"listed_share_{stem}"
        bad_col = f"bad_negative_nonlisted_{stem}"
        denom_col = f"city_{stem}"
        clean_col = f"{share_col}_clean"
        panel[clean_col] = panel[share_col]
        panel.loc[(panel[denom_col] <= 0) | (panel[bad_col].astype(bool)), clean_col] = np.nan
        panel[f"{share_col}_wins01"] = panel[share_col].clip(lower=0, upper=1)

    panel["city_key"] = panel["province"] + "_" + panel["city"]
    panel = panel.sort_values(["city_key", "year"]).reset_index(drop=True)
    panel["city_id"] = pd.factorize(panel["city_key"])[0] + 1

    # Lags should be generated after the city-year panel is sorted.
    panel["ln1p_idc_stock_l1"] = panel.groupby("city_id")["ln1p_idc_stock"].shift(1)
    panel["ln1p_idc_new_l1"] = panel.groupby("city_id")["ln1p_idc_new"].shift(1)

    # Stata-compatible numeric types.
    for c in panel.columns:
        if c not in {"province", "city", "merge_idc", "city_key"}:
            panel[c] = pd.to_numeric(panel[c], errors="ignore")

    panel.to_csv(csv_out, index=False, encoding="utf-8-sig")
    panel.to_stata(dta_out, write_index=False, version=118)

    report = {
        "rows": int(len(panel)),
        "cities": int(panel["city_id"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "idc_matched_rows": int((panel["merge_idc"] == "both").sum()),
        "idc_unmatched_rows_treated_as_zero": int((panel["merge_idc"] == "left_only").sum()),
        "city_with_any_idc_stock": int(panel.loc[panel["idc_stock"] > 0, "city_id"].nunique()),
        "negative_nonlisted_invgrant_rows": int(panel["bad_negative_nonlisted_invgrant"].sum()),
        "output_csv": str(csv_out),
        "output_dta": str(dta_out),
    }
    report_out.write_text(pd.Series(report).to_json(force_ascii=False, indent=2), encoding="utf-8")
    print(pd.Series(report).to_string())


if __name__ == "__main__":
    main()
