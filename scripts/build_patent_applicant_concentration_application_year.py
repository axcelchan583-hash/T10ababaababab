#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "results" / "reports"
RAR_PATH = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/"
    "上市公司其他/分年份保存数据.rar"
)

USECOLS = [
    "专利类型",
    "申请人",
    "申请人类型",
    "申请人城市",
    "申请号",
    "申请日",
    "申请年份",
    "授权公告年份",
]


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


def stream_member(pub_year: int) -> subprocess.Popen:
    member = f"分年份保存数据/中国全量专利数据库{pub_year}年.csv"
    return subprocess.Popen(
        ["bsdtar", "-xOf", str(RAR_PATH), member],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def append_group(
    groups: dict[str, list[pd.Series]],
    scope: str,
    chunk: pd.DataFrame,
    year_col: str,
    year_min: int,
    year_max: int,
) -> int:
    sub = chunk[["city", "applicant", "app_no", "ptype", year_col]].copy()
    sub["year"] = pd.to_numeric(sub[year_col], errors="coerce")
    sub = sub[sub["year"].between(year_min, year_max, inclusive="both")]
    if sub.empty:
        return 0
    sub["year"] = sub["year"].astype("int16")
    sub = sub.drop_duplicates(["year", "city", "applicant", "app_no"])
    grouped = sub.groupby(["year", "city", "applicant"], sort=False).size()
    if not grouped.empty:
        groups[scope].append(grouped)
    return int(len(sub))


def read_publication_file(
    pub_year: int,
    chunksize: int,
    year_min: int,
    year_max: int,
    scopes: set[str],
) -> tuple[dict[str, list[pd.Series]], dict[str, int]]:
    proc = stream_member(pub_year)
    assert proc.stdout is not None

    groups: dict[str, list[pd.Series]] = defaultdict(list)
    stats = {
        "pub_file_year": pub_year,
        "rows_seen": 0,
        "rows_clean": 0,
        "rows_missing_city_or_applicant": 0,
        "rows_inv_app_appyear": 0,
        "rows_inv_grant_appyear": 0,
        "rows_inv_grant_grantyear": 0,
    }

    reader = pd.read_csv(
        proc.stdout,
        usecols=lambda c: c in USECOLS,
        dtype=str,
        chunksize=chunksize,
        encoding="utf-8-sig",
        on_bad_lines="skip",
        low_memory=False,
    )

    for chunk in reader:
        stats["rows_seen"] += len(chunk)
        if not {"申请人", "申请人城市", "专利类型", "申请号"}.issubset(chunk.columns):
            continue

        chunk = chunk[(chunk["申请人"] != "申请人") & (chunk["申请人城市"] != "申请人城市")]
        chunk["city"] = normalize_city(chunk["申请人城市"])
        chunk["applicant"] = first_applicant(chunk["申请人"])
        chunk["app_no"] = clean_text(chunk["申请号"])
        chunk["ptype"] = chunk["专利类型"].astype("string").fillna("")
        before = len(chunk)
        chunk = chunk[(chunk["city"] != "") & (chunk["applicant"] != "") & (chunk["app_no"] != "")]
        stats["rows_clean"] += len(chunk)
        stats["rows_missing_city_or_applicant"] += before - len(chunk)
        if chunk.empty:
            continue

        inv_app_mask = chunk["ptype"].str.contains("发明申请", na=False)
        inv_grant_mask = chunk["ptype"].str.contains("发明授权", na=False)

        if "inv_app_appyear" in scopes:
            stats["rows_inv_app_appyear"] += append_group(
                groups,
                "inv_app_appyear",
                chunk.loc[inv_app_mask],
                "申请年份",
                year_min,
                year_max,
            )
        if "inv_grant_appyear" in scopes:
            stats["rows_inv_grant_appyear"] += append_group(
                groups,
                "inv_grant_appyear",
                chunk.loc[inv_grant_mask],
                "申请年份",
                year_min,
                year_max,
            )
        if "inv_grant_grantyear" in scopes:
            stats["rows_inv_grant_grantyear"] += append_group(
                groups,
                "inv_grant_grantyear",
                chunk.loc[inv_grant_mask],
                "授权公告年份",
                year_min,
                year_max,
            )

    stderr = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"bsdtar failed for {pub_year}: rc={rc}, stderr={stderr[:2000]}")
    return groups, stats


