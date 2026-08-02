# wxbox-utils

Utilities for:

- FV3 Grid Generation
- HRRR Download and Processing
- HRRR → FV3 Restart Conversion
- Ensemble Generation
- Observation Database Construction
- JEDI LETKF Cycling
- Diagnostics and Verification
- Experiment Summary Reporting
- Diagnostic Movie Generation

---

# Quick Start

Install:

```bash
pip install -e .
```

Verify:

```bash
pip show wxbox-utils
```

---

# Command Line Tools

## Grid Utilities

Create FV3 grid:

```bash
wxbox-create-grid c1667.yaml
```

Create FV3 mosaic:

```bash
wxbox-create-mosaic c1667.yaml
```

---

## HRRR Utilities

Download HRRR analyses:

```bash
wxbox-download-hrrr hrrr_download.yaml
```

Convert HRRR analyses to FV3 restart files:

```bash
wxbox-hrrr-to-fv3 hrrr_fv3_c1667.yaml
```

---

## Ensemble Utilities

Create synthetic ensemble perturbations:

```bash
wxbox-gen-ens ensemble_c1667.yaml
```

---

## Observation Database Utilities

Build cycle-aware IODA observation databases:

```bash
wxbox-build-obsdb asos_concat.yaml
```

---

## LETKF Workflow

Validate experiment:

```bash
wxbox-letkf check c1667.yaml
```

Render JEDI YAML configuration files:

```bash
wxbox-letkf render c1667.yaml
```

Run complete cycling experiment:

```bash
wxbox-letkf run c1667.yaml
```

---

## Diagnostics and Verification

Generate cycle diagnostics:

```bash
wxbox-plot run c1667.yaml
```

Generate experiment summary:

```bash
wxbox-plot summary c1667.yaml
```

Generate innovation density plot:

```bash
wxbox-density c1667.yaml
```

Generate MP4 animations:

```bash
wxbox-movie c1667.yaml
```

---

# Workflow

Typical end-to-end workflow:

```text
FV3 Grid
    ↓
HRRR Download
    ↓
FV3 Restart Generation
    ↓
Ensemble Generation
    ↓
IODA Observation Database
    ↓
LETKF Cycling
    ↓
Cycle Diagnostics
    ↓
Experiment Summary
    ↓
Movies
```

---

# Package Structure

```text
wxbox_utils/

├── configs/
│   └── templates/
│
├── drivers/
│   ├── letkf_driver.py
│   └── plot_driver.py
│
├── grid/
│   ├── create_esg_grid.py
│   └── create_mosaic.py
│
├── hrrr/
│   ├── download_hrrr.py
│   ├── hrrr_reader.py
│   ├── hrrr_horizontal_sample.py
│   ├── hrrr_vertical.py
│   └── hrrr_to_fv3_restart.py
│
├── ensemble/
│   └── gen_ens.py
│
├── obs/
│   └── build_obsdb_cycles.py
│
└── post/
    ├── cycle_stats.py
    ├── cycle_plot.py
    ├── plot_cycle_surface2m.py
    ├── experiment_density.py
    ├── summary_plots.py
    ├── pdf_report.py
    └── movie_builder.py
```

---

# Configuration Philosophy

wxbox-utils ships:

```text
Code
Templates
```

Users provide:

```text
Experiment YAML files
Grid YAML files
HRRR YAML files
Observation YAML files
```

Template files are distributed with the package:

```text
wxbox_utils/configs/templates/

├── letkf.yaml.j2
└── post_surface2m.yaml.j2
```

---

# Typical Products

## Grid

```text
C1667_grid.tile7.nc

grid_spec.tile7.halo3.nc
```

## HRRR

```text
*.grib2
```

## FV3 Restart

```text
hrrr.fv_core.res.tile1.nc

hrrr.fv_tracer.res.tile1.nc

hrrr.fv_srf_wnd.res.tile1.nc

hrrr.sfc_data.nc

*.coupler.res
```

## Ensemble

```text
mem001/
mem002/
mem003/
...
```

## Observation Database

```text
obsdb/

└── 20260723T12Z/
    └── iem_asos_obs_20260723T120000Z.nc4
```

## LETKF Diagnostics

```text
background_<cycle>.png

analysis_<cycle>.png

increment_<cycle>.png

obs_<cycle>.png

omb_<cycle>.png

oma_<cycle>.png

profile_<cycle>.png

density_<cycle>.png

summary_<cycle>.png

cycle_stats.json

cycle_report_<cycle>.pdf
```

## Experiment Summary

```text
summary_table.csv

innovation_timeseries.png

rmse_timeseries.png

obs_count_timeseries.png

assimilation_rate_timeseries.png

spread_timeseries.png

experiment_density.png

experiment_summary.pdf
```

## Movies

```text
background.mp4

analysis.mp4

increment.mp4

obs.mp4

omb.mp4

oma.mp4

profile.mp4

density.mp4
```

---

# Dependencies

Python:

```text
numpy
scipy
pandas
xarray
netCDF4

PyYAML
Jinja2

matplotlib
cartopy

boto3
botocore

cfgrib
```

Install:

```bash
pip install -r requirements.txt
```

---

# External Requirements

Required for MP4 animation generation:

```text
ffmpeg
```

Ubuntu:

```bash
sudo apt install ffmpeg
```

Verify:

```bash
ffmpeg -version
```

---

# Development Installation

Clone repository:

```bash
git clone <repository>
cd wxbox_utils
```

Install editable package:

```bash
pip install -e .
```

Update after changes:

```bash
pip install -e . --force-reinstall
```

---

# License

Internal research and development use.
