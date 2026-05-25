clear all
set more off

local t10 "/Users/mac/computerscience/23选题探索/T10"
local t07 "/Users/mac/computerscience/23选题探索/T07_public_data_ai_adoption"
local out "`t10'/outputs"

capture log close
log using "`out'/run_idc_digital_ai_innovation_stata_20260523.log", text replace

display "=== IDC proxy × digital innovation / AI-title innovation: Stata MCP run ==="

tempfile idc base y_digital y_ai y_strict panel

* ----------------------------------------------------------------------
* 1. Rebuild IDC city-year variables and lags by province-city, not city code.
* ----------------------------------------------------------------------
import delimited using "`out'/idc_proxy_city_year_2000_2024.csv", clear varnames(1) encoding("utf-8") stringcols(_all)
destring 年份 idc_new idc_stock ln1p_idc_new ln1p_idc_stock, replace force
duplicates report 省份 城市 年份
sort 省份 城市 年份
by 省份 城市: gen ln1p_idc_stock_l1 = ln1p_idc_stock[_n-1] if 年份 == 年份[_n-1] + 1
by 省份 城市: gen ln1p_idc_new_l1 = ln1p_idc_new[_n-1] if 年份 == 年份[_n-1] + 1
replace ln1p_idc_stock_l1 = 0 if missing(ln1p_idc_stock_l1)
replace ln1p_idc_new_l1 = 0 if missing(ln1p_idc_new_l1)
keep 省份 城市 年份 idc_new idc_stock ln1p_idc_new ln1p_idc_stock ln1p_idc_stock_l1 ln1p_idc_new_l1
save `idc', replace

* ----------------------------------------------------------------------
* 2. Base listed-firm city-year panel.
* ----------------------------------------------------------------------
use "`out'/public_innovation_resilience_rebuild_stata_2000_2024.dta", clear
drop if missing(股票代码) | missing(年份)
drop if missing(城市) | 城市 == ""
drop if missing(省份) | 省份 == ""
keep 股票代码 股票简称 年份 省份 城市 行业代码 是否ST类
merge m:1 省份 城市 年份 using `idc', keep(master match)
tab _merge
drop _merge

foreach x in idc_new idc_stock ln1p_idc_new ln1p_idc_stock ln1p_idc_stock_l1 ln1p_idc_new_l1 {
    replace `x' = 0 if missing(`x')
}

gen byte non_st = 是否ST类 == "0"
gen str1 industry_1d = substr(行业代码, 1, 1)
gen byte non_finance = industry_1d != "J"
gen byte base_clean = non_st == 1 & non_finance == 1
egen city_cluster = group(省份 城市)
save `base', replace

* ----------------------------------------------------------------------
* 3A. Route A outcome: vendor annual digital invention patent authorization.
* ----------------------------------------------------------------------
import delimited using "`t07'/data/interim/vendor_digital_invention_patent_annual.csv", clear varnames(1) encoding("utf-8") stringcols(_all)
ds
local vlist `r(varlist)'
local digital_var : word 4 of `vlist'
rename `digital_var' digital_invpat_raw
gen 股票代码 = real(symbol)
gen 年份 = real(year)
destring digital_invpat_raw, replace force
collapse (sum) digital_invpat = digital_invpat_raw, by(股票代码 年份)
gen ln1p_digital_invpat = ln(1 + digital_invpat)
gen has_digital_invpat = digital_invpat > 0
label var ln1p_digital_invpat "ln(1 + vendor digital invention patents authorized)"
label var has_digital_invpat "Any vendor digital invention patent authorized"
save `y_digital', replace

* ----------------------------------------------------------------------
* 3B. Route B outcome: annual digital/AI-title patent authorizations.
* This is a quick proxy from patent titles, broader than a final AI-only IPC/text classifier.
* ----------------------------------------------------------------------
import delimited using "`t07'/data/interim/patent_grants_monthly.csv", clear varnames(1) encoding("utf-8") stringcols(_all)
ds
local vlist `r(varlist)'
local patent_var : word 3 of `vlist'
local invention_var : word 4 of `vlist'
local ai_var : word 5 of `vlist'
rename `patent_var' patent_grant_count_raw
rename `invention_var' invention_grant_count_raw
rename `ai_var' ai_title_patent_raw
gen 股票代码 = real(symbol)
gen 年份 = real(substr(month, 1, 4))
destring ai_title_patent_raw invention_grant_count_raw patent_grant_count_raw, replace force
collapse (sum) ai_title_patent = ai_title_patent_raw ///
    invention_grant_count = invention_grant_count_raw patent_grant_count = patent_grant_count_raw, by(股票代码 年份)
gen ln1p_ai_title_patent = ln(1 + ai_title_patent)
gen has_ai_title_patent = ai_title_patent > 0
label var ln1p_ai_title_patent "ln(1 + digital/AI title patent grants)"
label var has_ai_title_patent "Any digital/AI title patent grant"
save `y_ai', replace

