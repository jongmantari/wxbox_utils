#!/usr/bin/env python3

"""
post/cycle_plot.py

Basic plotting utilities for LETKF diagnostics.

Produces:

    background map
    analysis map
    increment map

    observation map
    OMB map
    OMA map

    vertical profile

    HofX spread

    OMB/OMA density

    summary page

"""

from pathlib import Path

import numpy as np

import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature

from scipy.stats import gaussian_kde


# =====================================================
# Helpers
# =====================================================

def ensure_dir(path):

    Path(path).mkdir(
        parents=True,
        exist_ok=True,
    )


def setup_map(extent):

    ax = plt.axes(
        projection=ccrs.PlateCarree()
    )

    ax.set_extent(
        extent,
        crs=ccrs.PlateCarree()
    )

    ax.add_feature(
        cfeature.COASTLINE,
        linewidth=0.8,
    )

    ax.add_feature(
        cfeature.BORDERS,
        linewidth=0.5,
    )

    ax.add_feature(
        cfeature.STATES,
        linewidth=0.3,
    )

    return ax


def add_cbar(obj, label):

    cb = plt.colorbar(
        obj,
        orientation="horizontal",
        shrink=0.8,
        pad=0.05,
    )

    cb.set_label(label)


def vmax99(data):

    data = np.asarray(
        data,
        dtype=np.float64,
    )

    data = data[
        np.isfinite(data)
    ]

    #
    # Remove IODA fill values
    #
    data = data[
        np.abs(data) < 1.0e30
    ]

    if data.size == 0:
        return 1.0

    return np.percentile(
        np.abs(data),
        99,
    )

# =====================================================
# Model Fields
# =====================================================

def plot_background(

    outfile,

    field,

    lon,

    lat,

    cycle,

    variable,

    level,

):

    fig = plt.figure(
        figsize=(10, 7)
    )

    extent = [

        float(np.nanmin(lon)),
        float(np.nanmax(lon)),

        float(np.nanmin(lat)),
        float(np.nanmax(lat)),
    ]

    ax = setup_map(extent)

    h = ax.pcolormesh(

        lon,
        lat,
        field,

        shading="auto",

        cmap="viridis",

        transform=ccrs.PlateCarree(),
    )

    plt.title(
        f"Background {variable} "
        f"Level={level}\n"
        f"{cycle}"
    )

    add_cbar(
        h,
        variable,
    )

    fig.savefig(
        outfile,
        bbox_inches="tight",
    )

    plt.close(fig)


def plot_analysis(

    outfile,

    field,

    lon,

    lat,

    cycle,

    variable,

    level,

):

    fig = plt.figure(
        figsize=(10, 7)
    )

    extent = [

        float(np.nanmin(lon)),
        float(np.nanmax(lon)),

        float(np.nanmin(lat)),
        float(np.nanmax(lat)),
    ]

    ax = setup_map(extent)

    h = ax.pcolormesh(

        lon,
        lat,
        field,

        shading="auto",

        cmap="viridis",

        transform=ccrs.PlateCarree(),
    )

    plt.title(
        f"Analysis {variable} "
        f"Level={level}\n"
        f"{cycle}"
    )

    add_cbar(
        h,
        variable,
    )

    fig.savefig(
        outfile,
        bbox_inches="tight",
    )

    plt.close(fig)


def plot_increment(

    outfile,

    increment,

    cycle,

    variable,

    level,

):

    fig = plt.figure(
        figsize=(10, 7)
    )

    vmax = vmax99(
        increment
    )

    plt.imshow(

        increment,

        cmap="RdBu_r",

        vmin=-vmax,
        vmax=vmax,

        origin="lower",
    )

    plt.colorbar()

    plt.title(
        f"Increment {variable} "
        f"Level={level}\n"
        f"{cycle}"
    )

    fig.savefig(
        outfile,
        bbox_inches="tight",
    )

    plt.close(fig)


# =====================================================
# Observation Maps
# =====================================================

def plot_obs_map(

    outfile,

    lon,

    lat,

    values,

    cycle,

    title,

):

    fig = plt.figure(
        figsize=(10, 7)
    )

    extent = [

        float(np.nanmin(lon)),
        float(np.nanmax(lon)),

        float(np.nanmin(lat)),
        float(np.nanmax(lat)),
    ]

    ax = setup_map(extent)

    sc = ax.scatter(

        lon,
        lat,

        c=values,

        cmap="viridis",

        s=80,

        transform=ccrs.PlateCarree(),
    )

    plt.title(
        f"{title}\n{cycle}"
    )

    add_cbar(
        sc,
        title,
    )

    fig.savefig(
        outfile,
        bbox_inches="tight",
    )

    plt.close(fig)


def plot_innovation_map(

    outfile,

    lon,

    lat,

    innovation,

    cycle,

    title,

):

    innovation = np.asarray(
        innovation,
        dtype=np.float64,
    )

    innovation[
        np.abs(innovation) > 1.0e30
    ] = np.nan

    mask = (
        np.isfinite(lon)
        &
        np.isfinite(lat)
        &
        np.isfinite(innovation)
    )

    lon = lon[mask]
    lat = lat[mask]
    innovation = innovation[mask]

    if len(innovation) == 0:
        return
    
    fig = plt.figure(
        figsize=(10, 7)
    )

    extent = [

        float(np.nanmin(lon)),
        float(np.nanmax(lon)),

        float(np.nanmin(lat)),
        float(np.nanmax(lat)),
    ]

    ax = setup_map(extent)

    vmax = max(
        vmax99(innovation),
        0.1,
    )

    sc = ax.scatter(

        lon,
        lat,

        c=innovation,

        cmap="RdBu_r",

        s=90,

        vmin=-vmax,
        vmax=vmax,

        transform=ccrs.PlateCarree(),
    )

    plt.title(
        f"{title}\n{cycle}"
    )

    add_cbar(
        sc,
        title,
    )

    fig.savefig(
        outfile,
        bbox_inches="tight",
    )

    plt.close(fig)


