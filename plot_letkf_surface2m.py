#!/usr/bin/env python3

import sys
import yaml
import numpy as np
import xarray as xr

import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature

from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import gaussian_kde
from scipy.ndimage import zoom


# =====================================================
# CONFIG
# =====================================================

if len(sys.argv) > 1:
    yaml_file = sys.argv[1]
else:
    yaml_file = "plot_letkf_c1667.yaml"

with open(yaml_file) as f:
    cfg = yaml.safe_load(f)

print("Using:", yaml_file)

BKG_FILE  = cfg["files"]["background"]
INC_FILE  = cfg["files"]["increment"]
GRID_FILE = cfg["files"]["grid"]
OBS_FILE  = cfg["files"]["obsdiag"]

VAR   = cfg["plot"]["variable"]
LEVEL = cfg["plot"]["level"]

PDFNAME = cfg["plot"]["output_pdf"]

# =====================================================
# DATASETS
# =====================================================

print("Loading datasets...")

bkg  = xr.open_dataset(BKG_FILE, decode_coords=False)
inc  = xr.open_dataset(INC_FILE, decode_coords=False)

grid = xr.open_dataset(GRID_FILE)

meta = xr.open_dataset(
    OBS_FILE,
    group="MetaData",
    engine="netcdf4"
)

obsval_ds = xr.open_dataset(
    OBS_FILE,
    group="ObsValue",
    engine="netcdf4"
)

ombg_ds = xr.open_dataset(
    OBS_FILE,
    group="ombg",
    engine="netcdf4"
)

oman_ds = xr.open_dataset(
    OBS_FILE,
    group="oman",
    engine="netcdf4"
)

# =====================================================
# MODEL FIELDS
# =====================================================

bkg_map = bkg[VAR].values[
    0,
    LEVEL,
    :,
    :
]

inc_map = inc[VAR].values[
    0,
    LEVEL,
    :,
    :
]

inc_interp = zoom(
    inc_map,
    (
        bkg_map.shape[0] / inc_map.shape[0],
        bkg_map.shape[1] / inc_map.shape[1]
    ),
    order=1
)

analysis_map = bkg_map + inc_interp

# =====================================================
# GRID
# =====================================================

ny, nx = bkg_map.shape

lat = grid["y"].values[:ny, :nx]

lon = grid["x"].values[:ny, :nx]

lon = np.where(
    lon > 180,
    lon - 360,
    lon
)

extent = [
    float(np.nanmin(lon)),
    float(np.nanmax(lon)),
    float(np.nanmin(lat)),
    float(np.nanmax(lat)),
]

# =====================================================
# OBS
# =====================================================

# =====================================================
# OBS
# =====================================================

lat_obs = meta["latitude"].values
lon_obs = meta["longitude"].values

lon_obs = np.where(
    lon_obs > 180,
    lon_obs - 360,
    lon_obs
)

obsval = obsval_ds["airTemperatureAt2M"].values

ombg = ombg_ds["airTemperatureAt2M"].values
oman = oman_ds["airTemperatureAt2M"].values

# -----------------------------------------------------
# Some JEDI runs save ombg/oman as NaN even though
# HofX diagnostics are available.
# Reconstruct innovations automatically.
# -----------------------------------------------------

if np.isnan(ombg).all():

    print()
    print("OMB diagnostics are all NaN")
    print("Reconstructing from ObsValue - hofx_y_mean_xb0")

    hofx_b = xr.open_dataset(
        OBS_FILE,
        group="hofx_y_mean_xb0",
        engine="netcdf4"
    )

    ombg = (
        obsval
        - hofx_b["airTemperatureAt2M"].values
    )

if np.isnan(oman).all():

    print()
    print("OMA diagnostics are all NaN")
    print("Reconstructing from ObsValue - hofx_y_mean_xb1")

    hofx_a = xr.open_dataset(
        OBS_FILE,
        group="hofx_y_mean_xb1",
        engine="netcdf4"
    )

    oman = (
        obsval
        - hofx_a["airTemperatureAt2M"].values
    )

mask = (
    np.isfinite(lat_obs)
    & np.isfinite(lon_obs)
    & np.isfinite(obsval)
    & np.isfinite(ombg)
    & np.isfinite(oman)
)

print()
print(
    "Valid observations:",
    np.sum(mask)
)

lat_obs = lat_obs[mask]
lon_obs = lon_obs[mask]

obsval = obsval[mask]
ombg   = ombg[mask]
oman   = oman[mask]
# =====================================================
# HOFX SPREAD
# =====================================================

# =====================================================
# HOFX SPREAD
# =====================================================

import netCDF4 as nc

root = nc.Dataset(
    OBS_FILE
)

