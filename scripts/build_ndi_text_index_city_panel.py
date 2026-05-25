from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
OUT = ROOT / "outputs"
SRC = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/数字基础设施/"
    "地级市新型数字基础设施水平数据（2003-2024年）/数据结果/原始数据.xlsx"
)


def norm_city_name(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.strip()
        .str.replace("\u3000", "", regex=False)
        .str.replace(" ", "", regex=False)
    )


def minmax(series: pd.Series) -> pd.Series:
    lo = series.min(skipna=True)
    hi = series.max(skipna=True)
    if pd.isna(lo) or pd.isna(hi) or hi <= lo:
        return pd.Series(0.0, index=series.index)
    return (series - lo) / (hi - lo)


def entropy_weight_index(x: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    # Positive indicators only. Add a small constant so zero keyword counts can enter entropy weights.
    z = x.apply(minmax, axis=0).fillna(0.0)
    z = z + 1e-12
    p = z.div(z.sum(axis=0), axis=1)
    n = len(z)
    k = 1.0 / np.log(n)
    entropy = -k * (p * np.log(p)).sum(axis=0)
    diversity = 1 - entropy
    if diversity.sum() <= 0 or not np.isfinite(diversity.sum()):
        weights = pd.Series(1 / len(diversity), index=diversity.index)
    else:
        weights = diversity / diversity.sum()
    idx = z.mul(weights, axis=1).sum(axis=1)
    return idx, weights


def pca_first_component(x: pd.DataFrame) -> pd.Series:
    z = x.apply(lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) > 0 else 0.0)
    z = z.fillna(0.0).to_numpy()
    u, s, _ = np.linalg.svd(z, full_matrices=False)
    pc1 = u[:, 0] * s[0]
    out = pd.Series(pc1)
    # Orient so the component is positively correlated with total keyword intensity.
    return out


def main() -> None:
    raw = pd.read_excel(SRC, sheet_name="Sheet1")
    raw = raw.rename(columns={"年份": "year", "城市": "city", "总词数": "total_words"})
    raw["city"] = norm_city_name(raw["city"])
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce")
    raw["total_words"] = pd.to_numeric(raw["total_words"], errors="coerce")
    raw = raw.dropna(subset=["city", "year", "total_words"])
    raw["year"] = raw["year"].astype(int)

    meta_cols = {"year", "city", "total_words", "丘知数据分析会员之家"}
    keyword_cols = [c for c in raw.columns if c not in meta_cols]
    for c in keyword_cols:
        raw[c] = pd.to_numeric(raw[c], errors="coerce").fillna(0.0)

    # Keyword intensity per 10,000 report words.
    rates = raw[keyword_cols].div(raw["total_words"].replace(0, np.nan), axis=0) * 10000
    rates = rates.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    rates.columns = [f"kw_{i:02d}" for i in range(1, len(keyword_cols) + 1)]

    x_entropy, weights = entropy_weight_index(rates)
    x_pca1 = pca_first_component(np.log1p(rates))
    x_total = rates.sum(axis=1)

    # Orient PCA to be positively associated with total keyword intensity, then min-max for readability.
    if np.corrcoef(x_pca1, x_total)[0, 1] < 0:
        x_pca1 = -x_pca1

    idx = raw[["city", "year", "total_words"]].copy()
    idx["ndi_kw_total"] = raw[keyword_cols].sum(axis=1)
    idx["ndi_kw_per10k"] = x_total
    idx["ln1p_ndi_kw_per10k"] = np.log1p(idx["ndi_kw_per10k"])
    idx["ndi_entropy"] = x_entropy
    idx["ndi_entropy_mm"] = minmax(x_entropy)
    idx["ndi_pca1"] = x_pca1
    idx["ndi_pca1_mm"] = minmax(x_pca1)

    # Collapse possible duplicate city-year rows.
    idx = idx.groupby(["city", "year"], as_index=False).mean(numeric_only=True)
    idx = idx.sort_values(["city", "year"])

    base = pd.read_stata(OUT / "city_innovation_position_panel_2000_2024.dta")
    base["city"] = norm_city_name(base["city"])
    base["year"] = pd.to_numeric(base["year"], errors="coerce").astype(int)

    panel = base.merge(idx, on=["city", "year"], how="left", indicator=True)
    panel["merge_ndi"] = panel["_merge"].astype(str)
    panel = panel.drop(columns=["_merge"])
    panel = panel.sort_values(["city_id", "year"]).reset_index(drop=True)

    for x in ["ln1p_ndi_kw_per10k", "ndi_entropy_mm", "ndi_pca1_mm"]:
        panel[f"{x}_l1"] = panel.groupby("city_id")[x].shift(1)

    csv_out = OUT / "city_innovation_position_with_ndi_textindex_2003_2024.csv"
    dta_out = OUT / "city_innovation_position_with_ndi_textindex_2003_2024.dta"
    weight_out = OUT / "ndi_textindex_entropy_weights_20260523.csv"
    report_out = OUT / "ndi_textindex_panel_report_20260523.json"

    panel.to_csv(csv_out, index=False, encoding="utf-8-sig")
    panel.to_stata(dta_out, write_index=False, version=118)

    pd.DataFrame({"keyword": keyword_cols, "weight": weights.values}).sort_values(
        "weight", ascending=False
    ).to_csv(weight_out, index=False, encoding="utf-8-sig")

    report = {
        "raw_rows": int(len(raw)),
        "raw_cities": int(raw["city"].nunique()),
        "raw_year_min": int(raw["year"].min()),
        "raw_year_max": int(raw["year"].max()),
        "keyword_count": int(len(keyword_cols)),
        "panel_rows": int(len(panel)),
        "panel_matched_rows": int((panel["merge_ndi"] == "both").sum()),
        "panel_unmatched_rows": int((panel["merge_ndi"] == "left_only").sum()),
        "matched_cities": int(panel.loc[panel["merge_ndi"] == "both", "city"].nunique()),
        "output_csv": str(csv_out),
        "output_dta": str(dta_out),
    }
    report_out.write_text(pd.Series(report).to_json(force_ascii=False, indent=2), encoding="utf-8")
    print(pd.Series(report).to_string())


if __name__ == "__main__":
    main()