# =====================================================
# Vertical Profile
# =====================================================

def plot_vertical_profile(

    outfile,

    profile,

    cycle,

):

    fig, ax1 = plt.subplots(
        figsize=(8, 6)
    )

    ax1.plot(

        profile,

        np.arange(
            len(profile)
        ),

        "b-o",
    )

    ax1.invert_yaxis()

    ax1.set_xlabel(
        "Mean |Increment|"
    )

    ax1.set_ylabel(
        "Model Level"
    )

    ax1.grid(
        alpha=0.3
    )

    plt.title(
        f"Vertical Increment Profile\n"
        f"{cycle}"
    )

    fig.savefig(
        outfile,
        bbox_inches="tight",
    )

    plt.close(fig)


# =====================================================
# HofX Spread
# =====================================================

def plot_spread(

    outfile,

    spread_b,

    spread_a,

    spread_reduction,

    cycle,

):

    fig = plt.figure(
        figsize=(8, 6)
    )

    x = np.arange(
        len(spread_b)
    )

    plt.plot(
        x,
        spread_b,
        "o-",
        label="Background",
    )

    plt.plot(
        x,
        spread_a,
        "o-",
        label="Analysis",
    )

    plt.ylabel(
        "Spread"
    )

    plt.grid(
        alpha=0.3
    )

    plt.legend()

    plt.title(
        f"HofX Spread\n"
        f"Reduction={spread_reduction:.1f}%\n"
        f"{cycle}"
    )

    fig.savefig(
        outfile,
        bbox_inches="tight",
    )

    plt.close(fig)


# =====================================================
# OMB / OMA Density
# =====================================================

# =====================================================
# OMB / OMA Density
# =====================================================

def plot_density(

    outfile,

    ombg,

    oman,

    bandwidth,

    points,

    cycle,

):

    #
    # Convert to float64
    #
    ombg = np.asarray(
        ombg,
        dtype=np.float64,
    )

    oman = np.asarray(
        oman,
        dtype=np.float64,
    )

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
    # Remove NaNs
    #
    ombg = ombg[
        np.isfinite(ombg)
    ]

    oman = oman[
        np.isfinite(oman)
    ]

    #
    # Need enough points for KDE
    #
    if (
        len(ombg) < 3
        or
        len(oman) < 3
    ):

        print(
            f"[SKIP] density {cycle}"
        )

        return

    #
    # Debug
    #
    print()

    print(
        f"[DENSITY] {cycle}"
    )

    print(
        "OMB:",
        np.min(ombg),
        np.max(ombg),
    )

    print(
        "OMA:",
        np.min(oman),
        np.max(oman),
    )

    #
    # Common plotting range
    #
    xmin = min(
        np.min(ombg),
        np.min(oman),
    )

    xmax = max(
        np.max(ombg),
        np.max(oman),
    )

    #
    # Protect against degenerate range
    #
    if abs(xmax - xmin) < 1e-6:

        xmin -= 1.0
        xmax += 1.0

    xx = np.linspace(
        xmin,
        xmax,
        points,
    )

    fig = plt.figure(
        figsize=(8, 6)
    )

    kde_omb = gaussian_kde(
        ombg,
        bw_method=bandwidth,
    )

    kde_oma = gaussian_kde(
        oman,
        bw_method=bandwidth,
    )

    print("xmin =", xmin)
    print("xmax =", xmax)
    print("xx min =", xx.min())
    print("xx max =", xx.max())

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

    plt.xlabel(
        "Innovation"
    )

    plt.ylabel(
        "Density"
    )

    plt.grid(
        alpha=0.3
    )

    plt.legend()

    plt.title(
        f"Innovation Density\n"
        f"{cycle}"
    )

    fig.savefig(
        outfile,
        bbox_inches="tight",
    )

    plt.close(fig)

# =====================================================
# Summary Page
# =====================================================

def plot_summary_page(

    outfile,

    stats,

):

    fig = plt.figure(
        figsize=(8, 6)
    )

    plt.axis("off")

    text = f"""
Experiment           : {stats['experiment']}
Cycle                : {stats['cycle']}

Total Obs            : {stats['nobs_total']}
Assimilated Obs      : {stats['nobs_assimilated']}

Assimilation Rate    : {stats['assimilation_rate']:.1f} %

OMB Mean             : {stats['omb_mean']:.3f}
OMA Mean             : {stats['oma_mean']:.3f}

OMB RMSE             : {stats['omb_rmse']:.3f}
OMA RMSE             : {stats['oma_rmse']:.3f}

Background Spread    : {stats['spread_background']:.3f}

Analysis Spread      : {stats['spread_analysis']:.3f}

Spread Reduction     : {stats['spread_reduction']:.1f} %
"""

    plt.text(

        0.05,
        0.95,

        text,

        va="top",

        family="monospace",

        fontsize=11,
    )

    fig.savefig(
        outfile,
        bbox_inches="tight",
    )

    plt.close(fig)