group_names = list(
    root.groups.keys()
)

root.close()

hofx0_groups = sorted(
    [
        g
        for g in group_names
        if g.startswith("hofx0_")
    ]
)

hofx1_groups = sorted(
    [
        g
        for g in group_names
        if g.startswith("hofx1_")
    ]
)

print()
print(
    "Found",
    len(hofx0_groups),
    "background HofX members"
)

print(
    "Found",
    len(hofx1_groups),
    "analysis HofX members"
)

hofx0 = []
hofx1 = []

for g in hofx0_groups:

    ds = xr.open_dataset(
        OBS_FILE,
        group=g,
        engine="netcdf4"
    )

    hofx0.append(
        ds["airTemperatureAt2M"].values
    )

for g in hofx1_groups:

    ds = xr.open_dataset(
        OBS_FILE,
        group=g,
        engine="netcdf4"
    )

    hofx1.append(
        ds["airTemperatureAt2M"].values
    )

hofx0 = np.asarray(
    hofx0
)

hofx1 = np.asarray(
    hofx1
)

spread_b = np.std(
    hofx0,
    axis=0
)

spread_a = np.std(
    hofx1,
    axis=0
)

mean_spread_b = np.mean(
    spread_b
)

mean_spread_a = np.mean(
    spread_a
)

if mean_spread_b > 0.0:

    spread_reduction = (
        100.0
        *
        (
            mean_spread_b
            - mean_spread_a
        )
        /
        mean_spread_b
    )

else:

    spread_reduction = 0.0
    
# =====================================================
# PROFILE
# =====================================================

inc3d = inc[VAR].values[0]

profile = np.array([
    np.mean(
        np.abs(inc3d[k])
    )
    for k in range(
        inc3d.shape[0]
    )
])

peak_level = int(
    np.argmax(profile)
)

profile_pct = (
    100.0
    * profile
    / profile.max()
)

# =====================================================
# RMSE
# =====================================================

# =====================================================
# RMSE
# =====================================================

omb_rmse = np.sqrt(
    np.nanmean(ombg**2)
)

oma_rmse = np.sqrt(
    np.nanmean(oman**2)
)

rmse_reduction = (
    100.0
    * (omb_rmse - oma_rmse)
    / omb_rmse
)
# =====================================================
# HELPERS
# =====================================================

def setup_map():

    ax = plt.axes(
        projection=ccrs.PlateCarree()
    )

    ax.set_extent(extent)

    ax.add_feature(
        cfeature.COASTLINE,
        linewidth=0.8
    )

    ax.add_feature(
        cfeature.BORDERS,
        linewidth=0.5
    )

    ax.add_feature(
        cfeature.STATES,
        linewidth=0.3
    )

    return ax


def add_cbar(obj, label):

    cb = plt.colorbar(
        obj,
        orientation="horizontal",
        shrink=0.8,
        pad=0.05
    )

    cb.set_label(label)


def vmax99(data):

    valid = np.abs(
        data[np.isfinite(data)]
    )

    if valid.size == 0:
        return 1.0

    return np.percentile(
        valid,
        99
    )
# =====================================================
# PDF
# =====================================================

print("Writing:", PDFNAME)

