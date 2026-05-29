clear all
set more off
set linesize 255

local root "/Users/mac/computerscience/23实证选题探索/T10"
local panel "`root'/data/processed/overall_tech_entry_ddd_robustness_panel_2008_2023.dta"
local out "`root'/results/tables/overall_tech_ddd_rescue_results_20260528.dta"
local outcsv "`root'/results/tables/overall_tech_ddd_rescue_results_20260528.csv"
local log "`root'/results/logs/overall_tech_ddd_rescue_20260528.log"

capture log close _all
log using "`log'", text replace

capture which ppmlhdfe
if _rc {
    display as error "ppmlhdfe is required."
    exit 499
}
capture which reghdfe
if _rc {
    display as error "reghdfe is required."
    exit 499
}

use "`panel'", clear

gen double x_high = ln1p_idc_scope_stock_l1 * high_compute
label var x_high "ln(1+IDC scope stock lag) x HighCompute"

gen double ln_total_exp = ln(total_patents_field) if total_patents_field > 0
gen double ln_active_exp = ln(active_applicants_field) if active_applicants_field > 0

gen double city_new_applicant_rate_active = city_new_applicants_field / active_applicants_field if active_applicants_field > 0
gen double field_new_applicant_rate_active = field_new_applicants_field / active_applicants_field if active_applicants_field > 0
gen byte any_city_new_applicants = city_new_applicants_field > 0 if !missing(city_new_applicants_field)
gen byte any_city_new_patents = city_new_patents_field > 0 if !missing(city_new_patents_field)
gen byte any_field_new_applicants = field_new_applicants_field > 0 if !missing(field_new_applicants_field)
gen byte any_field_new_patents = field_new_patents_field > 0 if !missing(field_new_patents_field)

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
postfile `handle' str24 block str20 variant str32 applicant_sample str40 spec str44 outcome ///
    double coef se stat p N N_city mean_y converged using "`out'", replace

local variants broad no_h04 g06_g16_g10l g06_only
local samples all no_individual no_oneshot no_individual_no_oneshot
local count_outcomes city_new_applicants_field city_new_patents_field field_new_applicants_field field_new_patents_field
local rate_outcomes city_new_applicant_rate_active field_new_applicant_rate_active city_new_share_total_field field_new_share_total_field
local binary_outcomes any_city_new_applicants any_city_new_patents any_field_new_applicants any_field_new_patents

foreach v of local variants {
    foreach s of local samples {
        preserve
        keep if variant == "`v'" & sample == "`s'"

        foreach y of local count_outcomes {
            quietly summarize `y'
            local mean_y = r(mean)

            foreach spec in ppml_offset_total ppml_offset_active {
                if "`spec'" == "ppml_offset_total" {
                    local offsetvar ln_total_exp
                    local ifcond total_patents_field > 0
                }
                else {
                    local offsetvar ln_active_exp
                    local ifcond active_applicants_field > 0
                }

                capture noisily ppmlhdfe `y' x_high if `ifcond', ///
                    absorb(city_id#year city_id#high_compute year#high_compute) ///
                    vce(cluster city_id) offset(`offsetvar') nolog
                if !_rc {
                    local z = _b[x_high] / _se[x_high]
                    local p = 2 * normal(-abs(`z'))
                    capture local ncity = e(N_clust)
                    if _rc local ncity = .
                    post `handle' ("ddd_rescue") ("`v'") ("`s'") ("`spec'") ("`y'") ///
                        (_b[x_high]) (_se[x_high]) (`z') (`p') (e(N)) (`ncity') (`mean_y') (e(converged))
                }
                else {
                    post `handle' ("ddd_rescue") ("`v'") ("`s'") ("`spec'") ("`y'") ///
                        (.) (.) (.) (.) (.) (.) (`mean_y') (0)
                }

                capture noisily ppmlhdfe `y' x_high `policy_highs' if `ifcond', ///
                    absorb(city_id#year city_id#high_compute year#high_compute) ///
                    vce(cluster city_id) offset(`offsetvar') nolog
                if !_rc {
                    local z = _b[x_high] / _se[x_high]
                    local p = 2 * normal(-abs(`z'))
                    capture local ncity = e(N_clust)
                    if _rc local ncity = .
                    post `handle' ("ddd_rescue") ("`v'") ("`s'") ("`spec'_policy_x_high") ("`y'") ///
                        (_b[x_high]) (_se[x_high]) (`z') (`p') (e(N)) (`ncity') (`mean_y') (e(converged))
                }
                else {
                    post `handle' ("ddd_rescue") ("`v'") ("`s'") ("`spec'_policy_x_high") ("`y'") ///
                        (.) (.) (.) (.) (.) (.) (`mean_y') (0)
                }
            }
        }

        foreach y of local rate_outcomes {
            quietly summarize `y'
            local mean_y = r(mean)
            capture noisily reghdfe `y' x_high, ///
                absorb(city_id#year city_id#high_compute year#high_compute) ///
                vce(cluster city_id)
            if !_rc {
                local t = _b[x_high] / _se[x_high]
                local p = 2 * ttail(e(df_r), abs(`t'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("ddd_rescue") ("`v'") ("`s'") ("ols_rate_share") ("`y'") ///
                    (_b[x_high]) (_se[x_high]) (`t') (`p') (e(N)) (`ncity') (`mean_y') (1)
            }
            else {
                post `handle' ("ddd_rescue") ("`v'") ("`s'") ("ols_rate_share") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }

            capture noisily reghdfe `y' x_high `policy_highs', ///
                absorb(city_id#year city_id#high_compute year#high_compute) ///
                vce(cluster city_id)
            if !_rc {
                local t = _b[x_high] / _se[x_high]
                local p = 2 * ttail(e(df_r), abs(`t'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("ddd_rescue") ("`v'") ("`s'") ("ols_rate_share_policy_x_high") ("`y'") ///
                    (_b[x_high]) (_se[x_high]) (`t') (`p') (e(N)) (`ncity') (`mean_y') (1)
            }
            else {
                post `handle' ("ddd_rescue") ("`v'") ("`s'") ("ols_rate_share_policy_x_high") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }
        }

        foreach y of local binary_outcomes {
            quietly summarize `y'
            local mean_y = r(mean)
            capture noisily reghdfe `y' x_high, ///
                absorb(city_id#year city_id#high_compute year#high_compute) ///
                vce(cluster city_id)
            if !_rc {
                local t = _b[x_high] / _se[x_high]
                local p = 2 * ttail(e(df_r), abs(`t'))
                capture local ncity = e(N_clust)
                if _rc local ncity = .
                post `handle' ("ddd_rescue") ("`v'") ("`s'") ("ols_any_entry") ("`y'") ///
                    (_b[x_high]) (_se[x_high]) (`t') (`p') (e(N)) (`ncity') (`mean_y') (1)
            }
            else {
                post `handle' ("ddd_rescue") ("`v'") ("`s'") ("ols_any_entry") ("`y'") ///
                    (.) (.) (.) (.) (.) (.) (`mean_y') (0)
            }
        }
        restore
    }
}

postclose `handle'
use "`out'", clear
gen str3 sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order block variant applicant_sample spec outcome coef se stat p sig N N_city mean_y converged
save "`out'", replace
export delimited using "`outcsv'", replace

log close
