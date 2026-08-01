#!/usr/bin/env python3

"""
Experiment-wide OMB/OMA density plot.

Usage:

python post/experiment_density.py \
    configs/experiments/c1667.yaml
"""

from pathlib import Path
from datetime import datetime, timedelta

import yaml
import numpy as np
import xarray as xr

import matplotlib.pyplot as plt

from scipy.stats import gaussian_kde


# =====================================================
# YAML
# =====================================================

def load_yaml(filename):

    with open(filename, "r") as f:
        return yaml.safe_load(f)


# =====================================================
# Cycle utilities
# =====================================================

def parse_cycle(cycle):

    return datetime.strptime(
        cycle,
        "%Y%m%dT%HZ",
    )


def format_cycle(dt):

    return dt.strftime(
        "%Y%m%dT%HZ",
    )


def range_cycles(
    start,
    end,
    frequency_hours,
):

    cycles = []

    current = parse_cycle(start)

    end_dt = parse_cycle(end)

    while current <= end_dt:

        cycles.append(
            format_cycle(current)
        )

        current += timedelta(
            hours=frequency_hours
        )

    return cycles


def discover_cycles(cfg):

    experiment_dir = Path(
        cfg["experiment_dir"]
    )

    cycles = []

    for d in sorted(
        experiment_dir.iterdir()
    ):

        if d.is_dir() and "T" in d.name:

            cycles.append(
                d.name
            )

    return cycles


def get_cycles(cfg):

    mode = (
        cfg["cycling"]["mode"]
        .lower()
    )

    if mode == "range":

        return range_cycles(

            cfg["cycling"]["start"],

            cfg["cycling"]["end"],

            cfg["cycling"]["frequency_hours"],
        )

    elif mode == "explicit":

        return (
            cfg["cycling"]["cycles"]
        )

    elif mode == "discover":

        return discover_cycles(cfg)

    else:

        raise ValueError(
            f"Unknown cycling mode: {mode}"
        )


# =====================================================
# Read all innovations
# =====================================================

def collect_innovations(cfg):

    experiment_dir = Path(
        cfg["experiment_dir"]
    )

    obsvar = (
        cfg["post"]
        ["diagnostics"]
        ["obs_variable"]
    )

    ombg_all = []

    oman_all = []

    cycles = get_cycles(cfg)

    for cycle in cycles:

        letkf_dir = (
            experiment_dir
            / cycle
            / "letkf"
        )

        diag_files = sorted(
            letkf_dir.glob(
                "diag_*.nc4"
            )
        )

        if not diag_files:
            continue

        diag = diag_files[0]

        try:

            ombg_ds = xr.open_dataset(
                diag,
                group="ombg",
                engine="netcdf4",
            )

            oman_ds = xr.open_dataset(
                diag,
                group="oman",
                engine="netcdf4",
            )

            ombg = ombg_ds[
                obsvar
            ].values

            oman = oman_ds[
                obsvar
            ].values

            ombg = ombg[
                np.isfinite(ombg)
            ]

            oman = oman[
                np.isfinite(oman)
            ]

            ombg_all.extend(
                ombg.tolist()
            )

            oman_all.extend(
                oman.tolist()
            )

            print(
                f"[READ] {cycle}"
            )

        except Exception as e:

            print(
                f"[SKIP] {cycle}"
            )

            print(
                f"       {e}"
            )

    return (
        np.asarray(ombg_all),
        np.asarray(oman_all),
    )


# =====================================================
# Density plot
# =====================================================

def build_density_plot(
    ombg,
    oman,
    outfile,
    bandwidth,
    points,
):

    if len(ombg) == 0:

        raise RuntimeError(
            "No OMB values collected"
        )

    if len(oman) == 0:

        raise RuntimeError(
            "No OMA values collected"
        )

    xmin = min(
        ombg.min(),
        oman.min(),
    )

    xmax = max(
        ombg.max(),
        oman.max(),
    )

    xx = np.linspace(
        xmin,
        xmax,
        points,
    )

    kde_omb = gaussian_kde(
        ombg,
        bw_method=bandwidth,
    )

    kde_oma = gaussian_kde(
        oman,
        bw_method=bandwidth,
    )

    plt.figure(
        figsize=(8, 6)
    )

    plt.plot(
        xx,
        kde_omb(xx),
        lw=3,
        label="OMB",
    )

    plt.plot(
        xx,
        kde_oma(xx),
        lw=3,
        label="OMA",
    )

    plt.grid(
        alpha=0.3
    )

    plt.legend()

    plt.xlabel(
        "Innovation"
    )

    plt.ylabel(
        "Density"
    )

    plt.title(
        "Experiment-Wide Innovation Density"
    )

    plt.tight_layout()

    plt.savefig(
        outfile,
        dpi=150,
    )

    plt.close()


# =====================================================
# Main
# =====================================================

def main(config_file):

    cfg = load_yaml(
        config_file
    )

    ombg, oman = (
        collect_innovations(
            cfg
        )
    )

    summary_dir = (
        Path(
            cfg["experiment_dir"]
        )
        / "post"
    )

    summary_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    outfile = (
        summary_dir
        / "experiment_density.png"
    )

    build_density_plot(

        ombg,
        oman,

        outfile,

        bandwidth=
        cfg["post"]
        ["density"]
        ["bandwidth"],

        points=
        cfg["post"]
        ["density"]
        ["points"],
    )

    print()
    print(
        f"[DONE] {outfile}"
    )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "config"
    )

    args = parser.parse_args()

    main(
        args.config
    )
