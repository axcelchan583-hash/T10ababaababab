clear all
set more off

local out "/Users/mac/computerscience/23选题探索/T10/outputs"
local ydata "`out'/public_innovation_resilience_rebuild_stata_2000_2024.dta"
local idccsv "`out'/idc_proxy_city_year_2000_2024.csv"

display "=== Main effect pilot: IDC proxy × firm innovation resilience ==="

import delimited using "`idccsv'", clear varnames(1) encoding("utf-8")
destring 城市代码 年份 idc_new idc_stock ln1p_idc_new ln1p_idc_stock, replace force
sort 城市代码 年份
by 城市代码: gen ln1p_idc_stock_l1 = ln1p_idc_stock[_n-1] if 年份 == 年份[_n-1] + 1
by 城市代码: gen ln1p_idc_new_l1 = ln1p_idc_new[_n-1] if 年份 == 年份[_n-1] + 1
save "`out'/idc_proxy_city_year_2000_2024.dta", replace

use "`ydata'", clear
drop if missing(股票代码) | missing(年份)
drop if missing(城市代码) | 城市代码 == .
drop if missing(城市) | 城市 == ""
drop if missing(省份) | 省份 == ""

merge m:1 城市 年份 using "`out'/idc_proxy_city_year_2000_2024.dta", keep(master match) nogen

foreach x in idc_new idc_stock ln1p_idc_new ln1p_idc_stock ln1p_idc_stock_l1 ln1p_idc_new_l1 {
    replace `x' = 0 if missing(`x')
}

gen byte non_st = 是否ST类 == "0"
gen str1 industry_1d = substr(行业代码, 1, 1)
gen byte non_finance = industry_1d != "J"
gen byte base_clean = non_st == 1 & non_finance == 1

preserve
keep 股票代码 年份 省份 城市 城市代码 行业代码 是否ST类 idc_new idc_stock ln1p_idc_new ln1p_idc_stock ln1p_idc_stock_l1 ln1p_idc_new_l1 ///
    企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4
export delimited using "`out'/idc_proxy_innovation_resilience_panel_2000_2024.csv", replace
save "`out'/idc_proxy_innovation_resilience_panel_2000_2024.dta", replace
restore

egen tag_city = tag(城市代码)
egen city_cluster = group(城市)
drop tag_city
egen tag_city = tag(city_cluster)
count if tag_city == 1
display "N_CITIES_TOTAL=" r(N)
count if tag_city == 1 & idc_stock > 0
display "N_CITIES_IDC_STOCK_POSITIVE=" r(N)
drop tag_city

tempname handle
postfile `handle' str24 sample str40 outcome str24 xvar double coef se t p n firms clusters r2 ///
    using "`out'/idc_proxy_main_effect_results_20260523.dta", replace

local ys 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4
local xs ln1p_idc_stock ln1p_idc_stock_l1 ln1p_idc_new ln1p_idc_new_l1

foreach y of local ys {
    foreach x of local xs {
        quietly areg `y' `x' i.年份 if base_clean == 1 & 年份 >= 2012 & 年份 <= 2022, absorb(股票代码) vce(cluster city_cluster)
        local coef = _b[`x']
        local se = _se[`x']
        local t = `coef' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        tempvar tagfirm
        egen `tagfirm' = tag(股票代码) if e(sample)
        quietly count if `tagfirm' == 1
        local firms = r(N)
        drop `tagfirm'
        post `handle' ("clean_2012_2022") ("`y'") ("`x'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

        quietly areg `y' `x' i.年份 if base_clean == 1 & 年份 >= 2008 & 年份 <= 2024, absorb(股票代码) vce(cluster city_cluster)
        local coef = _b[`x']
        local se = _se[`x']
        local t = `coef' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        tempvar tagfirm
        egen `tagfirm' = tag(股票代码) if e(sample)
        quietly count if `tagfirm' == 1
        local firms = r(N)
        drop `tagfirm'
        post `handle' ("clean_2008_2024") ("`y'") ("`x'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))
    }
}

postclose `handle'

use "`out'/idc_proxy_main_effect_results_20260523.dta", clear
export delimited using "`out'/idc_proxy_main_effect_results_20260523.csv", replace
list, noobs abbrev(24)

display "=== Done ==="
