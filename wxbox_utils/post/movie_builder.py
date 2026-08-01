#!/usr/bin/env python3

"""
post/movie_builder.py

Build MP4 diagnostics animations from
cycle PNG files.

Usage:

python post/movie_builder.py \
    configs/experiments/c1667.yaml
"""

import shutil
import subprocess

from pathlib import Path

from datetime import (
    datetime,
    timedelta,
)

import yaml


# =====================================================
# YAML
# =====================================================

def load_yaml(filename):

    with open(filename, "r") as f:

        return yaml.safe_load(f)


# =====================================================
# Cycle Utilities
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

    current = parse_cycle(
        start
    )

    end_dt = parse_cycle(
        end
    )

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

        if not d.is_dir():
            continue

        if "T" not in d.name:
            continue

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

        return discover_cycles(
            cfg
        )

    else:

        raise ValueError(
            f"Unknown cycling mode: {mode}"
        )


# =====================================================
# FFMPEG
# =====================================================

def check_ffmpeg():

    ffmpeg = shutil.which(
        "ffmpeg"
    )

    if ffmpeg is None:

        raise RuntimeError(
            "ffmpeg not found in PATH"
        )

    return ffmpeg


# =====================================================
# PNG Collection
# =====================================================

def collect_cycle_pngs(

    cfg,

    prefix,

):

    experiment_dir = Path(
        cfg["experiment_dir"]
    )

    cycles = get_cycles(
        cfg
    )

    pngs = []

    for cycle in cycles:

        png = (

            experiment_dir

            / cycle

            / "letkf"

            / "post"

            / f"{prefix}{cycle}.png"

        )

        if png.exists():

            pngs.append(
                png
            )

    if not pngs:

        raise RuntimeError(
            f"No PNGs found for "
            f"{prefix}"
        )

    return pngs


# =====================================================
# Single Movie
# =====================================================

def build_movie(

    cfg,

    prefix,

    output_mp4,

    fps,

):

    ffmpeg = check_ffmpeg()

    pngs = collect_cycle_pngs(

        cfg,

        prefix,
    )

    output_mp4 = Path(
        output_mp4
    )

    output_mp4.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    listfile = (

        output_mp4.parent

        / f"{prefix}_frames.txt"

    )

    with open(
        listfile,
        "w",
    ) as fp:

        for png in pngs:

            fp.write(
                f"file '{png.resolve()}'\n"
            )

            fp.write(
                f"duration {1.0/fps:.3f}\n"
            )

    cmd = [

        ffmpeg,

        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(listfile),

        "-vf",
        "pad=ceil(iw/2)*2:"
        "ceil(ih/2)*2",

        "-pix_fmt",
        "yuv420p",

        str(output_mp4),
    ]

    print()
    print(
        "[FFMPEG]"
    )
    print(
        " ".join(cmd)
    )
    print()

    subprocess.run(
        cmd,
        check=True,
    )

    listfile.unlink(
        missing_ok=True
    )

    return output_mp4


# =====================================================
# Standard Movies
# =====================================================

def build_standard_movies(cfg):

    experiment_dir = Path(
        cfg["experiment_dir"]
    )

    summary_dir = (
        experiment_dir
        / "post"
    )

    summary_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    fps = (
        cfg["post"]
        ["movies"]
        ["fps"]
    )

    products = [

        (
            "background_",
            "background.mp4",
        ),

        (
            "analysis_",
            "analysis.mp4",
        ),

        (
            "increment_",
            "increment.mp4",
        ),

        (
            "obs_",
            "obs.mp4",
        ),

        (
            "omb_",
            "omb.mp4",
        ),

        (
            "oma_",
            "oma.mp4",
        ),

        (
            "profile_",
            "profile.mp4",
        ),

        (
            "density_",
            "density.mp4",
        ),
    ]

    movies = []

    for prefix, outfile in products:

        try:

            movie = build_movie(

                cfg,

                prefix,

                summary_dir
                / outfile,

                fps,
            )

            print(
                f"[MOVIE] {movie}"
            )

            movies.append(
                movie
            )

        except Exception as e:

            print(
                f"[SKIP] {prefix}"
            )

            print(
                f"       {e}"
            )

    return movies


# =====================================================
# CLI
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

    build_standard_movies(
        cfg
    )


if __name__ == "__main__":
    main()
