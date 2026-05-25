clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_application_year_event_thresholds_stata_20260524.log", text replace

use "`data'/idc_applicant_concentration_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc == "both"

tempfile base
save `base'

tempname handle
postfile `handle' ///
    str20 eventdef ///
    str24 spec ///
    str32 outcome ///
    str12 event ///
    double coef se t p ///
    double preF prep ///
    long N N_city N_treated_city ///
    double mean_y ///
    using "`tables'/idc_applicant_concentration_application_year_event_thresholds_20260524.dta", replace

local outcomes ///
    ln1p_new_applicants ///
    new_applicant_share ///
    hhi ///
    top10_share ///
    base_top_share ///
    base_mid_inc_share

local events es_m4 es_m3 es_m2 es_0 es_p1 es_p2 es_p3 es_p4

foreach thr in 1 3 5 10 {
    use `base', clear
    gen byte treat_flag = idc_stock >= `thr'
    bysort city_id: egen first_treat = min(cond(treat_flag == 1, year, .))
    gen byte ever_treat = first_treat < .
    gen byte clean_cohort = ever_treat == 0 | inrange(first_treat, 2012, 2020)
    keep if clean_cohort == 1
    gen rel_year = year - first_treat if ever_treat == 1

    gen byte es_m4 = rel_year == -4
    gen byte es_m3 = rel_year == -3
    gen byte es_m2 = rel_year == -2
    gen byte es_0  = rel_year == 0
    gen byte es_p1 = rel_year == 1
    gen byte es_p2 = rel_year == 2
    gen byte es_p3 = rel_year == 3
    gen byte es_p4 = rel_year == 4

    egen tag_city0 = tag(city_id)
    quietly count if tag_city0 == 1 & ever_treat == 1
    local ntreated = r(N)
    local edef "stock_ge_`thr'"

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
            local b = _b[`ev']
            local se = _se[`ev']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            post `handle' ("`edef'") ("province_year_fe") ("`y'") ("`ev'") ///
                (`b') (`se') (`t') (`p') (`preF') (`prep') ///
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
            local b = _b[`ev']
            local se = _se[`ev']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            post `handle' ("`edef'") ("provyr_baseyr_fe") ("`y'") ("`ev'") ///
                (`b') (`se') (`t') (`p') (`preF') (`prep') ///
                (e(N)) (`nc') (`ntreated') (`mean_y')
        }
        drop `es2' `tag2'
    }
}

postclose `handle'

use "`tables'/idc_applicant_concentration_application_year_event_thresholds_20260524.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order eventdef spec outcome event coef se t p sig preF prep N N_city N_treated_city mean_y
export delimited using "`tables'/idc_applicant_concentration_application_year_event_thresholds_20260524.csv", replace

display "=== Threshold event-study coefficients ==="
list eventdef spec outcome event coef se p preF prep N N_city N_treated_city ///
    if event == "es_m2" | event == "es_0" | event == "es_p1" | event == "es_p2" | event == "es_p3", ///
    noobs abbrev(24)

log close
