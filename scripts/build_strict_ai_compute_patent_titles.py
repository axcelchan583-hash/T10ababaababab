#!/usr/bin/env python3
"""Build annual strict AI / compute-intensive patent title counts from CSMAR patent details."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pandas as pd


ZIP_PATH = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/"
    "上市公司数据相关信息/专利明细情况093018090(仅供哈佛大学使用).zip"
)
MEMBER = "PT_LCDETAIL.xlsx"
OUT_DIR = Path("/Users/mac/computerscience/23选题探索/T10/outputs")

STRICT_AI_RE = re.compile(
    r"人工智能|机器学习|深度学习|神经网络|自然语言|语音识别|图像识别|图象识别|"
    r"计算机视觉|强化学习|知识图谱|智能识别|智能推荐|智能问答|智能算法|"
    r"大模型|生成式|AIGC|AI模型|AI算法",
    re.IGNORECASE,
)

COMPUTE_RE = re.compile(
    STRICT_AI_RE.pattern
    + r"|云计算|边缘计算|数据中心|算力|高性能计算|并行计算|分布式计算|GPU|"
    r"图形处理器|服务器|数据处理|大数据|数据库|数据挖掘|数据分析|算法",
    re.IGNORECASE,
)


def clean_symbol(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.extract(r"(\d+)", expand=False)
        .fillna("")
        .str.zfill(6)
        .replace("000000", "")
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        with zf.open(MEMBER) as fh:
            raw = pd.read_excel(fh, dtype=str)

    df = raw.iloc[2:].copy()
    df = df.dropna(how="all")
    df["symbol"] = clean_symbol(df["Symbol"])
    df["grant_date"] = pd.to_datetime(df["GrantDate"], errors="coerce")
    df["year"] = df["grant_date"].dt.year
    df["patent_name"] = df["PatentName"].fillna("").astype(str).str.strip()
    df["application_number"] = df["ApplicationNumber"].fillna("").astype(str).str.strip()
    df["is_invention"] = df["PatentType"].astype(str).str.contains("发明", na=False)
    df = df[(df["symbol"] != "") & df["grant_date"].notna() & (df["patent_name"] != "")]

    fallback_key = df["patent_name"] + "|" + df["grant_date"].dt.strftime("%Y-%m-%d").fillna("")
    app_key = df["application_number"].where(df["application_number"] != "", fallback_key)
    df["dedup_key"] = df["symbol"] + "|" + app_key
    before = len(df)
    df = df.sort_values(["symbol", "dedup_key", "grant_date"]).drop_duplicates(["symbol", "dedup_key"])

    df["strict_ai_title"] = df["patent_name"].str.contains(STRICT_AI_RE)
    df["ai_compute_title"] = df["patent_name"].str.contains(COMPUTE_RE)
    df["strict_ai_title_invention"] = df["strict_ai_title"] & df["is_invention"]
    df["ai_compute_title_invention"] = df["ai_compute_title"] & df["is_invention"]

    annual = (
        df.groupby(["symbol", "year"], as_index=False)
        .agg(
            patent_count_dedup=("patent_name", "size"),
            invention_count_dedup=("is_invention", "sum"),
            strict_ai_title_all_count=("strict_ai_title", "sum"),
            ai_compute_title_all_count=("ai_compute_title", "sum"),
            strict_ai_title_invention_count=("strict_ai_title_invention", "sum"),
            ai_compute_title_invention_count=("ai_compute_title_invention", "sum"),
        )
        .sort_values(["symbol", "year"])
    )

    out_csv = OUT_DIR / "strict_ai_compute_patent_title_annual.csv"
    annual.to_csv(out_csv, index=False, encoding="utf-8-sig")

    report = {
        "source_zip": str(ZIP_PATH),
        "raw_rows_after_header": int(len(raw.iloc[2:].dropna(how="all"))),
        "rows_with_grant_date_before_dedup": int(before),
        "rows_after_dedup": int(len(df)),
        "firms": int(df["symbol"].nunique()),
        "year_min": int(df["year"].min()),
        "year_max": int(df["year"].max()),
        "strict_ai_title_invention_total": int(df["strict_ai_title_invention"].sum()),
        "ai_compute_title_invention_total": int(df["ai_compute_title_invention"].sum()),
        "annual_rows": int(len(annual)),
        "output_csv": str(out_csv),
    }
    (OUT_DIR / "strict_ai_compute_patent_title_build_report_20260523.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
