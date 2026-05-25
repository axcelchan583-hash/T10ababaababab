clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_firm_tech_entry_ddd_event_stata_20260525.log", text replace

use "`data'/firm_tech_entry_ddd_panel_2008_2023.dta", clear

egen city_year_id = group(city_id year)
egen city_high_id = group(city_id high_compute)
egen high_year_id = group(high_compute year)

tempfile base
save `base'

tempname handle
postfile `handle' ///
    str20 eventdef ///
    str24 spec ///
    str36 outcome ///
    str12 event ///
    double rel coef se t p ///
    double preF prep ///
    long N N_city N_treated_city ///
    double mean_y ///
    using "`tables'/firm_tech_entry_ddd_event_results_20260525.dta", replace

local outcomes ///
    ln_city_new_firm_n_f ///
    ln_city_new_firm_pat_f ///
    city_new_share_tot_f ///
    city_new_share_firm_f ///
    ln_field_new_firm_n_f ///
    ln_field_new_firm_pat_f ///
    field_new_share_tot_f ///
    field_new_share_firm_f ///
    ln_firm_pat_f ///
    ln_firm_inc_pat_f ///
    ln_tot_pat_f

local eventvars es_m4_high es_m3_high es_m2_high es_0_high es_p1_high es_p2_high es_p3_high es_p4_high

foreach thr in 2 5 {
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

    foreach ev in es_m4 es_m3 es_m2 es_0 es_p1 es_p2 es_p3 es_p4 {
        gen byte `ev'_high = `ev' * high_compute
    }

    egen tag_city0 = tag(city_id)
    quietly count if tag_city0 == 1 & ever_treat == 1
    local ntreated = r(N)
    local edef "scope_ge_`thr'"

    foreach y of local outcomes {
        quietly reghdfe `y' `eventvars', ///
            absorb(city_year_id city_high_id high_year_id) ///
            vce(cluster city_id)
        test es_m4_high es_m3_high es_m2_high
        local preF = r(F)
        local prep = r(p)
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        foreach ev of local eventvars {
            local rel = .
            if "`ev'" == "es_m4_high" local rel = -4
            if "`ev'" == "es_m3_high" local rel = -3
            if "`ev'" == "es_m2_high" local rel = -2
            if "`ev'" == "es_0_high" local rel = 0
            if "`ev'" == "es_p1_high" local rel = 1
            if "`ev'" == "es_p2_high" local rel = 2
            if "`ev'" == "es_p3_high" local rel = 3
            if "`ev'" == "es_p4_high" local rel = 4
            local b = _b[`ev']
            local se = _se[`ev']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            post `handle' ("`edef'") ("cityyear_cityhigh_highyear") ("`y'") ("`ev'") ///
                (`rel') (`b') (`se') (`t') (`p') (`preF') (`prep') ///
                (e(N)) (e(N_clust)) (`ntreated') (`mean_y')
        }
    }
}

postclose `handle'

use "`tables'/firm_tech_entry_ddd_event_results_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order eventdef spec outcome event rel coef se t p sig preF prep N N_city N_treated_city mean_y
export delimited using "`tables'/firm_tech_entry_ddd_event_results_20260525.csv", replace
list if inlist(event, "es_m2_high", "es_0_high", "es_p1_high", "es_p2_high", "es_p3_high"), ///
    noobs abbrev(28)

log close
