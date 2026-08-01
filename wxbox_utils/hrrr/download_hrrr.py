#!/usr/bin/env python3

"""
WxBox HRRR Downloader

Downloads HRRR analyses for a specified cycle window.

Example
-------

python download_hrrr.py hrrr_download.yaml
"""

import sys
import yaml

from pathlib import Path

from datetime import datetime
from datetime import timedelta

import boto3

from botocore import UNSIGNED
from botocore.config import Config


# =====================================================
# Downloader
# =====================================================

class HRRRDownloader:

    def __init__(self, cfg):

        self.cfg = cfg

        self.bucket = (
            cfg["hrrr"]["bucket"]
        )

        self.product = (
            cfg["hrrr"]["product"]
        )

        self.forecast_hour = int(
            cfg["hrrr"]["forecast_hour"]
        )

        self.output_root = Path(
            cfg["output"]["root"]
        )

        self.output_root.mkdir(
            parents=True,
            exist_ok=True
        )

        self.s3 = boto3.client(
            "s3",
            config=Config(
                signature_version=UNSIGNED
            )
        )

        self.downloaded = 0
        self.skipped = 0
        self.failed = 0

    # -------------------------------------------------

    @staticmethod
    def size_mb(path):

        return (
            path.stat().st_size
            / 1024.0
            / 1024.0
        )

    # -------------------------------------------------

    def discover_cycles(self):

        start = datetime.strptime(
            self.cfg["cycles"]["start"],
            "%Y%m%dT%HZ"
        )

        end = datetime.strptime(
            self.cfg["cycles"]["end"],
            "%Y%m%dT%HZ"
        )

        interval = int(
            self.cfg["cycles"].get(
                "interval_hours",
                12
            )
        )

        cycles = []

        current = start

        while current <= end:

            cycles.append(
                current.strftime(
                    "%Y%m%dT%HZ"
                )
            )

            current += timedelta(
                hours=interval
            )

        return cycles

    # -------------------------------------------------

    def download_cycle(
        self,
        cycle_tag
    ):

        date = cycle_tag[:8]

        hour = (
            cycle_tag
            .split("T")[1]
            .replace("Z", "")
        )

        aws_key = (
            f"hrrr.{date}/conus/"
            f"hrrr.t{hour}z."
            f"{self.product}"
            f"{self.forecast_hour:02d}"
            ".grib2"
        )

        cycle_dir = (
            self.output_root
            / cycle_tag
        )

        cycle_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        outfile = (
            cycle_dir
            /
            (
                f"hrrr.t{hour}z."
                f"{self.product}"
                f"{self.forecast_hour:02d}"
                ".grib2"
            )
        )

        print()
        print(
            f"Cycle: {cycle_tag}"
        )

        if outfile.exists():

            print(
                "  SKIP"
            )

            print(
                f"  {outfile}"
            )

            print(
                f"  {self.size_mb(outfile):.1f} MB"
            )

            self.skipped += 1

            return

        print(
            f"  Bucket : {self.bucket}"
        )

        print(
            f"  Key    : {aws_key}"
        )

        print(
            f"  Output : {outfile}"
        )

        try:

            self.s3.download_file(
                self.bucket,
                aws_key,
                str(outfile)
            )

            size = (
                self.size_mb(outfile)
            )

            print(
                f"  SUCCESS "
                f"({size:.1f} MB)"
            )

            self.downloaded += 1

        except Exception as e:

            print()
            print(
                "  FAILED"
            )

            print(
                f"  {e}"
            )

            self.failed += 1

    # -------------------------------------------------

    def summary(self):

        print()
        print(
            "=" * 60
        )

        print(
            "HRRR Download Summary"
        )

        print(
            "=" * 60
        )

        print(
            f"Downloaded : "
            f"{self.downloaded}"
        )

        print(
            f"Skipped    : "
            f"{self.skipped}"
        )

        print(
            f"Failed     : "
            f"{self.failed}"
        )

        print()

    # -------------------------------------------------

    def run(self):

        print()
        print(
            "=" * 60
        )

        print(
            "WxBox HRRR Downloader"
        )

        print(
            "=" * 60
        )

        cycles = (
            self.discover_cycles()
        )

        print()

        print(
            f"Cycles: "
            f"{len(cycles)}"
        )

        print()

        for cycle in cycles:

            self.download_cycle(
                cycle
            )

        self.summary()


# =====================================================
# Main
# =====================================================

def main():

    if len(sys.argv) != 2:

        print()

        print(
            "Usage:\n"
            "python "
            "download_hrrr.py "
            "hrrr_download.yaml"
        )

        print()

        sys.exit(1)

    with open(
        sys.argv[1],
        "r"
    ) as f:

        cfg = yaml.safe_load(f)

    downloader = HRRRDownloader(
        cfg
    )

    downloader.run()


if __name__ == "__main__":

    main()
