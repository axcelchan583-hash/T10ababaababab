#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
REPORTS = ROOT / "results" / "reports"
RAR_PATH = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/"
    "上市公司其他/分年份保存数据.rar"
)


USECOLS = ["专利类型", "申请人", "申请人类型", "申请人城市", "申请号", "公开公告年份", "授权公告年份"]


def clean_text(s: pd.Series) -> pd.Series:
    return (
        s.astype("string")
        .str.strip()
        .str.replace("\u3000", "", regex=False)
        .str.replace(r"\s+", "", regex=True)
    )


def first_applicant(s: pd.Series) -> pd.Series:
    return (
        clean_text(s)
        .str.split(r"[;；]", regex=True)
        .str[0]
        .fillna("")
    )


def first_city(s: pd.Series) -> pd.Series:
    return (
        clean_text(s)
        .str.split(r"[;；,，/、]", regex=True)
        .str[0]
        .fillna("")
    )


def normalize_city(s: pd.Series) -> pd.Series:
    city = first_city(s)
    city = city.str.replace(r"^中国", "", regex=True)
    city = city.str.replace(r"市$", "", regex=True)
    city = city.mask(city.isin(["CN", "中国", "中华人民共和国", "不详", "未知", "无"]), "")
    return city


def stream_year(year: int):
    member = f"分年份保存数据/中国全量专利数据库{year}年.csv"
    return subprocess.Popen(
        ["bsdtar", "-xOf", str(RAR_PATH), member],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def aggregate_year(year: int, chunksize: int) -> tuple[dict[str, pd.Series], dict[str, int]]:
    proc = stream_year(year)
    assert proc.stdout is not None

    aggregators: dict[str, list[pd.Series]] = {
        "all_pub": [],
        "inv_app_pub": [],
        "inv_grant_pub": [],
    }
    stats = {
        "rows_seen": 0,
        "rows_valid": 0,
        "rows_missing_city_or_applicant": 0,
        "rows_inv_app": 0,
        "rows_inv_grant": 0,
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
        if not set(["申请人", "申请人城市", "专利类型"]).issubset(chunk.columns):
            continue

        # The CSV files contain a duplicated header row as the first data row.
        chunk = chunk[(chunk["申请人"] != "申请人") & (chunk["申请人城市"] != "申请人城市")]
        chunk["city"] = normalize_city(chunk["申请人城市"])
        chunk["applicant"] = first_applicant(chunk["申请人"])
        chunk["ptype"] = chunk["专利类型"].astype("string").fillna("")
        before_filter = len(chunk)
        chunk = chunk[(chunk["city"] != "") & (chunk["applicant"] != "")]
        stats["rows_valid"] += len(chunk)
        stats["rows_missing_city_or_applicant"] += before_filter - len(chunk)

        if chunk.empty:
            continue

        for scope, mask in [
            ("all_pub", pd.Series(True, index=chunk.index)),
            ("inv_app_pub", chunk["ptype"].str.contains("发明申请", na=False)),
            ("inv_grant_pub", chunk["ptype"].str.contains("发明授权", na=False)),
        ]:
            sub = chunk.loc[mask, ["city", "applicant"]]
            if sub.empty:
                continue
            if scope == "inv_app_pub":
                stats["rows_inv_app"] += len(sub)
            if scope == "inv_grant_pub":
                stats["rows_inv_grant"] += len(sub)
            grouped = sub.groupby(["city", "applicant"], sort=False).size()
            aggregators[scope].append(grouped)

    stderr = proc.stderr.read().decode("utf-8", "ignore") if proc.stderr else ""
    rc = proc.wait()
    if rc not in (0,):
        # bsdtar may emit broken-pipe warnings when the reader stops early, but here we read all stdout.
        raise RuntimeError(f"bsdtar failed for {year}: rc={rc}, stderr={stderr[:2000]}")

    out: dict[str, pd.Series] = {}
    for scope, parts in aggregators.items():
        if parts:
            out[scope] = pd.concat(parts).groupby(level=[0, 1]).sum().astype("int64")
        else:
            out[scope] = pd.Series(dtype="int64")
    return out, stats


def metrics_from_counts(
    year: int,
    scope: str,
    counts: pd.Series,
    seen: set[str] | None,
    write_detail_dir: Path | None = None,
) -> tuple[list[dict], set[str]]:
    rows: list[dict] = []
    if counts.empty:
        return rows, seen if seen is not None else set()

    df = counts.rename("patents").reset_index()
    df["year"] = year
    df["scope"] = scope
    if write_detail_dir is not None:
        write_detail_dir.mkdir(parents=True, exist_ok=True)
        df[["year", "scope", "city", "applicant", "patents"]].to_csv(
            write_detail_dir / f"city_applicant_counts_{scope}_{year}.csv.gz",
            index=False,
            encoding="utf-8-sig",
            compression="gzip",
        )

    new_seen = seen if seen is not None else set()
    key = df["city"] + "\t" + df["applicant"]
    df["_key"] = key
    if seen is None:
        df["_is_new"] = False
    else:
        df["_is_new"] = ~df["_key"].isin(seen)

    for city, g in df.groupby("city", sort=False):
        vals = g["patents"].to_numpy(dtype=float)
        total = float(vals.sum())
        if total <= 0:
            continue
        vals_sorted = np.sort(vals)[::-1]
        shares = vals_sorted / total
        hhi = float(np.sum(shares * shares))
        new_g = g[g["_is_new"]]
        rows.append(
            {
                "city": city,
                "year": year,
                "scope": scope,
                "total_patents": int(total),
                "active_applicants": int(len(vals)),
                "hhi": hhi,
                "top1_share": float(shares[:1].sum()) if len(shares) else np.nan,
                "top5_share": float(shares[:5].sum()) if len(shares) else np.nan,
                "top10_share": float(shares[:10].sum()) if len(shares) else np.nan,
                "effective_applicants": float(1.0 / hhi) if hhi > 0 else np.nan,
                "new_applicants": int(new_g["applicant"].nunique()),
                "new_patents": int(new_g["patents"].sum()),
                "new_applicant_share": float(new_g["patents"].sum() / total) if total > 0 else np.nan,
            }
        )

    if seen is not None:
        new_seen.update(df["_key"].tolist())
    return rows, new_seen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2008)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--warmup-start-year", type=int, default=2000)
    parser.add_argument("--chunksize", type=int, default=200_000)
    parser.add_argument("--write-detail", action="store_true")
    args = parser.parse_args()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    detail_dir = PROCESSED / "city_applicant_counts_by_year" if args.write_detail else None

    seen_by_scope: dict[str, set[str]] = {
        "all_pub": set(),
        "inv_app_pub": set(),
        "inv_grant_pub": set(),
    }
    all_metrics: list[dict] = []
    year_reports: list[dict] = []

    for year in range(args.warmup_start_year, args.end_year + 1):
        print(f"PROCESS_YEAR {year}", flush=True)
        counts_by_scope, stats = aggregate_year(year, chunksize=args.chunksize)
        for scope, counts in counts_by_scope.items():
            rows, seen_by_scope[scope] = metrics_from_counts(
                year=year,
                scope=scope,
                counts=counts,
                seen=seen_by_scope[scope],
                write_detail_dir=detail_dir if year >= args.start_year else None,
            )
            if year >= args.start_year:
                all_metrics.extend(rows)
            stats[f"{scope}_city_applicant_pairs"] = int(len(counts))
            stats[f"{scope}_seen_pairs"] = int(len(seen_by_scope[scope]))
        stats["year"] = year
        year_reports.append(stats)
        print(json.dumps(stats, ensure_ascii=False), flush=True)

    metrics = pd.DataFrame(all_metrics)
    out_csv = PROCESSED / f"patent_applicant_concentration_city_year_{args.start_year}_{args.end_year}.csv"
    out_dta = PROCESSED / f"patent_applicant_concentration_city_year_{args.start_year}_{args.end_year}.dta"
    report_csv = REPORTS / f"patent_applicant_concentration_build_report_{args.start_year}_{args.end_year}.csv"
    report_json = REPORTS / f"patent_applicant_concentration_build_report_{args.start_year}_{args.end_year}.json"

    metrics.to_csv(out_csv, index=False, encoding="utf-8-sig")
    metrics.to_stata(out_dta, write_index=False, version=118)
    pd.DataFrame(year_reports).to_csv(report_csv, index=False, encoding="utf-8-sig")
    summary = {
        "start_year": args.start_year,
        "end_year": args.end_year,
        "warmup_start_year": args.warmup_start_year,
        "rows": int(len(metrics)),
        "cities": int(metrics["city"].nunique()) if not metrics.empty else 0,
        "scopes": sorted(metrics["scope"].unique().tolist()) if not metrics.empty else [],
        "output_csv": str(out_csv),
        "output_dta": str(out_dta),
        "year_report_csv": str(report_csv),
    }
    report_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
