clear all
set more off

local root "/Users/mac/computerscience/23实证选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_ajg3_minimal_upgrade_stata_20260525.log", text replace

local x ln1p_idc_scope_stock_l1

tempname h
postfile `h' ///
    str24 block ///
    str32 sample ///
    str32 spec ///
    str36 xvar ///
    str42 outcome ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    using "`tables'/ajg3_minimal_upgrade_results_20260525.dta", replace

* ---------------------------------------------------------------------
* 1. Overall applicant x high-compute field DDD
* ---------------------------------------------------------------------
use "`data'/overall_tech_entry_ddd_panel_2008_2023.dta", clear
egen city_year_id = group(city_id year)
egen city_high_id = group(city_id high_compute)
egen high_year_id = group(high_compute year)

local ddd_outcomes ///
    ln1p_city_new_applicants_field ///
    ln1p_city_new_patents_field ///
    city_new_share_total_field ///
    ln1p_field_new_applicants_field ///
    ln1p_field_new_patents_field ///
    field_new_share_total_field ///
    ln1p_total_patents_field ///
    ln1p_incumbent_patents_field

foreach sample in all min20 min50 {
    preserve
    if "`sample'" == "min20" {
        keep if total_patents >= 20
    }
    if "`sample'" == "min50" {
        keep if total_patents >= 50
    }
    foreach y of local ddd_outcomes {
        quietly reghdfe `y' idc_stock_high, ///
            absorb(city_year_id city_high_id high_year_id) ///
            vce(cluster city_id)
        local b = _b[idc_stock_high]
        local se = _se[idc_stock_high]
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        post `h' ("overall_tech_ddd") ("`sample'") ("cityyear_cityhigh_highyear") ///
            ("idc_stock_high") ("`y'") ///
            (`b') (`se') (`t') (`p') (e(N)) (e(N_clust)) (`mean_y')
    }
    restore
}

* ---------------------------------------------------------------------
* 2. Low-compute field placebo: within non-high-compute fields only
* ---------------------------------------------------------------------
use "`data'/overall_tech_entry_ddd_panel_2008_2023.dta", clear
keep if high_compute == 0

local low_outcomes ///
    city_new_share_total_field ///
    ln1p_city_new_applicants_field ///
    ln1p_city_new_patents_field ///
    field_new_share_total_field ///
    ln1p_field_new_applicants_field ///
    ln1p_field_new_patents_field

foreach y of local low_outcomes {
    quietly areg `y' `x' i.province_id#i.year ///
        i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
        absorb(city_id) vce(cluster city_id)
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
    post `h' ("low_compute_placebo") ("all") ("provyr_baseyr_fe") ///
        ("`x'") ("`y'") ///
        (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
    drop `es' `tag'
}

* ---------------------------------------------------------------------
* 3. Time placebo: use future IDC coverage as fake early treatment
* ---------------------------------------------------------------------
use "`data'/idc_scope_formal_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"
xtset city_id year
gen ln1p_new_patents = ln(1 + new_patents)
gen x_lead3 = F3.`x'
gen x_lead5 = F5.`x'

local time_outcomes new_applicant_share ln1p_new_applicants ln1p_new_patents ln1p_total_patents
foreach lead in x_lead3 x_lead5 {
    foreach y of local time_outcomes {
        quietly areg `y' `lead' i.province_id#i.year ///
            i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
            absorb(city_id) vce(cluster city_id)
        local b = _b[`lead']
        local se = _se[`lead']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es tag
        quietly gen byte `es' = e(sample)
        quietly egen byte `tag' = tag(city_id) if `es'
        quietly count if `tag' == 1
        local nc = r(N)
        post `h' ("time_placebo") ("all") ("provyr_baseyr_fe") ///
            ("`lead'") ("`y'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es' `tag'
    }
}

* ---------------------------------------------------------------------
* 4. Organization-only entry quality check
* ---------------------------------------------------------------------
use "`data'/idc_scope_formal_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"
merge 1:1 city year using "`data'/org_applicant_concentration_clean_panel_2008_2023.dta", ///
    keep(match master) nogen

gen org_new_share_org = org_new_patents / org_total_patents if org_total_patents > 0
gen ln1p_org_new_patents = ln(1 + org_new_patents)

local org_outcomes ///
    org_new_share ///
    org_new_share_org ///
    org_patent_share_total ///
    ln1p_org_new_applicants ///
    ln1p_org_new_patents ///
    ln1p_org_total_patents

foreach y of local org_outcomes {
    quietly areg `y' `x' i.province_id#i.year ///
        i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
        absorb(city_id) vce(cluster city_id)
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
    post `h' ("org_quality") ("all") ("provyr_baseyr_fe") ///
        ("`x'") ("`y'") ///
        (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
    drop `es' `tag'
}

* ---------------------------------------------------------------------
* 5. Invention grant/publication quality robustness
* ---------------------------------------------------------------------
use "`data'/idc_scope_pubyear_quality_panel_2008_2024.dta", clear
keep if merge_idc_split == "both"

local quality_outcomes new_applicant_share ln1p_new_applicants ln1p_new_patents ln1p_total_patents
foreach scope_name in inv_app_pub inv_grant_pub all_pub {
    foreach ymax in 2021 2023 {
        preserve
        keep if scope == "`scope_name'"
        keep if year <= `ymax'
        foreach y of local quality_outcomes {
            quietly areg `y' `x' i.province_id#i.year ///
                i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
                absorb(city_id) vce(cluster city_id)
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
            post `h' ("pubyear_quality") ("`scope_name'_le`ymax'") ("provyr_baseyr_fe") ///
                ("`x'") ("`y'") ///
                (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
            drop `es' `tag'
        }
        restore
    }
}

postclose `h'

use "`tables'/ajg3_minimal_upgrade_results_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order block sample spec xvar outcome coef se t p sig N N_city mean_y
export delimited using "`tables'/ajg3_minimal_upgrade_results_20260525.csv", replace

list if block == "overall_tech_ddd" & sample == "all", noobs abbrev(28)
list if block == "low_compute_placebo", noobs abbrev(28)
list if block == "time_placebo", noobs abbrev(28)
list if block == "org_quality", noobs abbrev(28)
list if block == "pubyear_quality", noobs abbrev(28)

log close
