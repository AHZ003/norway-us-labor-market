# Norway vs. United States: Labor Market Comparison Dashboard

Interactive dashboard comparing employment, wages, and unemployment trends
between Norway and the United States (2010–2024), with a focus on the
technology sector. Built with real government data from Statistics Norway
(SSB) and the U.S. Bureau of Labor Statistics (BLS).

## Key Findings

*(Fill these in after running the real data pipeline — replace the placeholders below with your actual numbers.)*

1. **Unemployment resilience:** Norway's unemployment rate peaked at X% during COVID-19 (2020) vs. Y% in the US — a gap of Z percentage points, reflecting Norway's active labor market policies and social safety net.
2. **Tech wage gap (PPP-adjusted):** US tech workers earned ~$X more annually than Norwegian tech workers in PPP-adjusted terms in 2023, though the total compensation picture is more complex (benefits, hours, public services).
3. **Tech employment share:** X% of Norway's workforce is in the ICT sector vs. Y% in the US (2023), suggesting a [larger/smaller] relative tech workforce.

## Screenshot

*(Add a screenshot of the running dashboard here)*

## Data Sources

- [Statistics Norway (SSB)](https://data.ssb.no/api/v0/en/) — Employment, wages, and unemployment via SSB Open Data API (no API key required)
- [U.S. Bureau of Labor Statistics (BLS)](https://www.bls.gov/developers/) — IT employment, wages, and unemployment rate via BLS Public Data API v2
- [OECD](https://stats.oecd.org/) — Purchasing Power Parity (PPP) conversion factors for Norway

## Methodology

- **Industry mapping:** Norway NACE code J (Information & Communication) → US NAICS 51 (Information). Not a perfect match — see Limitations.
- **Wage normalization:** Norwegian monthly NOK wages converted to annual USD using OECD PPP factors (NOK ÷ PPP factor × 12). US hourly wages annualized at 2,080 hours/year.
- **Time aggregation:** Monthly BLS and SSB data averaged to annual figures for comparability.

## Tech Stack

Python · PostgreSQL · Streamlit · Plotly · Pandas · SQLAlchemy · SSB API · BLS API

## Project Structure

```
norway-us-labor-market/
├── app/dashboard.py          # Streamlit dashboard
├── src/
│   ├── fetch_ssb.py          # Norway data fetcher (SSB API)
│   ├── fetch_bls.py          # US data fetcher (BLS API)
│   ├── clean.py              # Data cleaning and normalization
│   ├── database.py           # PostgreSQL schema loading
│   └── analyze.py            # SQL analysis functions
├── sql/
│   ├── create_tables.sql     # Database schema DDL
│   └── queries.sql           # Analytical SQL queries
├── notebooks/exploration.ipynb   # EDA notebook
├── data/
│   ├── raw/                  # Raw API responses (gitignored)
│   └── processed/            # Cleaned CSVs
├── generate_sample_data.py   # Creates sample data for demo
├── run_pipeline.py           # Full data pipeline runner
└── requirements.txt
```

## How to Run

### Quick demo (no API keys needed)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate sample data based on published statistics
python generate_sample_data.py

# 3. Launch the dashboard
streamlit run app/dashboard.py
```

### With real API data

```bash
# 1. Copy and fill in your credentials
cp .env.example .env
# Add your BLS API key (free registration at https://data.bls.gov/registrationEngine/)

# 2. Run the full pipeline
python run_pipeline.py

# 3. (Optional) Load into PostgreSQL
python run_pipeline.py --load-db

# 4. Launch the dashboard
streamlit run app/dashboard.py
```

### PostgreSQL setup (optional)

```bash
createdb norway_us_labor
psql norway_us_labor < sql/create_tables.sql
python src/database.py
```

## Limitations

- **Industry classification mismatch:** NACE J (Norway) includes publishing and broadcasting that are not in NAICS 51 (US). Sector-level comparisons are indicative.
- **PPP approximation:** OECD PPP factors are economy-wide averages. Tech workers in Oslo or San Francisco face different local costs than the national average.
- **Wage coverage gaps:** SSB wages cover full-time employees in registered enterprises; BLS IT wages may exclude some worker categories. Neither fully captures gig workers.
- **Annual aggregation:** Monthly COVID spike (US: 14.7% in April 2020) is smoothed in annual averages.

---

*Built with assistance from Claude Code for API integration and data pipeline scaffolding.*
