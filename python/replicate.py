"""Replicates the Stata analysis in Python: does authoritarianism predict support for stiffer sentences?

Data: British Social Attitudes Survey 2022 (UK Data Service, SN 9283). Not included in this repo;
download it yourself and put p16974_bsa22_archive.dta in data/.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import scipy.stats as st
import statsmodels.formula.api as smf

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data" / "p16974_bsa22_archive.dta"

df, meta = pyreadstat.read_dta(str(DATA), encoding="latin1")
cols = ["StifSent", "libauth2", "HEdQual2", "HHincome", "RAgecat", "DVSex22"]
d = df[cols].copy()

# Outcome: 1 = agree / agree strongly; 0 = everyone else (neither, disagree, don't know, refused)
d["StifSent_bin"] = d["StifSent"].isin([1, 2]).astype(int)

# Treat "not applicable" (negative codes) as missing; keep other categories as their own groups
for c in ["libauth2", "HEdQual2", "HHincome", "RAgecat", "DVSex22"]:
    d.loc[d[c] < 0, c] = np.nan
d = d.dropna()

print(f"N = {len(d)}")
print("\nSupport for stiffer sentences by ideology (%):")
print((d.groupby("libauth2")["StifSent_bin"].mean() * 100).round(1).rename(index=meta.variable_value_labels["libauth2"]))

print("\nChi-squared tests (bivariate):")
for c in ["libauth2", "HEdQual2", "HHincome", "RAgecat", "DVSex22"]:
    chi2, p, dof, _ = st.chi2_contingency(pd.crosstab(d[c], d["StifSent_bin"]))
    print(f"  {c:9s} chi2 = {chi2:7.1f}  df = {dof}  p = {p:.3g}")

m1 = smf.logit("StifSent_bin ~ C(libauth2, Treatment(2))", d).fit(disp=0)
m2 = smf.logit("StifSent_bin ~ C(libauth2, Treatment(2)) + C(HEdQual2, Treatment(1)) + C(HHincome) + C(RAgecat) + C(DVSex22)", d).fit(disp=0)

def odds_table(m):
    ci = np.exp(m.conf_int())
    return pd.DataFrame({"OR": np.exp(m.params), "CI_low": ci[0], "CI_high": ci[1], "p": m.pvalues}).round(3)

print("\nModel 1 (ideology only), odds ratios vs centrist:")
print(odds_table(m1))
print(f"pseudo R2 = {m1.prsquared:.3f}")
print("\nModel 2 (with controls), odds ratios:")
print(odds_table(m2))
print(f"pseudo R2 = {m2.prsquared:.3f}")

# ---- Figures ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FIG = Path(__file__).resolve().parents[1] / "figures"
labels = {1: "Libertarian", 2: "Centrist", 3: "Authoritarian"}
share = d[d["libauth2"].isin([1, 2, 3])].groupby("libauth2")["StifSent_bin"].mean() * 100
fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar([labels[i] for i in share.index], share.values, color=["#4C9BE8", "#9AA5B1", "#D9534F"])
ax.bar_label(bars, fmt="%.0f%%")
ax.set_ylabel("Agree people who break the law\nshould get stiffer sentences (%)")
ax.set_ylim(0, 100)
ax.set_title("Support for stiffer sentences by political values (BSA 2022)")
fig.tight_layout(); fig.savefig(FIG / "support-by-ideology.png", dpi=150)

t = odds_table(m2).drop(index="Intercept")
nice = {
    "C(libauth2, Treatment(2))[T.1.0]": "Libertarian (vs centrist)",
    "C(libauth2, Treatment(2))[T.3.0]": "Authoritarian (vs centrist)",
    "C(HEdQual2, Treatment(1))[T.4.0]": "Below A-level (vs degree)",
    "C(HEdQual2, Treatment(1))[T.6.0]": "No qualifications (vs degree)",
    "C(HHincome)[T.3.0]": "Income band 3 (vs lowest)",
    "C(RAgecat)[T.3.0]": "Age 35-44 (vs 18-24)",
    "C(DVSex22)[T.2.0]": "Male (vs female)",
}
t = t.loc[list(nice)].rename(index=nice)
fig, ax = plt.subplots(figsize=(6, 4))
y = range(len(t))
ax.errorbar(t["OR"], y, xerr=[t["OR"] - t["CI_low"], t["CI_high"] - t["OR"]], fmt="o", capsize=3)
ax.axvline(1, color="grey", ls="--")
ax.set_xscale("log"); ax.set_yticks(list(y)); ax.set_yticklabels(t.index)
ax.set_xlabel("Odds ratio (log scale, 95% CI)")
ax.set_title("What predicts support for stiffer sentences?")
fig.tight_layout(); fig.savefig(FIG / "odds-ratios.png", dpi=150)
print(f"\nSaved figures to {FIG}")
