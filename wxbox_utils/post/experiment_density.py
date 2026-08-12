#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime, timedelta
import yaml
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde


def load_yaml(filename):
    with open(filename, 'r') as f:
        return yaml.safe_load(f)


def parse_cycle(cycle):
    return datetime.strptime(cycle, '%Y%m%dT%HZ')


def format_cycle(dt):
    return dt.strftime('%Y%m%dT%HZ')


def range_cycles(start, end, frequency_hours):
    cycles = []
    current = parse_cycle(start)
    end_dt = parse_cycle(end)
    while current <= end_dt:
        cycles.append(format_cycle(current))
        current += timedelta(hours=frequency_hours)
    return cycles


def discover_cycles(cfg):
    experiment_dir = Path(cfg['experiment_dir'])
    return [d.name for d in sorted(experiment_dir.iterdir()) if d.is_dir() and 'T' in d.name]


def get_cycles(cfg):
    mode = cfg['cycling']['mode'].lower()
    if mode == 'range':
        return range_cycles(cfg['cycling']['start'], cfg['cycling']['end'], cfg['cycling']['frequency_hours'])
    if mode == 'explicit':
        return cfg['cycling']['cycles']
    if mode == 'discover':
        return discover_cycles(cfg)
    raise ValueError(f'Unknown cycling mode: {mode}')


def collect_innovations(cfg):
    experiment_dir = Path(cfg['experiment_dir'])
    obsvar = cfg['post']['diagnostics']['obs_variable']
    qc_group = cfg['post']['diagnostics']['qc_group']

    ombg_all = []
    oman_all = []

    for cycle in get_cycles(cfg):
        letkf_dir = experiment_dir / cycle / 'letkf'
        diag_files = sorted(letkf_dir.glob('diag_*.nc4'))
        if not diag_files:
            continue

        diag = diag_files[0]

        try:
            ombg_ds = xr.open_dataset(diag, group='ombg', engine='netcdf4')
            oman_ds = xr.open_dataset(diag, group='oman', engine='netcdf4')
            qc_ds = xr.open_dataset(diag, group=qc_group, engine='netcdf4')

            ombg = np.asarray(ombg_ds[obsvar].values, dtype=np.float64)
            oman = np.asarray(oman_ds[obsvar].values, dtype=np.float64)
            qc = qc_ds[obsvar].values

            ombg[np.abs(ombg) > 1e30] = np.nan
            oman[np.abs(oman) > 1e30] = np.nan

            mask = np.isfinite(ombg) & np.isfinite(oman) & (qc == 0)

            ombg = ombg[mask]
            oman = oman[mask]

            if len(ombg) == 0:
                continue

            print(f'[READ] {cycle} n={len(ombg)}')

            ombg_all.extend(ombg.tolist())
            oman_all.extend(oman.tolist())

        except Exception as e:
            print(f'[SKIP] {cycle}: {e}')

    return np.asarray(ombg_all), np.asarray(oman_all)


def build_density_plot(ombg, oman, outfile, bandwidth, points):
    ombg = ombg[np.isfinite(ombg)]
    oman = oman[np.isfinite(oman)]

    if len(ombg) < 3 or len(oman) < 3:
        raise RuntimeError('Not enough innovations')

    xmin = min(np.min(ombg), np.min(oman))
    xmax = max(np.max(ombg), np.max(oman))

    if abs(xmax - xmin) < 1e-6:
        xmin -= 1
        xmax += 1

    xx = np.linspace(xmin, xmax, points)

    yy_omb = gaussian_kde(ombg)(xx)
    yy_oma = gaussian_kde(oman)(xx)

    omb_mean = np.mean(ombg)
    oma_mean = np.mean(oman)

    plt.figure(figsize=(8, 6))

    plt.plot(xx, yy_omb, lw=3, label='OMB', color='C0')
    plt.plot(xx, yy_oma, lw=3, label='OMA', color='C1')

    plt.axvline(0.0, color='black', linestyle='--', linewidth=1.5, alpha=0.8, label='Zero Innovation')

    plt.axvline(omb_mean, color='C0', linestyle=':', linewidth=2.0, label=f'OMB Mean ({omb_mean:.2f})')
    plt.axvline(oma_mean, color='C1', linestyle=':', linewidth=2.0, label=f'OMA Mean ({oma_mean:.2f})')

    plt.grid(alpha=0.3)
    plt.legend()
    plt.xlabel('Innovation (K)')
    plt.ylabel('Density')
    plt.title('Experiment-Wide Innovation Density')
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    plt.close()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    args = parser.parse_args()

    cfg = load_yaml(args.config)

    ombg, oman = collect_innovations(cfg)

    summary_dir = Path(cfg['experiment_dir']) / 'post'
    summary_dir.mkdir(parents=True, exist_ok=True)

    outfile = summary_dir / 'experiment_density.png'

    build_density_plot(
        ombg,
        oman,
        outfile,
        cfg['post']['density']['bandwidth'],
        cfg['post']['density']['points']
    )

    print(f'[DONE] {outfile}')


if __name__ == '__main__':
    main()
