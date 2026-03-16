"""
run_pipeline.py
---------------
Run the full data pipeline in order:
  1. Fetch data from SSB (Norway) API
  2. Fetch data from BLS (US) API
  3. Clean and normalize the data
  4. Load into PostgreSQL (optional)

Usage:
    python run_pipeline.py                  # Fetch + clean only
    python run_pipeline.py --load-db        # Also load into PostgreSQL
    python run_pipeline.py --sample-only    # Skip API calls, use sample data
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def main():
    parser = argparse.ArgumentParser(description="Run the Norway-US labor market data pipeline")
    parser.add_argument("--load-db",     action="store_true", help="Load cleaned data into PostgreSQL")
    parser.add_argument("--sample-only", action="store_true", help="Generate sample data instead of calling APIs")
    args = parser.parse_args()

    if args.sample_only:
        print("Generating sample data (no API calls)...")
        import generate_sample_data
        generate_sample_data.make_unemployment()
        generate_sample_data.make_wages()
        generate_sample_data.make_employment()
        print("\nSample data ready. Run:  streamlit run app/dashboard.py")
        return

    # Step 1: Fetch Norway data
    print("=" * 50)
    print("STEP 1: Fetching Norway data from SSB")
    print("=" * 50)
    try:
        from src.fetch_ssb import fetch_unemployment, fetch_wages, fetch_employment
        fetch_unemployment()
        fetch_wages()
        fetch_employment()
    except Exception as e:
        print(f"SSB fetch failed: {e}")
        print("Continuing with US data...\n")

    # Step 2: Fetch US data
    print("\n" + "=" * 50)
    print("STEP 2: Fetching US data from BLS")
    print("=" * 50)
    try:
        from src.fetch_bls import fetch_all
        fetch_all()
    except Exception as e:
        print(f"BLS fetch failed: {e}")
        print("Make sure BLS_API_KEY is set in .env\n")

    # Step 3: Clean data
    print("\n" + "=" * 50)
    print("STEP 3: Cleaning and normalizing data")
    print("=" * 50)
    try:
        from src.clean import run_all
        run_all()
    except Exception as e:
        print(f"Cleaning failed: {e}")
        raise

    # Step 4: Load to database (optional)
    if args.load_db:
        print("\n" + "=" * 50)
        print("STEP 4: Loading into PostgreSQL")
        print("=" * 50)
        try:
            from src.database import run_all as db_run_all
            db_run_all()
        except Exception as e:
            print(f"Database load failed: {e}")

    print("\n" + "=" * 50)
    print("Pipeline complete!")
    print("Run:  streamlit run app/dashboard.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
