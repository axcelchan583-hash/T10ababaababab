#!/usr/bin/env python3
"""Run reviewer-requested diagnostics without Stata.

The local machine does not expose a Stata binary in this environment. This
script runs OLS with high-dimensional fixed effects via dummy variables and
city-clustered standard errors. It is intended as a fast diagnostic companion to
the Stata tables, not as a final replacement for journal tables.
"""

from __future__ import annotations

import io
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
TABLES = ROOT / "results/tables"
REPORTS = ROOT / "results/reports"
MAIN = PROCESSED / "idc_scope_formal_application_year_panel_2008_2023.csv"
POLICY = PROCESSED / "idc_scope_policy_horserace_panel_2008_2023.csv"
ENTRY_TYPE = PROCESSED / "entry_type_mechanism_panel_2008_2023.csv"
FIRM = PROCESSED / "firm_entry_clean_panel_2008_2023.csv"
ORG = PROCESSED / "org_applicant_concentration_clean_panel_2008_2023.csv"
FEATURE_X = PROCESSED / "idc_scope_license_feature_city_year_2000_2024.csv"
QUALITY = PROCESSED / "idc_scope_appyear_quality_panel_2008_2023.csv"
OUT = TABLES / "reviewer_round_y_cleaning_results_20260527.csv"
WARMUP_OUT = TABLES / "warmup_1985_vs_2000_comparison_20260527.csv"
REPORT = REPORTS / "reviewer_round_y_cleaning_report_20260527.json"


POLICIES = [
    "broadband_china_pilot",
    "smart_city_pilot",
    "bigdata_comprehensive_pilot",
    "innovative_city_pilot",
    "national_hightech_zone",
    "ip_demo_city",
    "information_consumption_pilot",
    "ecommerce_demo_city",
]


