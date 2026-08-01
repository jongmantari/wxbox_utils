#!/usr/bin/env python3

"""
post/pdf_report.py

Build experiment-level summary PDF.

Inputs:

    innovation_timeseries.png
    rmse_timeseries.png
    obs_count_timeseries.png
    assimilation_rate_timeseries.png
    spread_timeseries.png
    experiment_density.png

    summary_table.csv

Output:

    experiment_summary.pdf

"""

from pathlib import Path

import pandas as pd

from matplotlib.backends.backend_pdf import PdfPages

import matplotlib.pyplot as plt

import matplotlib.image as mpimg


# =====================================================
# Helpers
# =====================================================

def add_image_page(

    pdf,

    image_file,

    title,

):

    fig = plt.figure(
        figsize=(8.5, 11)
    )

    ax = fig.add_subplot(
        111
    )

    ax.axis("off")

    img = mpimg.imread(
        image_file
    )

    ax.imshow(
        img
    )

    plt.title(
        title,
        fontsize=16,
    )

    pdf.savefig(
        fig,
        bbox_inches="tight",
    )

    plt.close(fig)


# =====================================================
# Executive Summary Page
# =====================================================

def build_summary_page(

    pdf,

    df,

    experiment,

):

    ncycles = len(df)

    total_obs = int(
        df["nobs_total"].sum()
    )

    total_assim = int(
        df["nobs_assimilated"].sum()
    )

    assim_rate = (

        100.0

        *

        total_assim

        /

        total_obs

    )

    fig = plt.figure(
        figsize=(8.5, 11)
    )

    plt.axis("off")

    start_cycle = (
        df["cycle"]
        .iloc[0]
    )

    end_cycle = (
        df["cycle"]
        .iloc[-1]
    )

    text = f"""
LETKF Experiment Summary

Experiment:
{experiment}

Cycles:
{start_cycle}
to
{end_cycle}

Number of Cycles:
{ncycles}

Total Observations:
{total_obs}

Assimilated Observations:
{total_assim}

Assimilation Rate:
{assim_rate:.2f} %

Mean OMB:
{df['omb_mean'].mean():.3f}

Mean OMA:
{df['oma_mean'].mean():.3f}

Mean OMB RMSE:
{df['omb_rmse'].mean():.3f}

Mean OMA RMSE:
{df['oma_rmse'].mean():.3f}

Mean Background Spread:
{df['spread_background'].mean():.3f}

Mean Analysis Spread:
{df['spread_analysis'].mean():.3f}

Mean Spread Reduction:
{df['spread_reduction'].mean():.2f} %
"""

    plt.text(

        0.05,
        0.95,

        text,

        va="top",

        fontsize=12,

        family="monospace",
    )

    pdf.savefig(
        fig,
        bbox_inches="tight",
    )

    plt.close(fig)


# =====================================================
# Main Builder
# =====================================================

def build_experiment_report(

    experiment,

    summary_csv,

    output_pdf,

    innovation_png,

    rmse_png,

    obs_count_png,

    assimilation_png,

    spread_png,

    density_png,

):

    df = pd.read_csv(
        summary_csv
    )

    with PdfPages(
        output_pdf
    ) as pdf:

        build_summary_page(

            pdf,

            df,

            experiment,
        )

        image_list = [

            (
                innovation_png,
                "Innovation Means",
            ),

            (
                rmse_png,
                "RMSE Evolution",
            ),

            (
                obs_count_png,
                "Observation Counts",
            ),

            (
                assimilation_png,
                "Assimilation Rate",
            ),

            (
                spread_png,
                "Spread Evolution",
            ),

            (
                density_png,
                "Experiment Density",
            ),
        ]

        for image_file, title in image_list:

            image_file = Path(
                image_file
            )

            if image_file.exists():

                add_image_page(

                    pdf,

                    image_file,

                    title,
                )

    return output_pdf


# =====================================================
# CLI
# =====================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--experiment",
        required=True,
    )

    parser.add_argument(
        "--summary-csv",
        required=True,
    )

    parser.add_argument(
        "--output-pdf",
        required=True,
    )

    parser.add_argument(
        "--innovation-png",
        required=True,
    )

    parser.add_argument(
        "--rmse-png",
        required=True,
    )

    parser.add_argument(
        "--obs-count-png",
        required=True,
    )

    parser.add_argument(
        "--assimilation-png",
        required=True,
    )

    parser.add_argument(
        "--spread-png",
        required=True,
    )

    parser.add_argument(
        "--density-png",
        required=True,
    )

    args = parser.parse_args()

    pdf = build_experiment_report(

        experiment=
            args.experiment,

        summary_csv=
            args.summary_csv,

        output_pdf=
            args.output_pdf,

        innovation_png=
            args.innovation_png,

        rmse_png=
            args.rmse_png,

        obs_count_png=
            args.obs_count_png,

        assimilation_png=
            args.assimilation_png,

        spread_png=
            args.spread_png,

        density_png=
            args.density_png,
    )

    print()
    print(
        f"Wrote: {pdf}"
    )
