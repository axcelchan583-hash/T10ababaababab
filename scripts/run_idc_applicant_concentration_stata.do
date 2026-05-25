clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_idc_applicant_concentration_stata_20260524.log", text replace

display "=== IDC proxy and city applicant concentration ==="

use "`data'/idc_applicant_concentration_panel_2008_2024.dta", clear

egen city_cluster = group(city)

tempname handle
postfile `handle' ///
    str20 sample ///
    str16 scope ///
    str32 outcome ///
    str24 xvar ///
    double coef se t p ///
    long N N_city ///
    double r2 mean_y ///
    using "`tables'/idc_applicant_concentration_results_20260524.dta", replace

local xs ln1p_idc_stock_l1 ln1p_idc_stock ln1p_idc_new_l1 ln1p_idc_new
local outcomes ///
    hhi ///
    top1_share ///
    top5_share ///
    top10_share ///
    ln_effective_applicants ///
    ln1p_active_applicants ///
    ln1p_new_applicants ///
    new_applicant_share ///
    ln1p_total_patents

local scopes all_pub inv_app_pub inv_grant_pub
local samples matched_2008_2024 matched_2012_2022
local y0_matched_2008_2024 2008
local y1_matched_2008_2024 2024
local y0_matched_2012_2022 2012
local y1_matched_2012_2022 2022

foreach s of local samples {
    local y0 = `y0_`s''
    local y1 = `y1_`s''

    foreach sc of local scopes {
        foreach y of local outcomes {
            foreach x of local xs {
                quietly areg `y' `x' i.year ///
                    if scope == "`sc'" ///
                    & merge_idc == "both" ///
                    & inrange(year, `y0', `y1') ///
                    & total_patents > 0, ///
                    absorb(city_id) vce(cluster city_cluster)

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
                post `handle' ("`s'") ("`sc'") ("`y'") ("`x'") ///
                    (`b') (`se') (`t') (`p') (e(N)) (`nc') (e(r2)) (`mean_y')
                drop `es' `tag'
            }
        }
    }
}

postclose `handle'

use "`tables'/idc_applicant_concentration_results_20260524.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order sample scope outcome xvar coef se t p sig N N_city r2 mean_y
export delimited using "`tables'/idc_applicant_concentration_results_20260524.csv", replace

display "=== Main results: inv_app_pub, lagged IDC stock ==="
list sample outcome xvar coef se t p sig N N_city mean_y ///
    if scope == "inv_app_pub" & xvar == "ln1p_idc_stock_l1", noobs abbrev(24)

display "=== Main results: inv_grant_pub, lagged IDC stock ==="
list sample outcome xvar coef se t p sig N N_city mean_y ///
    if scope == "inv_grant_pub" & xvar == "ln1p_idc_stock_l1", noobs abbrev(24)

log close
