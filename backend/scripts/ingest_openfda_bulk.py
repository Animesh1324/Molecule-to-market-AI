#!/usr/bin/env python3
"""Load the openFDA drug corpus into the Drug Intelligence catalogue.

The live openFDA adapter answers one search at a time and cannot page past
25,000 records. This loads the complete published bulk partitions instead:
roughly 137k marketed products (NDC) and 262k labels.

    # Everything (several hours, ~15 GB of transient download)
    python scripts/ingest_openfda_bulk.py

    # A quick representative slice to populate a dev database
    python scripts/ingest_openfda_bulk.py --limit 5000

    # Product identity only, no clinical narrative
    python scripts/ingest_openfda_bulk.py --datasets ndc

Writes through the same repository as every other source, so rows carry normal
provenance and the merge policy protects data an earlier source supplied.
Re-running is safe: records upsert on (generic_name, brand_name).
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db  # noqa: E402
from app.services import openfda_bulk_ingest as bulk  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--datasets", default="ndc,label",
                        help="comma-separated openFDA drug datasets (default: ndc,label)")
    parser.add_argument("--limit", type=int, default=None,
                        help="stop after N records per dataset (for a dev slice)")
    parser.add_argument("--max-partitions", type=int, default=None,
                        help="load at most N partitions per dataset")
    parser.add_argument("--cache-dir", default=None,
                        help="where partitions are downloaded (default: system temp)")
    parser.add_argument("--keep-files", action="store_true",
                        help="keep unpacked JSON instead of deleting after load")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    datasets = [d.strip() for d in args.datasets.split(",") if d.strip()]
    unknown = [d for d in datasets if d not in ("ndc", "label")]
    if unknown:
        parser.error(f"no bulk mapper for: {', '.join(unknown)}")

    init_db()

    started = time.time()

    def progress(result: bulk.IngestResult) -> None:
        rate = result.read / max(time.time() - started, 1e-6)
        print(f"  {result.dataset}: read {result.read:,} written {result.written:,} "
              f"unidentifiable {result.unidentifiable:,} failed {result.failed:,} ({rate:,.0f}/s)",
              end="\r", flush=True)

    results = bulk.ingest(
        datasets,
        cache_dir=args.cache_dir,
        limit=args.limit,
        max_partitions=args.max_partitions,
        progress=progress,
        keep_files=args.keep_files,
    )

    print(" " * 100, end="\r")
    print(f"\nCompleted in {time.time() - started:,.0f}s")
    failed_any = False
    for dataset, result in results.items():
        print(f"  {dataset:6s} partitions={result.partitions:<3} read={result.read:<8,} "
              f"written={result.written:<8,} unidentifiable={result.unidentifiable:<8,} "
              f"skipped={result.skipped:<5,} failed={result.failed:,}")
        if result.read == 0:
            failed_any = True

    from app.repositories import drug_repository as repo
    print(f"\nCatalogue now holds {repo.count_drugs():,} drugs.")
    return 1 if failed_any else 0


if __name__ == "__main__":
    raise SystemExit(main())
