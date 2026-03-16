"""
dashboard.py
------------
Interactive Streamlit dashboard: Norway vs. US Labor Market Comparison.

Loads data from data/processed/ CSVs (no database needed for demo).
Run:  streamlit run app/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Add the project root to path so we can import from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# ── Color scheme ──────────────────────────────────────────────────────────────
# Blue for Norway (matches Norwegian flag), red for US (matches US flag)
COLORS = {"Norway": "#003087", "United States": "#B22234"}

st.set_page_config(
    page_title="Norway vs. US Labor Market",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data():
    """Load all three processed CSVs. Cached so it only reads once."""
    def read(filename):
        path = os.path.join(PROCESSED_DIR, filename)
        if os.path.exists(path):
            return pd.read_csv(path)
        return None

    unemployment = read("unemployment_clean.csv")
    wages        = read("wages_clean.csv")
    employment   = read("employment_clean.csv")
    return unemployment, wages, employment


def check_data_exists():
    """Return True if data files are present."""
    path = os.path.join(PROCESSED_DIR, "unemployment_clean.csv")
    return os.path.exists(path)


# ── Header ────────────────────────────────────────────────────────────────────
st.title("Norway vs. United States: Labor Market Comparison")
st.markdown(
    "Comparing employment, wages, and unemployment trends between Norway and the US "
    "(2010–2024), with a focus on the technology sector. "
    "Data: [Statistics Norway (SSB)](https://www.ssb.no/en) · "
    "[U.S. Bureau of Labor Statistics (BLS)](https://www.bls.gov/)"
)

if not check_data_exists():
    st.error(
        "Data files not found. Run `python generate_sample_data.py` first to create sample data, "
        "or run the fetch scripts to pull real API data."
    )
    st.stop()

unemployment, wages, employment = load_data()

if unemployment is None or wages is None or employment is None:
    st.error("One or more data files are missing. Check data/processed/")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")

min_year = int(unemployment["year"].min())
max_year = int(unemployment["year"].max())
year_range = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.markdown(
    "Built with Python, Pandas, Plotly, and Streamlit. "
    "Wages are PPP-adjusted to 2023 international dollars using OECD conversion factors."
)

# Apply year filter
unemp_filtered  = unemployment[unemployment["year"].between(*year_range)]
wages_filtered  = wages[wages["year"].between(*year_range)]
emp_filtered    = employment[employment["year"].between(*year_range)]

# ── Section 1: Unemployment ───────────────────────────────────────────────────
st.subheader("Unemployment Over Time — Norway Stayed Below 5%, US Hit 9.6%")

fig_unemp = px.line(
    unemp_filtered,
    x="year",
    y="unemployment_rate",
    color="country",
    color_discrete_map=COLORS,
    markers=True,
    labels={"year": "Year", "unemployment_rate": "Unemployment Rate (%)", "country": "Country"},
)

# Shade COVID period
fig_unemp.add_vrect(
    x0=2020, x1=2021,
    fillcolor="rgba(255, 200, 0, 0.15)",
    line_width=0,
    annotation_text="COVID-19",
    annotation_position="top left",
)

fig_unemp.update_layout(
    legend_title_text="",
    yaxis_ticksuffix="%",
    hovermode="x unified",
    height=400,
)
st.plotly_chart(fig_unemp, use_container_width=True)

# Key stat callouts
col1, col2, col3 = st.columns(3)
us_2020 = unemp_filtered[(unemp_filtered["country"] == "United States") & (unemp_filtered["year"] == 2020)]["unemployment_rate"].values
no_2020 = unemp_filtered[(unemp_filtered["country"] == "Norway") & (unemp_filtered["year"] == 2020)]["unemployment_rate"].values
if len(us_2020) > 0 and len(no_2020) > 0:
    col1.metric("Norway peak (2020)", f"{no_2020[0]:.1f}%")
    col2.metric("US peak (2020)", f"{us_2020[0]:.1f}%")
    col3.metric("US-Norway gap in 2020", f"{us_2020[0] - no_2020[0]:.1f} pp")

st.markdown("---")

# ── Section 2: Tech Employment Share ─────────────────────────────────────────
st.subheader("Tech Sector Employment — Both Countries Growing, Different Starting Points")

tech_emp = emp_filtered[emp_filtered["industry"] == "Technology"]

fig_emp = px.line(
    tech_emp,
    x="year",
    y="employment_pct",
    color="country",
    color_discrete_map=COLORS,
    markers=True,
    labels={
        "year": "Year",
        "employment_pct": "Tech Employment (% of Total)",
        "country": "Country",
    },
)
fig_emp.update_layout(
    legend_title_text="",
    yaxis_ticksuffix="%",
    hovermode="x unified",
    height=380,
)
st.plotly_chart(fig_emp, use_container_width=True)

# Show latest year values
latest_emp = emp_filtered[emp_filtered["industry"] == "Technology"]
if not latest_emp.empty:
    latest_year = latest_emp["year"].max()
    latest = latest_emp[latest_emp["year"] == latest_year]
    col1, col2 = st.columns(2)
    for col, country in zip([col1, col2], ["Norway", "United States"]):
        row = latest[latest["country"] == country]
        if not row.empty:
            col.metric(
                f"{country} ({latest_year})",
                f"{row['employment_pct'].values[0]:.2f}% of workforce",
            )

st.markdown("---")

# ── Section 3: Wage Comparison ────────────────────────────────────────────────
st.subheader("Tech Wages (PPP-Adjusted USD) — How the Gap Has Changed")

tech_wages = wages_filtered[wages_filtered["industry"] == "Technology"]

fig_wages = px.line(
    tech_wages,
    x="year",
    y="wage_annual_usd_ppp",
    color="country",
    color_discrete_map=COLORS,
    markers=True,
    labels={
        "year": "Year",
        "wage_annual_usd_ppp": "Annual Wage (PPP-Adjusted USD)",
        "country": "Country",
    },
)
fig_wages.update_layout(
    legend_title_text="",
    yaxis_tickprefix="$",
    yaxis_tickformat=",",
    hovermode="x unified",
    height=380,
)
st.plotly_chart(fig_wages, use_container_width=True)

st.caption(
    "Wages converted to annually comparable USD using OECD Purchasing Power Parity (PPP) factors. "
    "Norway wages: SSB monthly earnings × 12, then ÷ PPP factor. "
    "US wages: BLS average hourly earnings × 2,080 hours."
)

# Bar chart: latest year wage comparison by available industries
st.subheader("Wage Comparison by Industry — Latest Available Year")

industry_wages = wages_filtered[wages_filtered["industry"] != "Total"]
latest_year_wages = industry_wages["year"].max()
latest_wages = industry_wages[industry_wages["year"] == latest_year_wages]

fig_bar = px.bar(
    latest_wages,
    x="industry",
    y="wage_annual_usd_ppp",
    color="country",
    barmode="group",
    color_discrete_map=COLORS,
    labels={
        "industry": "Industry",
        "wage_annual_usd_ppp": "Annual Wage (PPP-Adjusted USD)",
        "country": "Country",
    },
    title=f"Annual Wages by Industry ({latest_year_wages}, PPP-Adjusted USD)",
)
fig_bar.update_layout(
    legend_title_text="",
    yaxis_tickprefix="$",
    yaxis_tickformat=",",
    height=400,
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ── Section 4: Industry Composition ──────────────────────────────────────────
st.subheader("Industry Composition — How Different Are the Two Economies?")

latest_year_emp = emp_filtered["year"].max()
composition = emp_filtered[
    (emp_filtered["year"] == latest_year_emp) &
    (emp_filtered["industry"] != "Total")
]

fig_comp = px.bar(
    composition,
    x="employment_pct",
    y="industry",
    color="country",
    barmode="group",
    orientation="h",
    color_discrete_map=COLORS,
    labels={
        "employment_pct": "% of Total Workforce",
        "industry": "",
        "country": "Country",
    },
    title=f"Industry Share of Total Employment ({latest_year_emp})",
)
fig_comp.update_layout(
    legend_title_text="",
    xaxis_ticksuffix="%",
    height=350,
)
st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

# ── Key Findings ──────────────────────────────────────────────────────────────
st.subheader("Key Findings")

# Compute dynamic findings from the data
no_unemp_latest = unemployment[(unemployment["country"] == "Norway") &
                               (unemployment["year"] == unemployment["year"].max())]["unemployment_rate"].values
us_unemp_latest = unemployment[(unemployment["country"] == "United States") &
                               (unemployment["year"] == unemployment["year"].max())]["unemployment_rate"].values

no_tech_latest = tech_wages[tech_wages["country"] == "Norway"]["wage_annual_usd_ppp"].dropna()
us_tech_latest = tech_wages[tech_wages["country"] == "United States"]["wage_annual_usd_ppp"].dropna()

findings = []

if len(no_unemp_latest) > 0 and len(us_unemp_latest) > 0:
    findings.append(
        f"**1. Unemployment resilience:** Norway's unemployment rate ({no_unemp_latest[0]:.1f}%) "
        f"remains {us_unemp_latest[0] - no_unemp_latest[0]:.1f} percentage points below the US "
        f"({us_unemp_latest[0]:.1f}%) in the latest year. Norway's social safety net and active labor "
        f"market policies are likely contributors."
    )

if not no_tech_latest.empty and not us_tech_latest.empty:
    no_2023 = tech_wages[(tech_wages["country"] == "Norway") &
                         (tech_wages["year"] == 2023)]["wage_annual_usd_ppp"].values
    us_2023 = tech_wages[(tech_wages["country"] == "United States") &
                         (tech_wages["year"] == 2023)]["wage_annual_usd_ppp"].values
    if len(no_2023) > 0 and len(us_2023) > 0:
        findings.append(
            f"**2. Tech wage gap (PPP-adjusted):** US tech workers earned ${us_2023[0]:,.0f} annually "
            f"vs. Norway's ${no_2023[0]:,.0f} (PPP-adjusted) in 2023. The gap reflects the US "
            f"market's higher cash compensation, while Norway compensates through broader benefits, "
            f"shorter working hours, and lower out-of-pocket costs."
        )

no_emp_2023 = tech_emp[(tech_emp["country"] == "Norway") & (tech_emp["year"] == 2023)]["employment_pct"].values
us_emp_2023 = tech_emp[(tech_emp["country"] == "United States") & (tech_emp["year"] == 2023)]["employment_pct"].values
if len(no_emp_2023) > 0 and len(us_emp_2023) > 0:
    findings.append(
        f"**3. Tech employment share:** In 2023, {no_emp_2023[0]:.1f}% of Norway's workforce was in "
        f"tech (NACE J) vs. {us_emp_2023[0]:.1f}% in the US (NAICS 51). Note: these sector "
        f"definitions don't map perfectly — see Limitations."
    )

for finding in findings:
    st.markdown(f"- {finding}")

st.markdown("---")
st.caption(
    "**Data sources:** Statistics Norway (SSB) · U.S. Bureau of Labor Statistics (BLS) · "
    "OECD PPP Conversion Factors  |  "
    "**Limitation:** NACE J (Norway) and NAICS 51 (US) are the best available proxies for "
    "'tech' but are not identical — NACE J includes publishing and broadcasting. "
    "Treat sector comparisons as indicative, not exact."
)
