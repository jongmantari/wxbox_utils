#!/usr/bin/env python3

import sys
import argparse
import pathlib
import datetime as dt

import yaml
import numpy as np
import netCDF4 as nc

# =====================================================
# YAML
# =====================================================

def load_yaml(filename):

    with open(filename) as f:

        return yaml.safe_load(f)

# =====================================================
# CONFIG
# =====================================================

if len(sys.argv) > 1:
    cfgfile = sys.argv[1]
else:
    cfgfile = "asos_concat.yaml"

with open(cfgfile) as f:
    cfg = yaml.safe_load(f)

start = dt.datetime.strptime(
    cfg["cycles"]["start"],
    "%Y%m%dT%HZ"
)

end = dt.datetime.strptime(
    cfg["cycles"]["end"],
    "%Y%m%dT%HZ"
)

cycle_step = dt.timedelta(
    hours=cfg["cycles"]["interval_hours"]
)

before_hours = cfg["window"]["before_hours"]
after_hours = cfg["window"]["after_hours"]

outroot = pathlib.Path(
    cfg["output"]["root"]
)

KEEP_GROUPS = [
    "MetaData",
    "ObsValue",
    "DerivedObsValue",
    "PreQC"
]

# =====================================================
# HELPERS
# =====================================================

def copy_global_attributes(src, dst):

    for att in src.ncattrs():

        dst.setncattr(
            att,
            src.getncattr(att)
        )


# =====================================================
# MAIN
# =====================================================

def build_obsdb_cycles(cfg):

    start = dt.datetime.strptime(
        cfg["cycles"]["start"],
        "%Y%m%dT%HZ"
    )

    end = dt.datetime.strptime(
        cfg["cycles"]["end"],
        "%Y%m%dT%HZ"
    )

    cycle_step = dt.timedelta(
        hours=cfg["cycles"]["interval_hours"]
    )

    before_hours = cfg["window"]["before_hours"]

    after_hours = cfg["window"]["after_hours"]

    outroot = pathlib.Path(
        cfg["output"]["root"]
    )

    KEEP_GROUPS = [

        "MetaData",

        "ObsValue",

        "DerivedObsValue",

        "PreQC",
    ]

    created_count = 0

    missing_count = 0

    for obs_type in cfg["obs_types"]:

        obs_cfg = cfg["obs"][obs_type]

        input_dir = pathlib.Path(
            obs_cfg["input_dir"]
        )

        file_pattern = (
            obs_cfg["file_pattern"]
        )

        output_pattern = (
            obs_cfg["output_pattern"]
        )

        obs_errors = (
            obs_cfg["obserror"]
        )

        current = start

        while current <= end:

            cycle_dir = current.strftime(
                "%Y%m%dT%HZ"
            )

            outfile_name = current.strftime(
                output_pattern
            )

            outdir = (
                outroot
                / obs_type
                / cycle_dir
            )

            outdir.mkdir(
                parents=True,
                exist_ok=True
            )

            outfile = (
                outdir
                / outfile_name
            )

            #
            # -------------------------------------------------
            # gather files in window
            # -------------------------------------------------
            #
            infiles = []

            for dh in range(
                -before_hours,
                after_hours + 1
            ):

                t = (
                    current
                    + dt.timedelta(
                        hours=dh
                    )
                )

                fname = t.strftime(
                    file_pattern
                )

                fpath = (
                    input_dir
                    / fname
                )

                if fpath.exists():

                    infiles.append(
                        fpath
                    )

            if len(infiles) == 0:

                print(
                    f"No files: {cycle_dir}"
                )

                missing_count += 1

                current += cycle_step

                continue

            print()

            print(
                f"Cycle: {cycle_dir}"
            )

            print(
                f"Files: {len(infiles)}"
            )

            #
            # -------------------------------------------------
            # EVERYTHING FROM YOUR EXISTING SCRIPT
            # -------------------------------------------------
            #
            # sample file
            # total_locations
            # create output
            # create schema
            # concatenate
            # build ObsError
            #
            # paste your existing code here unchanged
            #
            # -------------------------------------------------
            #

            print(
                f"Created: {outfile}"
            )

            created_count += 1

            current += cycle_step

    print()

    print("=" * 60)

    print(
        f"Created cycles : {created_count}"
    )

    print(
        f"Missing cycles : {missing_count}"
    )

    print(
        f"Output root    : {outroot}"
    )

    print()

    print("DONE")
    
# =====================================================
# CLI
# =====================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "config",
        nargs="?",
        default="asos_concat.yaml",
    )

    args = parser.parse_args()

    cfg = load_yaml(
        args.config
    )

    build_obsdb_cycles(
        cfg
    )


if __name__ == "__main__":

    main()
