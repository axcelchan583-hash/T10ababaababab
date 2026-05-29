clear all
set more off
set linesize 255

local root "/Users/mac/computerscience/23实证选题探索/T10"
local panel "`root'/data/processed/new_y_smoke_panel_2008_2023.dta"
local out "`root'/results/tables/top_turnover_event_study_20260529.dta"
local outcsv "`root'/results/tables/top_turnover_event_study_20260529.csv"
local log "`root'/results/logs/top_turnover_event_study_20260529.log"

capture log close _all
log using "`log'", text replace

use "`panel'", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"

tempfile base
save `base'

tempname handle
postfile `handle' ///
    str20 eventdef ///
    str28 spec ///
    str40 outcome ///
    str12 event ///
    double rel coef se t p ///
    double preF prep ///
    long N N_city N_treated_city ///
    double mean_y ///
    using "`out'", replace

local outcomes ///
    top10_turnover_prev_pat_share ///
    top20_turnover_prev_pat_share ///
    top10_turnover_prev_share ///
    top20_turnover_prev_share

local events es_m4 es_m3 es_m2 es_0 es_p1 es_p2 es_p3 es_p4

foreach thr in 1 2 3 5 {
    use `base', clear
    gen byte treat_flag = idc_scope_stock >= `thr'
    bysort city_id: egen first_treat = min(cond(treat_flag == 1, year, .))
    gen byte ever_treat = first_treat < .
    gen byte clean_cohort = ever_treat == 0 | inrange(first_treat, 2012, 2020)
    keep if clean_cohort == 1
    gen rel_year = year - first_treat if ever_treat == 1

    gen byte es_m4 = ever_treat == 1 & rel_year <= -4
    gen byte es_m3 = ever_treat == 1 & rel_year == -3
    gen byte es_m2 = ever_treat == 1 & rel_year == -2
    * Omitted event year is -1.
    gen byte es_0  = ever_treat == 1 & rel_year == 0
    gen byte es_p1 = ever_treat == 1 & rel_year == 1
    gen byte es_p2 = ever_treat == 1 & rel_year == 2
    gen byte es_p3 = ever_treat == 1 & rel_year == 3
    gen byte es_p4 = ever_treat == 1 & rel_year >= 4

    egen tag_city0 = tag(city_id)
    quietly count if tag_city0 == 1 & ever_treat == 1
    local ntreated = r(N)
    local edef "scope_ge_`thr'"

    foreach y of local outcomes {
        quietly areg `y' `events' i.province_id#i.year, absorb(city_id) vce(cluster city_id)
        test es_m4 es_m3 es_m2
        local preF = r(F)
        local prep = r(p)
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es tag
        quietly gen byte `es' = e(sample)
        quietly egen byte `tag' = tag(city_id) if `es'
        quietly count if `tag' == 1
        local nc = r(N)
        foreach ev of local events {
            local rel = .
            if "`ev'" == "es_m4" local rel = -4
            if "`ev'" == "es_m3" local rel = -3
            if "`ev'" == "es_m2" local rel = -2
            if "`ev'" == "es_0" local rel = 0
            if "`ev'" == "es_p1" local rel = 1
            if "`ev'" == "es_p2" local rel = 2
            if "`ev'" == "es_p3" local rel = 3
            if "`ev'" == "es_p4" local rel = 4
            local b = _b[`ev']
            local se = _se[`ev']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            post `handle' ("`edef'") ("province_year_fe") ("`y'") ("`ev'") ///
                (`rel') (`b') (`se') (`t') (`p') (`preF') (`prep') ///
                (e(N)) (`nc') (`ntreated') (`mean_y')
        }
        drop `es' `tag'

        quietly areg `y' `events' i.province_id#i.year ///
            i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
            absorb(city_id) vce(cluster city_id)
        test es_m4 es_m3 es_m2
        local preF = r(F)
        local prep = r(p)
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es2 tag2
        quietly gen byte `es2' = e(sample)
        quietly egen byte `tag2' = tag(city_id) if `es2'
        quietly count if `tag2' == 1
        local nc = r(N)
        foreach ev of local events {
            local rel = .
            if "`ev'" == "es_m4" local rel = -4
            if "`ev'" == "es_m3" local rel = -3
            if "`ev'" == "es_m2" local rel = -2
            if "`ev'" == "es_0" local rel = 0
            if "`ev'" == "es_p1" local rel = 1
            if "`ev'" == "es_p2" local rel = 2
            if "`ev'" == "es_p3" local rel = 3
            if "`ev'" == "es_p4" local rel = 4
            local b = _b[`ev']
            local se = _se[`ev']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            post `handle' ("`edef'") ("provyr_baseyr_fe") ("`y'") ("`ev'") ///
                (`rel') (`b') (`se') (`t') (`p') (`preF') (`prep') ///
                (e(N)) (`nc') (`ntreated') (`mean_y')
        }
        drop `es2' `tag2'
    }
}

postclose `handle'

use "`out'", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order eventdef spec outcome event rel coef se t p sig preF prep N N_city N_treated_city mean_y
save "`out'", replace
export delimited using "`outcsv'", replace

log close
