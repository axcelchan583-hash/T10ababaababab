clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_application_year_sample_robustness_stata_20260524.log", text replace

use "`data'/idc_applicant_concentration_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc == "both"

gen byte drop_bsgsh = inlist(city, "北京", "上海", "广州", "深圳", "杭州")
gen byte drop_top10city = ///
    city == "北京" | city == "深圳" | city == "上海" | city == "杭州" | city == "广州" | ///
    city == "苏州" | city == "南京" | city == "武汉" | city == "成都" | city == "西安"
gen byte min20 = total_patents >= 20
gen byte min50 = total_patents >= 50

tempname handle
postfile `handle' ///
    str24 sample ///
    str24 spec ///
    str32 outcome ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    using "`tables'/idc_applicant_concentration_application_year_sample_robustness_20260524.dta", replace

local outcomes ///
    ln1p_new_applicants ///
    new_applicant_share ///
    hhi ///
    top10_share ///
    base_top_share ///
    base_mid_inc_share

local samples all drop_bsgsh drop_top10city min20 min50

foreach s of local samples {
    local cond "1 == 1"
    if "`s'" == "drop_bsgsh" local cond "drop_bsgsh == 0"
    if "`s'" == "drop_top10city" local cond "drop_top10city == 0"
    if "`s'" == "min20" local cond "min20 == 1"
    if "`s'" == "min50" local cond "min50 == 1"

    foreach y of local outcomes {
        quietly areg `y' ln1p_idc_stock_l1 i.province_id#i.year ///
            if `cond', absorb(city_id) vce(cluster city_id)
        local b = _b[ln1p_idc_stock_l1]
        local se = _se[ln1p_idc_stock_l1]
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es tag
        quietly gen byte `es' = e(sample)
        quietly egen byte `tag' = tag(city_id) if `es'
        quietly count if `tag' == 1
        local nc = r(N)
        post `handle' ("`s'") ("province_year_fe") ("`y'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es' `tag'

        quietly areg `y' ln1p_idc_stock_l1 i.province_id#i.year ///
            i.base_ln_patents_q#i.year i.base_top10_q#i.year ///
            if `cond', absorb(city_id) vce(cluster city_id)
        local b = _b[ln1p_idc_stock_l1]
        local se = _se[ln1p_idc_stock_l1]
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es tag
        quietly gen byte `es' = e(sample)
        quietly egen byte `tag' = tag(city_id) if `es'
        quietly count if `tag' == 1
        local nc = r(N)
        post `handle' ("`s'") ("provyr_baseyr_fe") ("`y'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es' `tag'
    }
}

postclose `handle'

use "`tables'/idc_applicant_concentration_application_year_sample_robustness_20260524.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order sample spec outcome coef se t p sig N N_city mean_y
export delimited using "`tables'/idc_applicant_concentration_application_year_sample_robustness_20260524.csv", replace
list, noobs abbrev(24)

log close