with PdfPages(PDFNAME) as pdf:

    # ---------------- Background ----------------

    fig = plt.figure(figsize=(10,7))

    ax = setup_map()

    h = ax.pcolormesh(
        lon,
        lat,
        bkg_map,
        shading="auto",
        cmap="viridis",
        transform=ccrs.PlateCarree()
    )

    plt.title(
        f"Background {VAR} Level={LEVEL}"
    )

    add_cbar(h, "K")

    pdf.savefig(fig)
    plt.close()

    # ---------------- Analysis ----------------

    fig = plt.figure(figsize=(10,7))

    ax = setup_map()

    h = ax.pcolormesh(
        lon,
        lat,
        analysis_map,
        shading="auto",
        cmap="viridis",
        transform=ccrs.PlateCarree()
    )

    plt.title(
        f"Analysis {VAR} Level={LEVEL}"
    )

    add_cbar(h, "K")

    pdf.savefig(fig)
    plt.close()

    # ---------------- Increment ----------------

    fig = plt.figure(figsize=(10,7))

    vmax = vmax99(inc_map)

    plt.imshow(
        inc_map,
        cmap="RdBu_r",
        vmin=-vmax,
        vmax=vmax,
        origin="lower"
    )

    plt.colorbar()

    plt.title(
        f"LETKF Increment {VAR} Level={LEVEL}"
    )

    pdf.savefig(fig)
    plt.close()

    # ---------------- Obs ----------------

    fig = plt.figure(figsize=(10,7))

    ax = setup_map()

    sc = ax.scatter(
        lon_obs,
        lat_obs,
        c=obsval,
        cmap="viridis",
        s=80,
        transform=ccrs.PlateCarree()
    )

    plt.title("Surface2M Observations")

    add_cbar(sc, "K")

    pdf.savefig(fig)
    plt.close()

    # ---------------- OMB ----------------

    fig = plt.figure(figsize=(10,7))

    ax = setup_map()

    vmax = max(vmax99(ombg), 0.1)

    sc = ax.scatter(
        lon_obs,
        lat_obs,
        c=ombg,
        cmap="RdBu_r",
        s=90,
        vmin=-vmax,
        vmax=vmax,
        transform=ccrs.PlateCarree()
    )

    plt.title("OMB")

    add_cbar(sc, "K")

    pdf.savefig(fig)
    plt.close()

    # ---------------- OMA ----------------

    fig = plt.figure(figsize=(10,7))

    ax = setup_map()

    vmax = max(vmax99(oman), 0.1)

    sc = ax.scatter(
        lon_obs,
        lat_obs,
        c=oman,
        cmap="RdBu_r",
        s=90,
        vmin=-vmax,
        vmax=vmax,
        transform=ccrs.PlateCarree()
    )

    plt.title("OMA")

    add_cbar(sc, "K")

    pdf.savefig(fig)
    plt.close()

    # ---------------- Vertical Profile ----------------

    fig, ax1 = plt.subplots(figsize=(8,6))

    ax1.plot(
        profile,
        np.arange(len(profile)),
        "b-o"
    )

    ax1.invert_yaxis()

    ax1.set_xlabel(
        "Mean |Increment|"
    )

    ax1.set_ylabel(
        "Model Level"
    )

    ax1.grid(alpha=0.3)

    ax2 = ax1.twiny()

    ax2.plot(
        profile_pct,
        np.arange(len(profile)),
        "r--"
    )

    ax2.set_xlabel(
      "% of Peak"
    )

    plt.title(
        "Vertical Increment Profile"
    )

    pdf.savefig(fig)
    plt.close()

    # ---------------- HofX Spread ----------------

    fig = plt.figure(figsize=(8,6))

    x = np.arange(len(spread_b))

    plt.plot(
        x,
        spread_b,
        "o-",
        label="Background"
    )

    plt.plot(
        x,
        spread_a,
        "o-",
        label="Analysis"
    )

    plt.title(
        f"HofX Spread\n"
        f"Reduction={spread_reduction:.1f}%"
    )

    plt.grid(alpha=0.3)

    plt.ylabel("K")

    plt.legend()

    pdf.savefig(fig)
    plt.close()

    # ---------------- OMB vs OMA ----------------

    fig = plt.figure(figsize=(8,6))

    xmin = min(
        ombg.min(),
        oman.min()
    )

    xmax = max(
        ombg.max(),
        oman.max()
    )

    xx = np.linspace(
        xmin,
        xmax,
        cfg["density"]["points"]
    )

    ombg_kde = ombg[
        np.isfinite(ombg)
    ]

    oman_kde = oman[
        np.isfinite(oman)
    ]

    kde_omb = gaussian_kde(
        ombg_kde,
        bw_method=cfg["density"]["bandwidth"]
    )

    kde_oma = gaussian_kde(
        oman_kde,
        bw_method=cfg["density"]["bandwidth"]
    )
    

    plt.plot(
        xx,
        kde_omb(xx),
        lw=3,
        label="OMB"
    )

    plt.plot(
        xx,
        kde_oma(xx),
        lw=3,
        label="OMA"
    )

    plt.title(
        f"RMSE {omb_rmse:.3f} → {oma_rmse:.3f} K"
    )

    plt.grid(alpha=0.3)

    plt.legend()

    pdf.savefig(fig)
    plt.close()

    # ---------------- Summary Page ----------------

    fig = plt.figure(figsize=(8,6))

    plt.axis("off")

    summary = f"""
Surface2M LETKF Diagnostics

Mean Background Spread : {np.mean(spread_b):.3f} K
Mean Analysis Spread   : {np.mean(spread_a):.3f} K

Spread Reduction       : {spread_reduction:.1f} %

OMB RMSE              : {omb_rmse:.3f} K
OMA RMSE              : {oma_rmse:.3f} K

RMSE Reduction        : {rmse_reduction:.1f} %

Peak Increment Level  : {peak_level}
"""

    plt.text(
        0.05,
        0.95,
        summary,
        va="top",
        family="monospace",
        fontsize=12
    )

    pdf.savefig(fig)
    plt.close()

print()
print("DONE ->", PDFNAME)
