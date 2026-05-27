clear all
set more off

local root "/Users/mac/computerscience/23实证选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_policy_horserace_stata_20260527.log", text replace

use "`data'/idc_scope_policy_horserace_panel_2008_2023.dta", clear
keep if merge_idc_split == "both"

local x ln1p_idc_scope_stock_l1
local policies ///
    broadband_china_pilot ///
    smart_city_pilot ///
    bigdata_comprehensive_pilot ///
    innovative_city_pilot ///
    national_hightech_zone ///
    ip_demo_city ///
    information_consumption_pilot ///
    ecommerce_demo_city

local keep_policies
foreach p of local policies {
    capture confirm variable `p'
    if !_rc {
        quietly summarize `p'
        if r(N) > 0 & r(sd) > 0 {
            local keep_policies `keep_policies' `p'
        }
    }
}

tempname h
postfile `h' ///
    str28 spec ///
    str32 outcome ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    str160 controls ///
    using "`tables'/policy_horserace_results_20260527.dta", replace

local outcomes ///
    new_applicant_share ///
    ln1p_new_applicants ///
    ln1p_new_patents ///
    ln1p_total_patents ///
    ln1p_incumbent_patents ///
    hhi ///
    top10_share

foreach y of local outcomes {
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
    post `h' ("province_year_fe") ("`y'") (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y') ("none")
    drop `es' `tag'

    quietly areg `y' `x' `keep_policies' i.province_id#i.year, absorb(city_id) vce(cluster city_id)
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
    post `h' ("policy_horserace") ("`y'") (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y') ("`keep_policies'")
    drop `es2' `tag2'

    quietly areg `y' `x' `keep_policies' i.province_id#i.year ///
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
    post `h' ("policy_baseyr_fe") ("`y'") (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y') ("`keep_policies'")
    drop `es3' `tag3'
}

postclose `h'

use "`tables'/policy_horserace_results_20260526.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order spec outcome coef se t p sig N N_city mean_y controls
export delimited using "`tables'/policy_horserace_results_20260527.csv", replace
list, noobs abbrev(28)

log close
