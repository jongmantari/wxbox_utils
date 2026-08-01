#!/usr/bin/env python3

"""
post/plot_cycle_surface2m.py

Single-cycle LETKF diagnostics workflow

Usage:

python post/plot_cycle_surface2m.py \
    runs/c1667/20260723T12Z/letkf/post/plot_surface2m.yaml

"""

import sys
import yaml

from pathlib import Path

import numpy as np
import xarray as xr

from scipy.ndimage import zoom

from matplotlib.backends.backend_pdf import PdfPages

from wxbox_utils.post.cycle_stats import (
    compute_cycle_statistics,
    write_cycle_statistics,
)

from wxbox_utils.post.cycle_plot import (
    plot_background,
    plot_analysis,
    plot_increment,

    plot_obs_map,
    plot_innovation_map,

    plot_vertical_profile,

    plot_spread,

    plot_density,

    plot_summary_page,
)


# =====================================================
# YAML
# =====================================================

def load_yaml(filename):

    with open(filename, "r") as f:

        return yaml.safe_load(f)


# =====================================================
# PDF
# =====================================================

def build_pdf(

    png_files,

    output_pdf,

):

    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg

    with PdfPages(
        output_pdf
    ) as pdf:

        for png in png_files:

            fig = plt.figure(
                figsize=(8.5, 11)
            )

            ax = fig.add_subplot(
                111
            )

            ax.axis("off")

            img = mpimg.imread(
                png
            )

            ax.imshow(
                img
            )

            pdf.savefig(
                fig,
                bbox_inches="tight",
            )

            plt.close(fig)


# =====================================================
# Main
# =====================================================

