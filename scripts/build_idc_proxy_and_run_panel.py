from __future__ import annotations

import concurrent.futures as cf
import csv
import html
import json
import math
import re
import time
import urllib.request
from pathlib import Path

import pandas as pd
from lxml import html as lxml_html


BASE = Path("/Users/mac/computerscience")
OUT = BASE / "23选题探索/T10/outputs"
Y_DTA = OUT / "public_innovation_resilience_rebuild_stata_2000_2024.dta"
LIST_URL = "https://www.51miit.com/s/idc/all/"
DETAIL_URL = "https://www.51miit.com/details/{id}/"


def fetch(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()


def get_text_after_label(tree: lxml_html.HtmlElement, label: str) -> str:
    nodes = tree.xpath(f"//td[contains(normalize-space(.), '{label}')]/following-sibling::td[1]")
    if not nodes:
        return ""
    return clean_text(nodes[0].text_content())


def extract_idc_scope(business_text: str) -> str:
    text = clean_text(business_text)
    marker = re.search(r"(?:互联网|因特网)数据中心业务\s*[:：]\s*", text)
    if not marker:
        return ""
    rest = text[marker.end():]
    next_markers = [
        "互联网接入服务业务：",
        "互联网接入服务业务:",
        "因特网接入服务业务：",
        "因特网接入服务业务:",
        "内容分发网络业务：",
        "内容分发网络业务:",
        "国内互联网虚拟专用网业务：",
        "国内互联网虚拟专用网业务:",
        "国内呼叫中心业务：",
        "国内呼叫中心业务:",
        "信息服务业务：",
        "信息服务业务:",
        "信息服务业务（不含互联网信息服务）：",
        "信息服务业务（不含互联网信息服务）:",
        "信息服务业务（仅限互联网信息服务）：",
        "信息服务业务（仅限互联网信息服务）:",
        "在线数据处理与交易处理业务：",
        "在线数据处理与交易处理业务:",
        "国内多方通信服务业务：",
        "国内多方通信服务业务:",
        "存储转发类业务：",
        "存储转发类业务:",
        "互联网域名解析服务业务：",
        "互联网域名解析服务业务:",
    ]
    cut = len(rest)
    for m in next_markers:
        idx = rest.find(m)
        if idx >= 0:
            cut = min(cut, idx)
    return clean_text(rest[:cut])


def parse_detail(detail_id: str) -> dict[str, str]:
    url = DETAIL_URL.format(id=detail_id)
    try:
        page = fetch(url)
        tree = lxml_html.fromstring(page)
        title = clean_text(tree.xpath("string(//title)"))
        company = ""
        license_no = ""
        m = re.search(r"^(.*?)\s+([A-Z一-龥]*[AB]?\d(?:\.[AB]?\d)?[^ ]*-\d{6,})", title)
        if m:
            company = clean_text(m.group(1))
            license_no = clean_text(m.group(2))
        if not license_no:
            license_no = get_text_after_label(tree, "许可证号")
        business = get_text_after_label(tree, "业务种类")
        address = get_text_after_label(tree, "注册地址")
        scope = extract_idc_scope(business)
        year_match = re.search(r"(19\d{2}|20\d{2})", license_no)
        year = year_match.group(1) if year_match else ""
        return {
            "detail_id": detail_id,
            "url": url,
            "company": company,
            "license_no": license_no,
            "license_year": year,
            "business_text": business,
            "idc_scope": scope,
            "registered_address": address,
            "status": "ok",
        }
    except Exception as exc:
        return {
            "detail_id": detail_id,
            "url": url,
            "company": "",
            "license_no": "",
            "license_year": "",
            "business_text": "",
            "idc_scope": "",
            "registered_address": "",
            "status": f"error:{type(exc).__name__}:{exc}",
        }


def collect_detail_ids(rounds: int = 36) -> list[str]:
    ids: set[str] = set()
    for i in range(rounds):
        page = fetch(LIST_URL)
        found = set(re.findall(r"/details/([a-f0-9]{32})/", page))
        ids |= found
        print(f"list_round={i + 1} found={len(found)} unique={len(ids)}", flush=True)
        time.sleep(0.15)
    return sorted(ids)


def city_lookup_from_y() -> tuple[pd.DataFrame, list[str], dict[str, str]]:
    y = pd.read_stata(Y_DTA, convert_categoricals=False)
    cities = (
        y[["省份", "城市", "城市代码"]]
        .dropna()
        .query("省份 != '' and 城市 != ''")
        .drop_duplicates()
        .copy()
    )
    cities = cities.sort_values(["城市", "城市代码"]).drop_duplicates(["城市"], keep="first")
    city_names = sorted(cities["城市"].astype(str).unique(), key=len, reverse=True)
    province_by_city = dict(zip(cities["城市"].astype(str), cities["省份"].astype(str)))
    return cities, city_names, province_by_city


def normalize_location_term(term: str) -> str:
    t = clean_text(term)
    t = t.strip(" ;；,，、。")
    repl = {
        "北京": "北京市",
        "上海": "上海市",
        "天津": "天津市",
        "重庆": "重庆市",
        "广州": "广州市",
        "深圳": "深圳市",
    }
    return repl.get(t, t)


def infer_city_from_text(text: str, city_names: list[str]) -> str:
    text = clean_text(text)
    for city in city_names:
        if city and city in text:
            return city
    return ""


def expand_detail_to_city_rows(details: pd.DataFrame, city_names: list[str], province_by_city: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, r in details.iterrows():
        try:
            year = int(r["license_year"])
        except Exception:
            continue
        if year < 2000 or year > 2024:
            continue
        scope = clean_text(str(r["idc_scope"]))
        terms = [normalize_location_term(x) for x in re.split(r"[;；,，、/]+", scope) if clean_text(x)]
        cities: set[str] = set()
        province_terms: list[str] = []
        for term in terms:
            if term in ("全国", "全网", "全国范围"):
                continue
            if term in province_by_city:
                cities.add(term)
            elif term.endswith("市") and term in city_names:
                cities.add(term)
            elif term.endswith("市"):
                city = infer_city_from_text(term, city_names)
                if city:
                    cities.add(city)
            elif term.endswith(("省", "自治区")):
                province_terms.append(term)
        if not cities:
            fallback_city = infer_city_from_text(str(r["registered_address"]) + " " + str(r["company"]), city_names)
            if fallback_city:
                cities.add(fallback_city)
        for city in sorted(cities):
            rows.append(
                {
                    "license_no": r["license_no"],
                    "license_year": year,
                    "company": r["company"],
                    "city": city,
                    "province": province_by_city.get(city, ""),
                    "idc_scope": scope,
                    "location_source": "scope_city_or_fallback",
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.drop_duplicates(["license_no", "license_year", "city"])


def build_city_year_panel(city_rows: pd.DataFrame, y_cities: pd.DataFrame) -> pd.DataFrame:
    years = pd.DataFrame({"年份": list(range(2000, 2025))})
    base = y_cities[["省份", "城市", "城市代码"]].drop_duplicates(["城市"]).merge(years, how="cross")
    new_counts = (
        city_rows.groupby(["city", "license_year"], as_index=False)
        .size()
        .rename(columns={"city": "城市", "license_year": "年份", "size": "idc_new"})
    )
    panel = base.merge(new_counts, on=["城市", "年份"], how="left")
    panel["idc_new"] = panel["idc_new"].fillna(0).astype(int)
    panel = panel.sort_values(["城市代码", "年份"])
    panel["idc_stock"] = panel.groupby("城市代码")["idc_new"].cumsum()
    panel["ln1p_idc_new"] = panel["idc_new"].map(lambda x: math.log1p(float(x)))
    panel["ln1p_idc_stock"] = panel["idc_stock"].map(lambda x: math.log1p(float(x)))
    return panel


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_ids_path = OUT / "idc_proxy_51miit_detail_ids.txt"
    detail_path = OUT / "idc_proxy_51miit_license_details.csv"
    city_license_path = OUT / "idc_proxy_city_license_rows.csv"
    city_year_path = OUT / "idc_proxy_city_year_2000_2024.csv"
    report_path = OUT / "idc_proxy_build_report_20260523.json"

    if detail_path.exists() and raw_ids_path.exists():
        details_df = pd.read_csv(detail_path)
        ids = raw_ids_path.read_text(encoding="utf-8").splitlines()
        print(f"reuse_cached_details={len(details_df)}", flush=True)
    else:
        ids = collect_detail_ids(rounds=36)
        raw_ids_path.write_text("\n".join(ids) + "\n", encoding="utf-8")

        details: list[dict[str, str]] = []
        with cf.ThreadPoolExecutor(max_workers=12) as ex:
            futures = [ex.submit(parse_detail, detail_id) for detail_id in ids]
            for i, fut in enumerate(cf.as_completed(futures), 1):
                details.append(fut.result())
                if i % 200 == 0:
                    print(f"detail_done={i}/{len(ids)}", flush=True)

        details_df = pd.DataFrame(details)
        details_df.to_csv(detail_path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)

    y_cities, city_names, province_by_city = city_lookup_from_y()
    city_rows = expand_detail_to_city_rows(details_df, city_names, province_by_city)
    city_rows.to_csv(city_license_path, index=False, encoding="utf-8-sig")

    city_year = build_city_year_panel(city_rows, y_cities)
    city_year.to_csv(city_year_path, index=False, encoding="utf-8-sig")

    report = {
        "list_rounds": 36,
        "detail_ids": len(ids),
        "details_ok": int((details_df["status"] == "ok").sum()),
        "details_with_idc_scope": int(details_df["idc_scope"].astype(str).str.len().gt(0).sum()),
        "city_license_rows": int(len(city_rows)),
        "city_count_with_any_idc": int(city_year.groupby("城市")["idc_stock"].max().gt(0).sum()),
        "year_min": int(city_year["年份"].min()),
        "year_max": int(city_year["年份"].max()),
        "annual_new_counts": city_year.groupby("年份")["idc_new"].sum().astype(int).to_dict(),
        "outputs": {
            "detail_ids": str(raw_ids_path),
            "details": str(detail_path),
            "city_license_rows": str(city_license_path),
            "city_year": str(city_year_path),
        },
        "caveat": "This is a quick 51miit mirror-based proxy, not the paper authors' hand-cleaned full MIIT license data.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