* ----------------------------------------------------------------------
* 3C. Route B stricter outcomes: deduplicated AI / compute-intensive invention titles.
* ----------------------------------------------------------------------
import delimited using "`out'/strict_ai_compute_patent_title_annual.csv", clear varnames(1) encoding("utf-8") stringcols(_all)
ds
local vlist `r(varlist)'
local strict_inv_var : word 7 of `vlist'
local compute_inv_var : word 8 of `vlist'
rename `strict_inv_var' strict_ai_inv_raw
rename `compute_inv_var' ai_compute_inv_raw
gen 股票代码 = real(symbol)
gen 年份 = real(year)
destring strict_ai_inv_raw ai_compute_inv_raw, replace force
collapse (sum) strict_ai_inv = strict_ai_inv_raw ai_compute_inv = ai_compute_inv_raw, by(股票代码 年份)
gen ln1p_strict_ai_inv = ln(1 + strict_ai_inv)
gen has_strict_ai_inv = strict_ai_inv > 0
gen ln1p_ai_compute_inv = ln(1 + ai_compute_inv)
gen has_ai_compute_inv = ai_compute_inv > 0
label var ln1p_strict_ai_inv "ln(1 + strict AI title invention patents)"
label var ln1p_ai_compute_inv "ln(1 + AI/compute title invention patents)"
save `y_strict', replace

* ----------------------------------------------------------------------
* 4. Merge outcomes and export the regression panel.
* ----------------------------------------------------------------------
use `base', clear
merge m:1 股票代码 年份 using `y_digital', keep(master match)
drop _merge
merge m:1 股票代码 年份 using `y_ai', keep(master match)
drop _merge
merge m:1 股票代码 年份 using `y_strict', keep(master match)
drop _merge

foreach y in digital_invpat ln1p_digital_invpat has_digital_invpat ai_title_patent ln1p_ai_title_patent has_ai_title_patent invention_grant_count patent_grant_count strict_ai_inv ln1p_strict_ai_inv has_strict_ai_inv ai_compute_inv ln1p_ai_compute_inv has_ai_compute_inv {
    replace `y' = 0 if missing(`y')
}

save "`out'/idc_proxy_digital_ai_innovation_panel_2000_2024.dta", replace
export delimited using "`out'/idc_proxy_digital_ai_innovation_panel_2000_2024.csv", replace

* Diagnostics.
count if base_clean == 1 & 年份 >= 2011 & 年份 <= 2024
display "N_CLEAN_2011_2024=" r(N)
count if base_clean == 1 & 年份 >= 2012 & 年份 <= 2022
display "N_CLEAN_2012_2022=" r(N)
sum digital_invpat ai_title_patent strict_ai_inv ai_compute_inv ln1p_digital_invpat ln1p_ai_title_patent ln1p_strict_ai_inv ln1p_ai_compute_inv if base_clean == 1 & 年份 >= 2011 & 年份 <= 2024

* ----------------------------------------------------------------------
* 5. Firm FE + year FE, clustered by city. No firm financial controls in this pilot.
* ----------------------------------------------------------------------
tempname handle
postfile `handle' str20 route str24 sample str32 outcome str24 xvar ///
    double coef se t p n firms clusters r2 mean_y ///
    using "`out'/idc_proxy_digital_ai_innovation_results_20260523.dta", replace

local xs ln1p_idc_stock ln1p_idc_stock_l1 ln1p_idc_new ln1p_idc_new_l1
local outcomes ln1p_digital_invpat has_digital_invpat ln1p_ai_title_patent has_ai_title_patent ln1p_strict_ai_inv has_strict_ai_inv ln1p_ai_compute_inv has_ai_compute_inv

foreach y of local outcomes {
    local route = "A_digital"
    if strpos("`y'", "ai_title_patent") > 0 local route = "B_broad_title"
    if strpos("`y'", "strict_ai_inv") > 0 local route = "B_strict_ai"
    if strpos("`y'", "ai_compute_inv") > 0 local route = "B_ai_compute"
    foreach x of local xs {
        quietly areg `y' `x' i.年份 if base_clean == 1 & 年份 >= 2012 & 年份 <= 2022, absorb(股票代码) vce(cluster city_cluster)
        local coef = _b[`x']
        local se = _se[`x']
        local t = `coef' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly sum `y' if e(sample)
        local mean_y = r(mean)
        tempvar tagfirm
        egen `tagfirm' = tag(股票代码) if e(sample)
        quietly count if `tagfirm' == 1
        local firms = r(N)
        drop `tagfirm'
        post `handle' ("`route'") ("clean_2012_2022") ("`y'") ("`x'") ///
            (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2)) (`mean_y')

        quietly areg `y' `x' i.年份 if base_clean == 1 & 年份 >= 2011 & 年份 <= 2024, absorb(股票代码) vce(cluster city_cluster)
        local coef = _b[`x']
        local se = _se[`x']
        local t = `coef' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly sum `y' if e(sample)
        local mean_y = r(mean)
        tempvar tagfirm
        egen `tagfirm' = tag(股票代码) if e(sample)
        quietly count if `tagfirm' == 1
        local firms = r(N)
        drop `tagfirm'
        post `handle' ("`route'") ("clean_2011_2024") ("`y'") ("`x'") ///
            (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2)) (`mean_y')
    }
}

postclose `handle'

use "`out'/idc_proxy_digital_ai_innovation_results_20260523.dta", clear
export delimited using "`out'/idc_proxy_digital_ai_innovation_results_20260523.csv", replace
list, noobs abbrev(24)

display "=== Done ==="
log close
