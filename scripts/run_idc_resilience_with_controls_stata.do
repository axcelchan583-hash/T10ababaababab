clear all
set more off

local t10 "/Users/mac/computerscience/23选题探索/T10"
local out "`t10'/outputs"

capture log close
log using "`out'/run_idc_resilience_with_controls_stata_20260523.log", text replace

display "=== IDC proxy × innovation resilience with firm controls ==="

tempfile idc controls panel

* IDC city-year X, with lags recalculated by province-city.
import delimited using "`out'/idc_proxy_city_year_2000_2024.csv", clear varnames(1) encoding("utf-8") stringcols(_all)
destring 年份 idc_new idc_stock ln1p_idc_new ln1p_idc_stock, replace force
sort 省份 城市 年份
by 省份 城市: gen ln1p_idc_stock_l1 = ln1p_idc_stock[_n-1] if 年份 == 年份[_n-1] + 1
by 省份 城市: gen ln1p_idc_new_l1 = ln1p_idc_new[_n-1] if 年份 == 年份[_n-1] + 1
replace ln1p_idc_stock_l1 = 0 if missing(ln1p_idc_stock_l1)
replace ln1p_idc_new_l1 = 0 if missing(ln1p_idc_new_l1)
keep 省份 城市 年份 idc_new idc_stock ln1p_idc_new ln1p_idc_stock ln1p_idc_stock_l1 ln1p_idc_new_l1
save `idc', replace

* Existing cleaned CSMAR firm-year controls.
import delimited using "`out'/csmar_controls_firm_year_from_existing.csv", clear varnames(1) encoding("utf-8") stringcols(_all)
gen 股票代码 = real(symbol)
gen 年份 = real(year)
rename size Size
rename lev Lev
rename roa ROA
rename growth Growth
rename be_ratio BE_ratio
destring Size Lev ROA Growth BE_ratio ta tl te ni rev, replace force
rename ta TA
rename tl TL
rename te TE
rename ni NI
rename rev REV
keep 股票代码 年份 Size Lev ROA Growth BE_ratio TA TL TE NI REV
duplicates drop 股票代码 年份, force
save `controls', replace

* Main panel.
use "`out'/public_innovation_resilience_rebuild_stata_2000_2024.dta", clear
drop if missing(股票代码) | missing(年份)
drop if missing(城市) | 城市 == ""
drop if missing(省份) | 省份 == ""

merge m:1 省份 城市 年份 using `idc', keep(master match) nogen
foreach x in idc_new idc_stock ln1p_idc_new ln1p_idc_stock ln1p_idc_stock_l1 ln1p_idc_new_l1 {
    replace `x' = 0 if missing(`x')
}

merge m:1 股票代码 年份 using `controls', keep(master match) nogen

capture confirm string variable 是否ST类
if _rc == 0 {
    gen byte non_st = 是否ST类 == "0"
}
else {
    gen byte non_st = 是否ST类 == 0
}
gen str1 industry_1d = substr(行业代码, 1, 1)
gen byte non_finance = industry_1d != "J"
gen byte base_clean = non_st == 1 & non_finance == 1
egen city_cluster = group(省份 城市)

gen byte has_ctrl = !missing(Size, Lev, ROA, Growth)

* Winsorize outcomes and controls on the broad clean regression window.
local winsor_vars 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4 Size Lev ROA Growth
foreach v of local winsor_vars {
    gen w_`v' = `v'
    quietly summarize `v' if base_clean == 1 & 年份 >= 2008 & 年份 <= 2024, detail
    local p1 = r(p1)
    local p99 = r(p99)
    replace w_`v' = `p1' if w_`v' < `p1' & !missing(w_`v')
    replace w_`v' = `p99' if w_`v' > `p99' & !missing(w_`v')
}

save "`out'/idc_proxy_innovation_resilience_controls_panel_2000_2024.dta", replace
export delimited using "`out'/idc_proxy_innovation_resilience_controls_panel_2000_2024.csv", replace

count if base_clean == 1 & 年份 >= 2012 & 年份 <= 2022
display "N_BASE_2012_2022=" r(N)
count if base_clean == 1 & has_ctrl == 1 & 年份 >= 2012 & 年份 <= 2022
display "N_CTRL_2012_2022=" r(N)
count if base_clean == 1 & 年份 >= 2008 & 年份 <= 2024
display "N_BASE_2008_2024=" r(N)
count if base_clean == 1 & has_ctrl == 1 & 年份 >= 2008 & 年份 <= 2024
display "N_CTRL_2008_2024=" r(N)

