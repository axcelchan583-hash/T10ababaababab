clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_idc_scope_formal_main_stata_20260525.log", text replace

use "`data'/idc_scope_formal_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"
xtset city_id year

tempname handle
postfile `handle' ///
    str24 table ///
    str28 spec ///
    str32 outcome ///
    str36 xvar ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    using "`tables'/idc_scope_formal_results_20260525.dta", replace

local outcomes ///
    ln1p_total_patents ///
    ln1p_new_applicants ///
    new_applicant_share ///
    hhi ///
    top10_share ///
    base_top_share ///
    base_mid_inc_share

local mainx ln1p_idc_scope_stock_l1

foreach y of local outcomes {
    quietly areg `y' `mainx' i.year, absorb(city_id) vce(cluster city_id)
    local b = _b[`mainx']
    local se = _se[`mainx']
    local t = `b' / `se'
    local p = 2 * ttail(e(df_r), abs(`t'))
    quietly summarize `y' if e(sample)
    local mean_y = r(mean)
    tempvar es tag
    quietly gen byte `es' = e(sample)
    quietly egen byte `tag' = tag(city_id) if `es'
    quietly count if `tag' == 1
    local nc = r(N)
    post `handle' ("main") ("city_year_fe") ("`y'") ("`mainx'") ///
        (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
    drop `es' `tag'

    quietly areg `y' `mainx' i.province_id#i.year, absorb(city_id) vce(cluster city_id)
    local b = _b[`mainx']
    local se = _se[`mainx']
    local t = `b' / `se'
    local p = 2 * ttail(e(df_r), abs(`t'))
    quietly summarize `y' if e(sample)
    local mean_y = r(mean)
    tempvar es2 tag2
    quietly gen byte `es2' = e(sample)
    quietly egen byte `tag2' = tag(city_id) if `es2'
    quietly count if `tag2' == 1
    local nc = r(N)
    post `handle' ("main") ("province_year_fe") ("`y'") ("`mainx'") ///
        (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
    drop `es2' `tag2'

    quietly areg `y' `mainx' i.province_id#i.year ///
        i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
        absorb(city_id) vce(cluster city_id)
    local b = _b[`mainx']
    local se = _se[`mainx']
    local t = `b' / `se'
    local p = 2 * ttail(e(df_r), abs(`t'))
    quietly summarize `y' if e(sample)
    local mean_y = r(mean)
    tempvar es3 tag3
    quietly gen byte `es3' = e(sample)
    quietly egen byte `tag3' = tag(city_id) if `es3'
    quietly count if `tag3' == 1
    local nc = r(N)
    post `handle' ("main") ("provyr_baseyr_fe") ("`y'") ("`mainx'") ///
        (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
    drop `es3' `tag3'

    quietly areg `y' `mainx' i.year c.year#i.city_id, absorb(city_id) vce(cluster city_id)
    local b = _b[`mainx']
    local se = _se[`mainx']
    local t = `b' / `se'
    local p = 2 * ttail(e(df_r), abs(`t'))
    quietly summarize `y' if e(sample)
    local mean_y = r(mean)
    tempvar es4 tag4
    quietly gen byte `es4' = e(sample)
    quietly egen byte `tag4' = tag(city_id) if `es4'
    quietly count if `tag4' == 1
    local nc = r(N)
    post `handle' ("main") ("city_trend") ("`y'") ("`mainx'") ///
        (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
    drop `es4' `tag4'
}

local cityxvars ///
    ln1p_idc_scope_new_l1 ///
    ln1p_idc_scope_pre5_l1 ///
    ln1p_idc_registered_stock_l1 ///
    ln1p_idc_combined_stock_l1

foreach x of local cityxvars {
    foreach y of local outcomes {
        quietly areg `y' `x' i.province_id#i.year, absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es5 tag5
        quietly gen byte `es5' = e(sample)
        quietly egen byte `tag5' = tag(city_id) if `es5'
        quietly count if `tag5' == 1
        local nc = r(N)
        post `handle' ("x_robust_city") ("province_year_fe") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es5' `tag5'

        quietly areg `y' `x' i.province_id#i.year ///
            i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
            absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es6 tag6
        quietly gen byte `es6' = e(sample)
        quietly egen byte `tag6' = tag(city_id) if `es6'
        quietly count if `tag6' == 1
        local nc = r(N)
        post `handle' ("x_robust_city") ("provyr_baseyr_fe") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es6' `tag6'
    }
}

local provxvars ///
    ln1p_idc_scope_prov_stock_l1 ///
    ln1p_idc_scope_prov_new_l1 ///
    ln1p_idc_scope_prov_pre5_l1

foreach x of local provxvars {
    foreach y of local outcomes {
        quietly areg `y' `x' i.year, absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es7 tag7
        quietly gen byte `es7' = e(sample)
        quietly egen byte `tag7' = tag(city_id) if `es7'
        quietly count if `tag7' == 1
        local nc = r(N)
        post `handle' ("x_robust_province") ("city_year_fe") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es7' `tag7'

        quietly areg `y' `x' i.year c.year#i.city_id, absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es8 tag8
        quietly gen byte `es8' = e(sample)
        quietly egen byte `tag8' = tag(city_id) if `es8'
        quietly count if `tag8' == 1
        local nc = r(N)
        post `handle' ("x_robust_province") ("city_trend") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es8' `tag8'
    }
}

postclose `handle'

use "`tables'/idc_scope_formal_results_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order table spec outcome xvar coef se t p sig N N_city mean_y
export delimited using "`tables'/idc_scope_formal_results_20260525.csv", replace
list if table == "main", noobs abbrev(28)

log close
