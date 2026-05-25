clear all
set more off

local root "/Users/mac/computerscience/23实证选题探索/T10"
local data "`root'/data/processed"
local tables "`root'/results/tables"
local logs "`root'/results/logs"

capture log close
log using "`logs'/run_idc_scope_modern_did_stata_20260525.log", text replace

use "`data'/idc_scope_formal_application_year_panel_2008_2023.dta", clear
keep if scope == "inv_app_appyear"
keep if merge_idc_split == "both"
gen ln1p_new_patents = ln(1 + new_patents)

gen byte treat_scope2 = idc_scope_stock >= 2 if !missing(idc_scope_stock)
bysort city_id: egen first_scope2 = min(cond(treat_scope2 == 1, year, .))
gen first_scope2_csdid = first_scope2
replace first_scope2_csdid = 0 if missing(first_scope2_csdid)
gen first_scope2_bjs = first_scope2
replace first_scope2_bjs = . if first_scope2_bjs == 0

tempvar treated_tag
egen byte `treated_tag' = tag(city_id) if !missing(first_scope2_bjs)
quietly count if `treated_tag' == 1
local n_treated_city = r(N)

tempname h
postfile `h' ///
    str18 estimator ///
    str16 eventdef ///
    str36 spec ///
    str42 outcome ///
    str16 term ///
    double rel coef se t p ///
    long N N_city N_treated_city ///
    double pre_p ///
    using "`tables'/idc_scope_modern_did_20260525.dta", replace

local outcomes new_applicant_share ln1p_new_applicants ln1p_new_patents ln1p_total_patents

foreach y of local outcomes {
    quietly summarize `y'
    local yN = r(N)
    quietly egen byte tag_city_`y' = tag(city_id) if !missing(`y')
    quietly count if tag_city_`y' == 1
    local yC = r(N)

    * Callaway-Sant'Anna: simpler cohort-robust dynamic DiD.
    capture noisily csdid `y' c.base_ln_patents c.base_top10 i.province_id, ///
        ivar(city_id) time(year) gvar(first_scope2_csdid) method(reg) notyet
    if _rc == 0 {
        capture noisily estat pretrend
        local prep = .
        capture local prep = r(p)
        capture noisily estat event, window(-3 4) post
        if _rc == 0 {
            matrix b = e(b)
            matrix V = e(V)
            local cn : colnames b
            local k = 0
            foreach term of local cn {
                local ++k
                local rel = .
                if regexm("`term'", "^Tm([0-9]+)$") {
                    local rel = -real(regexs(1))
                }
                if regexm("`term'", "^Tp([0-9]+)$") {
                    local rel = real(regexs(1))
                }
                if regexm("`term'", "^T([0-9]+)$") {
                    local rel = real(regexs(1))
                }
                if `rel' < . {
                    local bval = b[1, `k']
                    local seval = sqrt(V[`k', `k'])
                    local tval = `bval' / `seval'
                    local pval = 2 * normal(-abs(`tval'))
                    post `h' ("csdid") ("scope_ge_2") ("csdid_reg_notyet") ///
                        ("`y'") ("`term'") (`rel') ///
                        (`bval') (`seval') (`tval') (`pval') ///
                        (`yN') (`yC') (`n_treated_city') (`prep')
                }
            }
        }
    }

    * Borusyak-Jaravel-Spiess: imputation estimator with province-year FE
    * and baseline-capacity-by-year controls.
    capture noisily did_imputation `y' city_id year first_scope2_bjs, ///
        horizons(0/4) pretrends(3) ///
        fe(city_id province_id#year) ///
        timecontrols(base_ln_patents base_top10) ///
        autosample cluster(city_id)
    if _rc == 0 {
        local prep = e(pre_p)
        matrix b = e(b)
        matrix V = e(V)
        local cn : colnames b
        local k = 0
        foreach term of local cn {
            local ++k
            local rel = .
            if regexm("`term'", "^tau([0-9]+)$") {
                local rel = real(regexs(1))
            }
            if regexm("`term'", "^pre([0-9]+)$") {
                local rel = -real(regexs(1))
            }
            if `rel' < . {
                local bval = b[1, `k']
                local seval = sqrt(V[`k', `k'])
                local tval = `bval' / `seval'
                local pval = 2 * normal(-abs(`tval'))
                post `h' ("bjs") ("scope_ge_2") ("bjs_provyr_baseyr") ///
                    ("`y'") ("`term'") (`rel') ///
                    (`bval') (`seval') (`tval') (`pval') ///
                    (`yN') (`yC') (`n_treated_city') (`prep')
            }
        }
    }
    drop tag_city_`y'
}

postclose `h'

use "`tables'/idc_scope_modern_did_20260525.dta", clear
gen sig = cond(p < 0.01, "***", cond(p < 0.05, "**", cond(p < 0.1, "*", "")))
order estimator eventdef spec outcome term rel coef se t p sig N N_city N_treated_city pre_p
sort outcome estimator rel
export delimited using "`tables'/idc_scope_modern_did_20260525.csv", replace
list, sepby(outcome estimator) abbreviate(20)

log close
