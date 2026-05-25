version 17
clear all
set more off

global ROOT "/Users/mac/computerscience/23选题探索/T10"
global OUT "$ROOT/outputs"

use "$OUT/city_innovation_position_panel_2000_2024.dta", clear

gen diff_nl_ls_inv = ln1p_nonlisted_invgrant_proxy - ln1p_listed_invgrant
gen diff_ls_city_inv = ln1p_listed_invgrant - ln1p_city_invgrant
gen diff_nl_ls_apply = ln1p_nonlisted_apply_proxy - ln1p_listed_apply
gen diff_nl_ls_grant = ln1p_nonlisted_grant_proxy - ln1p_listed_grant

xtset city_id year

tempfile results
tempname handle
postfile `handle' ///
    str20 sample ///
    str36 outcome ///
    str24 xvar ///
    double coef se t p ///
    long N N_city ///
    double r2_within ///
    using `results', replace

local samples "2008_2024 2012_2022"
local y0_2008_2024 2008
local y1_2008_2024 2024
local y0_2012_2022 2012
local y1_2012_2022 2022

local mainx "ln1p_idc_stock ln1p_idc_new ln1p_idc_stock_l1 ln1p_idc_new_l1"

foreach s of local samples {
    local y0 = `y0_`s''
    local y1 = `y1_`s''

    foreach x of local mainx {

        * Main invention-grant decomposition, common clean sample.
        foreach y in ///
            ln1p_city_invgrant ///
            ln1p_listed_invgrant ///
            ln1p_nonlisted_invgrant_proxy ///
            diff_nl_ls_inv ///
            diff_ls_city_inv ///
            listed_share_invgrant_clean {

            quietly xtreg `y' `x' i.year ///
                if inrange(year, `y0', `y1') ///
                & city_invgrant > 0 ///
                & bad_negative_nonlisted_invgrant == 0, ///
                fe vce(cluster city_id)

            local b = _b[`x']
            local se = _se[`x']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar es tag
            quietly gen byte `es' = e(sample)
            quietly egen byte `tag' = tag(city_id) if `es'
            quietly count if `tag' == 1
            local nc = r(N)
            post `handle' ("`s'") ("`y'") ("`x'") ///
                (`b') (`se') (`t') (`p') (e(N)) (`nc') (e(r2_w))
            drop `es' `tag'
        }

        * Alternative patent measures for the listed-share outcome.
        foreach y in listed_share_apply_clean listed_share_grant_clean {
            local stem = subinstr("`y'", "listed_share_", "", .)
            local stem = subinstr("`stem'", "_clean", "", .)

            quietly xtreg `y' `x' i.year ///
                if inrange(year, `y0', `y1') ///
                & city_`stem' > 0 ///
                & bad_negative_nonlisted_`stem' == 0, ///
                fe vce(cluster city_id)

            local b = _b[`x']
            local se = _se[`x']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar es tag
            quietly gen byte `es' = e(sample)
            quietly egen byte `tag' = tag(city_id) if `es'
            quietly count if `tag' == 1
            local nc = r(N)
            post `handle' ("`s'") ("`y'") ("`x'") ///
                (`b') (`se') (`t') (`p') (e(N)) (`nc') (e(r2_w))
            drop `es' `tag'
        }
    }
}

postclose `handle'

use `results', clear
gen abs_t = abs(t)
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order sample outcome xvar coef se t p sig N N_city r2_within
export delimited using "$OUT/city_innovation_position_first_round_results_20260523.csv", replace
save "$OUT/city_innovation_position_first_round_results_20260523.dta", replace

display as text "Saved: $OUT/city_innovation_position_first_round_results_20260523.csv"
