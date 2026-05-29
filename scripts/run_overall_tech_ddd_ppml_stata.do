clear all
set more off
set linesize 255

local root "/Users/mac/computerscience/23实证选题探索/T10"
local panel "`root'/data/processed/overall_tech_entry_ddd_robustness_panel_2008_2023.dta"
local out "`root'/results/tables/overall_tech_ddd_ppml_results_20260528.dta"
local outcsv "`root'/results/tables/overall_tech_ddd_ppml_results_20260528.csv"
local log "`root'/results/logs/overall_tech_ddd_ppml_20260528.log"

capture log close _all
log using "`log'", text replace

capture which ppmlhdfe
if _rc {
    display as error "ppmlhdfe is required. Install with: net install ppmlhdfe, from(https://raw.githubusercontent.com/sergiocorreia/ppmlhdfe/master/src/)"
    exit 499
}

use "`panel'", clear

gen double x_high = ln1p_idc_scope_stock_l1 * high_compute
label var x_high "ln(1+IDC scope stock lag) x HighCompute"

local policy_list broadband_china_pilot smart_city_pilot bigdata_comprehensive_pilot innovative_city_pilot national_hightech_zone ip_demo_city information_consumption_pilot ecommerce_demo_city
local policy_highs
foreach p of local policy_list {
    capture confirm variable `p'
    if !_rc {
        quietly summarize `p'
        if r(min) < r(max) {
            gen double `p'_high = `p' * high_compute
            local policy_highs `policy_highs' `p'_high
        }
    }
}

tempname handle
postfile `handle' str24 block str20 variant str32 applicant_sample str36 spec str40 outcome ///
    double coef se z p N N_city mean_y converged using "`out'", replace

local variants broad no_h04 g06_g16_g10l g06_only
local samples all no_individual no_oneshot no_individual_no_oneshot
local outcomes city_new_applicants_field city_new_patents_field field_new_applicants_field field_new_patents_field

foreach v of local variants {
    foreach s of local samples {
        preserve
        keep if variant == "`v'" & sample == "`s'"
        foreach y of local outcomes {
            quietly summarize `y'
            local mean_y = r(mean)

            capture noisily ppmlhdfe `y' x_high, ///
                absorb(city_id#year city_id#high_compute year#high_compute) ///
                vce(cluster city_id) nolog
            if !_rc {
                local z = _b[x_high] / _se[x_high]
                local p = 2 * normal(-abs(`z'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("ppml_ddd") ("`v'") ("`s'") ("ppml_hdfe") ("`y'") ///
                    (_b[x_high]) (_se[x_high]) (`z') (`p') (e(N)) (`ncity') (`mean_y') (e(converged))
            }
            else {
                post `handle' ("ppml_ddd") ("`v'") ("`s'") ("ppml_hdfe") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }

            capture noisily ppmlhdfe `y' x_high `policy_highs', ///
                absorb(city_id#year city_id#high_compute year#high_compute) ///
                vce(cluster city_id) nolog
            if !_rc {
                local z = _b[x_high] / _se[x_high]
                local p = 2 * normal(-abs(`z'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("ppml_ddd") ("`v'") ("`s'") ("ppml_hdfe_policy_x_high") ("`y'") ///
                    (_b[x_high]) (_se[x_high]) (`z') (`p') (e(N)) (`ncity') (`mean_y') (e(converged))
            }
            else {
                post `handle' ("ppml_ddd") ("`v'") ("`s'") ("ppml_hdfe_policy_x_high") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }
        }
        restore
    }
}

postclose `handle'
use "`out'", clear
gen str3 sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order block variant applicant_sample spec outcome coef se z p sig N N_city mean_y converged
save "`out'", replace
export delimited using "`outcsv'", replace

log close