def main(yaml_file):

    cfg = load_yaml(
        yaml_file
    )

    experiment = (
        cfg["experiment"]
    )

    cycle = (
        cfg["cycle"]
    )

    outdir = Path(
        cfg["output"]
        ["outdir"]
    )

    outdir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------
    # Files
    # -----------------------------------

    bkg_file = (
        cfg["files"]
        ["background"]
    )

    inc_file = (
        cfg["files"]
        ["increment"]
    )

    grid_file = (
        cfg["files"]
        ["grid"]
    )

    obsdiag_file = (
        cfg["files"]
        ["obsdiag"]
    )

    variable = (
        cfg["plot"]
        ["variable"]
    )

    level = int(
        cfg["plot"]
        ["level"]
    )

    obs_variable = (
        cfg["diagnostics"]
        ["obs_variable"]
    )

    qc_group = (
        cfg["diagnostics"]
        ["qc_group"]
    )

    bandwidth = float(
        cfg["density"]
        ["bandwidth"]
    )

    points = int(
        cfg["density"]
        ["points"]
    )

    # -----------------------------------
    # Statistics
    # -----------------------------------

    stats = compute_cycle_statistics(

        experiment=
            experiment,

        cycle=
            cycle,

        obsdiag_file=
            obsdiag_file,

        obs_variable=
            obs_variable,

        qc_group=
            qc_group,
    )

    json_file = (
        outdir
        / "cycle_stats.json"
    )

    write_cycle_statistics(

        stats,

        json_file,
    )

    # -----------------------------------
    # Datasets
    # -----------------------------------

    print(
        "[LOAD]",
        bkg_file,
    )

    bkg = xr.open_dataset(
        bkg_file,
        decode_coords=False,
    )

    inc = xr.open_dataset(
        inc_file,
        decode_coords=False,
    )

    grid = xr.open_dataset(
        grid_file
    )

    meta = xr.open_dataset(
        obsdiag_file,
        group="MetaData",
        engine="netcdf4",
    )

    obs_ds = xr.open_dataset(
        obsdiag_file,
        group="ObsValue",
        engine="netcdf4",
    )

    ombg_ds = xr.open_dataset(
        obsdiag_file,
        group="ombg",
        engine="netcdf4",
    )

    oman_ds = xr.open_dataset(
        obsdiag_file,
        group="oman",
        engine="netcdf4",
    )

    # -----------------------------------
    # Fields
    # -----------------------------------

    bkg_map = bkg[
        variable
    ].values[
        0,
        level,
        :,
        :
    ]

    inc_map = inc[
        variable
    ].values[
        0,
        level,
        :,
        :
    ]

    inc_interp = zoom(

        inc_map,

        (
            bkg_map.shape[0]
            /
            inc_map.shape[0],

            bkg_map.shape[1]
            /
            inc_map.shape[1],
        ),

        order=1,
    )

    analysis_map = (
        bkg_map
        + inc_interp
    )

    ny, nx = (
        bkg_map.shape
    )

    lat = grid[
        "y"
    ].values[:ny, :nx]

    lon = grid[
        "x"
    ].values[:ny, :nx]

    lon = np.where(
        lon > 180.0,
        lon - 360.0,
        lon,
    )

    # -----------------------------------
    # Observations
    # -----------------------------------

    lat_obs = meta[
        "latitude"
    ].values

    lon_obs = meta[
        "longitude"
    ].values

    lon_obs = np.where(
        lon_obs > 180,
        lon_obs - 360,
        lon_obs,
    )

    obsval = obs_ds[
        obs_variable
    ].values

    ombg = ombg_ds[
        obs_variable
    ].values

    oman = oman_ds[
        obs_variable
    ].values

    mask = (

        np.isfinite(lat_obs)

        &

        np.isfinite(lon_obs)

        &

        np.isfinite(obsval)

        &

        np.isfinite(ombg)

        &

        np.isfinite(oman)

    )

    lat_obs = lat_obs[
        mask
    ]

    lon_obs = lon_obs[
        mask
    ]

    obsval = obsval[
        mask
    ]

    ombg = ombg[
        mask
    ]

    oman = oman[
        mask
    ]

    # -----------------------------------
    # Vertical profile
    # -----------------------------------

    inc3d = inc[
        variable
    ].values[0]

    profile = np.array(

        [

            np.mean(
                np.abs(
                    inc3d[k]
                )
            )

            for k in range(
                inc3d.shape[0]
            )

        ]

    )

    # -----------------------------------
    # PNGs
    # -----------------------------------

    pngs = []

    def add(name):

        p = outdir / name

        pngs.append(p)

        return p

    background_png = add(
        f"background_{cycle}.png"
    )

    analysis_png = add(
        f"analysis_{cycle}.png"
    )

    increment_png = add(
        f"increment_{cycle}.png"
    )

    obs_png = add(
        f"obs_{cycle}.png"
    )

    omb_png = add(
        f"omb_{cycle}.png"
    )

    oma_png = add(
        f"oma_{cycle}.png"
    )

    profile_png = add(
        f"profile_{cycle}.png"
    )

    density_png = add(
        f"density_{cycle}.png"
    )

    summary_png = add(
        f"summary_{cycle}.png"
    )

    # -----------------------------------
    # Plots
    # -----------------------------------

    plot_background(

        background_png,

        bkg_map,

        lon,

        lat,

        cycle,

        variable,

        level,
    )

    plot_analysis(

        analysis_png,

        analysis_map,

        lon,

        lat,

        cycle,

        variable,

        level,
    )

    plot_increment(

        increment_png,

        inc_map,

        cycle,

        variable,

        level,
    )

    plot_obs_map(

        obs_png,

        lon_obs,

        lat_obs,

        obsval,

        cycle,

        "Observations",
    )

    plot_innovation_map(

        omb_png,

        lon_obs,

        lat_obs,

        ombg,

        cycle,

        "OMB",
    )

    plot_innovation_map(

        oma_png,

        lon_obs,

        lat_obs,

        oman,

        cycle,

        "OMA",
    )

    plot_vertical_profile(

        profile_png,

        profile,

        cycle,
    )

    plot_density(

        density_png,

        ombg,

        oman,

        bandwidth,

        points,

        cycle,
    )

    plot_summary_page(

        summary_png,

        stats,
    )

    # -----------------------------------
    # PDF
    # -----------------------------------

    pdf_name = (
        cfg["output"]
        ["cycle_pdf"]
    )

    pdf_file = (
        outdir
        / pdf_name
    )

    build_pdf(

        pngs,

        pdf_file,
    )

    print()

    print(
        "[DONE]",
        pdf_file,
    )

    print(
        "[JSON]",
        json_file,
    )


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "python post/plot_cycle_surface2m.py "
            "<yaml>"
        )

        sys.exit(1)

    main(
        sys.argv[1]
    )
