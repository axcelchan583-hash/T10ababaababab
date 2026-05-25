version 17
clear all
set more off

global ROOT "/Users/mac/computerscience/23选题探索/T10"
global OUT "$ROOT/outputs"

use "$OUT/city_innovation_position_panel_2000_2024.dta", clear

gen byte treat_data_infra = 0

* Province/region-level National Big Data Comprehensive Pilot Zones.
replace treat_data_infra = 1 if inlist(province, "贵州省", "河南省", "重庆市", "上海市")
replace treat_data_infra = 1 if inlist(province, "北京市", "天津市", "河北省", "内蒙古自治区")

* Pearl River Delta pilot zone: nine PRD cities, not all Guangdong cities.
replace treat_data_infra = 1 if inlist(city, "广州市", "深圳市", "珠海市", "佛山市", "惠州市")
replace treat_data_infra = 1 if inlist(city, "东莞市", "中山市", "江门市", "肇庆市")

* Shenyang pilot zone.
replace treat_data_infra = 1 if city == "沈阳市"

gen byte post2016 = year >= 2016
gen byte Data_infra = treat_data_infra * post2016

gen diff_nl_ls_inv = ln1p_nonlisted_invgrant_proxy - ln1p_listed_invgrant
gen diff_ls_city_inv = ln1p_listed_invgrant - ln1p_city_invgrant

xtset city_id year

tempfile results
tempname handle
postfile `handle' ///
    str20 sample ///
    str36 outcome ///
    str16 xvar ///
    double coef se t p ///
    long N N_city ///
    double r2_within ///
    using `results', replace

local samples "2008_2024 2012_2022"
local y0_2008_2024 2008
local y1_2008_2024 2024
local y0_2012_2022 2012
local y1_2012_2022 2022

foreach s of local samples {
    local y0 = `y0_`s''
    local y1 = `y1_`s''

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

        quietly xtreg `y' Data_infra i.year ///
            if inrange(year, `y0', `y1') ///
            & city_`stem' > 0 ///
            & bad_negative_nonlisted_`stem' == 0, ///
            fe vce(cluster city_id)

        local b = _b[Data_infra]
        local se = _se[Data_infra]
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        tempvar es tag
        quietly gen byte `es' = e(sample)
        quietly egen byte `tag' = tag(city_id) if `es'
        quietly count if `tag' == 1
        local nc = r(N)
        post `handle' ("`s'") ("`y'") ("Data_infra") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (e(r2_w))
        drop `es' `tag'
    }
}

postclose `handle'

use `results', clear
gen abs_t = abs(t)
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order sample outcome xvar coef se t p sig N N_city r2_within
export delimited using "$OUT/data_infra_city_position_first_round_results_20260523.csv", replace
save "$OUT/data_infra_city_position_first_round_results_20260523.dta", replace

display as text "Saved: $OUT/data_infra_city_position_first_round_results_20260523.csv"
