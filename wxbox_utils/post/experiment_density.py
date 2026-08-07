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

    qc_group = (
        cfg["post"]
        ["diagnostics"]
        ["qc_group"]
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

            qc_ds = xr.open_dataset(
                diag,
                group=qc_group,
                engine="netcdf4",
            )

            ombg = np.asarray(
                ombg_ds[
                    obsvar
                ].values,
                dtype=np.float64,
            )

            oman = np.asarray(
                oman_ds[
                    obsvar
                ].values,
                dtype=np.float64,
            )

            qc = qc_ds[
                obsvar
            ].values

            #
            # Remove IODA fill values
            #
            ombg[
                np.abs(ombg) > 1.0e30
            ] = np.nan

            oman[
                np.abs(oman) > 1.0e30
            ] = np.nan

            #
            # Assimilated obs only
            #
            mask = (
                np.isfinite(ombg)
                &
                np.isfinite(oman)
                &
                (qc == 0)
            )

            ombg = ombg[
                mask
            ]

            oman = oman[
                mask
            ]

            if len(ombg) == 0:
                continue

            print(
                f"[READ] {cycle} "
                f"n={len(ombg)} "
                f"OMB[{ombg.min():.2f},{ombg.max():.2f}] "
                f"OMA[{oman.min():.2f},{oman.max():.2f}]"
            )

            ombg_all.extend(
                ombg.tolist()
            )

            oman_all.extend(
                oman.tolist()
            )

        except Exception as e:

            print(
                f"[SKIP] {cycle}"
            )

            print(
                f"       {e}"
            )

    return (
        np.asarray(
            ombg_all,
            dtype=np.float64,
        ),
        np.asarray(
            oman_all,
            dtype=np.float64,
        ),
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

    ombg = np.asarray(
        ombg,
        dtype=np.float64,
    )

    oman = np.asarray(
        oman,
        dtype=np.float64,
    )

    ombg = ombg[
        np.isfinite(ombg)
    ]

    oman = oman[
        np.isfinite(oman)
    ]

    if len(ombg) < 3:

        raise RuntimeError(
            "No valid OMB values"
        )

    if len(oman) < 3:

        raise RuntimeError(
            "No valid OMA values"
        )

    print()

    print(
        f"[DENSITY] "
        f"OMB {ombg.min():.3f} "
        f"{ombg.max():.3f}"
    )

    print(
        f"[DENSITY] "
        f"OMA {oman.min():.3f} "
        f"{oman.max():.3f}"
    )

    xmin = min(
        np.min(ombg),
        np.min(oman),
    )

    xmax = max(
        np.max(ombg),
        np.max(oman),
    )

    if abs(
        xmax - xmin
    ) < 1.0e-6:

        xmin -= 1.0
        xmax += 1.0

    xx = np.linspace(
        xmin,
        xmax,
        points,
    )

    #
    # Use default KDE
    #
    kde_omb = gaussian_kde(
        ombg
    )

    kde_oma = gaussian_kde(
        oman
    )

    yy_omb = kde_omb(xx)
    yy_oma = kde_oma(xx)

    plt.figure(
        figsize=(8, 6)
    )

    plt.plot(
        xx,
        yy_omb,
        lw=3,
        label="OMB",
    )

    plt.plot(
        xx,
        yy_oma,
        lw=3,
        label="OMA",
    )

    plt.grid(
        alpha=0.3
    )

    plt.legend()

    plt.xlabel(
        "Innovation (K)"
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

def main():

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "config"
    )

    args = parser.parse_args()

    cfg = load_yaml(
        args.config
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
        cfg["post"]["density"]
        ["bandwidth"],
        points=
        cfg["post"]["density"]
        ["points"],
    )

    print()
    print(
        f"[DONE] {outfile}"
    )


if __name__ == "__main__":
    main()
