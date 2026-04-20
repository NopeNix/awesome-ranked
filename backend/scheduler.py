import os
import time

import schedule

from scraper import backfill_and_update
from database import ensure_schema


def _source_url() -> str:
    return os.getenv(
        "SCRAPE_SOURCE_URL",
        "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/refs/heads/master/README.md",
    )


def _interval_hours() -> int:
    try:
        return int(os.getenv("SCRAPE_INTERVAL_HOURS", "24"))
    except ValueError:
        return 24


def job():
    ensure_schema()
    # Run in event loop via scraper
    import asyncio

    stats = asyncio.run(backfill_and_update(_source_url()))
    print(f"[scheduler] scrape stats: {stats}", flush=True)


def main():
    schedule.every(_interval_hours()).hours.do(job)
    job()
    while True:
        schedule.run_pending()
        time.sleep(5)


if __name__ == "__main__":
    main()
