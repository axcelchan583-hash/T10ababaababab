clear all
set more off
set linesize 255

local root "/Users/mac/computerscience/23实证选题探索/T10"
local panel "`root'/data/processed/new_y_smoke_panel_2008_2023.dta"
local out "`root'/results/tables/new_y_smoke_results_20260528.dta"
local outcsv "`root'/results/tables/new_y_smoke_results_20260528.csv"
local log "`root'/results/logs/new_y_smoke_tests_20260528.log"

capture log close _all
log using "`log'", text replace

capture which reghdfe
if _rc {
    display as error "reghdfe is required."
    exit 499
}
capture which ppmlhdfe
if _rc {
    display as error "ppmlhdfe is required."
    exit 499
}

use "`panel'", clear

local x ln1p_idc_scope_stock_l1
local policies broadband_china_pilot smart_city_pilot bigdata_comprehensive_pilot innovative_city_pilot national_hightech_zone ip_demo_city information_consumption_pilot ecommerce_demo_city

local count_sustained surv2_applicants surv3_applicants surv2_entry_patents surv3_entry_patents surv2_future_patents surv3_future_patents
local count_quality qgrant_new_n qgrant_new_pat qgrantyr_new_n qgrantyr_new_pat qcited_new_n qcited_new_pat qfcited_new_n qfcited_new_pat
local share_sustained surv2_applicant_rate surv3_applicant_rate surv2_entry_pat_share_new surv3_entry_pat_share_new surv2_entry_pat_share_total surv3_entry_pat_share_total
local share_top top10_turnover_prev_share top20_turnover_prev_share top10_turnover_base_share top20_turnover_base_share top10_turnover_prev_pat_share top20_turnover_prev_pat_share top10_turnover_base_pat_share top20_turnover_base_pat_share top10_persistence_prev_share top20_persistence_prev_share top10_persistence_base_share top20_persistence_base_share
local share_quality qgrant_share_total qgrant_share_new qgrantyr_share_total qgrantyr_share_new qcited_share_total qcited_share_new qfcited_share_total qfcited_share_new

tempname handle
postfile `handle' str24 family str24 outcome_type str16 sample str28 spec str40 outcome ///
    double coef se stat p N N_city mean_y converged using "`out'", replace

local samples all min20 min50

foreach sample of local samples {
    local ifsample "1"
    if "`sample'" == "min20" local ifsample "total_patents >= 20"
    if "`sample'" == "min50" local ifsample "total_patents >= 50"

    foreach y of local count_sustained {
        quietly summarize `y' if `ifsample'
        local mean_y = r(mean)

        foreach spec in city_year provyr_base provyr_base_policy {
            if "`spec'" == "city_year" local absorb city_id year
            if "`spec'" == "provyr_base" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local rhs `x' `policies'
            else local rhs `x'

            capture noisily ppmlhdfe `y' `rhs' if `ifsample', absorb(`absorb') vce(cluster city_id) nolog
            if !_rc {
                local z = _b[`x'] / _se[`x']
                local pval = 2 * normal(-abs(`z'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("sustained_entry") ("count_ppml") ("`sample'") ("`spec'") ("`y'") ///
                    (_b[`x']) (_se[`x']) (`z') (`pval') (e(N)) (`ncity') (`mean_y') (e(converged))
            }
            else {
                post `handle' ("sustained_entry") ("count_ppml") ("`sample'") ("`spec'") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }
        }
    }

    foreach y of local count_quality {
        quietly summarize `y' if `ifsample'
        local mean_y = r(mean)

        foreach spec in city_year provyr_base provyr_base_policy {
            if "`spec'" == "city_year" local absorb city_id year
            if "`spec'" == "provyr_base" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local rhs `x' `policies'
            else local rhs `x'

            capture noisily ppmlhdfe `y' `rhs' if `ifsample', absorb(`absorb') vce(cluster city_id) nolog
            if !_rc {
                local z = _b[`x'] / _se[`x']
                local pval = 2 * normal(-abs(`z'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("quality_entry") ("count_ppml") ("`sample'") ("`spec'") ("`y'") ///
                    (_b[`x']) (_se[`x']) (`z') (`pval') (e(N)) (`ncity') (`mean_y') (e(converged))
            }
            else {
                post `handle' ("quality_entry") ("count_ppml") ("`sample'") ("`spec'") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }
        }
    }

    foreach y of local share_sustained {
        quietly summarize `y' if `ifsample'
        local mean_y = r(mean)

        foreach spec in city_year provyr_base provyr_base_policy {
            if "`spec'" == "city_year" local absorb city_id year
            if "`spec'" == "provyr_base" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local rhs `x' `policies'
            else local rhs `x'

            capture noisily reghdfe `y' `rhs' if `ifsample', absorb(`absorb') vce(cluster city_id)
            if !_rc {
                local t = _b[`x'] / _se[`x']
                local pval = 2 * ttail(e(df_r), abs(`t'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("sustained_entry") ("share_rate_ols") ("`sample'") ("`spec'") ("`y'") ///
                    (_b[`x']) (_se[`x']) (`t') (`pval') (e(N)) (`ncity') (`mean_y') (1)
            }
            else {
                post `handle' ("sustained_entry") ("share_rate_ols") ("`sample'") ("`spec'") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }
        }
    }

    foreach y of local share_top {
        quietly summarize `y' if `ifsample'
        local mean_y = r(mean)

        foreach spec in city_year provyr_base provyr_base_policy {
            if "`spec'" == "city_year" local absorb city_id year
            if "`spec'" == "provyr_base" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local rhs `x' `policies'
            else local rhs `x'

            capture noisily reghdfe `y' `rhs' if `ifsample', absorb(`absorb') vce(cluster city_id)
            if !_rc {
                local t = _b[`x'] / _se[`x']
                local pval = 2 * ttail(e(df_r), abs(`t'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("top_mobility") ("share_rate_ols") ("`sample'") ("`spec'") ("`y'") ///
                    (_b[`x']) (_se[`x']) (`t') (`pval') (e(N)) (`ncity') (`mean_y') (1)
            }
            else {
                post `handle' ("top_mobility") ("share_rate_ols") ("`sample'") ("`spec'") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }
        }
    }

    foreach y of local share_quality {
        quietly summarize `y' if `ifsample'
        local mean_y = r(mean)

        foreach spec in city_year provyr_base provyr_base_policy {
            if "`spec'" == "city_year" local absorb city_id year
            if "`spec'" == "provyr_base" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local absorb city_id province_id#year base_ln_patents_q#year base_top10_q#year
            if "`spec'" == "provyr_base_policy" local rhs `x' `policies'
            else local rhs `x'

            capture noisily reghdfe `y' `rhs' if `ifsample', absorb(`absorb') vce(cluster city_id)
            if !_rc {
                local t = _b[`x'] / _se[`x']
                local pval = 2 * ttail(e(df_r), abs(`t'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("quality_entry") ("share_rate_ols") ("`sample'") ("`spec'") ("`y'") ///
                    (_b[`x']) (_se[`x']) (`t') (`pval') (e(N)) (`ncity') (`mean_y') (1)
            }
            else {
                post `handle' ("quality_entry") ("share_rate_ols") ("`sample'") ("`spec'") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }
        }
    }
}

postclose `handle'
use "`out'", clear
gen str3 sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order family outcome_type sample spec outcome coef se stat p sig N N_city mean_y converged
save "`out'", replace
export delimited using "`outcsv'", replace

log close
