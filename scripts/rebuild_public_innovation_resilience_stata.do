clear all
set more off

local source "/Users/mac/computerscience/第三方资料/90_临时下载待归档/上市公司创新韧性数据（2000-2024年）"
local raw "`source'/原始数据"
local out "/Users/mac/computerscience/23选题探索/T10/outputs"

display "=== Rebuild public listed-firm innovation resilience data with Stata ==="
display "Source: `source'"
display "Output: `out'"

import excel "`raw'/地级市专利数据.xlsx", firstrow clear
destring 年份 城市代码 市专利申请总量 市专利授权总量 市发明专利授权量, replace force
drop if missing(年份)
xtset 城市代码 年份
gen 城市发明专利授权量变化 = (市发明专利授权量-L.市发明专利授权量)/L.市发明专利授权量
gen 城市专利申请量变化 = (市专利申请总量-L.市专利申请总量)/L.市专利申请总量
gen 城市专利授权量变化 = (市专利授权总量-L.市专利授权总量)/L.市专利授权总量
save "`out'/地级市专利数据_rebuild_stata.dta", replace

import excel "`raw'/上市公司专利数据.xlsx", firstrow clear
destring 年份 股票代码 城市代码 企业专利申请总量 企业专利授权总量 企业发明专利授权量, replace force
drop if missing(年份) | missing(股票代码)
merge m:1 年份 城市 using "`out'/地级市专利数据_rebuild_stata.dta"
drop if _merge == 2
drop _merge
save "`out'/原始数据_rebuild_stata.dta", replace

collapse (sum) patent_industry = 企业专利申请总量, by(行业代码 年份)
sort 行业代码 年份
by 行业代码: gen 行业专利申请量变化 = patent_industry - patent_industry[_n-1]
save "`out'/行业专利数据_rebuild_stata.dta", replace

use "`out'/原始数据_rebuild_stata.dta", clear
merge m:1 行业代码 年份 using "`out'/行业专利数据_rebuild_stata.dta"
drop _merge

xtset 股票代码 年份

gen 企业发明专利授权量变化 = 企业发明专利授权量 - L.企业发明专利授权量
gen 企业创新韧性1 = (企业发明专利授权量变化-(城市发明专利授权量变化*企业发明专利授权量))/abs(城市发明专利授权量变化*企业发明专利授权量)

gen 企业专利申请量变化 = 企业专利申请总量-L.企业专利申请总量
label data 马克集数
gen 企业创新韧性2 = (企业专利申请量变化-(城市专利申请量变化*企业专利申请总量))/abs(城市专利申请量变化*企业专利申请总量)

gen 企业专利授权量变化 = 企业专利授权总量-L.企业专利授权总量
gen 企业创新韧性3 = (企业专利授权量变化-(城市专利授权量变化*企业专利授权总量))/abs(城市专利授权量变化*企业专利授权总量)

gen 企业创新韧性4 = (企业专利申请量变化-(行业专利申请量变化*企业专利申请总量))/abs(行业专利申请量变化*企业专利申请总量)

drop patent_industry 行业专利申请量变化 企业发明专利授权量变化 企业专利申请量变化 企业专利授权量变化 城市发明专利授权量变化 城市专利申请量变化 城市专利授权量变化

save "`out'/public_innovation_resilience_rebuild_stata_2000_2024.dta", replace
export delimited using "`out'/public_innovation_resilience_rebuild_stata_2000_2024.csv", replace

count
display "REBUILT_ROWS=" r(N)
quietly summarize 年份
display "YEAR_MIN=" r(min)
display "YEAR_MAX=" r(max)
egen tag_firm = tag(股票代码)
quietly count if tag_firm == 1
display "FIRM_COUNT=" r(N)
drop tag_firm
foreach v in 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4 {
    quietly count if !missing(`v')
    display "`v'_NONMISSING=" r(N)
}

tempfile rebuilt product compare
save `rebuilt', replace

use "`source'/企业创新韧性（2000-2024年）.dta", clear
keep 股票代码 年份 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4
rename 企业创新韧性1 企业创新韧性1_product
rename 企业创新韧性2 企业创新韧性2_product
rename 企业创新韧性3 企业创新韧性3_product
rename 企业创新韧性4 企业创新韧性4_product
save `product', replace

use `rebuilt', clear
keep 股票代码 年份 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4
merge 1:1 股票代码 年份 using `product'
tab _merge
count if _merge == 3
display "MERGED_BOTH=" r(N)

foreach v in 企业创新韧性1 企业创新韧性2 企业创新韧性3 企业创新韧性4 {
    gen diff_`v' = abs(`v' - `v'_product)
    quietly summarize diff_`v'
    display "`v'_MAX_ABS_DIFF=" r(max)
    quietly count if !(missing(`v') & missing(`v'_product)) ///
        & !(diff_`v' <= 1e-5)
    display "`v'_MISMATCH_GT_1E-5=" r(N)
}

display "=== Done ==="
