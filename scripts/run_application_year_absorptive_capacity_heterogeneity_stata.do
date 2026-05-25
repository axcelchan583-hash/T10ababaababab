clear all
set more off

local root "/Users/mac/computerscience/23选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_application_year_absorptive_capacity_heterogeneity_stata_20260524.log", text replace

use "`data'/idc_applicant_concentration_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc == "both"

gen byte high_base_patents = base_ln_patents_q >= 3 if base_ln_patents_q < .
gen byte high_base_top10 = base_top10_q >= 3 if base_top10_q < .
gen byte high_base_hhi = base_hhi_q >= 3 if base_hhi_q < .

tempname handle
postfile `handle' ///
    str24 hetvar ///
    str24 spec ///
    str32 outcome ///
    double low_effect interaction high_effect ///
    double se_low se_interaction se_high ///
    double p_low p_interaction p_high ///
    long N N_city ///
    using "`tables'/idc_applicant_concentration_application_year_absorptive_heterogeneity_20260524.dta", replace

local outcomes ///
    ln1p_new_applicants ///
    new_applicant_share ///
    hhi ///
    top10_share ///
    base_top_share ///
    base_mid_inc_share

local hetvars high_base_patents high_base_top10 high_base_hhi

foreach h of local hetvars {
    foreach y of local outcomes {
        quietly areg `y' c.ln1p_idc_stock_l1##i.`h' i.province_id#i.year, ///
            absorb(city_id) vce(cluster city_id)
        local b_low = _b[ln1p_idc_stock_l1]
        local se_low = _se[ln1p_idc_stock_l1]
        local t_low = `b_low' / `se_low'
        local p_low = 2 * ttail(e(df_r), abs(`t_low'))
        local b_int = _b[1.`h'#c.ln1p_idc_stock_l1]
        local se_int = _se[1.`h'#c.ln1p_idc_stock_l1]
        local t_int = `b_int' / `se_int'
        local p_int = 2 * ttail(e(df_r), abs(`t_int'))
        lincom ln1p_idc_stock_l1 + 1.`h'#c.ln1p_idc_stock_l1
        local b_high = r(estimate)
        local se_high = r(se)
        local p_high = r(p)
        tempvar es tag
        quietly gen byte `es' = e(sample)
        quietly egen byte `tag' = tag(city_id) if `es'
        quietly count if `tag' == 1
        local nc = r(N)
        post `handle' ("`h'") ("province_year_fe") ("`y'") ///
            (`b_low') (`b_int') (`b_high') ///
            (`se_low') (`se_int') (`se_high') ///
            (`p_low') (`p_int') (`p_high') ///
            (e(N)) (`nc')
        drop `es' `tag'

        quietly areg `y' c.ln1p_idc_stock_l1##i.`h' i.province_id#i.year i.`h'#i.year, ///
            absorb(city_id) vce(cluster city_id)
        local b_low = _b[ln1p_idc_stock_l1]
        local se_low = _se[ln1p_idc_stock_l1]
        local t_low = `b_low' / `se_low'
        local p_low = 2 * ttail(e(df_r), abs(`t_low'))
        local b_int = _b[1.`h'#c.ln1p_idc_stock_l1]
        local se_int = _se[1.`h'#c.ln1p_idc_stock_l1]
        local t_int = `b_int' / `se_int'
        local p_int = 2 * ttail(e(df_r), abs(`t_int'))
        lincom ln1p_idc_stock_l1 + 1.`h'#c.ln1p_idc_stock_l1
        local b_high = r(estimate)
        local se_high = r(se)
        local p_high = r(p)
        tempvar es2 tag2
        quietly gen byte `es2' = e(sample)
        quietly egen byte `tag2' = tag(city_id) if `es2'
        quietly count if `tag2' == 1
        local nc = r(N)
        post `handle' ("`h'") ("provyr_het_year_fe") ("`y'") ///
            (`b_low') (`b_int') (`b_high') ///
            (`se_low') (`se_int') (`se_high') ///
            (`p_low') (`p_int') (`p_high') ///
            (e(N)) (`nc')
        drop `es2' `tag2'
    }
}

postclose `handle'

use "`tables'/idc_applicant_concentration_application_year_absorptive_heterogeneity_20260524.dta", clear
gen sig_low = cond(p_low < 0.01, "***", cond(p_low < 0.05, "**", cond(p_low < 0.1, "*", "")))
gen sig_interaction = cond(p_interaction < 0.01, "***", cond(p_interaction < 0.05, "**", cond(p_interaction < 0.1, "*", "")))
gen sig_high = cond(p_high < 0.01, "***", cond(p_high < 0.05, "**", cond(p_high < 0.1, "*", "")))
order hetvar spec outcome low_effect interaction high_effect se_low se_interaction se_high p_low p_interaction p_high sig_low sig_interaction sig_high N N_city
export delimited using "`tables'/idc_applicant_concentration_application_year_absorptive_heterogeneity_20260524.csv", replace

list, noobs abbrev(24)

log close
