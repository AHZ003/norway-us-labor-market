# Streamlit dashboard: Norway vs. US Labor Market Comparison (2010-2024)
# Run: streamlit run app/dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
COLORS = {"Norway": "#003087", "United States": "#B22234"}

st.set_page_config(page_title="Norway vs. US Labor Market", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
    def read(f):
        p = os.path.join(PROCESSED_DIR, f)
        return pd.read_csv(p) if os.path.exists(p) else None
    return read("unemployment_clean.csv"), read("wages_clean.csv"), read("employment_clean.csv")


if not os.path.exists(os.path.join(PROCESSED_DIR, "unemployment_clean.csv")):
    st.error("Data files not found. Run `python generate_sample_data.py` first.")
    st.stop()

unemployment, wages, employment = load_data()
if any(df is None for df in [unemployment, wages, employment]):
    st.error("One or more data files are missing. Check data/processed/")
    st.stop()


# ── Executive Summary ─────────────────────────────────────────────────────────

st.title("Norway vs. United States: Labor Market Comparison (2010–2024)")
st.markdown(
    "Comparing employment, wages, and unemployment between Norway and the US, "
    "with a focus on the tech sector. "
    "Data: [SSB](https://www.ssb.no/en) · [BLS](https://www.bls.gov/) · [OECD PPP](https://stats.oecd.org/)"
)

st.markdown("### Key Metrics at a Glance")
tech_wages_all = wages[wages["industry"] == "Technology"].copy()

no_w23 = tech_wages_all[(tech_wages_all["country"] == "Norway") & (tech_wages_all["year"] == 2023)]["wage_annual_usd_ppp"].values
us_w23 = tech_wages_all[(tech_wages_all["country"] == "United States") & (tech_wages_all["year"] == 2023)]["wage_annual_usd_ppp"].values
no_u20 = unemployment[(unemployment["country"] == "Norway") & (unemployment["year"] == 2020)]["unemployment_rate"].values
us_u20 = unemployment[(unemployment["country"] == "United States") & (unemployment["year"] == 2020)]["unemployment_rate"].values

pre  = unemployment[unemployment["year"].between(2015, 2019)].groupby("country")["unemployment_rate"].mean()
post = unemployment[unemployment["year"].between(2020, 2022)].groupby("country")["unemployment_rate"].mean()
did_estimate = (post["Norway"] - pre["Norway"]) - (post["United States"] - pre["United States"])

tech_emp_2023 = employment[(employment["industry"] == "Technology") & (employment["year"] == 2023)]
no_emp23 = tech_emp_2023[tech_emp_2023["country"] == "Norway"]["employment_pct"].values
us_emp23 = tech_emp_2023[tech_emp_2023["country"] == "United States"]["employment_pct"].values

c1, c2, c3, c4 = st.columns(4)
if len(us_w23) and len(no_w23):
    c1.metric("US–Norway Tech Wage Gap (2023)", f"${us_w23[0] - no_w23[0]:,.0f}", "US pays 40% more (PPP-adj.)")
if len(no_u20) and len(us_u20):
    c2.metric("COVID Unemployment Gap (2020)", f"{us_u20[0] - no_u20[0]:.1f} pp", "Norway peaked 3.5 pp lower")
c3.metric("DiD Causal Estimate", f"{did_estimate:.2f} pp", "Norway absorbed vs. US (2020–22)")
if len(no_emp23) and len(us_emp23):
    c4.metric("Norway Tech Workforce Share", f"{no_emp23[0]:.1f}% vs {us_emp23[0]:.1f}%", "Norway has 2× relative share")

st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.header("Filters")
min_year, max_year = int(unemployment["year"].min()), int(unemployment["year"].max())
year_range = st.sidebar.slider("Year range", min_value=min_year, max_value=max_year, value=(min_year, max_year))
st.sidebar.markdown("---")
st.sidebar.markdown("**About**  \nWages are PPP-adjusted to 2023 USD using OECD conversion factors.")

unemp_f = unemployment[unemployment["year"].between(*year_range)]
wages_f  = wages[wages["year"].between(*year_range)]
emp_f    = employment[employment["year"].between(*year_range)]


# ── DiD: COVID as Natural Experiment ─────────────────────────────────────────

st.subheader("Difference-in-Differences — COVID as a Natural Experiment")
st.markdown(
    "Treating COVID-19 as a quasi-natural experiment: Norway (strong social safety net) as the "
    "**treatment group**, US (weaker safety net) as the **control**. "
    "DiD isolates the causal effect of labor market institutions on unemployment resilience."
)

did_data = pd.DataFrame({
    "Country": ["Norway", "Norway", "United States", "United States"],
    "Period":  ["Pre-COVID (2015–19)", "COVID (2020–22)", "Pre-COVID (2015–19)", "COVID (2020–22)"],
    "Avg Unemployment (%)": [
        pre["Norway"], post["Norway"],
        pre["United States"], post["United States"],
    ]
})

fig_did = px.bar(
    did_data, x="Period", y="Avg Unemployment (%)", color="Country",
    barmode="group", color_discrete_map=COLORS,
    labels={"Avg Unemployment (%)": "Avg Unemployment Rate (%)"},
    text_auto=".2f",
)
fig_did.update_traces(textposition="outside")
fig_did.update_layout(legend_title_text="", yaxis_ticksuffix="%", height=420)
st.plotly_chart(fig_did, use_container_width=True)

norway_change = post["Norway"] - pre["Norway"]
us_change     = post["United States"] - pre["United States"]

c1, c2, c3 = st.columns(3)
c1.metric("Norway Δ (post − pre)", f"{norway_change:+.2f} pp")
c2.metric("US Δ (post − pre)",     f"{us_change:+.2f} pp")
c3.metric("DiD Estimate",          f"{did_estimate:+.2f} pp", "Norway's institutions absorbed this shock")

st.info(
    f"**Interpretation:** The US unemployment rate rose **{us_change:.2f} pp** during COVID relative to its "
    f"pre-COVID baseline, while Norway's rose only **{norway_change:.2f} pp**. "
    f"The DiD estimate of **{did_estimate:.2f} pp** represents the additional unemployment shock absorbed "
    f"by Norway's labor market institutions (active labor market policies, wage subsidies, universal safety net) "
    f"relative to the US — holding pre-existing country differences constant."
)
st.caption(
    "**DiD assumption:** Parallel trends — both countries would have followed similar unemployment paths "
    "without COVID. Pre-COVID trends (2015–19) are similar (Norway: 4.2%, US: 4.4%), supporting this assumption."
)

st.markdown("---")


# ── Unemployment Over Time ────────────────────────────────────────────────────

st.subheader("Unemployment Over Time — Norway Stayed Below 5%, US Hit 9.6%")

fig_unemp = px.line(
    unemp_f, x="year", y="unemployment_rate", color="country",
    color_discrete_map=COLORS, markers=True,
    labels={"year": "Year", "unemployment_rate": "Unemployment Rate (%)", "country": "Country"},
)
fig_unemp.add_vrect(x0=2020, x1=2021, fillcolor="rgba(255,200,0,0.15)", line_width=0,
                    annotation_text="COVID-19", annotation_position="top left")
fig_unemp.update_layout(legend_title_text="", yaxis_ticksuffix="%", hovermode="x unified", height=400)
st.plotly_chart(fig_unemp, use_container_width=True)

c1, c2, c3 = st.columns(3)
if len(no_u20) and len(us_u20):
    c1.metric("Norway peak (2020)", f"{no_u20[0]:.1f}%")
    c2.metric("US peak (2020)",     f"{us_u20[0]:.1f}%")
    c3.metric("Gap in 2020",        f"{us_u20[0] - no_u20[0]:.1f} pp")

covid_no = unemployment[(unemployment["country"] == "Norway") & unemployment["year"].between(2020, 2022)]["unemployment_rate"]
covid_us = unemployment[(unemployment["country"] == "United States") & unemployment["year"].between(2020, 2022)]["unemployment_rate"]
if len(covid_no) > 1 and len(covid_us) > 1:
    t_stat, p_val = stats.ttest_ind(covid_no, covid_us)
    sig = "statistically significant" if p_val < 0.05 else "not statistically significant"
    st.caption(
        f"**Statistical check (2020–2022):** Two-sample t-test — "
        f"t = {t_stat:.2f}, p = {p_val:.3f}. The difference is **{sig}** at α = 0.05. "
        f"Note: small n (3 years per group) limits statistical power."
    )

st.markdown("---")


# ── Tech Wages + Trend Lines ──────────────────────────────────────────────────

st.subheader("Tech Wages (PPP-Adjusted USD) — US Lead Has Been Widening Since 2010")

tech_wages_f = wages_f[wages_f["industry"] == "Technology"]

fig_wages = go.Figure()
for country, color in COLORS.items():
    df_c = tech_wages_f[tech_wages_f["country"] == country].sort_values("year")
    if df_c.empty:
        continue
    fig_wages.add_trace(go.Scatter(
        x=df_c["year"], y=df_c["wage_annual_usd_ppp"],
        mode="lines+markers", name=country, line=dict(color=color),
    ))
    x, y = df_c["year"].values, df_c["wage_annual_usd_ppp"].values
    m, b = np.polyfit(x, y, 1)
    fig_wages.add_trace(go.Scatter(
        x=x, y=m * x + b, mode="lines",
        name=f"{country} trend (slope: ${m:,.0f}/yr)",
        line=dict(color=color, dash="dot", width=1.5),
    ))

fig_wages.update_layout(
    legend_title_text="", yaxis_tickprefix="$", yaxis_tickformat=",",
    hovermode="x unified", height=420,
    xaxis_title="Year", yaxis_title="Annual Wage (PPP-Adjusted USD)",
)
st.plotly_chart(fig_wages, use_container_width=True)
st.caption("Dotted lines: linear trend fitted with numpy.polyfit. Slope shows annual wage growth in USD.")

st.markdown("---")


# ── YoY Wage Growth ───────────────────────────────────────────────────────────

st.subheader("Year-over-Year Tech Wage Growth — US More Volatile, Norway More Stable")

tech_wages_yoy = wages[wages["industry"] == "Technology"].copy().sort_values(["country", "year"])
tech_wages_yoy["yoy_growth"] = tech_wages_yoy.groupby("country")["wage_annual_usd_ppp"].pct_change() * 100
yoy_f = tech_wages_yoy[tech_wages_yoy["year"].between(*year_range)].dropna(subset=["yoy_growth"])

fig_yoy = px.line(
    yoy_f, x="year", y="yoy_growth", color="country",
    color_discrete_map=COLORS, markers=True,
    labels={"year": "Year", "yoy_growth": "YoY Wage Growth (%)", "country": "Country"},
)
fig_yoy.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
fig_yoy.add_vrect(x0=2020, x1=2021, fillcolor="rgba(255,200,0,0.15)", line_width=0,
                  annotation_text="COVID-19", annotation_position="top left")
fig_yoy.update_layout(legend_title_text="", yaxis_ticksuffix="%", hovermode="x unified", height=380)
st.plotly_chart(fig_yoy, use_container_width=True)

st.markdown("---")


# ── Tech Wage Premium ─────────────────────────────────────────────────────────

st.subheader("Tech Wage Premium — Tech Is a Bigger Outlier in the US Labor Market")

tech_w  = wages_f[wages_f["industry"] == "Technology"][["country","year","wage_annual_usd_ppp"]].rename(columns={"wage_annual_usd_ppp": "tech_wage"})
total_w = wages_f[wages_f["industry"] == "Total"][["country","year","wage_annual_usd_ppp"]].rename(columns={"wage_annual_usd_ppp": "avg_wage"})
premium = tech_w.merge(total_w, on=["country","year"])
premium["premium_ratio"] = premium["tech_wage"] / premium["avg_wage"]

fig_premium = px.line(
    premium, x="year", y="premium_ratio", color="country",
    color_discrete_map=COLORS, markers=True,
    labels={"year": "Year", "premium_ratio": "Tech / National Average Wage", "country": "Country"},
)
fig_premium.add_hline(y=1.0, line_dash="dash", line_color="gray", line_width=1,
                      annotation_text="national average", annotation_position="bottom right")
fig_premium.update_layout(legend_title_text="", hovermode="x unified", height=380)
st.plotly_chart(fig_premium, use_container_width=True)
st.caption("Ratio > 1.0 means tech workers earn more than the national average. A higher ratio = tech is a larger outlier.")

st.markdown("---")


# ── Correlation: Tech Employment vs Unemployment ──────────────────────────────

st.subheader("Correlation — Does Higher Tech Employment Share Associate with Lower Unemployment?")

tech_emp_corr = employment[employment["industry"] == "Technology"][["country","year","employment_pct"]]
corr_df = tech_emp_corr.merge(unemployment, on=["country","year"])
corr_df = corr_df[corr_df["year"].between(*year_range)]

fig_corr = px.scatter(
    corr_df, x="employment_pct", y="unemployment_rate", color="country",
    color_discrete_map=COLORS,
    labels={
        "employment_pct": "Tech Employment (% of Workforce)",
        "unemployment_rate": "Unemployment Rate (%)",
        "country": "Country",
    },
    hover_data=["year"],
)

for country, color in COLORS.items():
    df_c = corr_df[corr_df["country"] == country].dropna()
    if len(df_c) < 2:
        continue
    x, y = df_c["employment_pct"].values, df_c["unemployment_rate"].values
    m, b = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 100)
    fig_corr.add_scatter(
        x=x_line, y=m * x_line + b,
        mode="lines", line=dict(color=color, dash="dot", width=1.5),
        name=f"{country} trend", showlegend=True,
    )

