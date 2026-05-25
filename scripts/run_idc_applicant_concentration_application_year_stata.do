clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_idc_applicant_concentration_application_year_stata_20260524.log", text replace

display "=== IDC proxy and applicant concentration, application-year invention applications ==="

use "`data'/idc_applicant_concentration_application_year_panel_2008_2023.dta", clear

keep if scope == "inv_app_appyear"
keep if merge_idc == "both"
xtset city_id year

tempname handle
postfile `handle' ///
    str24 spec ///
    str32 outcome ///
    str24 xvar ///
    double coef se t p ///
    long N N_city ///
    double r2 mean_y ///
    using "`tables'/idc_applicant_concentration_application_year_results_20260524.dta", replace

local outcomes ///
    ln1p_total_patents ///
    ln1p_new_applicants ///
    new_applicant_share ///
    hhi ///
    top10_share ///
    roll_top_share ///
    roll_mid_inc_share ///
    base_top_share ///
    base_mid_inc_share

local xs ln1p_idc_stock_l1 ln1p_idc_stock

foreach y of local outcomes {
    foreach x of local xs {

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
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (e(r2)) (`mean_y')
        drop `es' `tag'

        quietly areg `y' `x' i.province_id#i.year, absorb(city_id) vce(cluster city_id)
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
        post `handle' ("province_year_fe") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (e(r2)) (`mean_y')
        drop `es' `tag'

        quietly areg `y' `x' i.province_id#i.year ///
            i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
            absorb(city_id) vce(cluster city_id)
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
        post `handle' ("provyr_baseyr_fe") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (e(r2)) (`mean_y')
        drop `es' `tag'

        quietly areg `y' `x' i.year c.year#i.city_id, absorb(city_id) vce(cluster city_id)
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
        post `handle' ("city_trend") ("`y'") ("`x'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (e(r2)) (`mean_y')
        drop `es' `tag'
    }
}

postclose `handle'

use "`tables'/idc_applicant_concentration_application_year_results_20260524.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order spec outcome xvar coef se t p sig N N_city r2 mean_y
export delimited using "`tables'/idc_applicant_concentration_application_year_results_20260524.csv", replace

display "=== Main x: lagged IDC stock ==="
list spec outcome xvar coef se t p sig N N_city mean_y ///
    if xvar == "ln1p_idc_stock_l1", noobs abbrev(24)

log close
