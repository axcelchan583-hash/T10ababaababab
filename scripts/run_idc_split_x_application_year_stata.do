clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_idc_split_x_application_year_stata_20260524.log", text replace

use "`data'/idc_split_applicant_concentration_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"

tempname handle
postfile `handle' ///
    str24 spec ///
    str32 outcome ///
    str32 xvar ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    using "`tables'/idc_split_x_application_year_results_20260524.dta", replace

local outcomes ///
    ln1p_new_applicants ///
    new_applicant_share ///
    hhi ///
    top10_share ///
    base_top_share ///
    base_mid_inc_share

local xvars ///
    ln1p_idc_scope_stock_l1 ///
    ln1p_idc_registered_stock_l1 ///
    ln1p_idc_combined_stock_l1

foreach x of local xvars {
    foreach y of local outcomes {
        quietly areg `y' `x' i.year, absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es tag
        quietly gen byte `es' = e(sample)
        quietly egen byte `tag' = tag(city_id) if `es'
        quietly count if `tag' == 1
        local nc = r(N)
        post `handle' ("city_year_fe") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es' `tag'

        quietly areg `y' `x' i.province_id#i.year, absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es2 tag2
        quietly gen byte `es2' = e(sample)
        quietly egen byte `tag2' = tag(city_id) if `es2'
        quietly count if `tag2' == 1
        local nc = r(N)
        post `handle' ("province_year_fe") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es2' `tag2'

        quietly areg `y' `x' i.province_id#i.year ///
            i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
            absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es3 tag3
        quietly gen byte `es3' = e(sample)
        quietly egen byte `tag3' = tag(city_id) if `es3'
        quietly count if `tag3' == 1
        local nc = r(N)
        post `handle' ("provyr_baseyr_fe") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es3' `tag3'
    }
}

postclose `handle'

use "`tables'/idc_split_x_application_year_results_20260524.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order spec outcome xvar coef se t p sig N N_city mean_y
export delimited using "`tables'/idc_split_x_application_year_results_20260524.csv", replace
list, noobs abbrev(28)

log close