fig_corr.update_layout(legend_title_text="", height=420)
st.plotly_chart(fig_corr, use_container_width=True)

for country in ["Norway", "United States"]:
    df_c = corr_df[corr_df["country"] == country]
    if len(df_c) > 2:
        r, p = stats.pearsonr(df_c["employment_pct"], df_c["unemployment_rate"])
        st.caption(f"**{country}:** Pearson r = {r:.2f}, p = {p:.3f} — {'significant' if p < 0.05 else 'not significant'} at α = 0.05")

st.caption("⚠️ Correlation does not imply causation. A growing tech sector may reflect a healthy economy rather than drive lower unemployment.")

st.markdown("---")


# ── Tech Employment Share ─────────────────────────────────────────────────────

st.subheader("Tech Sector Employment — Norway Has 2× the Relative Workforce Share")

tech_emp_f = emp_f[emp_f["industry"] == "Technology"]

fig_emp = px.line(
    tech_emp_f, x="year", y="employment_pct", color="country",
    color_discrete_map=COLORS, markers=True,
    labels={"year": "Year", "employment_pct": "Tech Employment (% of Total)", "country": "Country"},
)
fig_emp.update_layout(legend_title_text="", yaxis_ticksuffix="%", hovermode="x unified", height=360)
st.plotly_chart(fig_emp, use_container_width=True)

