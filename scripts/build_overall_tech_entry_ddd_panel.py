#!/usr/bin/env python3
"""Build city-tech-year applicant entry panel for overall high-compute DDD.

This complements the firm-only DDD panel. It asks whether IDC service coverage
is followed by stronger new applicant entry in compute-intensive patent fields
than in other fields within the same city-year.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23实证选题探索/T10")
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


def clean_text(s: pd.Series) -> pd.Series:
    return (
        s.astype("string")
        .str.strip()
        .str.replace("\u3000", "", regex=False)
        .str.replace(r"\s+", "", regex=True)
    )


def first_token(s: pd.Series, pattern: str) -> pd.Series:
    return clean_text(s).str.split(pattern, regex=True).str[0].fillna("")


def normalize_city(s: pd.Series) -> pd.Series:
    city = first_token(s, r"[;；,，/、]")
    city = city.str.replace(r"^中国", "", regex=True)
    city = city.str.replace(r"市$", "", regex=True)
    city = city.mask(city.isin(["CN", "中国", "中华人民共和国", "不详", "未知", "无"]), "")
    return city


def first_applicant(s: pd.Series) -> pd.Series:
    return first_token(s, r"[;；]")


def norm_name(name: object) -> str:
    text = "" if pd.isna(name) else str(name)
    text = text.strip()
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[;；,，]+$", "", text)
    return text


def stream_member(pub_year: int) -> subprocess.Popen:
    member = f"分年份保存数据/中国全量专利数据库{pub_year}年.csv"
    return subprocess.Popen(
        ["bsdtar", "-xOf", str(RAR_PATH), member],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def first_ipc_subclass(chunk: pd.DataFrame) -> pd.Series:
    main = chunk.get("IPC主分类号", pd.Series("", index=chunk.index, dtype="string")).astype("string").fillna("")
    all_ipc = chunk.get("IPC分类号", pd.Series("", index=chunk.index, dtype="string")).astype("string").fillna("")
    ipc = main.mask(main.str.strip().eq(""), all_ipc)
    ipc = ipc.str.upper().str.replace(" ", "", regex=False)
    return ipc.str.extract(IPC_SUBCLASS_RE, expand=False).fillna("")


def read_publication_file(pub_year: int) -> tuple[list[pd.Series], dict]:
    proc = stream_member(pub_year)
    assert proc.stdout is not None

    parts: list[pd.Series] = []
    stats = {
        "pub_file_year": pub_year,
        "rows_seen": 0,
        "rows_clean": 0,
        "rows_inv_app": 0,
        "groups": 0,
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
        chunk["applicant"] = first_applicant(chunk["申请人"]).map(norm_name)
        chunk["app_no"] = clean_text(chunk["申请号"])
        chunk["ipc_subclass"] = first_ipc_subclass(chunk)
        chunk = chunk[
            (chunk["city"] != "")
            & (chunk["applicant"] != "")
            & (chunk["app_no"] != "")
            & (chunk["ipc_subclass"] != "")
        ].copy()
        stats["rows_clean"] += len(chunk)
        stats["rows_inv_app"] += len(chunk)
        if chunk.empty:
            continue

        chunk["high_compute"] = chunk["ipc_subclass"].isin(HIGH_COMPUTE_SUBCLASSES).astype("int8")
        sub = chunk[["year", "city", "high_compute", "applicant", "app_no"]].drop_duplicates()
        grouped = sub.groupby(["year", "city", "high_compute", "applicant"], sort=False).size()
        if not grouped.empty:
            parts.append(grouped)
            stats["groups"] += len(grouped)

    stderr = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"bsdtar failed for {pub_year}: rc={rc}, stderr={stderr[:2000]}")
    return parts, stats


def combine(parts: list[pd.Series]) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame(columns=["year", "city", "high_compute", "applicant", "patents"])
    out = pd.concat(parts).groupby(level=[0, 1, 2, 3]).sum().astype("int64")
    return out.rename("patents").reset_index()


def build_metrics(detail: pd.DataFrame) -> pd.DataFrame:
    detail = detail.copy()
    detail["city_applicant_key"] = detail["city"] + "||" + detail["applicant"]
    detail["city_field_applicant_key"] = (
        detail["city"] + "||" + detail["high_compute"].astype(str) + "||" + detail["applicant"]
    )
    first_city = detail.groupby("city_applicant_key")["year"].min()
    first_field = detail.groupby("city_field_applicant_key")["year"].min()
    detail["first_city_year"] = detail["city_applicant_key"].map(first_city)
    detail["first_field_year"] = detail["city_field_applicant_key"].map(first_field)
    detail["is_city_new_applicant"] = detail["year"].eq(detail["first_city_year"])
    detail["is_field_new_applicant"] = detail["year"].eq(detail["first_field_year"])
    detail["city_new_patents_part"] = np.where(detail["is_city_new_applicant"], detail["patents"], 0)
    detail["field_new_patents_part"] = np.where(detail["is_field_new_applicant"], detail["patents"], 0)

    sample = detail[detail["year"].between(START_YEAR, END_YEAR, inclusive="both")].copy()
    out = (
        sample.groupby(["city", "year", "high_compute"], as_index=False)
        .agg(
            total_patents_field=("patents", "sum"),
            active_applicants_field=("applicant", "nunique"),
            city_new_applicants_field=("is_city_new_applicant", "sum"),
            field_new_applicants_field=("is_field_new_applicant", "sum"),
            city_new_patents_field=("city_new_patents_part", "sum"),
            field_new_patents_field=("field_new_patents_part", "sum"),
        )
    )
    out["incumbent_patents_field"] = out["total_patents_field"] - out["city_new_patents_field"]
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
    frame = idc.merge(pd.DataFrame({"high_compute": [0, 1]}), how="cross")
    out = frame.merge(metrics, on=["city", "year", "high_compute"], how="left")

    count_cols = [
        "total_patents_field",
        "active_applicants_field",
        "city_new_applicants_field",
        "field_new_applicants_field",
        "city_new_patents_field",
        "field_new_patents_field",
        "incumbent_patents_field",
    ]
    for col in count_cols:
        out[col] = out[col].fillna(0)

    out["city_new_share_total_field"] = out["city_new_patents_field"] / out["total_patents_field"].where(
        out["total_patents_field"] > 0
    )
    out["field_new_share_total_field"] = out["field_new_patents_field"] / out["total_patents_field"].where(
        out["total_patents_field"] > 0
    )
    out["incumbent_share_field"] = out["incumbent_patents_field"] / out["total_patents_field"].where(
        out["total_patents_field"] > 0
    )
    for col in count_cols:
        out[f"ln1p_{col}"] = np.log1p(out[col])

    out["high_compute_label"] = np.where(out["high_compute"].eq(1), "high_compute", "other")
    out["idc_stock_high"] = out["ln1p_idc_scope_stock_l1"] * out["high_compute"]
    out["idc_new_high"] = out["ln1p_idc_scope_new_l1"] * out["high_compute"]
    out["idc_pre5_high"] = out["ln1p_idc_scope_pre5_l1"] * out["high_compute"]
    return out


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    all_parts: list[pd.Series] = []
    stats: list[dict] = []
    for pub_year in range(PUB_START_YEAR, PUB_END_YEAR + 1):
        parts, one_stats = read_publication_file(pub_year)
        all_parts.extend(parts)
        stats.append(one_stats)
        print(
            f"{pub_year}: seen={one_stats['rows_seen']:,} clean={one_stats['rows_clean']:,} "
            f"parts={len(parts)}"
        )

    detail = combine(all_parts)
    metrics = build_metrics(detail)
    panel = balance_and_merge_idc(metrics)

    out_csv = PROCESSED / "overall_tech_entry_ddd_panel_2008_2023.csv"
    out_dta = PROCESSED / "overall_tech_entry_ddd_panel_2008_2023.dta"
    panel.to_csv(out_csv, index=False, encoding="utf-8-sig")
    panel.to_stata(out_dta, write_index=False, version=118)

    report = {
        "detail_rows": int(len(detail)),
        "panel_rows": int(len(panel)),
        "cities": int(panel["city"].nunique()),
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "high_compute_subclasses": sorted(HIGH_COMPUTE_SUBCLASSES),
        "source_stats": stats,
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
    }
    report_path = REPORTS / "overall_tech_entry_ddd_build_report_2008_2023.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2)[:3000])


if __name__ == "__main__":
    main()
