#!/usr/bin/env python3
"""Build city-tech-year firm entry panel for DDD smoke tests.

The panel asks whether licensed IDC service coverage is followed by stronger
firm entry in compute-intensive patent fields than in other fields within the
same city-year.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from build_patent_applicant_concentration_application_year import (
    clean_text,
    first_applicant,
    normalize_city,
)
from build_top_applicant_type_clean_panel import FIRM_MARKERS, norm_name


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
PROCESSED = ROOT / "data/processed"
REPORTS = ROOT / "results/reports"
RAR_PATH = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/"
    "上市公司其他/分年份保存数据.rar"
)
IDC_PANEL = PROCESSED / "idc_scope_formal_application_year_panel_2008_2023.csv"

PUB_START_YEAR = 2000
PUB_END_YEAR = 2025
WARMUP_YEAR = 2000
START_YEAR = 2008
END_YEAR = 2023
CHUNKSIZE = 200_000

USECOLS = [
    "专利类型",
    "申请人",
    "申请人城市",
    "申请号",
    "申请年份",
    "IPC分类号",
    "IPC主分类号",
]

FIRM_REGEX = re.compile("|".join(re.escape(x) for x in sorted(FIRM_MARKERS, key=len, reverse=True)))
IPC_SUBCLASS_RE = re.compile(r"([A-H][0-9]{2}[A-Z])")

HIGH_COMPUTE_SUBCLASSES = {
    "B25J",
    "G05B",
    "G06C",
    "G06D",
    "G06E",
    "G06F",
    "G06G",
    "G06J",
    "G06K",
    "G06M",
    "G06N",
    "G06Q",
    "G06T",
    "G06V",
    "G10L",
    "G16B",
    "G16C",
    "G16H",
    "G16Y",
    "H04B",
    "H04L",
    "H04M",
    "H04N",
    "H04W",
}


def stream_member(pub_year: int) -> subprocess.Popen:
    member = f"分年份保存数据/中国全量专利数据库{pub_year}年.csv"
    return subprocess.Popen(
        ["bsdtar", "-xOf", str(RAR_PATH), member],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def first_ipc_subclass(chunk: pd.DataFrame) -> pd.Series:
    if "IPC主分类号" in chunk.columns:
        main = chunk["IPC主分类号"].astype("string").fillna("")
    else:
        main = pd.Series("", index=chunk.index, dtype="string")
    if "IPC分类号" in chunk.columns:
        all_ipc = chunk["IPC分类号"].astype("string").fillna("")
    else:
        all_ipc = pd.Series("", index=chunk.index, dtype="string")
    ipc = main.mask(main.str.strip().eq(""), all_ipc)
    ipc = ipc.str.upper().str.replace(" ", "", regex=False)
    return ipc.str.extract(IPC_SUBCLASS_RE, expand=False).fillna("")


def read_publication_file(pub_year: int) -> tuple[list[pd.Series], list[pd.Series], dict]:
    proc = stream_member(pub_year)
    assert proc.stdout is not None

    all_parts: list[pd.Series] = []
    firm_parts: list[pd.Series] = []
    stats = {
        "pub_file_year": pub_year,
        "rows_seen": 0,
        "rows_clean": 0,
        "rows_inv_app": 0,
        "rows_missing_ipc": 0,
        "rows_firm_inv_app": 0,
    }

    reader = pd.read_csv(
        proc.stdout,
        usecols=lambda c: c in USECOLS,
        dtype=str,
        chunksize=CHUNKSIZE,
        encoding="utf-8-sig",
        on_bad_lines="skip",
        low_memory=False,
    )

    for chunk in reader:
        stats["rows_seen"] += len(chunk)
        required = {"专利类型", "申请人", "申请人城市", "申请号", "申请年份"}
        if not required.issubset(chunk.columns):
            continue
        chunk = chunk[(chunk["申请人"] != "申请人") & (chunk["申请人城市"] != "申请人城市")].copy()
        chunk["ptype"] = chunk["专利类型"].astype("string").fillna("")
        chunk = chunk[chunk["ptype"].str.contains("发明申请", na=False)].copy()
        if chunk.empty:
            continue

        chunk["year"] = pd.to_numeric(chunk["申请年份"], errors="coerce")
        chunk = chunk[chunk["year"].between(WARMUP_YEAR, END_YEAR, inclusive="both")].copy()
        if chunk.empty:
            continue
        chunk["year"] = chunk["year"].astype("int16")
        chunk["city"] = normalize_city(chunk["申请人城市"])
        chunk["applicant"] = first_applicant(chunk["申请人"])
        chunk["applicant_norm"] = chunk["applicant"].map(norm_name)
        chunk["app_no"] = clean_text(chunk["申请号"])
        chunk["ipc_subclass"] = first_ipc_subclass(chunk)
        chunk = chunk[
            (chunk["city"] != "")
            & (chunk["applicant_norm"] != "")
            & (chunk["app_no"] != "")
            & (chunk["ipc_subclass"] != "")
        ].copy()
        stats["rows_clean"] += len(chunk)
        stats["rows_inv_app"] += len(chunk)
        stats["rows_missing_ipc"] += int((chunk["ipc_subclass"] == "").sum())
        if chunk.empty:
            continue

        chunk["high_compute"] = chunk["ipc_subclass"].isin(HIGH_COMPUTE_SUBCLASSES).astype("int8")

        all_sub = chunk[["year", "city", "high_compute", "app_no"]].drop_duplicates()
        all_grouped = all_sub.groupby(["year", "city", "high_compute"], sort=False).size()
        if not all_grouped.empty:
            all_parts.append(all_grouped)

        firm_mask = chunk["applicant_norm"].str.contains(FIRM_REGEX, na=False)
        firm = chunk.loc[firm_mask, ["year", "city", "high_compute", "applicant_norm", "app_no"]].drop_duplicates()
        stats["rows_firm_inv_app"] += len(firm)
        firm_grouped = firm.groupby(["year", "city", "high_compute", "applicant_norm"], sort=False).size()
        if not firm_grouped.empty:
            firm_parts.append(firm_grouped)

    stderr = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"bsdtar failed for {pub_year}: rc={rc}, stderr={stderr[:2000]}")
    stats["all_parts"] = len(all_parts)
    stats["firm_parts"] = len(firm_parts)
    return all_parts, firm_parts, stats


def combine(parts: list[pd.Series], names: list[str], value_name: str) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame(columns=names + [value_name])
    out = pd.concat(parts).groupby(level=list(range(len(names)))).sum().astype("int64")
    return out.rename(value_name).reset_index()


def build_metrics(all_counts: pd.DataFrame, firm_counts: pd.DataFrame) -> pd.DataFrame:
    all_metrics = all_counts.rename(columns={"patents": "total_patents_field"})
    if firm_counts.empty:
        firm_metrics = pd.DataFrame(columns=["city", "year", "high_compute"])
    else:
        firm_counts = firm_counts.copy()
        firm_counts["city_firm_key"] = firm_counts["city"] + "||" + firm_counts["applicant_norm"]
        firm_counts["city_field_firm_key"] = (
            firm_counts["city"] + "||" + firm_counts["high_compute"].astype(str) + "||" + firm_counts["applicant_norm"]
        )
        first_city = firm_counts.groupby("city_firm_key")["year"].min()
        first_field = firm_counts.groupby("city_field_firm_key")["year"].min()
        firm_counts["first_city_year"] = firm_counts["city_firm_key"].map(first_city)
        firm_counts["first_field_year"] = firm_counts["city_field_firm_key"].map(first_field)
        firm_counts["is_city_new_firm"] = firm_counts["year"].eq(firm_counts["first_city_year"])
        firm_counts["is_field_new_firm"] = firm_counts["year"].eq(firm_counts["first_field_year"])
        firm_counts["city_new_firm_patents_part"] = np.where(
            firm_counts["is_city_new_firm"], firm_counts["patents"], 0
        )
        firm_counts["field_new_firm_patents_part"] = np.where(
            firm_counts["is_field_new_firm"], firm_counts["patents"], 0
        )

        sample = firm_counts[firm_counts["year"].between(START_YEAR, END_YEAR, inclusive="both")].copy()
        firm_metrics = (
            sample.groupby(["city", "year", "high_compute"], as_index=False)
            .agg(
                firm_total_patents_field=("patents", "sum"),
                firm_active_applicants_field=("applicant_norm", "nunique"),
                city_new_firm_applicants_field=("is_city_new_firm", "sum"),
                field_new_firm_applicants_field=("is_field_new_firm", "sum"),
                city_new_firm_patents_field=("city_new_firm_patents_part", "sum"),
                field_new_firm_patents_field=("field_new_firm_patents_part", "sum"),
            )
        )
        firm_metrics["firm_incumbent_patents_field"] = (
            firm_metrics["firm_total_patents_field"] - firm_metrics["city_new_firm_patents_field"]
        )

    sample_all = all_metrics[all_metrics["year"].between(START_YEAR, END_YEAR, inclusive="both")].copy()
    out = sample_all.merge(firm_metrics, on=["city", "year", "high_compute"], how="left")
    fill_cols = [
        "firm_total_patents_field",
        "firm_active_applicants_field",
        "city_new_firm_applicants_field",
        "field_new_firm_applicants_field",
        "city_new_firm_patents_field",
        "field_new_firm_patents_field",
        "firm_incumbent_patents_field",
    ]
    for col in fill_cols:
        if col not in out.columns:
            out[col] = 0
        out[col] = out[col].fillna(0)
    return out


def balance_and_merge_idc(metrics: pd.DataFrame) -> pd.DataFrame:
    idc = pd.read_csv(IDC_PANEL, low_memory=False, encoding="utf-8-sig")
    idc = idc[(idc["scope"] == "inv_app_appyear") & (idc["merge_idc_split"] == "both")].copy()
    keep_cols = [
        "city",
        "province",
        "year",
        "total_patents",
        "city_id",
        "province_id",
        "base_ln_patents_q",
        "base_top10_q",
        "idc_scope_new",
        "idc_scope_stock",
        "idc_scope_pre5",
        "ln1p_idc_scope_stock_l1",
        "ln1p_idc_scope_pre5_l1",
        "ln1p_idc_scope_new_l1",
    ]
    idc = idc[keep_cols].copy()
    high = pd.DataFrame({"high_compute": [0, 1]})
    frame = idc.merge(high, how="cross")
    out = frame.merge(metrics, on=["city", "year", "high_compute"], how="left")

    count_cols = [
        "total_patents_field",
        "firm_total_patents_field",
        "firm_active_applicants_field",
        "city_new_firm_applicants_field",
        "field_new_firm_applicants_field",
        "city_new_firm_patents_field",
        "field_new_firm_patents_field",
        "firm_incumbent_patents_field",
    ]
    for col in count_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    out["city_new_firm_share_total_field"] = out["city_new_firm_patents_field"] / out[
        "total_patents_field"
    ].where(out["total_patents_field"] > 0)
    out["field_new_firm_share_total_field"] = out["field_new_firm_patents_field"] / out[
        "total_patents_field"
    ].where(out["total_patents_field"] > 0)
    out["city_new_firm_share_firm_field"] = out["city_new_firm_patents_field"] / out[
        "firm_total_patents_field"
    ].where(out["firm_total_patents_field"] > 0)
    out["field_new_firm_share_firm_field"] = out["field_new_firm_patents_field"] / out[
        "firm_total_patents_field"
    ].where(out["firm_total_patents_field"] > 0)
    out["firm_patent_share_field"] = out["firm_total_patents_field"] / out["total_patents_field"].where(
        out["total_patents_field"] > 0
    )
    out["high_compute_label"] = np.where(out["high_compute"].eq(1), "high_compute", "other")

    for col in count_cols:
        out[f"ln1p_{col}"] = np.log1p(out[col])

    aliases = {
        "total_patents_field": "tot_pat_f",
        "firm_total_patents_field": "firm_pat_f",
        "firm_active_applicants_field": "firm_act_f",
        "city_new_firm_applicants_field": "city_new_firm_n_f",
        "field_new_firm_applicants_field": "field_new_firm_n_f",
        "city_new_firm_patents_field": "city_new_firm_pat_f",
        "field_new_firm_patents_field": "field_new_firm_pat_f",
        "firm_incumbent_patents_field": "firm_inc_pat_f",
        "city_new_firm_share_total_field": "city_new_share_tot_f",
        "field_new_firm_share_total_field": "field_new_share_tot_f",
        "city_new_firm_share_firm_field": "city_new_share_firm_f",
        "field_new_firm_share_firm_field": "field_new_share_firm_f",
        "firm_patent_share_field": "firm_share_f",
        "ln1p_total_patents_field": "ln_tot_pat_f",
        "ln1p_firm_total_patents_field": "ln_firm_pat_f",
        "ln1p_firm_active_applicants_field": "ln_firm_act_f",
        "ln1p_city_new_firm_applicants_field": "ln_city_new_firm_n_f",
        "ln1p_field_new_firm_applicants_field": "ln_field_new_firm_n_f",
        "ln1p_city_new_firm_patents_field": "ln_city_new_firm_pat_f",
        "ln1p_field_new_firm_patents_field": "ln_field_new_firm_pat_f",
        "ln1p_firm_incumbent_patents_field": "ln_firm_inc_pat_f",
    }
    for old, new in aliases.items():
        out[new] = out[old]
    out = out.fillna(0)
    return out


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    all_parts: list[pd.Series] = []
    firm_parts: list[pd.Series] = []
    reports: list[dict] = []

    for pub_year in range(PUB_START_YEAR, PUB_END_YEAR + 1):
        print(f"PROCESS_PUBLICATION_FILE {pub_year}", flush=True)
        all_part, firm_part, stats = read_publication_file(pub_year)
        all_parts.extend(all_part)
        firm_parts.extend(firm_part)
        reports.append(stats)
        print(json.dumps(stats, ensure_ascii=False), flush=True)

    all_counts = combine(all_parts, ["year", "city", "high_compute"], "patents")
    firm_counts = combine(firm_parts, ["year", "city", "high_compute", "applicant_norm"], "patents")
    metrics = build_metrics(all_counts, firm_counts)
    out = balance_and_merge_idc(metrics)

    out_csv = PROCESSED / f"firm_tech_entry_ddd_panel_{START_YEAR}_{END_YEAR}.csv"
    out_dta = PROCESSED / f"firm_tech_entry_ddd_panel_{START_YEAR}_{END_YEAR}.dta"
    report_csv = REPORTS / f"firm_tech_entry_ddd_build_report_{START_YEAR}_{END_YEAR}.csv"
    report_json = REPORTS / f"firm_tech_entry_ddd_build_report_{START_YEAR}_{END_YEAR}.json"

    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    out.to_stata(out_dta, write_index=False, version=118)
    pd.DataFrame(reports).to_csv(report_csv, index=False, encoding="utf-8-sig")
    summary = {
        "rows": int(len(out)),
        "cities": int(out["city"].nunique()),
        "years": [int(out["year"].min()), int(out["year"].max())],
        "high_compute_fields": sorted(HIGH_COMPUTE_SUBCLASSES),
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
        "report_csv": str(report_csv),
    }
    report_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    print(
        out[
            [
                "high_compute",
                "total_patents_field",
                "firm_total_patents_field",
                "city_new_firm_patents_field",
                "field_new_firm_patents_field",
                "city_new_firm_applicants_field",
                "field_new_firm_applicants_field",
            ]
        ]
        .groupby("high_compute")
        .sum(numeric_only=True)
        .to_string()
    )


if __name__ == "__main__":
    main()
