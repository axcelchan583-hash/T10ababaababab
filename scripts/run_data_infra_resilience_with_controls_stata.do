clear all
set more off

local t10 "/Users/mac/computerscience/23选题探索/T10"
local out "`t10'/outputs"

capture log close
log using "`out'/run_data_infra_resilience_with_controls_stata_20260523.log", text replace

display "=== National big-data pilot zone × innovation resilience with firm controls ==="

tempfile controls

* Existing cleaned CSMAR firm-year controls.
import delimited using "`out'/csmar_controls_firm_year_from_existing.csv", clear varnames(1) encoding("utf-8") stringcols(_all)
gen 股票代码 = real(symbol)
gen 年份 = real(year)
rename size Size
rename lev Lev
rename roa ROA
rename growth Growth
rename be_ratio BE_ratio
destring Size Lev ROA Growth BE_ratio ta tl te ni rev, replace force
rename ta TA
rename tl TL
rename te TE
rename ni NI
rename rev REV
keep 股票代码 年份 Size Lev ROA Growth BE_ratio TA TL TE NI REV
duplicates drop 股票代码 年份, force
save `controls', replace

use "`out'/public_innovation_resilience_rebuild_stata_2000_2024.dta", clear

drop if missing(股票代码) | missing(年份)
drop if missing(城市) | 城市 == ""
drop if missing(省份) | 省份 == ""

gen byte treat_data_infra = 0

* Province/region-level National Big Data Comprehensive Pilot Zones.
replace treat_data_infra = 1 if inlist(省份, "贵州省", "河南省", "重庆市", "上海市")
replace treat_data_infra = 1 if inlist(省份, "北京市", "天津市", "河北省", "内蒙古自治区")

* Pearl River Delta pilot zone: nine PRD cities, not all Guangdong cities.
replace treat_data_infra = 1 if inlist(城市, "广州市", "深圳市", "珠海市", "佛山市", "惠州市")
replace treat_data_infra = 1 if inlist(城市, "东莞市", "中山市", "江门市", "肇庆市")

* Shenyang pilot zone.
replace treat_data_infra = 1 if 城市 == "沈阳市"

gen byte post2016 = 年份 >= 2016
gen byte Data_infra = treat_data_infra * post2016

capture confirm string variable 是否ST类
if _rc == 0 {
    gen byte non_st = 是否ST类 == "0"
}
else {
    gen byte non_st = 是否ST类 == 0
}
gen str1 industry_1d = substr(行业代码, 1, 1)
gen byte non_finance = industry_1d != "J"
gen byte base_clean = non_st == 1 & non_finance == 1
egen city_cluster = group(省份 城市)

merge m:1 股票代码 年份 using `controls', keep(master match) nogen
gen byte has_ctrl = !missing(Size, Lev, ROA, Growth)

label var treat_data_infra "National big-data pilot zone treated city/region"
label var post2016 "Post 2016"
label var Data_infra "Treat x Post2016"

egen tag_city = tag(city_cluster)
count if tag_city == 1
display "N_CITIES_TOTAL=" r(N)
count if tag_city == 1 & treat_data_infra == 1
display "N_CITIES_TREATED=" r(N)
drop tag_city

* Winsorize outcomes and controls on the broad clean regression window.
local winsor_vars 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4 Size Lev ROA Growth
foreach v of local winsor_vars {
    gen w_`v' = `v'
    quietly summarize `v' if base_clean == 1 & 年份 >= 2008 & 年份 <= 2024, detail
    local p1 = r(p1)
    local p99 = r(p99)
    replace w_`v' = `p1' if w_`v' < `p1' & !missing(w_`v')
    replace w_`v' = `p99' if w_`v' > `p99' & !missing(w_`v')
}

save "`out'/data_infra_innovation_resilience_controls_panel_2000_2024.dta", replace
export delimited using "`out'/data_infra_innovation_resilience_controls_panel_2000_2024.csv", replace

count if base_clean == 1 & 年份 >= 2012 & 年份 <= 2022
display "N_BASE_2012_2022=" r(N)
count if base_clean == 1 & has_ctrl == 1 & 年份 >= 2012 & 年份 <= 2022
display "N_CTRL_2012_2022=" r(N)
count if base_clean == 1 & 年份 >= 2008 & 年份 <= 2024
display "N_BASE_2008_2024=" r(N)
count if base_clean == 1 & has_ctrl == 1 & 年份 >= 2008 & 年份 <= 2024
display "N_CTRL_2008_2024=" r(N)

tempname handle
postfile `handle' str28 spec str18 sample str40 outcome str8 y_version ///
    double coef se t p n firms clusters r2 ///
    using "`out'/data_infra_resilience_with_controls_results_20260523.dta", replace

local ys 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4
local controls Size Lev ROA Growth
local wcontrols w_Size w_Lev w_ROA w_Growth

foreach y of local ys {
    foreach yv in raw winsor {
        local yuse "`y'"
        local cuse "`controls'"
        if "`yv'" == "winsor" {
            local yuse "w_`y'"
            local cuse "`wcontrols'"
        }
        foreach sample in 2012_2022 2008_2024 {
            local cond "年份 >= 2012 & 年份 <= 2022"
            if "`sample'" == "2008_2024" local cond "年份 >= 2008 & 年份 <= 2024"

            quietly areg `yuse' Data_infra i.年份 if base_clean == 1 & `cond', absorb(股票代码) vce(cluster city_cluster)
            local coef = _b[Data_infra]
            local se = _se[Data_infra]
            local t = `coef' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar tagfirm
            egen `tagfirm' = tag(股票代码) if e(sample)
            quietly count if `tagfirm' == 1
            local firms = r(N)
            drop `tagfirm'
            post `handle' ("nocontrol_full") ("`sample'") ("`y'") ("`yv'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

            quietly areg `yuse' Data_infra i.年份 if base_clean == 1 & has_ctrl == 1 & `cond', absorb(股票代码) vce(cluster city_cluster)
            local coef = _b[Data_infra]
            local se = _se[Data_infra]
            local t = `coef' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar tagfirm
            egen `tagfirm' = tag(股票代码) if e(sample)
            quietly count if `tagfirm' == 1
            local firms = r(N)
            drop `tagfirm'
            post `handle' ("nocontrol_ctrlsample") ("`sample'") ("`y'") ("`yv'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))

            quietly areg `yuse' Data_infra `cuse' i.年份 if base_clean == 1 & has_ctrl == 1 & `cond', absorb(股票代码) vce(cluster city_cluster)
            local coef = _b[Data_infra]
            local se = _se[Data_infra]
            local t = `coef' / `se'
            local p = 2 * ttail(e(df_r), abs(`t'))
            tempvar tagfirm
            egen `tagfirm' = tag(股票代码) if e(sample)
            quietly count if `tagfirm' == 1
            local firms = r(N)
            drop `tagfirm'
            post `handle' ("controls") ("`sample'") ("`y'") ("`yv'") (`coef') (`se') (`t') (`p') (e(N)) (`firms') (e(N_clust)) (e(r2))
        }
    }
}

postclose `handle'

use "`out'/data_infra_resilience_with_controls_results_20260523.dta", clear
export delimited using "`out'/data_infra_resilience_with_controls_results_20260523.csv", replace
list if outcome == "企业创新韧性1", noobs abbrev(24)

display "=== Done ==="
log close