def combine_counts(parts: list[pd.Series]) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame(columns=["year", "city", "applicant", "patents"])
    counts = pd.concat(parts).groupby(level=[0, 1, 2]).sum().astype("int64")
    return counts.rename("patents").reset_index()


def top_set_for_counts(g: pd.DataFrame, n: int) -> set[str]:
    if g.empty:
        return set()
    ranked = (
        g.groupby("applicant", as_index=False)["patents"]
        .sum()
        .sort_values(["patents", "applicant"], ascending=[False, True])
        .head(n)
    )
    return set(ranked["applicant"].tolist())


def metrics_from_detail(
    detail: pd.DataFrame,
    start_year: int,
    end_year: int,
    baseline_start: int,
    baseline_end: int,
    rolling_window: int,
    top_n: int,
) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame()

    detail = detail.copy()
    detail["key"] = detail["city"] + "\t" + detail["applicant"]
    first_year = detail.groupby("key")["year"].min().to_dict()
    baseline_top: dict[str, set[str]] = {}
    base = detail[detail["year"].between(baseline_start, baseline_end, inclusive="both")]
    for city, g in base.groupby("city", sort=False):
        baseline_top[city] = top_set_for_counts(g, top_n)

    rows: list[dict] = []
    years = list(range(int(detail["year"].min()), end_year + 1))

    for city, city_df in detail.groupby("city", sort=False):
        by_year = {
            int(y): g[["applicant", "patents", "key"]].copy()
            for y, g in city_df.groupby("year", sort=False)
        }
        hist: deque[pd.DataFrame] = deque(maxlen=rolling_window)
        rolling_top: dict[int, set[str]] = {}
        for year in years:
            if hist:
                rolling_top[year] = top_set_for_counts(pd.concat(list(hist), ignore_index=True), top_n)
            else:
                rolling_top[year] = set()
            if year in by_year:
                hist.append(by_year[year])

        base_top = baseline_top.get(city, set())
        for year in range(start_year, end_year + 1):
            g = by_year.get(year)
            if g is None or g.empty:
                continue
            vals = g["patents"].to_numpy(dtype=float)
            total = float(vals.sum())
            if total <= 0:
                continue
            vals_sorted = np.sort(vals)[::-1]
            shares = vals_sorted / total
            hhi = float(np.sum(shares * shares))
            is_new = g["key"].map(first_year).eq(year)
            new_patents = float(g.loc[is_new, "patents"].sum())
            roll_top_set = rolling_top.get(year, set())
            base_top_set = base_top
            roll_top_mask = g["applicant"].isin(roll_top_set)
            base_top_mask = g["applicant"].isin(base_top_set)
            roll_top_patents = float(g.loc[roll_top_mask, "patents"].sum())
            base_top_patents = float(g.loc[base_top_mask, "patents"].sum())
            roll_middle_patents = float(g.loc[(~is_new) & (~roll_top_mask), "patents"].sum())
            base_middle_patents = float(g.loc[(~is_new) & (~base_top_mask), "patents"].sum())
            rows.append(
                {
                    "city": city,
                    "year": year,
                    "total_patents": int(total),
                    "active_applicants": int(len(g)),
                    "hhi": hhi,
                    "top1_share": float(shares[:1].sum()),
                    "top5_share": float(shares[:5].sum()),
                    "top10_share": float(shares[:10].sum()),
                    "effective_applicants": float(1.0 / hhi) if hhi > 0 else np.nan,
                    "new_applicants": int(is_new.sum()),
                    "new_patents": int(new_patents),
                    "new_applicant_share": float(new_patents / total),
                    "roll_top_patents": int(roll_top_patents),
                    "roll_top_share": float(roll_top_patents / total),
                    "roll_mid_inc_patents": int(roll_middle_patents),
                    "roll_mid_inc_share": float(roll_middle_patents / total),
                    "base_top_patents": int(base_top_patents),
                    "base_top_share": float(base_top_patents / total),
                    "base_mid_inc_patents": int(base_middle_patents),
                    "base_mid_inc_share": float(base_middle_patents / total),
                    "roll_top_n": top_n,
                    "baseline_top_n": top_n,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pub-start-year", type=int, default=2000)
    parser.add_argument("--pub-end-year", type=int, default=2025)
    parser.add_argument("--warmup-start-year", type=int, default=2000)
    parser.add_argument("--start-year", type=int, default=2008)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--baseline-start-year", type=int, default=2008)
    parser.add_argument("--baseline-end-year", type=int, default=2010)
    parser.add_argument("--rolling-window", type=int, default=3)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--chunksize", type=int, default=200_000)
    parser.add_argument(
        "--scopes",
        default="inv_app_appyear,inv_grant_grantyear",
        help="Comma-separated scopes: inv_app_appyear, inv_grant_appyear, inv_grant_grantyear",
    )
    parser.add_argument("--write-detail", action="store_true")
    args = parser.parse_args()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    scopes = {x.strip() for x in args.scopes.split(",") if x.strip()}
    all_parts: dict[str, list[pd.Series]] = defaultdict(list)
    reports: list[dict] = []

    for pub_year in range(args.pub_start_year, args.pub_end_year + 1):
        print(f"PROCESS_PUBLICATION_FILE {pub_year}", flush=True)
        groups, stats = read_publication_file(
            pub_year=pub_year,
            chunksize=args.chunksize,
            year_min=args.warmup_start_year,
            year_max=args.end_year,
            scopes=scopes,
        )
        for scope, parts in groups.items():
            all_parts[scope].extend(parts)
            stats[f"{scope}_parts"] = len(parts)
        reports.append(stats)
        print(json.dumps(stats, ensure_ascii=False), flush=True)

    all_metrics: list[pd.DataFrame] = []
    detail_dir = PROCESSED / "city_applicant_counts_application_year"
    for scope in sorted(scopes):
        print(f"COMBINE_SCOPE {scope}", flush=True)
        detail = combine_counts(all_parts.get(scope, []))
        if detail.empty:
            continue
        detail["scope"] = scope
        if args.write_detail:
            detail_dir.mkdir(parents=True, exist_ok=True)
            detail.to_csv(
                detail_dir / f"city_applicant_counts_{scope}_{args.warmup_start_year}_{args.end_year}.csv.gz",
                index=False,
                encoding="utf-8-sig",
                compression="gzip",
            )
        metrics = metrics_from_detail(
            detail[["year", "city", "applicant", "patents"]],
            start_year=args.start_year,
            end_year=args.end_year,
            baseline_start=args.baseline_start_year,
            baseline_end=args.baseline_end_year,
            rolling_window=args.rolling_window,
            top_n=args.top_n,
        )
        if not metrics.empty:
            metrics.insert(2, "scope", scope)
            all_metrics.append(metrics)
        reports.append(
            {
                "scope": scope,
                "detail_rows": int(len(detail)),
                "detail_cities": int(detail["city"].nunique()),
                "detail_year_min": int(detail["year"].min()),
                "detail_year_max": int(detail["year"].max()),
            }
        )

    out = pd.concat(all_metrics, ignore_index=True) if all_metrics else pd.DataFrame()
    out_csv = PROCESSED / f"patent_applicant_concentration_application_year_{args.start_year}_{args.end_year}.csv"
    out_dta = PROCESSED / f"patent_applicant_concentration_application_year_{args.start_year}_{args.end_year}.dta"
    report_csv = REPORTS / f"patent_applicant_concentration_application_year_build_report_{args.start_year}_{args.end_year}.csv"
    report_json = REPORTS / f"patent_applicant_concentration_application_year_build_report_{args.start_year}_{args.end_year}.json"

    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    if not out.empty:
        out.to_stata(out_dta, write_index=False, version=118)
    pd.DataFrame(reports).to_csv(report_csv, index=False, encoding="utf-8-sig")
    summary = {
        "pub_start_year": args.pub_start_year,
        "pub_end_year": args.pub_end_year,
        "warmup_start_year": args.warmup_start_year,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "baseline_years": [args.baseline_start_year, args.baseline_end_year],
        "rolling_window": args.rolling_window,
        "top_n": args.top_n,
        "scopes": sorted(scopes),
        "rows": int(len(out)),
        "cities": int(out["city"].nunique()) if not out.empty else 0,
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
        "report_csv": str(report_csv),
    }
    report_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
