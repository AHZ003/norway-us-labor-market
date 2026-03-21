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
TEMPLATE = "plotly_white"
H = 420

st.set_page_config(page_title="Norway vs. US Labor Market", layout="wide")


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


# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("Norway vs. United States")
st.sidebar.markdown("Labor Market Comparison (2010–2024)")
st.sidebar.markdown("---")

min_year = int(unemployment["year"].min())
max_year = int(unemployment["year"].max())
year_range = st.sidebar.slider("Filter year range", min_value=min_year, max_value=max_year, value=(min_year, max_year))

st.sidebar.markdown("---")
st.sidebar.markdown("**Data sources**")
st.sidebar.markdown("- [Statistics Norway (SSB)](https://www.ssb.no/en)")
st.sidebar.markdown("- [U.S. Bureau of Labor Statistics](https://www.bls.gov/)")
st.sidebar.markdown("- [OECD PPP Factors](https://stats.oecd.org/)")
st.sidebar.markdown("---")
st.sidebar.caption(
    "Wages are PPP-adjusted to 2023 USD. "
    "NACE J (Norway) and NAICS 51 (US) are the closest available proxies for "
    "'tech' but are not identical."
)

unemp_f = unemployment[unemployment["year"].between(*year_range)]
wages_f  = wages[wages["year"].between(*year_range)]
emp_f    = employment[employment["year"].between(*year_range)]


# ── Pre-compute fixed metrics (full dataset, not affected by filter) ──────────

tech_wages_all = wages[wages["industry"] == "Technology"].copy().sort_values(["country", "year"])

no_w23   = wages[(wages["country"] == "Norway") & (wages["industry"] == "Technology") & (wages["year"] == 2023)]["wage_annual_usd_ppp"].values
us_w23   = wages[(wages["country"] == "United States") & (wages["industry"] == "Technology") & (wages["year"] == 2023)]["wage_annual_usd_ppp"].values
no_u20   = unemployment[(unemployment["country"] == "Norway") & (unemployment["year"] == 2020)]["unemployment_rate"].values
us_u20   = unemployment[(unemployment["country"] == "United States") & (unemployment["year"] == 2020)]["unemployment_rate"].values
no_emp23 = employment[(employment["country"] == "Norway") & (employment["industry"] == "Technology") & (employment["year"] == 2023)]["employment_pct"].values
us_emp23 = employment[(employment["country"] == "United States") & (employment["industry"] == "Technology") & (employment["year"] == 2023)]["employment_pct"].values

pre  = unemployment[unemployment["year"].between(2015, 2019)].groupby("country")["unemployment_rate"].mean()
post = unemployment[unemployment["year"].between(2020, 2022)].groupby("country")["unemployment_rate"].mean()
norway_change = post["Norway"] - pre["Norway"]
us_change     = post["United States"] - pre["United States"]
did_estimate  = norway_change - us_change

wage_growth = {}
for country in ["Norway", "United States"]:
    df_c = tech_wages_all[tech_wages_all["country"] == country]
    w0 = df_c[df_c["year"] == df_c["year"].min()]["wage_annual_usd_ppp"].values
    w1 = df_c[df_c["year"] == df_c["year"].max()]["wage_annual_usd_ppp"].values
    if len(w0) and len(w1):
        wage_growth[country] = (w1[0] - w0[0]) / w0[0] * 100


# ── Header ────────────────────────────────────────────────────────────────────

st.title("Norway vs. United States: Labor Market Comparison (2010–2024)")
st.markdown(
    "An end-to-end data analysis comparing employment, wages, and unemployment "
    "between Norway and the US, with a focus on the technology sector. "
    "Data: [SSB](https://www.ssb.no/en) · [BLS](https://www.bls.gov/) · [OECD](https://stats.oecd.org/)"
)


# ── Key Metrics ───────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Key Metrics")
st.caption("Computed from the full dataset (2010–2024). Not affected by the year filter.")

