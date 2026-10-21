*******************************************************
* How do political values influence support for
* harsher sentencing?
* British Social Attitudes Survey 2022 (UKDS SN 9283)
* Liam McColl - Introduction to Political Data Analysis
*******************************************************

clear all
set more off

* ---- Paths: change this to where you saved the data ----
global raw_data "data"
use "$raw_data/p16974_bsa22_archive.dta", clear

* ---- 1. Descriptives ----
tab libauth2
tab StifSent
histogram libauth2, discrete percent title("Distribution of Political Ideology")
histogram StifSent, discrete percent title("Support for Stiffer Sentences")

* ---- 2. Recode outcome to binary ----
* 1 = agree / agree strongly, 0 = everyone else
gen StifSent_bin = inlist(StifSent, 1, 2)
label define bin 0 "Not supportive" 1 "Supportive"
label values StifSent_bin bin
tab StifSent StifSent_bin

* Treat "not applicable" as missing in the predictors
foreach v in libauth2 HEdQual2 HHincome RAgecat DVSex22 {
    replace `v' = . if `v' < 0
}

* ---- 3. Bivariate tests ----
foreach v in libauth2 HEdQual2 HHincome RAgecat DVSex22 {
    tab `v' StifSent_bin, row chi2
}
graph bar (mean) StifSent_bin, over(libauth2) ///
    ytitle("Share supporting stiffer sentences") ///
    title("Support for stiffer sentences by ideology")

* ---- 4. Logistic regression (centrist = baseline) ----
* Model 1: ideology only
logit StifSent_bin ib2.libauth2, or

* Model 2: with demographic controls
logit StifSent_bin ib2.libauth2 i.HEdQual2 i.HHincome i.RAgecat i.DVSex22, or

* Predicted probabilities by ideology, holding controls at observed values
margins libauth2
marginsplot, title("Predicted probability of supporting stiffer sentences")
