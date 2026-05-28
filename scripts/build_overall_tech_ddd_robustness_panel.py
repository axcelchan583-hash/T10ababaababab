#!/usr/bin/env python3
"""Build robustness panels for the city x technology-field DDD design.

This one-pass builder extends the main high-compute DDD panel along two axes:

1. Alternative HighCompute definitions.
2. Applicant cleaning samples: all, excluding individuals, excluding one-shot
   city applicants, and excluding both.

It reads the full patent RAR once, aggregates to variant-city-field-applicant-
year, and writes a balanced city-year-field panel for downstream regressions.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
REPORTS = ROOT / "results/reports"
RAR_PATH = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/"
    "上市公司其他/分年份保存数据.rar"
)
IDC_PANEL = PROCESSED / "idc_scope_formal_application_year_panel_2008_2023.csv"
POLICY_PANEL = ROOT / "data/external_proxy/city_policy_horserace_panel_2008_2023.csv"

PUB_START_YEAR = 1985
PUB_END_YEAR = 2025
WARMUP_YEAR = 1985
START_YEAR = 2008
END_YEAR = 2023
CHUNKSIZE = 250_000

USECOLS = [
    "专利类型",
    "申请人",
    "申请人类型",
    "申请人城市",
    "申请号",
    "申请年份",
    "IPC分类号",
    "IPC主分类号",
]

IPC_SUBCLASS_RE = re.compile(r"([A-H][0-9]{2}[A-Z])")

BROAD_HIGH = {
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
G06_ALL = {v for v in BROAD_HIGH if v.startswith("G06")}
G16_ALL = {v for v in BROAD_HIGH if v.startswith("G16")}
H04_ALL = {v for v in BROAD_HIGH if v.startswith("H04")}

HIGH_VARIANTS: dict[str, set[str]] = {
    "broad": BROAD_HIGH,
    "no_h04": BROAD_HIGH - H04_ALL,
    "g06_g16_g10l": G06_ALL | G16_ALL | {"G10L"},
    "g06_only": G06_ALL,
}

FIRM_MARKERS = [
    "有限公司",
    "有限责任公司",
    "股份有限公司",
    "集团",
    "公司",
    "总公司",
    "分公司",
    "厂",
    "企业",
    "合作社",
    "银行",
    "保险",
    "证券",
    "商行",
    "事务所",
    "农场",
    "牧场",
    "矿",
]
KNOWLEDGE_MARKERS = [
    "大学",
    "学院",
    "高等专科学校",
    "职业技术学院",
    "职业学院",
    "专科学校",
    "学校",
    "中学",
    "小学",
    "幼儿园",
    "技校",
    "职校",
    "中等专业学校",
    "研究院",
    "研究所",
    "研究中心",
    "研发中心",
    "科学院",
    "设计院",
    "勘察院",
    "实验室",
    "工程中心",
    "技术中心",
    "医院",
    "卫生院",
    "疾控中心",
    "疾病预防控制中心",
]
GOV_MARKERS = [
    "人民政府",
    "政府",
    "委员会",
    "管理局",
    "财政局",
    "科技局",
    "知识产权局",
    "公安局",
    "检察院",
    "法院",
    "管委会",
    "水利局",
    "农业局",
    "林业局",
    "税务局",
    "交通局",
    "公路管理",
    "气象局",
    "规划局",
    "自然资源局",
    "生态环境局",
]
ORG_HINTS = set("公司厂院所校学局部委会中心站社团馆场矿队室库店行")


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
    text = text.strip().replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[;；,，]+$", "", text)
    return text


def contains_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)


def is_likely_person(text: str) -> bool:
    if not 2 <= len(text) <= 4:
        return False
    if contains_any(text, FIRM_MARKERS + KNOWLEDGE_MARKERS + GOV_MARKERS):
        return False
    if any(ch in ORG_HINTS for ch in text):
        return False
    return bool(re.fullmatch(r"[\u4e00-\u9fff·]+", text))


def infer_type(name: object, raw_type: object = "") -> str:
    raw = "" if pd.isna(raw_type) else str(raw_type)
    if "个人" in raw or raw.lower() in {"person", "individual"}:
        return "individual"
    text = norm_name(name)
    if not text:
        return "other"
    if is_likely_person(text):
        return "individual"
    if contains_any(text, FIRM_MARKERS):
        return "firm"
    if contains_any(text, KNOWLEDGE_MARKERS):
        return "knowledge"
    if contains_any(text, GOV_MARKERS):
        return "government"
    return "other"


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
    variant_parts: list[pd.Series] = []
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
        raw_type = chunk["申请人类型"] if "申请人类型" in chunk.columns else pd.Series("", index=chunk.index)
        chunk["clean_type"] = [infer_type(n, t) for n, t in zip(chunk["applicant"], raw_type)]
        chunk = chunk[
            (chunk["city"] != "")
            & (chunk["applicant"] != "")
            & (chunk["app_no"] != "")
            & (chunk["ipc_subclass"] != "")
        ].copy()
        if chunk.empty:
            continue
        stats["rows_clean"] += len(chunk)
        stats["rows_inv_app"] += len(chunk)

        for variant, high_set in HIGH_VARIANTS.items():
            sub = chunk[["year", "city", "applicant", "clean_type", "app_no", "ipc_subclass"]].copy()
            sub["variant"] = variant
            sub["high_compute"] = sub["ipc_subclass"].isin(high_set).astype("int8")
            sub = sub[["variant", "year", "city", "high_compute", "applicant", "clean_type", "app_no"]]
            sub = sub.drop_duplicates()
            grouped = sub.groupby(["variant", "year", "city", "high_compute", "applicant", "clean_type"], sort=False).size()
            if not grouped.empty:
                variant_parts.append(grouped)
                stats["groups"] += len(grouped)

    stderr = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"bsdtar failed for {pub_year}: rc={rc}, stderr={stderr[:2000]}")
    return variant_parts, stats


def combine(parts: list[pd.Series]) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame(columns=["variant", "year", "city", "high_compute", "applicant", "clean_type", "patents"])
    out = pd.concat(parts).groupby(level=[0, 1, 2, 3, 4, 5]).sum().astype("int64")
    return out.rename("patents").reset_index()


def sample_detail(detail: pd.DataFrame, sample: str) -> pd.DataFrame:
    d = detail
    if sample in {"no_individual", "no_individual_no_oneshot"}:
        d = d[d["clean_type"] != "individual"]
    if sample in {"no_oneshot", "no_individual_no_oneshot"}:
        d = d[~d["is_one_shot"]]
    return d.copy()


def build_metrics_for_sample(detail: pd.DataFrame, sample: str) -> pd.DataFrame:
    d = sample_detail(detail, sample)
    if d.empty:
        return pd.DataFrame()

    d = d.copy()
    d["variant_city_applicant_key"] = d["variant"] + "||" + d["city"] + "||" + d["applicant"]
    d["variant_city_field_applicant_key"] = (
        d["variant"] + "||" + d["city"] + "||" + d["high_compute"].astype(str) + "||" + d["applicant"]
    )
    first_city = d.groupby("variant_city_applicant_key")["year"].min()
    first_field = d.groupby("variant_city_field_applicant_key")["year"].min()
    d["first_city_year"] = d["variant_city_applicant_key"].map(first_city)
    d["first_field_year"] = d["variant_city_field_applicant_key"].map(first_field)
    d["is_city_new_applicant"] = d["year"].eq(d["first_city_year"])
    d["is_field_new_applicant"] = d["year"].eq(d["first_field_year"])
    d["city_new_patents_part"] = np.where(d["is_city_new_applicant"], d["patents"], 0)
    d["field_new_patents_part"] = np.where(d["is_field_new_applicant"], d["patents"], 0)

    s = d[d["year"].between(START_YEAR, END_YEAR, inclusive="both")].copy()
    out = (
        s.groupby(["variant", "city", "year", "high_compute"], as_index=False)
        .agg(
            total_patents_field=("patents", "sum"),
            active_applicants_field=("applicant", "nunique"),
            city_new_applicants_field=("is_city_new_applicant", "sum"),
            field_new_applicants_field=("is_field_new_applicant", "sum"),
            city_new_patents_field=("city_new_patents_part", "sum"),
            field_new_patents_field=("field_new_patents_part", "sum"),
        )
    )
    out["sample"] = sample
    out["incumbent_patents_field"] = out["total_patents_field"] - out["city_new_patents_field"]
    return out


def load_idc_frame() -> pd.DataFrame:
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
    if POLICY_PANEL.exists():
        policy = pd.read_csv(POLICY_PANEL, low_memory=False, encoding="utf-8-sig")
        policy_cols = [c for c in policy.columns if c not in {"province", "policy_source_note"}]
        idc = idc.merge(policy[policy_cols], on=["city", "year"], how="left")
    policy_cols = [
        "broadband_china_pilot",
        "smart_city_pilot",
        "bigdata_comprehensive_pilot",
        "innovative_city_pilot",
        "national_hightech_zone",
        "ip_demo_city",
        "information_consumption_pilot",
        "ecommerce_demo_city",
    ]
    for col in policy_cols:
        if col not in idc.columns:
            idc[col] = 0
        idc[col] = pd.to_numeric(idc[col], errors="coerce").fillna(0)
    return idc


def balance_and_merge(metrics: pd.DataFrame) -> pd.DataFrame:
    idc = load_idc_frame()
    variants = pd.DataFrame({"variant": list(HIGH_VARIANTS)})
    samples = pd.DataFrame({"sample": ["all", "no_individual", "no_oneshot", "no_individual_no_oneshot"]})
    highs = pd.DataFrame({"high_compute": [0, 1]})
    frame = idc.merge(variants, how="cross").merge(samples, how="cross").merge(highs, how="cross")
    out = frame.merge(metrics, on=["variant", "sample", "city", "year", "high_compute"], how="left")
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
    out["idc_stock_high"] = out["ln1p_idc_scope_stock_l1"] * out["high_compute"]
    return out


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    all_parts: list[pd.Series] = []
    stats: list[dict] = []
    for pub_year in range(PUB_START_YEAR, PUB_END_YEAR + 1):
        parts, one_stats = read_publication_file(pub_year)
        all_parts.extend(parts)
        stats.append(one_stats)
        print(
            f"{pub_year}: seen={one_stats['rows_seen']:,} clean={one_stats['rows_clean']:,} "
            f"groups={one_stats['groups']:,} parts={len(parts)}",
            flush=True,
        )

    detail = combine(all_parts)
    detail["variant_city_applicant_key"] = detail["variant"] + "||" + detail["city"] + "||" + detail["applicant"]
    city_applicant_total = detail.groupby("variant_city_applicant_key")["patents"].sum()
    detail["city_applicant_total"] = detail["variant_city_applicant_key"].map(city_applicant_total)
    detail["is_one_shot"] = detail["city_applicant_total"].le(1)

    metrics = pd.concat(
        [build_metrics_for_sample(detail, sample) for sample in ["all", "no_individual", "no_oneshot", "no_individual_no_oneshot"]],
        ignore_index=True,
    )
    panel = balance_and_merge(metrics)

    out_csv = PROCESSED / "overall_tech_entry_ddd_robustness_panel_2008_2023.csv"
    out_dta = PROCESSED / "overall_tech_entry_ddd_robustness_panel_2008_2023.dta"
    panel.to_csv(out_csv, index=False, encoding="utf-8-sig")
    panel.to_stata(out_dta, write_index=False, version=118)

    summary = {
        "pub_start_year": PUB_START_YEAR,
        "pub_end_year": PUB_END_YEAR,
        "warmup_year": WARMUP_YEAR,
        "start_year": START_YEAR,
        "end_year": END_YEAR,
        "detail_rows": int(len(detail)),
        "panel_rows": int(len(panel)),
        "cities": int(panel["city"].nunique()),
        "variants": {k: sorted(v) for k, v in HIGH_VARIANTS.items()},
        "samples": sorted(panel["sample"].unique().tolist()),
        "source_stats": stats,
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
    }
    report_path = REPORTS / "overall_tech_entry_ddd_robustness_build_report_2008_2023.json"
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ["detail_rows", "panel_rows", "cities", "samples", "output_csv"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
