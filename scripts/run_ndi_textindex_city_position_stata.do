version 17
clear all
set more off

global ROOT "/Users/mac/computerscience/23选题探索/T10"
global OUT "$ROOT/outputs"

use "$OUT/city_innovation_position_with_ndi_textindex_2003_2024.dta", clear

gen diff_nl_ls_inv = ln1p_nonlisted_invgrant_proxy - ln1p_listed_invgrant
gen diff_ls_city_inv = ln1p_listed_invgrant - ln1p_city_invgrant

xtset city_id year

tempfile results
tempname handle
postfile `handle' ///
    str20 sample ///
    str36 outcome ///
    str28 xvar ///
    double coef se t p ///
    long N N_city ///
    double r2_within ///
    using `results', replace

local samples "2008_2024 2012_2022"
local y0_2008_2024 2008
local y1_2008_2024 2024
local y0_2012_2022 2012
local y1_2012_2022 2022

local xvars "ln1p_ndi_kw_per10k ndi_entropy_mm ndi_pca1_mm ln1p_ndi_kw_per10k_l1 ndi_entropy_mm_l1 ndi_pca1_mm_l1"

foreach s of local samples {
    local y0 = `y0_`s''
    local y1 = `y1_`s''

    foreach x of local xvars {
        foreach y in ///
            ln1p_city_invgrant ///
            ln1p_listed_invgrant ///
            ln1p_nonlisted_invgrant_proxy ///
            diff_nl_ls_inv ///
            diff_ls_city_inv ///
            listed_share_invgrant_clean ///
            listed_share_apply_clean ///
            listed_share_grant_clean {

            local stem "invgrant"
            if "`y'" == "listed_share_apply_clean" local stem "apply"
            if "`y'" == "listed_share_grant_clean" local stem "grant"

            quietly xtreg `y' `x' i.year ///
                if inrange(year, `y0', `y1') ///
                & city_`stem' > 0 ///
                & bad_negative_nonlisted_`stem' == 0 ///
                & merge_ndi == "both", ///
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
export delimited using "$OUT/ndi_textindex_city_position_results_20260523.csv", replace
save "$OUT/ndi_textindex_city_position_results_20260523.dta", replace

display as text "Saved: $OUT/ndi_textindex_city_position_results_20260523.csv"
