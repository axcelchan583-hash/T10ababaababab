clear all
set more off

local out "/Users/mac/computerscience/23选题探索/T10/outputs"
local ydata "`out'/public_innovation_resilience_rebuild_stata_2000_2024.dta"

display "=== Main effect pilot: Data infrastructure × firm innovation resilience ==="
display "Y data: `ydata'"

use "`ydata'", clear

drop if missing(股票代码) | missing(年份)
drop if missing(城市代码) | 城市代码 == .
drop if missing(城市) | 城市 == ""
drop if missing(省份) | 省份 == ""

gen byte treat_data_infra = 0

* Province/region-level National Big Data Comprehensive Pilot Zones.
replace treat_data_infra = 1 if inlist(省份, "贵州省", "河南省", "重庆市", "上海市")
replace treat_data_infra = 1 if inlist(省份, "北京市", "天津市", "河北省", "内蒙古自治区")

* Pearl River Delta pilot zone: nine PRD cities, not all Guangdong cities.
replace treat_data_infra = 1 if inlist(城市, "广州市", "深圳市", "珠海市", "佛山市", "惠州市")
replace treat_data_infra = 1 if inlist(城市, "东莞市", "中山市", "江门市", "肇庆市")

* Shenyang pilot zone.
replace treat_data_infra = 1 if 城市 == "沈阳市"

gen byte post2016 = 年份 >= 2016
gen byte Data_infra = treat_data_infra * post2016

gen byte non_st = 是否ST类 == "0"
gen str1 industry_1d = substr(行业代码, 1, 1)
gen byte non_finance = industry_1d != "J"
gen byte base_clean = non_st == 1 & non_finance == 1

label var treat_data_infra "National big-data pilot zone treated city/region"
label var post2016 "Post 2016"
label var Data_infra "Treat x Post2016"

egen tag_city = tag(城市代码)
count if tag_city == 1
display "N_CITIES_TOTAL=" r(N)
count if tag_city == 1 & treat_data_infra == 1
display "N_CITIES_TREATED=" r(N)
drop tag_city

preserve
keep 股票代码 年份 省份 城市 城市代码 行业代码 是否ST类 treat_data_infra post2016 Data_infra ///
    企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4
export delimited using "`out'/data_infra_innovation_resilience_panel_2000_2024.csv", replace
save "`out'/data_infra_innovation_resilience_panel_2000_2024.dta", replace
restore

tempname handle
postfile `handle' str24 sample str40 outcome str12 transform double coef se t p n firms clusters r2 ///
    using "`out'/main_effect_data_infra_results_20260523.dta", replace

foreach y in 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4 {
    capture drop `y'_w
    gen `y'_w = `y'
    quietly summarize `y' if base_clean == 1 & 年份 >= 2008 & 年份 <= 2024, detail
    local p1 = r(p1)
    local p99 = r(p99)
    replace `y'_w = `p1' if `y'_w < `p1' & base_clean == 1 & 年份 >= 2008 & 年份 <= 2024 & !missing(`y'_w)
    replace `y'_w = `p99' if `y'_w > `p99' & base_clean == 1 & 年份 >= 2008 & 年份 <= 2024 & !missing(`y'_w)
}

local ys 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4

foreach y of local ys {
    quietly areg `y' Data_infra i.年份 if base_clean == 1 & 年份 >= 2008 & 年份 <= 2024, absorb(股票代码) vce(cluster 城市代码)
    local coef = _b[Data_infra]
    local se = _se[Data_infra]
    local t = `coef' / `se'
    local p = 2 * ttail(e(df_r), abs(`t'))
    tempvar tagfirm
    egen `tagfirm' = tag(股票代码) if e(sample)
    quietly count if `tagfirm' == 1
    local firms = r(N)
    drop `tagfirm'
    post `handle' ("clean_2008_2024") ("`y'") ("raw") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

    quietly areg `y'_w Data_infra i.年份 if base_clean == 1 & 年份 >= 2008 & 年份 <= 2024, absorb(股票代码) vce(cluster 城市代码)
    local coef = _b[Data_infra]
    local se = _se[Data_infra]
    local t = `coef' / `se'
    local p = 2 * ttail(e(df_r), abs(`t'))
    tempvar tagfirm
    egen `tagfirm' = tag(股票代码) if e(sample)
    quietly count if `tagfirm' == 1
    local firms = r(N)
    drop `tagfirm'
    post `handle' ("clean_2008_2024") ("`y'") ("winsor_p1p99") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

    quietly areg `y' Data_infra i.年份 if base_clean == 1 & 年份 >= 2000 & 年份 <= 2024, absorb(股票代码) vce(cluster 城市代码)
    local coef = _b[Data_infra]
    local se = _se[Data_infra]
    local t = `coef' / `se'
    local p = 2 * ttail(e(df_r), abs(`t'))
    tempvar tagfirm
    egen `tagfirm' = tag(股票代码) if e(sample)
    quietly count if `tagfirm' == 1
    local firms = r(N)
    drop `tagfirm'
    post `handle' ("clean_2000_2024") ("`y'") ("raw") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

    quietly areg `y' Data_infra i.年份 if 年份 >= 2008 & 年份 <= 2024, absorb(股票代码) vce(cluster 城市代码)
    local coef = _b[Data_infra]
    local se = _se[Data_infra]
    local t = `coef' / `se'
    local p = 2 * ttail(e(df_r), abs(`t'))
    tempvar tagfirm
    egen `tagfirm' = tag(股票代码) if e(sample)
    quietly count if `tagfirm' == 1
    local firms = r(N)
    drop `tagfirm'
    post `handle' ("all_2008_2024") ("`y'") ("raw") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))
}

postclose `handle'

use "`out'/main_effect_data_infra_results_20260523.dta", clear
export delimited using "`out'/main_effect_data_infra_results_20260523.csv", replace
list, noobs abbrev(24)

display "=== Done ==="
