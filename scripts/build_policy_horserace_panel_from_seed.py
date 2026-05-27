#!/usr/bin/env python3
"""Build a preliminary city-year policy horse-race panel from seed policy lists.

The seed list is intentionally auditable and source-backed. This script maps
city, district, province, and region-level entries onto the T10 application-year
city panel and expands them into post-treatment city-year dummies.

This is a first-pass "broad coding" panel. It should be used for diagnostics,
not as the final submission-grade policy database.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/23实证选题探索/T10")
EXTERNAL = ROOT / "data/external_proxy"
PROCESSED = ROOT / "data/processed"
MAIN = PROCESSED / "idc_scope_formal_application_year_panel_2008_2023.csv"
SEED = EXTERNAL / "policy_seed_lists_20260527.csv"
OUT = EXTERNAL / "city_policy_horserace_panel_2008_2023.csv"
MATCH_REPORT = EXTERNAL / "policy_seed_city_match_report_20260527.csv"

START_YEAR = 2008
END_YEAR = 2023

POLICY_COLS = [
    "broadband_china_pilot",
    "smart_city_pilot",
    "bigdata_comprehensive_pilot",
    "innovative_city_pilot",
    "national_hightech_zone",
    "ip_demo_city",
    "information_consumption_pilot",
    "ecommerce_demo_city",
]

# County/district-level policies are mapped to the prefecture-level T10 city
# where the local meaning is unambiguous.
CITY_ALIASES = {
    "昆山": "苏州",
    "常熟": "苏州",
    "永城": "商丘",
    "阿拉尔": "自治区直辖县级行政区划",
    "石河子": "自治区直辖县级行政区划",
    "海淀": "北京",
    "海淀区": "北京",
    "滨海新区": "天津",
    "杨浦": "上海",
    "杨浦区": "上海",
    "沙坪坝": "重庆",
    "沙坪坝区": "重庆",
    "江津": "重庆",
    "荣昌": "重庆",
    "九龙坡": "重庆",
    "北碚": "重庆",
}

REGION_MAP = {
    "京津冀": {
        "province": ["北京", "天津", "河北省"],
        "city": [],
    },
    "珠江三角洲": {
        "province": [],
        "city": ["广州", "深圳", "珠海", "佛山", "惠州", "东莞", "中山", "江门", "肇庆"],
    },
}


def norm_city(value: object) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip()
    for suffix in ["市", "地区"]:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    return CITY_ALIASES.get(s, s)


def main() -> None:
    base = pd.read_csv(MAIN, encoding="utf-8-sig", low_memory=False)
    panel = base[["city", "province", "year"]].drop_duplicates().copy()
    panel = panel[panel["year"].between(START_YEAR, END_YEAR, inclusive="both")]
    panel = panel.sort_values(["city", "year"]).reset_index(drop=True)
    for col in POLICY_COLS:
        panel[col] = 0
    panel["policy_source_note"] = ""

    seed = pd.read_csv(SEED, encoding="utf-8-sig", low_memory=False)
    city_set = set(panel["city"].dropna().astype(str))
    report_rows: list[dict] = []

    def mark(policy: str, batch_year: int, cities: set[str], note: str) -> int:
        if not cities:
            return 0
        mask = panel["city"].isin(cities) & (panel["year"] >= batch_year)
        n = int(mask.sum())
        if n:
            panel.loc[mask, policy] = 1
            add_note = f"{policy}:{batch_year};"
            empty = panel.loc[mask, "policy_source_note"].eq("")
            panel.loc[mask & empty, "policy_source_note"] = add_note
            panel.loc[mask & ~empty, "policy_source_note"] = panel.loc[mask & ~empty, "policy_source_note"] + add_note
        return n

    for _, row in seed.iterrows():
        policy = row["policy_name"]
        batch = int(row["batch_year"])
        level = str(row.get("mapping_level", "city"))
        raw = str(row.get("raw_region_name", ""))
        parent = norm_city(row.get("parent_city_for_t10", ""))
        province_hint = str(row.get("province_hint", "")).strip()

        matched: set[str] = set()
        coding = "unmatched"
        if level in {"city", "city_group_expanded", "district_mapped_to_municipality"}:
            candidate = CITY_ALIASES.get(parent, parent)
            if candidate in city_set:
                matched = {candidate}
                coding = "city"
        elif level == "province":
            province = province_hint or raw
            matched = set(panel.loc[panel["province"].eq(province), "city"].dropna().astype(str))
            coding = "province_broad"
        elif level == "region":
            spec = REGION_MAP.get(raw, {})
            matched = set(spec.get("city", [])) & city_set
            for prov in spec.get("province", []):
                matched |= set(panel.loc[panel["province"].eq(prov), "city"].dropna().astype(str))
            coding = "region_broad"

        rows_marked = mark(policy, batch, matched, raw)
        report_rows.append(
            {
                "policy_name": policy,
                "batch_year": batch,
                "raw_region_name": raw,
                "mapping_level": level,
                "coding": coding,
                "matched_city_count": len(matched),
                "matched_cities": "、".join(sorted(matched)),
                "rows_marked": rows_marked,
                "source_name": row.get("source_name", ""),
                "source_url": row.get("source_url", ""),
                "note": row.get("note", ""),
            }
        )

    # Columns not yet seeded remain as explicit zeros with a note in the report.
    for col in ["smart_city_pilot", "national_hightech_zone", "information_consumption_pilot", "ecommerce_demo_city"]:
        report_rows.append(
            {
                "policy_name": col,
                "batch_year": "",
                "raw_region_name": "",
                "mapping_level": "not_seeded",
                "coding": "all_zero_pending_source",
                "matched_city_count": 0,
                "matched_cities": "",
                "rows_marked": int(panel[col].sum()),
                "source_name": "",
                "source_url": "",
                "note": "Pending complete source list; kept as zero placeholder and excluded by Stata if no variation.",
            }
        )

    panel = panel[["city", "year", "province", *POLICY_COLS, "policy_source_note"]]
    panel.to_csv(OUT, index=False, encoding="utf-8-sig")
    pd.DataFrame(report_rows).to_csv(MATCH_REPORT, index=False, encoding="utf-8-sig")

    print(f"wrote {OUT} rows={len(panel):,}")
    print(panel[POLICY_COLS].sum().to_string())
    print(f"wrote {MATCH_REPORT} rows={len(report_rows):,}")


if __name__ == "__main__":
    main()