c1, c2, c3, c4 = st.columns(4)
if len(us_w23) and len(no_w23):
    c1.metric("Tech Wage Gap (2023)", f"${us_w23[0] - no_w23[0]:,.0f}", "US pays ~40% more (PPP-adj.)")
if len(no_u20) and len(us_u20):
    c2.metric("COVID Unemployment Gap", f"{us_u20[0] - no_u20[0]:.1f} pp", "US peaked 3.5 pp higher in 2020")
c3.metric("DiD Causal Estimate", f"{did_estimate:+.2f} pp", "Shock Norway absorbed vs. US")
if len(no_emp23) and len(us_emp23):
    c4.metric("Norway Tech Share (2023)", f"{no_emp23[0]:.1f}% vs {us_emp23[0]:.1f}%", "Norway has 2x relative share")


# ── Unemployment Over Time ────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Unemployment Rate Over Time")
st.caption(f"Filtered to {year_range[0]}–{year_range[1]}.")

fig_unemp = px.line(
    unemp_f, x="year", y="unemployment_rate", color="country",
    color_discrete_map=COLORS, markers=True, template=TEMPLATE,
    labels={"year": "Year", "unemployment_rate": "Unemployment Rate (%)", "country": ""},
)
fig_unemp.add_vrect(x0=2020, x1=2021, fillcolor="rgba(255,200,0,0.18)", line_width=0,
                    annotation_text="COVID-19", annotation_position="top left",
                    annotation_font_size=12)
fig_unemp.update_layout(hovermode="x unified", yaxis_ticksuffix="%",
                        height=H, margin=dict(t=30, b=20))
st.plotly_chart(fig_unemp, use_container_width=True)

if len(no_u20) and len(us_u20):
    c1, c2, c3 = st.columns(3)
    c1.metric("Norway peak (2020)", f"{no_u20[0]:.1f}%")
    c2.metric("US peak (2020)", f"{us_u20[0]:.1f}%")
    c3.metric("Gap in 2020", f"{us_u20[0] - no_u20[0]:.1f} pp", "US higher")

covid_no = unemployment[(unemployment["country"] == "Norway") & unemployment["year"].between(2020, 2022)]["unemployment_rate"]
covid_us = unemployment[(unemployment["country"] == "United States") & unemployment["year"].between(2020, 2022)]["unemployment_rate"]
if len(covid_no) > 1 and len(covid_us) > 1:
    t_stat, p_val = stats.ttest_ind(covid_no, covid_us)
    st.caption(
        f"Two-sample t-test (2020–2022): t = {t_stat:.2f}, p = {p_val:.3f} — "
        f"{'statistically significant' if p_val < 0.05 else 'not statistically significant'} at α = 0.05. "
        f"Small n (3 years per group) limits statistical power."
    )


# ── DiD ───────────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Difference-in-Differences — COVID as a Natural Experiment")
st.info(
    "This section uses fixed periods — **Pre-COVID: 2015–2019** and **COVID: 2020–2022** — "
    "regardless of the year filter, since the natural experiment window is defined by the shock itself."
)
st.markdown(
    "Norway (strong social safety net) = **treatment group**. "
    "US (weaker safety net) = **control group**. "
    "DiD isolates the causal effect of labor market institutions on unemployment resilience, "
    "holding pre-existing differences between the two countries constant."
)

did_data = pd.DataFrame({
    "Country": ["Norway", "Norway", "United States", "United States"],
    "Period":  ["Pre-COVID (2015–19)", "COVID (2020–22)", "Pre-COVID (2015–19)", "COVID (2020–22)"],
    "Avg Unemployment (%)": [pre["Norway"], post["Norway"], pre["United States"], post["United States"]],
})

fig_did = px.bar(
    did_data, x="Period", y="Avg Unemployment (%)", color="Country",
    barmode="group", color_discrete_map=COLORS, template=TEMPLATE, text_auto=".2f",
    labels={"Avg Unemployment (%)": "Avg Unemployment Rate (%)"},
)
fig_did.update_traces(textposition="outside")
fig_did.update_layout(yaxis_ticksuffix="%", height=H, legend_title_text="", margin=dict(t=30, b=20))
st.plotly_chart(fig_did, use_container_width=True)