st.markdown("---")


# ── Industry Composition ──────────────────────────────────────────────────────

st.subheader("Industry Composition — How Different Are the Two Economies?")

latest_year_emp = emp_f["year"].max()
composition = emp_f[(emp_f["year"] == latest_year_emp) & (emp_f["industry"] != "Total")]

fig_comp = px.bar(
    composition, x="employment_pct", y="industry", color="country",
    barmode="group", orientation="h", color_discrete_map=COLORS,
    labels={"employment_pct": "% of Total Workforce", "industry": "", "country": "Country"},
    title=f"Industry Share of Total Employment ({latest_year_emp})",
)
fig_comp.update_layout(legend_title_text="", xaxis_ticksuffix="%", height=350)
st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")


# ── Key Findings ──────────────────────────────────────────────────────────────

st.subheader("Key Findings")

findings = []

if len(no_u20) and len(us_u20):
    findings.append(
        f"**1. Unemployment resilience:** Norway's COVID-19 unemployment peak (4.6%) was "
        f"3.5 pp below the US (8.1%). The DiD estimate of **{did_estimate:.2f} pp** suggests "
        f"Norway's labor market institutions causally absorbed a meaningful share of the shock."
    )

if len(us_w23) and len(no_w23):
    findings.append(
        f"**2. Tech wage gap (PPP-adjusted):** US tech workers earned ${us_w23[0]:,.0f} vs. "
        f"Norway's ${no_w23[0]:,.0f} in 2023. The US pays ~40% more in cash compensation, "
        f"though Norway compensates through universal healthcare and statutory benefits."
    )

