clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_firm_entry_clean_event_study_stata_20260525.log", text replace

use "`data'/idc_scope_formal_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"

local firmvars ///
    firm_new_share_total firm_new_share_firm new_firm_share_all_new_patents ///
    ln1p_new_firm_patents ln1p_new_firm_applicants ///
    ln1p_firm_incumbent_patents ln1p_firm_total_patents

merge 1:1 city year using "`data'/firm_entry_clean_panel_2008_2023.dta", ///
    keep(match master) nogen keepusing(`firmvars')

tempfile base
save `base'

tempname handle
postfile `handle' ///
    str20 eventdef ///
    str28 spec ///
    str36 outcome ///
    str12 event ///
    double rel coef se t p ///
    double preF prep ///
    long N N_city N_treated_city ///
    double mean_y ///
    using "`tables'/firm_entry_clean_event_study_20260525.dta", replace

local outcomes ///
    firm_new_share_total ///
    firm_new_share_firm ///
    ln1p_new_firm_patents ///
    ln1p_new_firm_applicants ///
    ln1p_firm_incumbent_patents ///
    ln1p_firm_total_patents ///
    new_firm_share_all_new_patents

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

use "`tables'/firm_entry_clean_event_study_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order eventdef spec outcome event rel coef se t p sig preF prep N N_city N_treated_city mean_y
export delimited using "`tables'/firm_entry_clean_event_study_20260525.csv", replace
list if event == "es_m2" | event == "es_0" | event == "es_p1" | event == "es_p2" | event == "es_p3", ///
    noobs abbrev(28)

log close