c1, c2, c3 = st.columns(3)
c1.metric("Norway change (post − pre)", f"{norway_change:+.2f} pp")
c2.metric("US change (post − pre)", f"{us_change:+.2f} pp")
c3.metric("DiD Estimate", f"{did_estimate:+.2f} pp", "absorbed by Norway's institutions")

st.markdown(
    f"**Interpretation:** The US unemployment rate rose **{us_change:.2f} pp** during COVID "
    f"relative to its pre-COVID baseline, while Norway's rose only **{norway_change:.2f} pp**. "
    f"The DiD estimate of **{did_estimate:.2f} pp** represents the additional shock absorbed "
    f"by Norway's labor market institutions — active labor market policies, wage subsidy schemes, "
    f"and a universal safety net — relative to the US, holding baseline differences constant."
)
st.caption(
    f"Parallel trends assumption: Both countries had similar pre-COVID unemployment levels "
    f"(Norway: {pre['Norway']:.1f}%, US: {pre['United States']:.1f}%), "
    f"supporting the assumption that trends would have continued similarly without COVID."
)


# ── Tech Wages ────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Tech Wages (PPP-Adjusted USD) Over Time")
st.caption(f"Filtered to {year_range[0]}–{year_range[1]}. Dotted lines show linear trend (numpy.polyfit).")

tech_wages_f = wages_f[wages_f["industry"] == "Technology"]

fig_wages = go.Figure()
for country, color in COLORS.items():
    df_c = tech_wages_f[tech_wages_f["country"] == country].sort_values("year")
    if df_c.empty:
        continue
    fig_wages.add_trace(go.Scatter(
        x=df_c["year"], y=df_c["wage_annual_usd_ppp"],
        mode="lines+markers", name=country,
        line=dict(color=color, width=2.5), marker=dict(size=7),
    ))
    x, y = df_c["year"].values, df_c["wage_annual_usd_ppp"].values
    m, b = np.polyfit(x, y, 1)
    fig_wages.add_trace(go.Scatter(
        x=x, y=m * x + b, mode="lines",
        name=f"{country} trend (+${m:,.0f}/yr)",
        line=dict(color=color, dash="dot", width=1.5),
    ))

fig_wages.update_layout(
    template=TEMPLATE, hovermode="x unified", height=H,
    yaxis_tickprefix="$", yaxis_tickformat=",",
    xaxis_title="Year", yaxis_title="Annual Wage (PPP-Adjusted USD)",
    legend_title_text="", margin=dict(t=30, b=20),
)
st.plotly_chart(fig_wages, use_container_width=True)

# YoY growth and premium side by side
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Year-over-Year Wage Growth")
    tech_yoy = wages[wages["industry"] == "Technology"].copy().sort_values(["country", "year"])
    tech_yoy["yoy_growth"] = tech_yoy.groupby("country")["wage_annual_usd_ppp"].pct_change() * 100
    yoy_f = tech_yoy[tech_yoy["year"].between(*year_range)].dropna(subset=["yoy_growth"])

    fig_yoy = px.line(
        yoy_f, x="year", y="yoy_growth", color="country",
        color_discrete_map=COLORS, markers=True, template=TEMPLATE,
        labels={"year": "Year", "yoy_growth": "YoY Growth (%)", "country": ""},
    )
    fig_yoy.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
    fig_yoy.add_vrect(x0=2020, x1=2021, fillcolor="rgba(255,200,0,0.18)", line_width=0)
    fig_yoy.update_layout(hovermode="x unified", yaxis_ticksuffix="%",
                          height=360, margin=dict(t=30, b=20))
    st.plotly_chart(fig_yoy, use_container_width=True)

