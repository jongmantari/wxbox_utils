#!/usr/bin/env python3

"""
cycle_stats.py

Extract cycle-level LETKF statistics from
diag_*.nc4 files.

Outputs:

{
  "experiment": "c1667",
  "cycle": "20260723T12Z",

  "nobs_total": 59,
  "nobs_assimilated": 59,
  "assimilation_rate": 100.0,

  "omb_mean": 0.74,
  "oma_mean": 0.53,

  "omb_rmse": 1.18,
  "oma_rmse": 0.87,

  "spread_background": 1.25,
  "spread_analysis": 0.98,

  "spread_reduction": 21.6
}

"""

from pathlib import Path
import json

import numpy as np
import xarray as xr
import netCDF4 as nc


# ======================================================
# Basic Helpers
# ======================================================

def rmse(x):

    x = np.asarray(x)

    return float(
        np.sqrt(
            np.nanmean(x ** 2)
        )
    )


def mean_abs(x):

    x = np.asarray(x)

    return float(
        np.nanmean(
            np.abs(x)
        )
    )


# ======================================================
# Diagnostics Readers
# ======================================================

def read_group(obsdiag_file, group):

    return xr.open_dataset(
        obsdiag_file,
        group=group,
        engine="netcdf4",
    )


def read_obs_values(
    obsdiag_file,
    obsvar,
):

    ds = read_group(
        obsdiag_file,
        "ObsValue",
    )

    return ds[obsvar].values


def read_omb(
    obsdiag_file,
    obsvar,
):

    ds = read_group(
        obsdiag_file,
        "ombg",
    )

    return ds[obsvar].values


def read_oma(
    obsdiag_file,
    obsvar,
):

    ds = read_group(
        obsdiag_file,
        "oman",
    )

    return ds[obsvar].values


def read_qc(
    obsdiag_file,
    qc_group,
    obsvar,
):

    ds = read_group(
        obsdiag_file,
        qc_group,
    )

    return ds[obsvar].values


# ======================================================
# Ensemble HofX Spread
# ======================================================

def read_hofx_members(
    obsdiag_file,
    prefix,
    obsvar,
):

    root = nc.Dataset(
        obsdiag_file
    )

    groups = list(
        root.groups.keys()
    )

    root.close()

    member_groups = sorted(

        [
            g
            for g in groups
            if g.startswith(prefix)
        ]
    )

    members = []

    for g in member_groups:

        ds = xr.open_dataset(
            obsdiag_file,
            group=g,
            engine="netcdf4",
        )

        members.append(
            ds[obsvar].values
        )

    return np.asarray(
        members
    )


def compute_spreads(
    obsdiag_file,
    obsvar,
):

    hofx0 = read_hofx_members(
        obsdiag_file,
        "hofx0_",
        obsvar,
    )

    hofx1 = read_hofx_members(
        obsdiag_file,
        "hofx1_",
        obsvar,
    )

    spread_b_pt = np.std(
        hofx0,
        axis=0,
    )

    spread_a_pt = np.std(
        hofx1,
        axis=0,
    )

    spread_b = float(
        np.nanmean(
            spread_b_pt
        )
    )

    spread_a = float(
        np.nanmean(
            spread_a_pt
        )
    )

    if spread_b > 0.0:

        reduction = float(
            100.0
            *
            (
                spread_b
                - spread_a
            )
            / spread_b
        )

    else:

        reduction = 0.0

    return (
        spread_b,
        spread_a,
        reduction,
    )


# ======================================================
# Main Statistics
# ======================================================

def compute_cycle_statistics(

    experiment,
    cycle,

    obsdiag_file,

    obs_variable,

    qc_group,

):

    obsval = read_obs_values(
        obsdiag_file,
        obs_variable,
    )

    ombg = read_omb(
        obsdiag_file,
        obs_variable,
    )

    oman = read_oma(
        obsdiag_file,
        obs_variable,
    )

    qc = read_qc(
        obsdiag_file,
        qc_group,
        obs_variable,
    )

    mask = (
        np.isfinite(obsval)
        &
        np.isfinite(ombg)
        &
        np.isfinite(oman)
    )

    obsval = obsval[mask]
    ombg = ombg[mask]
    oman = oman[mask]
    qc = qc[mask]

    nobs_total = int(
        len(obsval)
    )

    #
    # EffectiveQC0 confirmed:
    #
    # 0 == assimilated
    #
    nobs_assimilated = int(
        np.sum(qc == 0)
    )

    if nobs_total > 0:

        assimilation_rate = (

            100.0

            *

            nobs_assimilated

            /

            nobs_total

        )

    else:

        assimilation_rate = 0.0

    spread_b, spread_a, spread_reduction = (
        compute_spreads(
            obsdiag_file,
            obs_variable,
        )
    )

    stats = {

        "experiment":
            experiment,

        "cycle":
            cycle,

        "nobs_total":
            nobs_total,

        "nobs_assimilated":
            nobs_assimilated,

        "assimilation_rate":
            round(
                assimilation_rate,
                3,
            ),

        "omb_mean":
            round(
                mean_abs(ombg),
                6,
            ),

        "oma_mean":
            round(
                mean_abs(oman),
                6,
            ),

        "omb_rmse":
            round(
                rmse(ombg),
                6,
            ),

        "oma_rmse":
            round(
                rmse(oman),
                6,
            ),

        "spread_background":
            round(
                spread_b,
                6,
            ),

        "spread_analysis":
            round(
                spread_a,
                6,
            ),

        "spread_reduction":
            round(
                spread_reduction,
                3,
            ),
    }

    return stats


# ======================================================
# JSON Writer
# ======================================================

def write_cycle_statistics(

    stats,

    output_json,

):

    output_json = Path(
        output_json
    )

    output_json.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_json,
        "w",
    ) as f:

        json.dump(
            stats,
            f,
            indent=2,
        )

    return output_json


# ======================================================
# CLI
# ======================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--experiment",
        required=True,
    )

    parser.add_argument(
        "--cycle",
        required=True,
    )

    parser.add_argument(
        "--obsdiag",
        required=True,
    )

    parser.add_argument(
        "--obs-variable",
        default="airTemperatureAt2M",
    )

    parser.add_argument(
        "--qc-group",
        default="EffectiveQC0",
    )

    parser.add_argument(
        "--output-json",
        required=True,
    )

    args = parser.parse_args()

    stats = compute_cycle_statistics(

        experiment=
            args.experiment,

        cycle=
            args.cycle,

        obsdiag_file=
            args.obsdiag,

        obs_variable=
            args.obs_variable,

        qc_group=
            args.qc_group,
    )

    outfile = write_cycle_statistics(

        stats,

        args.output_json,
    )

    print()
    print("Cycle statistics:")
    print(json.dumps(stats, indent=2))
    print()
    print("Wrote:", outfile)