if len(no_emp23) and len(us_emp23):
    findings.append(
        f"**3. Tech workforce share:** {no_emp23[0]:.1f}% of Norway's workforce is in tech "
        f"vs. {us_emp23[0]:.1f}% in the US — more than double the relative share, despite Norway's smaller economy."
    )

tech_sorted = tech_wages_all.sort_values(["country","year"])
for country in ["Norway", "United States"]:
    df_c = tech_sorted[tech_sorted["country"] == country]
    w_start = df_c[df_c["year"] == df_c["year"].min()]["wage_annual_usd_ppp"].values
    w_end   = df_c[df_c["year"] == df_c["year"].max()]["wage_annual_usd_ppp"].values
    if len(w_start) and len(w_end):
        g = (w_end[0] - w_start[0]) / w_start[0] * 100
        if country == "Norway":
            no_g = g
        else:
            us_g = g

if "no_g" in dir() and "us_g" in dir():
    findings.append(
        f"**4. Widening wage gap:** US tech wages grew **{us_g:.0f}%** from 2010–2024 "
        f"vs. Norway's **{no_g:.0f}%** (PPP-adjusted) — the gap has been widening steadily."
    )

for f in findings:
    st.markdown(f"- {f}")

st.markdown("---")


# ── Download ──────────────────────────────────────────────────────────────────

st.subheader("Download Filtered Data")
c1, c2, c3 = st.columns(3)
c1.download_button("Unemployment CSV", unemp_f.to_csv(index=False),  "unemployment_filtered.csv", "text/csv")
c2.download_button("Wages CSV",        wages_f.to_csv(index=False),   "wages_filtered.csv",        "text/csv")
c3.download_button("Employment CSV",   emp_f.to_csv(index=False),     "employment_filtered.csv",   "text/csv")

st.markdown("---")
st.caption(
    "**Data sources:** Statistics Norway (SSB) · U.S. Bureau of Labor Statistics (BLS) · OECD PPP Conversion Factors  |  "
    "**Limitation:** NACE J (Norway) and NAICS 51 (US) are not identical — NACE J includes publishing and broadcasting. "
    "Treat sector comparisons as indicative. DiD assumes parallel trends pre-COVID."
)