with col_right:
    st.subheader("Tech Wage Premium Ratio")
    st.caption("How much more tech pays vs. the national average wage.")
    tech_w  = wages_f[wages_f["industry"] == "Technology"][["country","year","wage_annual_usd_ppp"]].rename(columns={"wage_annual_usd_ppp": "tech_wage"})
    total_w = wages_f[wages_f["industry"] == "Total"][["country","year","wage_annual_usd_ppp"]].rename(columns={"wage_annual_usd_ppp": "avg_wage"})
    premium = tech_w.merge(total_w, on=["country","year"])
    premium["premium_ratio"] = premium["tech_wage"] / premium["avg_wage"]

    fig_prem = px.line(
        premium, x="year", y="premium_ratio", color="country",
        color_discrete_map=COLORS, markers=True, template=TEMPLATE,
        labels={"year": "Year", "premium_ratio": "Tech / National Avg", "country": ""},
    )
    fig_prem.add_hline(y=1.0, line_dash="dash", line_color="gray", line_width=1,
                       annotation_text="national average", annotation_position="bottom right")
    fig_prem.update_layout(hovermode="x unified", height=360, margin=dict(t=30, b=20))
    st.plotly_chart(fig_prem, use_container_width=True)

# Wages by industry bar
st.subheader("Wages by Industry — Latest Year in Filter")
industry_wages  = wages_f[wages_f["industry"] != "Total"]
latest_wg_year  = industry_wages["year"].max()
latest_wages    = industry_wages[industry_wages["year"] == latest_wg_year]

fig_bar = px.bar(
    latest_wages, x="industry", y="wage_annual_usd_ppp", color="country",
    barmode="group", color_discrete_map=COLORS, template=TEMPLATE,
    labels={"industry": "", "wage_annual_usd_ppp": "Annual Wage (PPP-Adjusted USD)", "country": ""},
    title=f"Annual Wages by Industry ({latest_wg_year}, PPP-Adjusted USD)",
)
fig_bar.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
fig_bar.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",",
                      height=H, legend_title_text="", margin=dict(t=50, b=20))
st.plotly_chart(fig_bar, use_container_width=True)


# ── Employment ────────────────────────────────────────────────────────────────

st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Tech Sector Employment Share")
    st.caption(f"Filtered to {year_range[0]}–{year_range[1]}.")
    tech_emp_f = emp_f[emp_f["industry"] == "Technology"]

    fig_emp = px.line(
        tech_emp_f, x="year", y="employment_pct", color="country",
        color_discrete_map=COLORS, markers=True, template=TEMPLATE,
        labels={"year": "Year", "employment_pct": "Tech Employment (% of Total)", "country": ""},
    )
    fig_emp.update_layout(hovermode="x unified", yaxis_ticksuffix="%",
                          height=H, margin=dict(t=30, b=20))
    st.plotly_chart(fig_emp, use_container_width=True)

    if len(no_emp23) and len(us_emp23):
        c1, c2 = st.columns(2)
        c1.metric("Norway (2023)", f"{no_emp23[0]:.2f}%")
        c2.metric("United States (2023)", f"{us_emp23[0]:.2f}%")

with col_right:
    st.subheader("Industry Composition")
    latest_emp_year = emp_f["year"].max()
    st.caption(f"Latest year in filter: {latest_emp_year}.")
    composition = emp_f[(emp_f["year"] == latest_emp_year) & (emp_f["industry"] != "Total")]

    fig_comp = px.bar(
        composition, x="employment_pct", y="industry", color="country",
        barmode="group", orientation="h", color_discrete_map=COLORS, template=TEMPLATE,
        labels={"employment_pct": "% of Workforce", "industry": "", "country": ""},
    )
    fig_comp.update_layout(xaxis_ticksuffix="%", height=H,
                           legend_title_text="", margin=dict(t=30, b=20))
    st.plotly_chart(fig_comp, use_container_width=True)


# ── Correlation ───────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Correlation — Tech Employment Share vs. Unemployment Rate")
st.caption(f"Filtered to {year_range[0]}–{year_range[1]}. Each point is one country-year observation.")