tempname handle
postfile `handle' str28 spec str18 sample str40 outcome str8 y_version str24 xvar ///
    double coef se t p n firms clusters r2 ///
    using "`out'/idc_resilience_with_controls_results_20260523.dta", replace

local ys 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4
local xs ln1p_idc_stock ln1p_idc_stock_l1 ln1p_idc_new ln1p_idc_new_l1
local controls Size Lev ROA Growth
local wcontrols w_Size w_Lev w_ROA w_Growth

foreach y of local ys {
    foreach yv in raw winsor {
        local yuse "`y'"
        local cuse "`controls'"
        if "`yv'" == "winsor" {
            local yuse "w_`y'"
            local cuse "`wcontrols'"
        }
        foreach x of local xs {
            quietly areg `yuse' `x' i.年份 if base_clean == 1 & 年份 >= 2012 & 年份 <= 2022, absorb(股票代码) vce(cluster city_cluster)
            local coef = _b[`x']
            local se = _se[`x']
            local t = `coef' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar tagfirm
            egen `tagfirm' = tag(股票代码) if e(sample)
            quietly count if `tagfirm' == 1
            local firms = r(N)
            drop `tagfirm'
            post `handle' ("nocontrol_full") ("2012_2022") ("`y'") ("`yv'") ("`x'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

            quietly areg `yuse' `x' i.年份 if base_clean == 1 & has_ctrl == 1 & 年份 >= 2012 & 年份 <= 2022, absorb(股票代码) vce(cluster city_cluster)
            local coef = _b[`x']
            local se = _se[`x']
            local t = `coef' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar tagfirm
            egen `tagfirm' = tag(股票代码) if e(sample)
            quietly count if `tagfirm' == 1
            local firms = r(N)
            drop `tagfirm'
            post `handle' ("nocontrol_ctrlsample") ("2012_2022") ("`y'") ("`yv'") ("`x'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

            quietly areg `yuse' `x' `cuse' i.年份 if base_clean == 1 & has_ctrl == 1 & 年份 >= 2012 & 年份 <= 2022, absorb(股票代码) vce(cluster city_cluster)
            local coef = _b[`x']
            local se = _se[`x']
            local t = `coef' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar tagfirm
            egen `tagfirm' = tag(股票代码) if e(sample)
            quietly count if `tagfirm' == 1
            local firms = r(N)
            drop `tagfirm'
            post `handle' ("controls") ("2012_2022") ("`y'") ("`yv'") ("`x'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

            quietly areg `yuse' `x' i.年份 if base_clean == 1 & 年份 >= 2008 & 年份 <= 2024, absorb(股票代码) vce(cluster city_cluster)
            local coef = _b[`x']
            local se = _se[`x']
            local t = `coef' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar tagfirm
            egen `tagfirm' = tag(股票代码) if e(sample)
            quietly count if `tagfirm' == 1
            local firms = r(N)
            drop `tagfirm'
            post `handle' ("nocontrol_full") ("2008_2024") ("`y'") ("`yv'") ("`x'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

            quietly areg `yuse' `x' i.年份 if base_clean == 1 & has_ctrl == 1 & 年份 >= 2008 & 年份 <= 2024, absorb(股票代码) vce(cluster city_cluster)
            local coef = _b[`x']
            local se = _se[`x']
            local t = `coef' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar tagfirm
            egen `tagfirm' = tag(股票代码) if e(sample)
            quietly count if `tagfirm' == 1
            local firms = r(N)
            drop `tagfirm'
            post `handle' ("nocontrol_ctrlsample") ("2008_2024") ("`y'") ("`yv'") ("`x'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

            quietly areg `yuse' `x' `cuse' i.年份 if base_clean == 1 & has_ctrl == 1 & 年份 >= 2008 & 年份 <= 2024, absorb(股票代码) vce(cluster city_cluster)
            local coef = _b[`x']
            local se = _se[`x']
            local t = `coef' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar tagfirm
            egen `tagfirm' = tag(股票代码) if e(sample)
            quietly count if `tagfirm' == 1
            local firms = r(N)
            drop `tagfirm'
            post `handle' ("controls") ("2008_2024") ("`y'") ("`yv'") ("`x'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))
        }
    }
}

postclose `handle'

use "`out'/idc_resilience_with_controls_results_20260523.dta", clear
export delimited using "`out'/idc_resilience_with_controls_results_20260523.csv", replace
list if outcome == "企业创新韧性1" & y_version == "winsor", noobs abbrev(24)

display "=== Done ==="
log close
