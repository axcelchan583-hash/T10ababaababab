#!/usr/bin/env python3
"""Build quality-scope Top applicant turnover panels from full CNIPA data.

This is intentionally separate from the city-year quality panel because Top
turnover requires applicant-level quality-patent counts by city-year.
"""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
BASE = PROCESSED / "new_y_smoke_panel_2008_2023.csv"
RAR_PATH = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/"
    "上市公司其他/分年份保存数据.rar"
)
OUT_CSV = PROCESSED / "quality_top_turnover_panel_2008_2023.csv"
OUT_DTA = PROCESSED / "quality_top_turnover_panel_2008_2023.dta"

START_YEAR = 2008
END_YEAR = 2023
PUB_START_YEAR = 2000
PUB_END_YEAR = 2025
CHUNKSIZE = 250_000
USECOLS = [
    "专利类型",
    "申请人",
    "申请人城市",
    "申请号",
    "申请年份",
    "被引证次数",
    "家族被引证次数",
]
SCOPES = {
    "inv_grant_appyear": "qgrant",
    "inv_grant_cited_appyear": "qcited",
    "inv_grant_familycited_appyear": "qfcited",
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
    text = text.strip().replace("（", "(").replace("）", ")")
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


def append_group(groups: dict[str, list[pd.Series]], scope: str, sub: pd.DataFrame) -> None:
    if sub.empty:
        return
    grouped = sub.groupby(["year", "city", "applicant"], sort=False).size()
    if not grouped.empty:
        groups[scope].append(grouped)


def read_quality_counts() -> dict[str, pd.DataFrame]:
    all_parts: dict[str, list[pd.Series]] = defaultdict(list)
    for pub_year in range(PUB_START_YEAR, PUB_END_YEAR + 1):
        print(f"PROCESS_PUBLICATION_FILE {pub_year}", flush=True)
        proc = stream_member(pub_year)
        assert proc.stdout is not None
        reader = pd.read_csv(
            proc.stdout,
            usecols=lambda c: c in USECOLS,
            dtype=str,
            chunksize=CHUNKSIZE,
            encoding="utf-8-sig",
            on_bad_lines="skip",
            low_memory=False,
        )
        rows_seen = rows_kept = 0
        for chunk in reader:
            rows_seen += len(chunk)
            required = {"申请人", "申请人城市", "专利类型", "申请号", "申请年份"}
            if not required.issubset(chunk.columns):
                continue
            chunk = chunk[(chunk["申请人"] != "申请人") & (chunk["申请人城市"] != "申请人城市")].copy()
            chunk["city"] = normalize_city(chunk["申请人城市"])
            chunk["applicant"] = first_applicant(chunk["申请人"]).map(norm_name)
            chunk["app_no"] = clean_text(chunk["申请号"])
            chunk["year"] = pd.to_numeric(chunk["申请年份"], errors="coerce")
            chunk["ptype"] = chunk["专利类型"].astype("string").fillna("")
            chunk["cited"] = pd.to_numeric(chunk.get("被引证次数", 0), errors="coerce").fillna(0)
            chunk["family_cited"] = pd.to_numeric(chunk.get("家族被引证次数", 0), errors="coerce").fillna(0)
            chunk = chunk[
                chunk["year"].between(START_YEAR, END_YEAR, inclusive="both")
                & (chunk["city"] != "")
                & (chunk["applicant"] != "")
                & (chunk["app_no"] != "")
            ].copy()
            if chunk.empty:
                continue
            chunk["year"] = chunk["year"].astype("int16")
            inv_grant = chunk["ptype"].str.contains("发明授权", na=False)
            base = chunk.loc[inv_grant, ["year", "city", "applicant", "app_no", "cited", "family_cited"]]
            if base.empty:
                continue
            rows_kept += len(base)
            base = base.drop_duplicates(["year", "city", "applicant", "app_no"])
            append_group(all_parts, "inv_grant_appyear", base[["year", "city", "applicant", "app_no"]])
            append_group(
                all_parts,
                "inv_grant_cited_appyear",
                base.loc[base["cited"] > 0, ["year", "city", "applicant", "app_no"]],
            )
            append_group(
                all_parts,
                "inv_grant_familycited_appyear",
                base.loc[base["family_cited"] > 0, ["year", "city", "applicant", "app_no"]],
            )
        stderr = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"bsdtar failed for {pub_year}: rc={rc}, stderr={stderr[:2000]}")
        print(f"PUBLICATION_FILE_DONE {pub_year} rows_seen={rows_seen:,} inv_grant_rows={rows_kept:,}", flush=True)

    details: dict[str, pd.DataFrame] = {}
    for scope, parts in all_parts.items():
        if not parts:
            continue
        counts = pd.concat(parts).groupby(level=[0, 1, 2]).sum().astype("int64")
        detail = counts.rename("patents").reset_index()
        details[scope] = detail
        print(f"COMBINED {scope} rows={len(detail):,}", flush=True)
    return details