def p_norm(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return math.erfc(abs(z) / math.sqrt(2.0))


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def add_common(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    if "province" not in df.columns:
        df["province"] = ""
    df["province_year"] = df["province"].astype(str) + "_" + df["year"].astype(str)
    df["base_ln_patents_q_year"] = df.get("base_ln_patents_q", 1).astype(str) + "_" + df["year"].astype(str)
    df["base_top10_q_year"] = df.get("base_top10_q", 1).astype(str) + "_" + df["year"].astype(str)
    if "new_patents" in df.columns:
        df["ln1p_new_patents"] = np.log1p(pd.to_numeric(df["new_patents"], errors="coerce").fillna(0))
    if "total_patents" in df.columns and "new_patents" in df.columns:
        df["incumbent_patents"] = pd.to_numeric(df["total_patents"], errors="coerce").fillna(0) - pd.to_numeric(
            df["new_patents"], errors="coerce"
        ).fillna(0)
        df["ln1p_incumbent_patents"] = np.log1p(df["incumbent_patents"].clip(lower=0))
    return df


def design(df: pd.DataFrame, xvars: list[str], fe_cols: list[str], controls: list[str] | None = None) -> tuple[np.ndarray, list[str]]:
    controls = controls or []
    parts = []
    names: list[str] = []
    for x in xvars + controls:
        parts.append(pd.to_numeric(df[x], errors="coerce").fillna(0).to_numpy(dtype=float).reshape(-1, 1))
        names.append(x)
    for fe in fe_cols:
        d = pd.get_dummies(df[fe].astype(str), prefix=fe, drop_first=True, dtype=float)
        if not d.empty:
            parts.append(d.to_numpy(dtype=float))
            names.extend(d.columns.tolist())
    return np.column_stack(parts), names


def cluster_ols(df: pd.DataFrame, y: str, xvars: list[str], fe_cols: list[str], controls: list[str] | None = None) -> dict[str, float]:
    use_cols = list(dict.fromkeys([y, "city"] + xvars + fe_cols + (controls or [])))
    d = df[use_cols].replace([np.inf, -np.inf], np.nan).dropna(subset=[y] + xvars).copy()
    if len(d) < 50:
        return {"coef": np.nan, "se": np.nan, "t": np.nan, "p": np.nan, "N": len(d), "N_city": d["city"].nunique()}
    yy = pd.to_numeric(d[y], errors="coerce").to_numpy(dtype=float)
    X, names = design(d, xvars=xvars, fe_cols=fe_cols, controls=controls)
    keep = np.isfinite(yy) & np.isfinite(X).all(axis=1)
    yy = yy[keep]
    X = X[keep]
    clusters = d.loc[keep, "city"].astype(str).to_numpy()
    if len(yy) <= X.shape[1]:
        return {"coef": np.nan, "se": np.nan, "t": np.nan, "p": np.nan, "N": len(yy), "N_city": len(set(clusters))}

    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ yy
    resid = yy - X @ beta
    meat = np.zeros((X.shape[1], X.shape[1]), dtype=float)
    for g in np.unique(clusters):
        idx = clusters == g
        xg = X[idx]
        eg = resid[idx].reshape(-1, 1)
        score = xg.T @ eg
        meat += score @ score.T
    n = len(yy)
    g = len(np.unique(clusters))
    k = X.shape[1]
    scale = (g / (g - 1)) * ((n - 1) / max(n - k, 1)) if g > 1 else 1.0
    vcov = scale * xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.maximum(np.diag(vcov), 0))
    x0 = xvars[0]
    j = names.index(x0)
    t = beta[j] / se[j] if se[j] > 0 else np.nan
    return {
        "coef": float(beta[j]),
        "se": float(se[j]),
        "t": float(t),
        "p": float(p_norm(t)),
        "N": int(n),
        "N_city": int(g),
        "mean_y": float(np.nanmean(yy)),
    }


def post(rows: list[dict], table: str, sample: str, spec: str, outcome: str, xvar: str, result: dict, controls: list[str] | None = None) -> None:
    rows.append(
        {
            "table": table,
            "sample": sample,
            "spec": spec,
            "outcome": outcome,
            "xvar": xvar,
            "coef": result.get("coef"),
            "se": result.get("se"),
            "t": result.get("t"),
            "p": result.get("p"),
            "N": result.get("N"),
            "N_city": result.get("N_city"),
            "mean_y": result.get("mean_y"),
            "controls": ",".join(controls or []),
        }
    )


def warmup_comparison() -> dict:
    current = read(PROCESSED / "patent_applicant_concentration_application_year_2008_2023.csv")
    old_bytes = subprocess.check_output(
        ["git", "show", "HEAD:data/processed/patent_applicant_concentration_application_year_2008_2023.csv"],
        cwd=ROOT,
    )
    old = pd.read_csv(io.BytesIO(old_bytes))
    keys = ["city", "year", "scope"]
    cols = ["new_applicants", "new_patents", "new_applicant_share", "total_patents", "active_applicants"]
    m = old[keys + cols].merge(current[keys + cols], on=keys, suffixes=("_old2000", "_new1985"))
    rows = []
    for col in cols:
        diff = m[f"{col}_new1985"] - m[f"{col}_old2000"]
        rows.append(
            {
                "variable": col,
                "mean_old2000": m[f"{col}_old2000"].mean(),
                "mean_new1985": m[f"{col}_new1985"].mean(),
                "mean_diff": diff.mean(),
                "min_diff": diff.min(),
                "max_diff": diff.max(),
                "changed_rows": int((diff != 0).sum()),
            }
        )
    pd.DataFrame(rows).to_csv(WARMUP_OUT, index=False, encoding="utf-8-sig")
    return {"comparison_rows": int(len(m)), "output_csv": str(WARMUP_OUT)}


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    main = add_common(read(MAIN))
    main = main[(main["scope"] == "inv_app_appyear") & (main["merge_idc_split"] == "both")].copy()
    policy = add_common(read(POLICY))
    policy = policy[(policy["scope"] == "inv_app_appyear") & (policy["merge_idc_split"] == "both")].copy()
    kept_policies = [p for p in POLICIES if p in policy.columns and policy[p].nunique(dropna=True) > 1]

    main_outcomes = [
        "new_applicant_share",
        "ln1p_new_applicants",
        "ln1p_new_patents",
        "ln1p_total_patents",
        "ln1p_incumbent_patents",
        "hhi",
        "top10_share",
    ]
    for y in main_outcomes:
        for spec, fe, src, controls in [
            ("province_year_fe", ["city", "province_year"], main, []),
            ("provyr_baseyr_fe", ["city", "province_year", "base_ln_patents_q_year", "base_top10_q_year"], main, []),
            ("policy_horserace", ["city", "province_year"], policy, kept_policies),
            ("policy_baseyr_fe", ["city", "province_year", "base_ln_patents_q_year", "base_top10_q_year"], policy, kept_policies),
        ]:
            res = cluster_ols(src, y, ["ln1p_idc_scope_stock_l1"], fe, controls)
            post(rows, "main_1985_warmup", "all", spec, y, "ln1p_idc_scope_stock_l1", res, controls)

    entry = add_common(main.merge(read(ENTRY_TYPE), on=["city", "year"], how="left", suffixes=("", "_type")))
    type_outcomes = [
        "individual_new_share_total",
        "ln_individual_new_n",
        "org_new_share_total",
        "ln_org_new_n",
        "firm_new_share_total",
        "ln_firm_new_n",
        "knowledge_new_share_total",
        "ln_knowledge_new_n",
    ]
    for y in type_outcomes:
        for spec, fe in [
            ("province_year_fe", ["city", "province_year"]),
            ("provyr_baseyr_fe", ["city", "province_year", "base_ln_patents_q_year", "base_top10_q_year"]),
        ]:
            res = cluster_ols(entry, y, ["ln1p_idc_scope_stock_l1"], fe)
            post(rows, "entry_type_1985_warmup", "all", spec, y, "ln1p_idc_scope_stock_l1", res)

    firm = add_common(main.merge(read(FIRM), on=["city", "year"], how="left", suffixes=("", "_firm")))
    for y in ["firm_new_share_total", "ln1p_new_firm_applicants", "ln1p_new_firm_patents", "ln1p_firm_incumbent_patents"]:
        if y not in firm.columns:
            continue
        for spec, fe in [
            ("province_year_fe", ["city", "province_year"]),
            ("provyr_baseyr_fe", ["city", "province_year", "base_ln_patents_q_year", "base_top10_q_year"]),
        ]:
            res = cluster_ols(firm, y, ["ln1p_idc_scope_stock_l1"], fe)
            post(rows, "firm_only_1985_warmup", "all", spec, y, "ln1p_idc_scope_stock_l1", res)

    org = add_common(main.merge(read(ORG), on=["city", "year"], how="left", suffixes=("", "_org")))
    for y in ["org_new_share", "ln1p_org_new_applicants", "org_hhi", "org_top10_share"]:
        if y not in org.columns:
            continue
        for spec, fe in [
            ("province_year_fe", ["city", "province_year"]),
            ("provyr_baseyr_fe", ["city", "province_year", "base_ln_patents_q_year", "base_top10_q_year"]),
        ]:
            res = cluster_ols(org, y, ["ln1p_idc_scope_stock_l1"], fe)
            post(rows, "org_only_1985_warmup", "all", spec, y, "ln1p_idc_scope_stock_l1", res)

    if FEATURE_X.exists():
        feature = read(FEATURE_X)
        fx = main.merge(feature.drop(columns=["province"], errors="ignore"), on=["city", "year"], how="left")
        fx = add_common(fx)
        feature_xvars = [
            "ln1p_idc_scope_cloud_stock_l1",
            "ln1p_idc_scope_noncloud_stock_l1",
            "ln1p_idc_scope_cross_stock_l1",
            "ln1p_idc_scope_provlic_stock_l1",
            "ln1p_idc_scope_carrier_stock_l1",
            "ln1p_idc_scope_noncarrier_stock_l1",
        ]
        for x in [v for v in feature_xvars if v in fx.columns]:
            for y in ["new_applicant_share", "ln1p_new_applicants", "ln1p_new_patents"]:
                res = cluster_ols(fx, y, [x], ["city", "province_year", "base_ln_patents_q_year", "base_top10_q_year"])
                post(rows, "idc_feature_x", "all", "provyr_baseyr_fe", y, x, res)

    if QUALITY.exists():
        quality = add_common(read(QUALITY))
        quality = quality[quality["merge_idc_split"].eq("both")].copy()
        quality_outcomes = [
            "new_applicant_share",
            "ln1p_new_applicants",
            "ln1p_new_patents",
            "ln1p_total_patents",
        ]
        for scope, scope_df in quality.groupby("scope", sort=True):
            for y in quality_outcomes:
                for spec, fe in [
                    ("province_year_fe", ["city", "province_year"]),
                    (
                        "provyr_baseyr_fe",
                        ["city", "province_year", "base_ln_patents_q_year", "base_top10_q_year"],
                    ),
                ]:
                    res = cluster_ols(scope_df, y, ["ln1p_idc_scope_stock_l1"], fe)
                    post(rows, "quality_appyear_2000_warmup", scope, spec, y, "ln1p_idc_scope_stock_l1", res)

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    warmup = warmup_comparison()
    report = {
        "results_csv": str(OUT),
        "rows": int(len(out)),
        "warmup_comparison": warmup,
        "kept_policy_controls": kept_policies,
        "note": "Python OLS with dummy fixed effects and city-clustered SE; diagnostic until Stata tables are rerun.",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