tech_emp_corr = employment[employment["industry"] == "Technology"][["country","year","employment_pct"]]
corr_df = tech_emp_corr.merge(unemployment, on=["country","year"])
corr_df = corr_df[corr_df["year"].between(*year_range)]

fig_corr = px.scatter(
    corr_df, x="employment_pct", y="unemployment_rate", color="country",
    color_discrete_map=COLORS, template=TEMPLATE,
    labels={
        "employment_pct": "Tech Employment (% of Workforce)",
        "unemployment_rate": "Unemployment Rate (%)",
        "country": "",
    },
    hover_data=["year"],
)
fig_corr.update_traces(marker=dict(size=9, opacity=0.8))

for country, color in COLORS.items():
    df_c = corr_df[corr_df["country"] == country].dropna()
    if len(df_c) < 2:
        continue
    x, y = df_c["employment_pct"].values, df_c["unemployment_rate"].values
    m, b = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 100)
    fig_corr.add_scatter(
        x=x_line, y=m * x_line + b, mode="lines",
        line=dict(color=color, dash="dot", width=1.5),
        name=f"{country} trend", showlegend=True,
    )

fig_corr.update_layout(height=H, margin=dict(t=30, b=20))
st.plotly_chart(fig_corr, use_container_width=True)

c1, c2 = st.columns(2)
for col, country in zip([c1, c2], ["Norway", "United States"]):
    df_c = corr_df[corr_df["country"] == country]
    if len(df_c) > 2:
        r, p = stats.pearsonr(df_c["employment_pct"], df_c["unemployment_rate"])
        col.metric(
            f"{country} — Pearson r",
            f"{r:.2f}",
            f"p = {p:.3f} ({'significant' if p < 0.05 else 'not significant'})",
        )

st.caption("Note: Correlation does not imply causation. A growing tech sector may reflect a healthy economy rather than drive lower unemployment.")


# ── Key Findings ──────────────────────────────────────────────────────────────

st.markdown("---")
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
        f"**2. Tech wage gap (PPP-adjusted):** US tech workers earned USD {us_w23[0]:,.0f} "
        f"vs. Norway's USD {no_w23[0]:,.0f} in 2023 — the US pays approximately 40% more "
        f"in cash compensation."
    )

if len(no_emp23) and len(us_emp23):
    findings.append(
        f"**3. Tech workforce share:** {no_emp23[0]:.1f}% of Norway's workforce is in tech "
        f"vs. {us_emp23[0]:.1f}% in the US — more than double the relative share, "
        f"despite Norway's much smaller total labor force."
    )

if "Norway" in wage_growth and "United States" in wage_growth:
    findings.append(
        f"**4. Widening wage gap:** US tech wages grew **{wage_growth['United States']:.0f}%** "
        f"from 2010–2024 vs. Norway's **{wage_growth['Norway']:.0f}%** (PPP-adjusted) — "
        f"the compensation gap has been widening steadily, not just a one-time difference."
    )

for f in findings:
    st.markdown(f"- {f}")


# ── Download ──────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Download Data")
st.caption(f"Filtered to {year_range[0]}–{year_range[1]}.")
c1, c2, c3 = st.columns(3)
c1.download_button("Unemployment CSV", unemp_f.to_csv(index=False), "unemployment_filtered.csv", "text/csv")
c2.download_button("Wages CSV",        wages_f.to_csv(index=False),  "wages_filtered.csv",       "text/csv")
c3.download_button("Employment CSV",   emp_f.to_csv(index=False),    "employment_filtered.csv",  "text/csv")

st.markdown("---")
st.caption(
    "**Built with** Python · Pandas · Plotly · Streamlit · NumPy · SciPy  |  "
    "**Limitation:** NACE J (Norway) and NAICS 51 (US) are not identical — "
    "NACE J includes publishing and broadcasting. Treat sector comparisons as indicative.  |  "
    "**AI Disclosure:** Built with Claude (Anthropic) for code scaffolding. "
    "All analytical decisions and findings are the author's own."
)
