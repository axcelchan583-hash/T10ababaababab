clear all
set more off

local root "/Users/mac/computerscience/23实证选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_entry_mechanism_heterogeneity_stata_20260525.log", text replace

use "`data'/idc_scope_formal_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"

merge 1:1 city year using "`data'/entry_type_mechanism_panel_2008_2023.dta", ///
    keep(match master) nogen

local x ln1p_idc_scope_stock_l1

tempname h1
postfile `h1' ///
    str20 table ///
    str16 sample ///
    str28 spec ///
    str36 outcome ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    using "`tables'/entry_mechanism_results_20260525.dta", replace

local decomp_outcomes ///
    new_applicant_share ///
    ln1p_new_applicants ///
    ln_new_patents ///
    ln1p_total_patents ///
    ln_incumbent_patents ///
    incumbent_share ///
    ln1p_active_applicants ///
    ln_incumbent_applicants

local type_outcomes ///
    firm_new_share_total ///
    ln_firm_new_n ///
    ln_firm_new_pat ///
    firm_new_share_new ///
    knowledge_new_share_total ///
    ln_knowledge_new_n ///
    ln_knowledge_new_pat ///
    knowledge_new_share_new ///
    individual_new_share_total ///
    ln_individual_new_n ///
    ln_individual_new_pat ///
    individual_new_share_new ///
    org_new_share_total ///
    ln_org_new_n ///
    ln_org_new_pat ///
    org_new_share_new

foreach sample in all min20 min50 {
    preserve
    if "`sample'" == "min20" {
        keep if total_patents >= 20
    }
    if "`sample'" == "min50" {
        keep if total_patents >= 50
    }

    foreach y of local decomp_outcomes {
        quietly areg `y' `x' i.province_id#i.year, absorb(city_id) vce(cluster city_id)
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
        post `h1' ("decomp") ("`sample'") ("province_year_fe") ("`y'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es' `tag'

        quietly areg `y' `x' i.province_id#i.year ///
            i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
            absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es2 tag2
        quietly gen byte `es2' = e(sample)
        quietly egen byte `tag2' = tag(city_id) if `es2'
        quietly count if `tag2' == 1
        local nc = r(N)
        post `h1' ("decomp") ("`sample'") ("provyr_baseyr_fe") ("`y'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es2' `tag2'
    }

    foreach y of local type_outcomes {
        quietly areg `y' `x' i.province_id#i.year, absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es3 tag3
        quietly gen byte `es3' = e(sample)
        quietly egen byte `tag3' = tag(city_id) if `es3'
        quietly count if `tag3' == 1
        local nc = r(N)
        post `h1' ("type") ("`sample'") ("province_year_fe") ("`y'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es3' `tag3'

        quietly areg `y' `x' i.province_id#i.year ///
            i.base_ln_patents_q#i.year i.base_top10_q#i.year, ///
            absorb(city_id) vce(cluster city_id)
        local b = _b[`x']
        local se = _se[`x']
        local t = `b' / `se'
        local p = 2 * ttail(e(df_r), abs(`t'))
        quietly summarize `y' if e(sample)
        local mean_y = r(mean)
        tempvar es4 tag4
        quietly gen byte `es4' = e(sample)
        quietly egen byte `tag4' = tag(city_id) if `es4'
        quietly count if `tag4' == 1
        local nc = r(N)
        post `h1' ("type") ("`sample'") ("provyr_baseyr_fe") ("`y'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es4' `tag4'
    }
    restore
}

postclose `h1'

use "`tables'/entry_mechanism_results_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order table sample spec outcome coef se t p sig N N_city mean_y
export delimited using "`tables'/entry_mechanism_results_20260525.csv", replace
list if sample == "all", noobs abbrev(28)

use "`data'/idc_scope_formal_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"
merge 1:1 city year using "`data'/entry_type_mechanism_panel_2008_2023.dta", ///
    keep(match master) nogen

gen byte high_base_patents = base_ln_patents_q >= 3 if base_ln_patents_q < .
gen byte high_base_top10 = base_top10_q >= 3 if base_top10_q < .
gen byte high_base_hhi = base_hhi_q >= 3 if base_hhi_q < .
gen byte high_base_active = base_active_q >= 3 if base_active_q < .

tempname h2
postfile `h2' ///
    str28 hetvar ///
    str28 outcome ///
    double low_effect interaction high_effect ///
    double se_low se_interaction se_high ///
    double p_low p_interaction p_high ///
    long N N_city ///
    using "`tables'/entry_heterogeneity_results_20260525.dta", replace

local hetvars ///
    high_base_patents ///
    high_base_top10 ///
    high_base_hhi ///
    high_base_active ///
    high_base_firm_share ///
    high_base_knowledge_share ///
    high_base_individual_share ///
    high_base_org_share

local het_outcomes ///
    new_applicant_share ///
    ln1p_new_applicants ///
    ln_new_patents

foreach h of local hetvars {
    foreach y of local het_outcomes {
        quietly areg `y' c.`x'##i.`h' i.province_id#i.year i.`h'#i.year, ///
            absorb(city_id) vce(cluster city_id)
        local b_low = _b[`x']
        local se_low = _se[`x']
        local t_low = `b_low' / `se_low'
        local p_low = 2 * ttail(e(df_r), abs(`t_low'))
        local b_int = _b[1.`h'#c.`x']
        local se_int = _se[1.`h'#c.`x']
        local t_int = `b_int' / `se_int'
        local p_int = 2 * ttail(e(df_r), abs(`t_int'))
        lincom `x' + 1.`h'#c.`x'
        local b_high = r(estimate)
        local se_high = r(se)
        local p_high = r(p)
        tempvar es tag
        quietly gen byte `es' = e(sample)
        quietly egen byte `tag' = tag(city_id) if `es'
        quietly count if `tag' == 1
        local nc = r(N)
        post `h2' ("`h'") ("`y'") ///
            (`b_low') (`b_int') (`b_high') ///
            (`se_low') (`se_int') (`se_high') ///
            (`p_low') (`p_int') (`p_high') ///
            (e(N)) (`nc')
        drop `es' `tag'
    }
}

postclose `h2'

use "`tables'/entry_heterogeneity_results_20260525.dta", clear
gen sig_low = cond(p_low < 0.01, "***", cond(p_low < 0.05, "**", cond(p_low < 0.1, "*", "")))
gen sig_interaction = cond(p_interaction < 0.01, "***", cond(p_interaction < 0.05, "**", cond(p_interaction < 0.1, "*", "")))
gen sig_high = cond(p_high < 0.01, "***", cond(p_high < 0.05, "**", cond(p_high < 0.1, "*", "")))
order hetvar outcome low_effect interaction high_effect se_low se_interaction se_high p_low p_interaction p_high sig_low sig_interaction sig_high N N_city
export delimited using "`tables'/entry_heterogeneity_results_20260525.csv", replace
list, noobs abbrev(28)

log close
