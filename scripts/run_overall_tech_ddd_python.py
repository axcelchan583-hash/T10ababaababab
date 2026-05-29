#!/usr/bin/env python3
"""Run the city x technology-field DDD main effect in Python.

The Stata DDD specification absorbs city-year, city-field, and field-year fixed
effects:

    Y_cft = beta * IDC_ct-1 * HighCompute_f
          + city-year FE + city-field FE + field-year FE + error_cft

Because HighCompute is binary, this script estimates the equivalent differenced
model:

    (Y_high - Y_low)_ct = beta * IDC_ct-1 + city FE + year FE + error_ct

and clusters standard errors at the city level.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
TABLES = ROOT / "results/tables"
REPORTS = ROOT / "results/reports"
PANEL = PROCESSED / "overall_tech_entry_ddd_panel_2008_2023.csv"
OUT = TABLES / "overall_tech_ddd_main_results_20260528.csv"
REPORT = REPORTS / "overall_tech_ddd_main_results_20260528.json"


OUTCOMES = [
    "ln1p_city_new_applicants_field",
    "ln1p_city_new_patents_field",
    "city_new_share_total_field",
    "ln1p_field_new_applicants_field",
    "ln1p_field_new_patents_field",
    "field_new_share_total_field",
    "ln1p_total_patents_field",
    "ln1p_incumbent_patents_field",
]


def p_norm(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return math.erfc(abs(z) / math.sqrt(2.0))


def cluster_ols(df: pd.DataFrame, y: str, x: str, fe_cols: list[str], cluster: str = "city") -> dict:
    use_cols = list(dict.fromkeys([y, x, cluster] + fe_cols))
    d = df[use_cols].replace([np.inf, -np.inf], np.nan).dropna(subset=[y, x]).copy()
    if len(d) < 50:
        return {"coef": np.nan, "se": np.nan, "t": np.nan, "p": np.nan, "N": len(d), "N_city": d[cluster].nunique()}

    parts = [np.ones((len(d), 1), dtype=float)]
    names = ["_cons"]
    parts.append(pd.to_numeric(d[x], errors="coerce").fillna(0).to_numpy(dtype=float).reshape(-1, 1))
    names.append(x)
    for fe in fe_cols:
        dd = pd.get_dummies(d[fe].astype(str), prefix=fe, drop_first=True, dtype=float)
        if not dd.empty:
            parts.append(dd.to_numpy(dtype=float))
            names.extend(dd.columns.tolist())
    X = np.column_stack(parts)
    yy = pd.to_numeric(d[y], errors="coerce").to_numpy(dtype=float)
    keep = np.isfinite(yy) & np.isfinite(X).all(axis=1)
    X = X[keep]
    yy = yy[keep]
    clusters = d.loc[keep, cluster].astype(str).to_numpy()
    if len(yy) <= X.shape[1]:
        return {"coef": np.nan, "se": np.nan, "t": np.nan, "p": np.nan, "N": len(yy), "N_city": len(set(clusters))}

    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ yy
    resid = yy - X @ beta
    meat = np.zeros((X.shape[1], X.shape[1]), dtype=float)
    for g in np.unique(clusters):
        idx = clusters == g
        score = X[idx].T @ resid[idx].reshape(-1, 1)
        meat += score @ score.T

    n = len(yy)
    g = len(np.unique(clusters))
    k = X.shape[1]
    scale = (g / (g - 1)) * ((n - 1) / max(n - k, 1)) if g > 1 else 1.0
    vcov = scale * xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.maximum(np.diag(vcov), 0))
    j = names.index(x)
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


def make_diff_panel(panel: pd.DataFrame, min_total: int | None = None) -> pd.DataFrame:
    d = panel.copy()
    if min_total is not None:
        d = d[d["total_patents"] >= min_total].copy()
    idx_cols = [
        "city",
        "province",
        "year",
        "city_id",
        "province_id",
        "total_patents",
        "ln1p_idc_scope_stock_l1",
    ]
    wide = d.pivot_table(index=idx_cols, columns="high_compute", values=OUTCOMES, aggfunc="first")
    wide.columns = [f"{col}_h{int(high)}" for col, high in wide.columns]
    wide = wide.reset_index()
    for y in OUTCOMES:
        wide[f"d_{y}"] = wide[f"{y}_h1"] - wide[f"{y}_h0"]
    wide["year_fe"] = wide["year"].astype(str)
    return wide


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    panel = pd.read_csv(PANEL, low_memory=False, encoding="utf-8-sig")
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype(int)
    panel["year_fe"] = panel["year"].astype(str)
    rows: list[dict] = []

    for sample, min_total in [("all", None), ("min20", 20), ("min50", 50)]:
        diff = make_diff_panel(panel, min_total=min_total)
        for y in OUTCOMES:
            dy = f"d_{y}"
            res = cluster_ols(diff, dy, "ln1p_idc_scope_stock_l1", ["city", "year_fe"], cluster="city")
            rows.append(
                {
                    "block": "overall_tech_ddd_diff",
                    "sample": sample,
                    "spec": "diff_city_year_fe",
                    "xvar": "ln1p_idc_scope_stock_l1",
                    "outcome": y,
                    "diff_outcome": dy,
                    "coef": res["coef"],
                    "se": res["se"],
                    "t": res["t"],
                    "p": res["p"],
                    "sig": "***" if res["p"] < 0.01 else "**" if res["p"] < 0.05 else "*" if res["p"] < 0.1 else "",
                    "N": res["N"],
                    "N_city": res["N_city"],
                    "mean_diff_y": res.get("mean_y"),
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    report = {
        "panel_csv": str(PANEL),
        "results_csv": str(OUT),
        "rows": int(len(out)),
        "samples": sorted(out["sample"].unique().tolist()),
        "outcomes": OUTCOMES,
        "note": "Differenced DDD: high-compute field minus other field within city-year; constant + city and year FE; city-clustered SE.",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
