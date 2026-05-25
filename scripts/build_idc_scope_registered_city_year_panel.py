#!/usr/bin/env python3
"""Build IDC city-year proxies separating license scope and registered address."""

from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/23选题探索/T10")
DETAIL = ROOT / "data/external_proxy/idc_proxy_51miit_license_details.csv"
CITY_BASE = ROOT / "data/processed/idc_proxy_city_year_2000_2024.csv"
PROCESSED = ROOT / "data/processed"
REPORTS = ROOT / "results/reports"


def clean_text(s: object) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(s or ""))).strip()


def norm_city_name(s: object) -> str:
    t = clean_text(s)
    t = re.sub(r"^中国", "", t)
    t = re.sub(r"市$", "", t)
    return t


def extract_idc_scope(business_text: object) -> str:
    text = clean_text(business_text)
    marker = re.search(r"(?:互联网|因特网)数据中心业务\s*[:：]\s*", text)
    if not marker:
        return ""
    rest = text[marker.end():]
    next_markers = [
        "互联网接入服务业务",
        "因特网接入服务业务",
        "内容分发网络业务",
        "国内互联网虚拟专用网业务",
        "国内呼叫中心业务",
        "信息服务业务",
        "信息服务业务（不含互联网信息服务）",
        "信息服务业务（仅限互联网信息服务）",
        "在线数据处理与交易处理业务",
        "国内多方通信服务业务",
        "存储转发类业务",
        "互联网域名解析服务业务",
    ]
    cut = len(rest)
    for m in next_markers:
        mm = re.search(re.escape(m) + r"\s*[:：]", rest)
        if mm:
            cut = min(cut, mm.start())
    return clean_text(rest[:cut]).strip(" ;；,，、。")


def split_scope_terms(scope: str) -> list[str]:
    return [clean_text(x).strip(" ;；,，、。") for x in re.split(r"[;；,，、/]+", scope) if clean_text(x)]


def find_city_in_text(text: object, city_terms: list[str]) -> str:
    t = clean_text(text)
    for city in city_terms:
        if city and city in t:
            return city
    return ""


def add_license_row(rows: list[dict[str, object]], r: pd.Series, city: str, source: str) -> None:
    try:
        year = int(float(r["license_year"]))
    except Exception:
        return
    if year < 2000 or year > 2024:
        return
    rows.append(
        {
            "license_no": r.get("license_no", ""),
            "license_year": year,
            "company": r.get("company", ""),
            "city": city,
            "source": source,
            "idc_scope_raw": r.get("idc_scope_clean", ""),
            "registered_address": r.get("registered_address", ""),
        }
    )


def make_city_year(city_rows: pd.DataFrame, city_base: pd.DataFrame, prefix: str) -> pd.DataFrame:
    years = pd.DataFrame({"year": list(range(2000, 2025))})
    base = city_base[["province", "city"]].drop_duplicates("city").merge(years, how="cross")
    if city_rows.empty:
        new_counts = pd.DataFrame(columns=["city", "year", f"{prefix}_new"])
    else:
        new_counts = (
            city_rows.groupby(["city", "license_year"], as_index=False)
            .size()
            .rename(columns={"license_year": "year", "size": f"{prefix}_new"})
        )
    panel = base.merge(new_counts, on=["city", "year"], how="left")
    panel[f"{prefix}_new"] = panel[f"{prefix}_new"].fillna(0).astype(int)
    panel = panel.sort_values(["city", "year"])
    panel[f"{prefix}_stock"] = panel.groupby("city")[f"{prefix}_new"].cumsum()
    panel[f"ln1p_{prefix}_new"] = panel[f"{prefix}_new"].map(lambda x: math.log1p(float(x)))
    panel[f"ln1p_{prefix}_stock"] = panel[f"{prefix}_stock"].map(lambda x: math.log1p(float(x)))
    panel[f"ln1p_{prefix}_stock_l1"] = panel.groupby("city")[f"ln1p_{prefix}_stock"].shift(1).fillna(0)
    return panel


