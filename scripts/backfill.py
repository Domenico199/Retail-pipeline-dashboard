"""
Backfill script: generates historical data day by day and runs the full pipeline
after each day, so that inventory is updated before generating the next day.

Usage:
    python scripts/backfill.py --start 2026-01-01 --end 2026-03-31
"""

import argparse
import os
from datetime import datetime, timedelta

from scripts.simulate_api_daily_dump import main as simulate
from pipeline.extract.extract_raw_movements import main as extract
from pipeline.transform.transform_raw_movements import main as transform
from pipeline.load.load_movements import main as load


def daterange(start_date, end_date):
    """Yield each date from start to end (inclusive)."""
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser(description="Backfill historical data")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end, "%Y-%m-%d").date()

    total_days = (end_date - start_date).days + 1
    print(f"Backfill: {start_date} → {end_date} ({total_days} days)")
    print("=" * 60)

    for i, date in enumerate(daterange(start_date, end_date), 1):
        date_str = date.strftime("%Y-%m-%d")
        file_name = f"movements_{date_str}.csv"
        file_path = os.path.join("data/source", file_name)

        print(f"\n[{i}/{total_days}] {date_str}")
        print("-" * 40)

        # Skip if CSV already exists (avoid overwriting processed data)
        if os.path.exists(file_path):
            print(f"  ⏭ CSV already exists, skipping generation")
        else:
            simulate(date_str)

        extract()
        transform()
        load()

    print("\n" + "=" * 60)
    print(f"Backfill complete: {total_days} days processed.")


if __name__ == "__main__":
    main()