def turnover_for_n(detail: pd.DataFrame, prefix: str, n: int) -> pd.DataFrame:
    ranked = detail.sort_values(["city", "year", "patents", "applicant"], ascending=[True, True, False, True]).copy()
    ranked["rank"] = ranked.groupby(["city", "year"], sort=False).cumcount() + 1
    top = ranked[ranked["rank"] <= n].copy()
    city_year_sets = {
        (city, int(year)): set(g["applicant"])
        for (city, year), g in top.groupby(["city", "year"], sort=False)
    }
    rows: list[dict] = []
    for (city, year), g in top.groupby(["city", "year"], sort=False):
        year = int(year)
        prev = city_year_sets.get((city, year - 1), set())
        top_patents = float(g["patents"].sum())
        new = ~g["applicant"].isin(prev)
        turnover_patents = float(g.loc[new, "patents"].sum())
        rows.append(
            {
                "city": city,
                "year": year,
                f"{prefix}_t{n}_top_pat": top_patents,
                f"{prefix}_t{n}_new_pat": turnover_patents,
                f"{prefix}_t{n}_new_pat_sh": turnover_patents / top_patents if top_patents > 0 else np.nan,
                f"{prefix}_t{n}_new_n_sh": float(new.sum() / len(g)) if len(g) else np.nan,
            }
        )
    out = pd.DataFrame(rows)
    share_cols = [c for c in out.columns if c.endswith("_share")]
    out.loc[out["year"].eq(START_YEAR), share_cols] = np.nan
    return out


def main() -> None:
    details = read_quality_counts()
    metrics: list[pd.DataFrame] = []
    for scope, prefix in SCOPES.items():
        detail = details.get(scope)
        if detail is None or detail.empty:
            continue
        m10 = turnover_for_n(detail, prefix, 10)
        m20 = turnover_for_n(detail, prefix, 20)
        metrics.append(m10.merge(m20, on=["city", "year"], how="outer"))
    if metrics:
        qual = metrics[0]
        for m in metrics[1:]:
            qual = qual.merge(m, on=["city", "year"], how="outer")
    else:
        qual = pd.DataFrame(columns=["city", "year"])

    base = pd.read_csv(BASE, low_memory=False, encoding="utf-8-sig")
    base = base[
        (base["scope"].eq("inv_app_appyear"))
        & (base["year"].between(START_YEAR, END_YEAR, inclusive="both"))
        & (base["merge_idc_split"].eq("both"))
    ].drop_duplicates(["city", "year"])
    out = base.merge(qual, on=["city", "year"], how="left")
    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    out.to_stata(OUT_DTA, write_index=False, version=118)
    print(f"wrote {OUT_CSV} rows={len(out):,} cols={len(out.columns):,}")


if __name__ == "__main__":
    main()