def main() -> None:
    details = pd.read_csv(DETAIL, low_memory=False, encoding="utf-8-sig")
    city_base = pd.read_csv(CITY_BASE, low_memory=False, encoding="utf-8-sig")
    city_base = city_base.rename(columns={"省份": "province", "城市": "city", "年份": "year"})
    city_base["province"] = city_base["province"].map(norm_city_name)
    city_base["city"] = city_base["city"].map(norm_city_name)
    city_base = city_base[["province", "city"]].drop_duplicates()

    city_terms = sorted(city_base["city"].dropna().astype(str).unique(), key=len, reverse=True)
    province_terms = set(city_base["province"].dropna().astype(str).unique())

    details["idc_scope_clean"] = details["business_text"].map(extract_idc_scope)
    details["registered_city"] = (
        details["registered_address"].fillna("").astype(str) + " " + details["company"].fillna("").astype(str)
    ).map(lambda x: find_city_in_text(x, city_terms))

    scope_rows: list[dict[str, object]] = []
    registered_rows: list[dict[str, object]] = []
    combined_rows: list[dict[str, object]] = []
    province_scope_count = 0

    for _, r in details.iterrows():
        scope = clean_text(r["idc_scope_clean"])
        scope_cities: set[str] = set()
        for term in split_scope_terms(scope):
            term_norm = norm_city_name(term)
            if term_norm in ("全国", "全网", "全国范围"):
                continue
            if term_norm in city_terms:
                scope_cities.add(term_norm)
            elif term_norm in province_terms:
                province_scope_count += 1
            else:
                hit = find_city_in_text(term_norm, city_terms)
                if hit:
                    scope_cities.add(hit)
        for c in sorted(scope_cities):
            add_license_row(scope_rows, r, c, "scope_city")
            add_license_row(combined_rows, r, c, "scope_city")

        reg_city = clean_text(r["registered_city"])
        if reg_city:
            add_license_row(registered_rows, r, reg_city, "registered_city")
            if not scope_cities:
                add_license_row(combined_rows, r, reg_city, "registered_fallback")

    scope_df = pd.DataFrame(scope_rows).drop_duplicates(["license_no", "license_year", "city"]) if scope_rows else pd.DataFrame()
    registered_df = pd.DataFrame(registered_rows).drop_duplicates(["license_no", "license_year", "city"]) if registered_rows else pd.DataFrame()
    combined_df = pd.DataFrame(combined_rows).drop_duplicates(["license_no", "license_year", "city"]) if combined_rows else pd.DataFrame()

    outdir = PROCESSED / "idc_split_proxy"
    outdir.mkdir(parents=True, exist_ok=True)
    scope_df.to_csv(outdir / "idc_scope_city_license_rows.csv", index=False, encoding="utf-8-sig")
    registered_df.to_csv(outdir / "idc_registered_city_license_rows.csv", index=False, encoding="utf-8-sig")
    combined_df.to_csv(outdir / "idc_combined_city_license_rows.csv", index=False, encoding="utf-8-sig")

    panels = [
        make_city_year(scope_df, city_base, "idc_scope"),
        make_city_year(registered_df, city_base, "idc_registered"),
        make_city_year(combined_df, city_base, "idc_combined"),
    ]
    panel = panels[0]
    for p in panels[1:]:
        panel = panel.merge(p.drop(columns=["province"]), on=["city", "year"], how="left")
    panel = panel.sort_values(["city", "year"])
    panel.to_csv(PROCESSED / "idc_split_proxy_city_year_2000_2024.csv", index=False, encoding="utf-8-sig")
    panel.to_stata(PROCESSED / "idc_split_proxy_city_year_2000_2024.dta", write_index=False, version=118)

    report = {
        "detail_rows": int(len(details)),
        "scope_nonempty_old": int(details["idc_scope"].fillna("").astype(str).str.len().gt(0).sum()),
        "scope_nonempty_clean": int(details["idc_scope_clean"].fillna("").astype(str).str.len().gt(0).sum()),
        "registered_city_nonempty": int(details["registered_city"].fillna("").astype(str).str.len().gt(0).sum()),
        "scope_license_rows": int(len(scope_df)),
        "registered_license_rows": int(len(registered_df)),
        "combined_license_rows": int(len(combined_df)),
        "province_scope_terms_seen": int(province_scope_count),
        "scope_cities": int(scope_df["city"].nunique()) if not scope_df.empty else 0,
        "registered_cities": int(registered_df["city"].nunique()) if not registered_df.empty else 0,
        "combined_cities": int(combined_df["city"].nunique()) if not combined_df.empty else 0,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "idc_split_proxy_city_year_report_20260524.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
