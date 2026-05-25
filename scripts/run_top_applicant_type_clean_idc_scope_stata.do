clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_top_applicant_type_clean_idc_scope_stata_20260525.log", text replace

use "`data'/idc_scope_formal_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"

local typevars ///
    cur_top_patents base_top_patents ///
    cur_top_firm_share_total cur_top_univ_share_total cur_top_research_share_total ///
    cur_top_hospital_share_total cur_top_individual_share_total ///
    cur_top_knowledge_share_total cur_top_org_share_total ///
    base_top_firm_share_total base_top_univ_share_total base_top_research_share_total ///
    base_top_hospital_share_total base_top_individual_share_total ///
    base_top_knowledge_share_total base_top_org_share_total ///
    cur_top_firm_share_top cur_top_univ_share_top cur_top_research_share_top ///
    cur_top_individual_share_top cur_top_knowledge_share_top cur_top_org_share_top ///
    base_top_firm_share_base base_top_univ_share_base base_top_research_share_base ///
    base_top_individual_share_base base_top_knowledge_share_base base_top_org_share_base

merge 1:1 city year using "`data'/top_applicant_type_clean_panel_2008_2023.dta", ///
    keep(match master) nogen keepusing(`typevars')

tempname handle
postfile `handle' ///
    str16 sample ///
    str28 spec ///
    str36 outcome ///
    double coef se t p ///
    long N N_city ///
    double mean_y ///
    using "`tables'/top_applicant_type_clean_idc_scope_results_20260525.dta", replace

local outcomes_total ///
    cur_top_firm_share_total ///
    cur_top_univ_share_total ///
    cur_top_research_share_total ///
    cur_top_hospital_share_total ///
    cur_top_individual_share_total ///
    cur_top_knowledge_share_total ///
    cur_top_org_share_total ///
    base_top_firm_share_total ///
    base_top_univ_share_total ///
    base_top_research_share_total ///
    base_top_hospital_share_total ///
    base_top_individual_share_total ///
    base_top_knowledge_share_total ///
    base_top_org_share_total

local outcomes_within ///
    cur_top_firm_share_top ///
    cur_top_univ_share_top ///
    cur_top_research_share_top ///
    cur_top_individual_share_top ///
    cur_top_knowledge_share_top ///
    cur_top_org_share_top ///
    base_top_firm_share_base ///
    base_top_univ_share_base ///
    base_top_research_share_base ///
    base_top_individual_share_base ///
    base_top_knowledge_share_base ///
    base_top_org_share_base

local outcomes `outcomes_total' `outcomes_within'
local x ln1p_idc_scope_stock_l1

foreach sample in all min20 min50 {
    preserve
    if "`sample'" == "min20" {
        keep if total_patents >= 20
    }
    if "`sample'" == "min50" {
        keep if total_patents >= 50
    }

    foreach y of local outcomes {
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
        post `handle' ("`sample'") ("province_year_fe") ("`y'") ///
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
        post `handle' ("`sample'") ("provyr_baseyr_fe") ("`y'") ///
            (`b') (`se') (`t') (`p') (e(N)) (`nc') (`mean_y')
        drop `es2' `tag2'
    }
    restore
}

postclose `handle'

use "`tables'/top_applicant_type_clean_idc_scope_results_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order sample spec outcome coef se t p sig N N_city mean_y
export delimited using "`tables'/top_applicant_type_clean_idc_scope_results_20260525.csv", replace
list if sample == "all" & (spec == "province_year_fe" | spec == "provyr_baseyr_fe"), noobs abbrev(28)

log close
