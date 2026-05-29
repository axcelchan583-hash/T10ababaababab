clear all
set more off
set linesize 255

local root "/Users/mac/computerscience/23实证选题探索/T10"
local panel "`root'/data/processed/top_turnover_type_panel_2008_2023.dta"
local out "`root'/results/tables/top_turnover_type_results_20260529.dta"
local outcsv "`root'/results/tables/top_turnover_type_results_20260529.csv"
local log "`root'/results/logs/top_turnover_type_20260529.log"

capture log close _all
log using "`log'", text replace

capture which reghdfe
if _rc {
    display as error "reghdfe is required."
    exit 499
}

use "`panel'", clear

local x ln1p_idc_scope_stock_l1
local policies broadband_china_pilot smart_city_pilot bigdata_comprehensive_pilot innovative_city_pilot national_hightech_zone ip_demo_city information_consumption_pilot ecommerce_demo_city

local outcomes ///
    t10_new_firm_top ///
    t10_new_ind_top ///
    t10_new_org_top ///
    t10_new_kn_top ///
    t10_new_univ_top ///
    t10_new_res_top ///
    t20_new_firm_top ///
    t20_new_ind_top ///
    t20_new_org_top ///
    t20_new_kn_top ///
    t20_new_univ_top ///
    t20_new_res_top

tempname handle
postfile `handle' str16 sample str28 spec str44 outcome ///
    double coef se t p N N_city mean_y using "`out'", replace

foreach sample in all min20 min50 {
    local ifsample "1"
    if "`sample'" == "min20" local ifsample "total_patents >= 20"
    if "`sample'" == "min50" local ifsample "total_patents >= 50"

    foreach y of local outcomes {
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
                post `handle' ("`sample'") ("`spec'") ("`y'") ///
                    (_b[`x']) (_se[`x']) (`t') (`pval') (e(N)) (`ncity') (`mean_y')
            }
            else {
                post `handle' ("`sample'") ("`spec'") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y')
            }
        }
    }
}

postclose `handle'

use "`out'", clear
gen str3 sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order sample spec outcome coef se t p sig N N_city mean_y
save "`out'", replace
export delimited using "`outcsv'", replace

log close
