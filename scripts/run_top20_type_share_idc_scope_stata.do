clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_top20_type_share_idc_scope_stata_20260525.log", text replace

use "`data'/idc_scope_formal_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"
merge 1:1 city year using "`data'/top20_type_share_panel_2008_2023.dta", keep(match master) nogen

tempname handle
postfile `handle' ///
    str28 spec ///
    str36 outcome ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    using "`tables'/top20_type_share_idc_scope_results_20260525.dta", replace

local outcomes ///
    top20_firm_share_total ///
    top20_univ_share_total ///
    top20_research_share_total ///
    top20_individual_share_total ///
    top20_firm_share_top20 ///
    top20_univ_share_top20 ///
    top20_research_share_top20 ///
    top20_individual_share_top20

local x ln1p_idc_scope_stock_l1

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
    post `handle' ("province_year_fe") ("`y'") (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
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
    tempvar es2 tag2
    quietly gen byte `es2' = e(sample)
    quietly egen byte `tag2' = tag(city_id) if `es2'
    quietly count if `tag2' == 1
    local nc = r(N)
    post `handle' ("provyr_baseyr_fe") ("`y'") (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
    drop `es2' `tag2'
}

postclose `handle'

use "`tables'/top20_type_share_idc_scope_results_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order spec outcome coef se t p sig N N_city mean_y
export delimited using "`tables'/top20_type_share_idc_scope_results_20260525.csv", replace
list, noobs abbrev(28)

log close
