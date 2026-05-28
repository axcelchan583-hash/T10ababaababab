#!/usr/bin/env python3
"""Run DDD robustness checks for T10.

Checks covered:
1. Alternative HighCompute definitions.
2. Policy x HighCompute controls, implemented as policy controls in the
   high-minus-low differenced regression.
3. Event DDD around first IDC scope stock >= 2.
4. Excluding individual applicants and one-shot city applicants.
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
PANEL = PROCESSED / "overall_tech_entry_ddd_robustness_panel_2008_2023.csv"
OUT = TABLES / "overall_tech_ddd_robustness_results_20260528.csv"
EVENT_OUT = TABLES / "overall_tech_ddd_event_results_20260528.csv"
REPORT = REPORTS / "overall_tech_ddd_robustness_results_20260528.json"

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
KEY_OUTCOMES = [
    "ln1p_city_new_applicants_field",
    "ln1p_city_new_patents_field",
    "city_new_share_total_field",
    "field_new_share_total_field",
]
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


def sig(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def build_design(d: pd.DataFrame, xvars: list[str], fe_cols: list[str]) -> tuple[np.ndarray, list[str]]:
    parts = []
    names: list[str] = []
    for x in xvars:
        parts.append(pd.to_numeric(d[x], errors="coerce").fillna(0).to_numpy(dtype=float).reshape(-1, 1))
        names.append(x)
    for fe in fe_cols:
        dd = pd.get_dummies(d[fe].astype(str), prefix=fe, drop_first=True, dtype=float)
        if not dd.empty:
            parts.append(dd.to_numpy(dtype=float))
            names.extend(dd.columns.tolist())
    return np.column_stack(parts), names


def cluster_ols(df: pd.DataFrame, y: str, xvars: list[str], fe_cols: list[str], cluster: str = "city") -> dict:
    use_cols = list(dict.fromkeys([y, cluster] + xvars + fe_cols))
    d = df[use_cols].replace([np.inf, -np.inf], np.nan).dropna(subset=[y] + xvars).copy()
    if len(d) < 50:
        return {"N": len(d), "N_city": d[cluster].nunique(), "params": {}}
    yy = pd.to_numeric(d[y], errors="coerce").to_numpy(dtype=float)
    X, names = build_design(d, xvars, fe_cols)
    keep = np.isfinite(yy) & np.isfinite(X).all(axis=1)
    yy = yy[keep]
    X = X[keep]
    clusters = d.loc[keep, cluster].astype(str).to_numpy()
    if len(yy) <= X.shape[1]:
        return {"N": len(yy), "N_city": len(set(clusters)), "params": {}}

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
    params = {}
    for x in xvars:
        j = names.index(x)
        t = beta[j] / se[j] if se[j] > 0 else np.nan
        params[x] = {
            "coef": float(beta[j]),
            "se": float(se[j]),
            "t": float(t),
            "p": float(p_norm(t)),
        }
    return {"N": int(n), "N_city": int(g), "mean_y": float(np.nanmean(yy)), "params": params}


def make_diff_panel(panel: pd.DataFrame, variant: str, sample: str, min_total: int | None = None) -> pd.DataFrame:
    d = panel[(panel["variant"] == variant) & (panel["sample"] == sample)].copy()
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
        "idc_scope_stock",
    ] + [p for p in POLICIES if p in d.columns]
    wide = d.pivot_table(index=idx_cols, columns="high_compute", values=OUTCOMES, aggfunc="first")
    wide.columns = [f"{col}_h{int(high)}" for col, high in wide.columns]
    wide = wide.reset_index()
    for y in OUTCOMES:
        wide[f"d_{y}"] = wide[f"{y}_h1"] - wide[f"{y}_h0"]
    wide["year_fe"] = wide["year"].astype(str)
    return wide


def first_event_year(panel: pd.DataFrame, threshold: int = 2) -> pd.DataFrame:
    base = panel[["city", "year", "idc_scope_stock"]].drop_duplicates().copy()
    treated = base[base["idc_scope_stock"] >= threshold].groupby("city", as_index=False)["year"].min()
    treated = treated.rename(columns={"year": "event_year"})
    return treated


def add_event_bins(diff: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    d = diff.merge(events, on="city", how="left")
    d["rel"] = d["year"] - d["event_year"]
    bins = {
        "ev_m4": d["rel"].le(-4),
        "ev_m3": d["rel"].eq(-3),
        "ev_m2": d["rel"].eq(-2),
        # ev_m1 omitted
        "ev_0": d["rel"].eq(0),
        "ev_p1": d["rel"].eq(1),
        "ev_p2": d["rel"].eq(2),
        "ev_p3": d["rel"].eq(3),
        "ev_p4": d["rel"].ge(4),
    }
    for name, mask in bins.items():
        d[name] = np.where(d["event_year"].notna() & mask, 1, 0)
    return d


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    panel = pd.read_csv(PANEL, low_memory=False, encoding="utf-8-sig")
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype(int)
    kept_policies = [p for p in POLICIES if p in panel.columns and panel[p].nunique(dropna=True) > 1]

    rows: list[dict] = []
    variants = sorted(panel["variant"].dropna().unique().tolist())
    samples = ["all", "no_individual", "no_oneshot", "no_individual_no_oneshot"]
    sample_mins = {"all": None, "min20": 20, "min50": 50}

    for variant in variants:
        for sample in samples:
            for sample_label, min_total in sample_mins.items():
                diff = make_diff_panel(panel, variant, sample, min_total=min_total)
                if diff.empty:
                    continue
                for y in KEY_OUTCOMES:
                    dy = f"d_{y}"
                    for spec, xvars in [
                        ("diff_city_year_fe", ["ln1p_idc_scope_stock_l1"]),
                        ("diff_city_year_fe_policy_x_high", ["ln1p_idc_scope_stock_l1"] + kept_policies),
                    ]:
                        res = cluster_ols(diff, dy, xvars, ["city", "year_fe"], cluster="city")
                        main = res.get("params", {}).get("ln1p_idc_scope_stock_l1", {})
                        rows.append(
                            {
                                "block": "ddd_robustness",
                                "variant": variant,
                                "applicant_sample": sample,
                                "city_sample": sample_label,
                                "spec": spec,
                                "outcome": y,
                                "coef": main.get("coef"),
                                "se": main.get("se"),
                                "t": main.get("t"),
                                "p": main.get("p"),
                                "sig": sig(main.get("p", np.nan)),
                                "N": res.get("N"),
                                "N_city": res.get("N_city"),
                                "mean_diff_y": res.get("mean_y"),
                                "policy_controls": ",".join(kept_policies) if "policy" in spec else "",
                            }
                        )

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False, encoding="utf-8-sig")

    event_rows: list[dict] = []
    events = first_event_year(panel, threshold=2)
    event_terms = ["ev_m4", "ev_m3", "ev_m2", "ev_0", "ev_p1", "ev_p2", "ev_p3", "ev_p4"]
    for variant in variants:
        diff = make_diff_panel(panel, variant, "all", min_total=None)
        diff = add_event_bins(diff, events)
        for y in KEY_OUTCOMES:
            dy = f"d_{y}"
            res = cluster_ols(diff, dy, event_terms, ["city", "year_fe"], cluster="city")
            for term in event_terms:
                param = res.get("params", {}).get(term, {})
                event_rows.append(
                    {
                        "block": "event_ddd_scope_ge_2",
                        "variant": variant,
                        "applicant_sample": "all",
                        "event_term": term,
                        "outcome": y,
                        "coef": param.get("coef"),
                        "se": param.get("se"),
                        "t": param.get("t"),
                        "p": param.get("p"),
                        "sig": sig(param.get("p", np.nan)),
                        "N": res.get("N"),
                        "N_city": res.get("N_city"),
                    }
                )
    event_out = pd.DataFrame(event_rows)
    event_out.to_csv(EVENT_OUT, index=False, encoding="utf-8-sig")

    report = {
        "panel_csv": str(PANEL),
        "results_csv": str(OUT),
        "event_results_csv": str(EVENT_OUT),
        "rows": int(len(out)),
        "event_rows": int(len(event_out)),
        "variants": variants,
        "samples": samples,
        "kept_policy_controls": kept_policies,
        "note": "Differenced DDD: high-compute minus low-compute within city-year; city and year FE; city-clustered SE.",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
