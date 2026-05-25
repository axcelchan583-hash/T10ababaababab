clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_application_year_event_study_stata_20260524.log", text replace

use "`data'/idc_applicant_concentration_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc == "both"

bysort city_id: egen first_idc = min(cond(idc_stock > 0, year, .))
gen byte ever_idc = first_idc < .
gen byte clean_cohort = ever_idc == 0 | inrange(first_idc, 2012, 2020)
keep if clean_cohort == 1

gen rel_year = year - first_idc if ever_idc == 1

gen byte es_m4 = rel_year == -4
gen byte es_m3 = rel_year == -3
gen byte es_m2 = rel_year == -2
gen byte es_0  = rel_year == 0
gen byte es_p1 = rel_year == 1
gen byte es_p2 = rel_year == 2
gen byte es_p3 = rel_year == 3
gen byte es_p4 = rel_year == 4

tempname handle
postfile `handle' ///
    str24 spec ///
    str32 outcome ///
    str12 event ///
    double coef se t p ///
    double preF prep ///
    long N N_city ///
    double mean_y ///
    using "`tables'/idc_applicant_concentration_application_year_event_study_20260524.dta", replace

local outcomes ///
    ln1p_new_applicants ///
    new_applicant_share ///
    hhi ///
    top10_share ///
    base_top_share ///
    base_mid_inc_share

local events es_m4 es_m3 es_m2 es_0 es_p1 es_p2 es_p3 es_p4

foreach y of local outcomes {
    quietly areg `y' `events' i.year, absorb(city_id) vce(cluster city_id)
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
        post `handle' ("city_year_fe") ("`y'") ("`ev'") ///
            (`b') (`se') (`t') (`p') (`preF') (`prep') (e(N)) (`nc') (`mean_y')
    }
    drop `es' `tag'

    quietly areg `y' `events' i.province_id#i.year, absorb(city_id) vce(cluster city_id)
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
        post `handle' ("province_year_fe") ("`y'") ("`ev'") ///
            (`b') (`se') (`t') (`p') (`preF') (`prep') (e(N)) (`nc') (`mean_y')
    }
    drop `es2' `tag2'

    quietly areg `y' `events' i.province_id#i.year ///
        i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
        absorb(city_id) vce(cluster city_id)
    test es_m4 es_m3 es_m2
    local preF = r(F)
    local prep = r(p)
    quietly summarize `y' if e(sample)
    local mean_y = r(mean)
    tempvar es3 tag3
    quietly gen byte `es3' = e(sample)
    quietly egen byte `tag3' = tag(city_id) if `es3'
    quietly count if `tag3' == 1
    local nc = r(N)
    foreach ev of local events {
        local b = _b[`ev']
        local se = _se[`ev']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        post `handle' ("provyr_baseyr_fe") ("`y'") ("`ev'") ///
            (`b') (`se') (`t') (`p') (`preF') (`prep') (e(N)) (`nc') (`mean_y')
    }
    drop `es3' `tag3'
}

postclose `handle'

use "`tables'/idc_applicant_concentration_application_year_event_study_20260524.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order spec outcome event coef se t p sig preF prep N N_city mean_y
export delimited using "`tables'/idc_applicant_concentration_application_year_event_study_20260524.csv", replace

display "=== Cohort distribution used in event study ==="
use "`data'/idc_applicant_concentration_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc == "both"
bysort city_id: egen first_idc = min(cond(idc_stock > 0, year, .))
egen tag_city = tag(city_id)
tab first_idc if tag_city == 1 & inrange(first_idc, 2008, 2023), missing

display "=== Event-study coefficients ==="
use "`tables'/idc_applicant_concentration_application_year_event_study_20260524.dta", clear
list spec outcome event coef se p preF prep N N_city ///
    if event == "es_m4" | event == "es_m3" | event == "es_m2" | ///
       event == "es_0" | event == "es_p1" | event == "es_p2" | event == "es_p3", ///
    noobs abbrev(24)

log close
