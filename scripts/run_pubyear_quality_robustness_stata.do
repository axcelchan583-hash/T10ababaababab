clear all
set more off

local root "/Users/mac/computerscience/23实证选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_pubyear_quality_robustness_stata_20260525.log", text replace

use "`data'/idc_scope_pubyear_quality_panel_2008_2024.dta", clear
keep if merge_idc_split == "both"

local x ln1p_idc_scope_stock_l1

tempname h
postfile `h' ///
    str16 sample ///
    str20 scope ///
    str28 spec ///
    str32 outcome ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    using "`tables'/pubyear_quality_robustness_results_20260525.dta", replace

local outcomes ///
    new_applicant_share ///
    ln1p_new_applicants ///
    ln1p_new_patents ///
    ln1p_total_patents ///
    ln1p_incumbent_patents ///
    hhi ///
    top10_share

foreach scope_name in inv_grant_pub inv_app_pub all_pub {
    foreach sample in y2023 y2021 {
        preserve
        keep if scope == "`scope_name'"
        if "`sample'" == "y2023" {
            keep if year <= 2023
        }
        if "`sample'" == "y2021" {
            keep if year <= 2021
        }

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
            post `h' ("`sample'") ("`scope_name'") ("province_year_fe") ("`y'") ///
                (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
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
            post `h' ("`sample'") ("`scope_name'") ("provyr_baseyr_fe") ("`y'") ///
                (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
            drop `es2' `tag2'
        }
        restore
    }
}

postclose `h'

use "`tables'/pubyear_quality_robustness_results_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order sample scope spec outcome coef se t p sig N N_city mean_y
export delimited using "`tables'/pubyear_quality_robustness_results_20260525.csv", replace
list if sample == "y2023" & spec == "provyr_baseyr_fe", noobs abbrev(28)

log close
