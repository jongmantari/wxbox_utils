#!/usr/bin/env python3

"""
post/summary_plots.py

Experiment-level summary plots.

Reads:

    cycle_stats.json

Produces:

    innovation_timeseries.png

    rmse_timeseries.png

    obs_count_timeseries.png

    assimilation_rate_timeseries.png

    spread_timeseries.png

"""

from pathlib import Path
import json

import pandas as pd

import matplotlib.pyplot as plt

import numpy as np

# =====================================================
# Cycle Tick Helper
# =====================================================

def apply_cycle_ticks(df):

    n = len(df)

    #
    # About 15 labels max
    #
    stride = max(
        1,
        n // 15
    )

    idx = np.arange(
        0,
        n,
        stride,
    )

    plt.xticks(
        idx,
        df["cycle"].iloc[idx],
        rotation=45,
        ha="right",
    )

# =====================================================
# Load Summary Table
# =====================================================

def load_cycle_statistics(experiment_dir):

    experiment_dir = Path(
        experiment_dir
    )

    stats_files = sorted(

        experiment_dir.glob(
            "*/letkf/post/cycle_stats.json"
        )
    )

    records = []

    for f in stats_files:

        with open(f) as fp:

            records.append(
                json.load(fp)
            )

    if not records:

        raise RuntimeError(
            f"No cycle_stats.json found under "
            f"{experiment_dir}"
        )

    df = pd.DataFrame(
        records
    )

    df = df.sort_values(
        "cycle"
    )

    return df


# =====================================================
# Helpers
# =====================================================

def save_plot(outfile):

    plt.legend()

    plt.grid(
        alpha=0.30
    )

    plt.tight_layout()

    plt.savefig(
        outfile,
        bbox_inches="tight",
        dpi=150,
    )

    plt.close()


# =====================================================
# Innovation Means
# =====================================================

def plot_innovation_timeseries(
    df,
    outfile,
):

    plt.figure(
        figsize=(14, 5)
    )

    x = np.arange(
        len(df)
    )

    plt.plot(
        x,
        df["omb_mean"],
        "-",
        lw=1.5, markersize=3,
        label="OMB Mean",
    )

    plt.plot(
        x,
        df["oma_mean"],
        "-",
        lw=1.5, markersize=3,
        label="OMA Mean",
    )

    plt.ylabel(
        "Mean Innovation"
    )

    plt.xlabel(
        "Cycle"
    )

    #
    # show ~12 cycle labels
    #
    stride = max(
        1,
        len(df) // 12
    )

    idx = np.arange(
        0,
        len(df),
        stride,
    )

    plt.xticks(
        idx,
        df["cycle"].iloc[idx],
        rotation=45,
        ha="right",
    )

    plt.title(
        "Innovation Mean Time Series"
    )

    save_plot(
        outfile
    )

# =====================================================
# RMSE
# =====================================================

def plot_rmse_timeseries(
    df,
    outfile,
):

    plt.figure(
        figsize=(12, 4)
    )

    x = np.arange(
        len(df)
    )

    plt.plot(
        x,
        df["omb_rmse"],
        "-o",
        lw=1.5, markersize=3,
        label="OMB RMSE",
    )

    plt.plot(
        x,
        df["oma_rmse"],
        "-o",
        lw=1.5, markersize=3,
        label="OMA RMSE",
    )

    plt.ylabel(
        "RMSE"
    )

    plt.xlabel(
        "Cycle"
    )

    apply_cycle_ticks(df)

    plt.title(
        "RMSE Time Series"
    )

    save_plot(
        outfile
    )


# =====================================================
# Observation Counts
# =====================================================

def plot_obs_count_timeseries(
    df,
    outfile,
):

    plt.figure(
        figsize=(12, 4)
    )

    x = np.arange(
        len(df)
    )

    plt.plot(
        x,
        df["nobs_total"],
        "-o",
        lw=1.5, markersize=3,
        label="Total Obs",
    )

    plt.plot(
        x,
        df["nobs_assimilated"],
        "-o",
        lw=1.5, markersize=3,
        label="Assimilated Obs",
    )

    plt.ylabel(
        "Count"
    )

    plt.xlabel(
        "Cycle"
    )

    apply_cycle_ticks(df)

    plt.title(
        "Observation Counts"
    )

    save_plot(
        outfile
    )

# =====================================================
# Assimilation Rate
# =====================================================

def plot_assimilation_rate(
    df,
    outfile,
):

    plt.figure(
        figsize=(12, 4)
    )

    x = np.arange(
        len(df)
    )

    plt.plot(
        x,
        df["assimilation_rate"],
        "-o",
        lw=1.5, markersize=3,
    )

    plt.ylabel(
        "Assimilation Rate (%)"
    )

    plt.xlabel(
        "Cycle"
    )

    apply_cycle_ticks(df)

    plt.title(
        "Assimilation Rate"
    )

    plt.grid(
        alpha=0.30
    )

    plt.tight_layout()

    plt.savefig(
        outfile,
        bbox_inches="tight",
        dpi=150,
    )

    plt.close()


# =====================================================
# Spread Evolution
# =====================================================

def plot_spread_timeseries(
    df,
    outfile,
):

    plt.figure(
        figsize=(12, 4)
    )

    x = np.arange(
        len(df)
    )

    plt.plot(
        x,
        df["spread_background"],
        "-o",
        lw=1.5, markersize=3,
        label="Background",
    )

    plt.plot(
        x,
        df["spread_analysis"],
        "-o",
        lw=1.5, markersize=3,
        label="Analysis",
    )

    plt.ylabel(
        "Mean Spread"
    )

    plt.xlabel(
        "Cycle"
    )

    apply_cycle_ticks(df)

    plt.title(
        "Spread Evolution"
    )

    save_plot(
        outfile
    )

# =====================================================
# CSV
# =====================================================

def write_summary_csv(
    df,
    outfile,
):

    df.to_csv(
        outfile,
        index=False,
    )


# =====================================================
# Generate All
# =====================================================

def generate_summary_plots(

    experiment_dir,

    output_dir,

):

    df = load_cycle_statistics(
        experiment_dir
    )

    output_dir = Path(
        output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_summary_csv(

        df,

        output_dir
        / "summary_table.csv",
    )

    plot_innovation_timeseries(

        df,

        output_dir
        / "innovation_timeseries.png",
    )

    plot_rmse_timeseries(

        df,

        output_dir
        / "rmse_timeseries.png",
    )

    plot_obs_count_timeseries(

        df,

        output_dir
        / "obs_count_timeseries.png",
    )

    plot_assimilation_rate(

        df,

        output_dir
        / "assimilation_rate_timeseries.png",
    )

    plot_spread_timeseries(

        df,

        output_dir
        / "spread_timeseries.png",
    )

    return df


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--experiment-dir",
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        required=True,
    )

    args = parser.parse_args()

    generate_summary_plots(

        args.experiment_dir,

        args.output_dir,
    )
