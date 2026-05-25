clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_firm_tech_entry_ddd_stata_20260525.log", text replace

use "`data'/firm_tech_entry_ddd_panel_2008_2023.dta", clear

egen city_year_id = group(city_id year)
egen city_high_id = group(city_id high_compute)
egen high_year_id = group(high_compute year)

gen idc_stock_high = ln1p_idc_scope_stock_l1 * high_compute
gen idc_new_high = ln1p_idc_scope_new_l1 * high_compute
gen idc_pre5_high = ln1p_idc_scope_pre5_l1 * high_compute

tempname handle
postfile `handle' ///
    str16 sample ///
    str24 spec ///
    str24 xvar ///
    str36 outcome ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    using "`tables'/firm_tech_entry_ddd_results_20260525.dta", replace

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
    ln_firm_act_f ///
    firm_share_f ///
    ln_tot_pat_f

local xvars idc_stock_high idc_new_high idc_pre5_high

foreach sample in all min20 min50 {
    preserve
    if "`sample'" == "min20" {
        keep if total_patents >= 20
    }
    if "`sample'" == "min50" {
        keep if total_patents >= 50
    }

    foreach x of local xvars {
        foreach y of local outcomes {
            quietly reghdfe `y' `x', ///
                absorb(city_year_id city_high_id high_year_id) ///
                vce(cluster city_id)
            local b = _b[`x']
            local se = _se[`x']
            local t = `b' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            quietly summarize `y' if e(sample)
            local mean_y = r(mean)
            post `handle' ("`sample'") ("cityyear_cityhigh_highyear") ("`x'") ("`y'") ///
                (`b') (`se') (`t') (`p') (e(N)) (e(N_clust)) (`mean_y')
        }
    }
    restore
}

postclose `handle'

use "`tables'/firm_tech_entry_ddd_results_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order sample spec xvar outcome coef se t p sig N N_city mean_y
export delimited using "`tables'/firm_tech_entry_ddd_results_20260525.csv", replace
list if sample == "all" & xvar == "idc_stock_high", noobs abbrev(28)

log close
