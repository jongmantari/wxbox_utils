#!/usr/bin/env python3

"""
drivers/plot_driver.py

Cycle plotting driver

Commands:

    check
    render
    run
    summary
    movie

"""

import argparse
import subprocess

from pathlib import Path

import yaml

from jinja2 import (
    Environment,
    FileSystemLoader,
)

import sys

from pathlib import Path

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

from wxbox_utils.post.summary_plots import (
    generate_summary_plots,
)

from wxbox_utils.post.movie_builder import (
    build_standard_movies,
)

from datetime import (
    datetime,
    timedelta,
)

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
            format_cycle(
                current
            )
        )

        current += timedelta(
            hours=frequency_hours
        )

    return cycles


def get_cycles(cfg):

    mode = (

        cfg["cycling"]
        ["mode"]

        .lower()

    )

    if mode == "discover":

        return discover_cycles(
            cfg
        )

    elif mode == "range":

        return range_cycles(

            cfg["cycling"]
            ["start"],

            cfg["cycling"]
            ["end"],

            cfg["cycling"]
            ["frequency_hours"],
        )

    elif mode == "explicit":

        return (
            cfg["cycling"]
            ["cycles"]
        )

    else:

        raise ValueError(
            f"Unknown cycling mode: {mode}"
        )
    
# =====================================================
# Cycle discovery
# =====================================================

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


def get_cycle_dir(cfg, cycle):

    return (
        Path(
            cfg["experiment_dir"]
        )
        / cycle
    )


# =====================================================
# Files
# =====================================================

def find_background_file(
    cfg,
    cycle,
):

    cycle_dir = get_cycle_dir(
        cfg,
        cycle,
    )

    return (

        cycle_dir

        / "ensemble"

        / "mem01"

        / "hrrr.fv_core.res.tile1.nc"

    )


def find_increment_file(
    cfg,
    cycle,
):

    cycle_dir = get_cycle_dir(
        cfg,
        cycle,
    )

    increment_dir = (

        cycle_dir

        / "letkf"

        / "increment"

    )

    files = sorted(
        increment_dir.glob(
            "*.fv_core.res.nc"
        )
    )

    if not files:

        raise RuntimeError(
            f"No increment file "
            f"found in "
            f"{increment_dir}"
        )

    return files[0]


def find_diag_file(
    cfg,
    cycle,
):

    cycle_dir = get_cycle_dir(
        cfg,
        cycle,
    )

    letkf_dir = (
        cycle_dir
        / "letkf"
    )

    files = sorted(
        letkf_dir.glob(
            "diag_*.nc4"
        )
    )

    if not files:

        raise RuntimeError(
            f"No diagnostic file "
            f"found in {letkf_dir}"
        )

    return files[0]


# =====================================================
# Check
# =====================================================

def check_cycle(
    cfg,
    cycle,
):

    try:

        background = (
            find_background_file(
                cfg,
                cycle,
            )
        )

        increment = (
            find_increment_file(
                cfg,
                cycle,
            )
        )

        obsdiag = (
            find_diag_file(
                cfg,
                cycle,
            )
        )

        grid = Path(
            cfg["post"]
            ["grid_file"]
        )

        if not background.exists():
            raise FileNotFoundError(
                background
            )

        if not increment.exists():
            raise FileNotFoundError(
                increment
            )

        if not obsdiag.exists():
            raise FileNotFoundError(
                obsdiag
            )

        if not grid.exists():
            raise FileNotFoundError(
                grid
            )

        print(
            f"[OK] {cycle}"
        )

        return True

    except Exception as e:

        print(
            f"[SKIP] {cycle}"
        )

        print(
            f"       {e}"
        )

        return False


# =====================================================
# Render YAML
# =====================================================

def render_cycle(
    cfg,
    cycle,
):

    cycle_dir = get_cycle_dir(
        cfg,
        cycle,
    )

    post_dir = (
        cycle_dir
        / "letkf"
        / "post"
    )

    post_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    #==========================
    template_dir = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "configs"
        / "templates"
    )

    env = Environment(
        loader=FileSystemLoader(
            str(template_dir)
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template(
        "post_surface2m.yaml.j2"
    )    
    #==========================

    #==========================
    rendered = template.render(

        experiment=cfg["experiment"],

        cycle=cycle,

        background_file=
        find_background_file(
            cfg,
            cycle,
        ),

        increment_file=
        find_increment_file(
            cfg,
            cycle,
        ),

        grid_file=
        cfg["post"]["grid_file"],

        obsdiag_file=
        find_diag_file(
            cfg,
            cycle,
        ),

        variable=
        cfg["post"]["variable"],
        
        level=
        cfg["post"]["level"],

        obs_variable=
        cfg["post"]["diagnostics"]
        ["obs_variable"],

        qc_group=
        cfg["post"]["diagnostics"]
        ["qc_group"],

        outdir=
        str(post_dir),

        dpi=
        cfg["post"]["png"]["dpi"],

        cycle_pdf=
        cfg["post"]["outputs"]
        ["cycle_pdf"]
        .format(cycle=cycle),

        bandwidth=
        cfg["post"]["density"]
        ["bandwidth"],

        points=
        cfg["post"]["density"]
        ["points"],

        summary_title=
        cfg["summary"]["title"],

        summary_author=
        cfg["summary"]["author"],
    )
    #==========================

    outfile = (
        post_dir
        / "plot_surface2m.yaml"
    )

    outfile.write_text(
        rendered
    )

    print(
        f"[RENDER] {outfile}"
    )

    return outfile


# =====================================================
# Run cycle plotting
# =====================================================

def run_cycle(
    cfg,
    cycle,
):

    yamlfile = render_cycle(
        cfg,
        cycle,
    )

    cmd = [

        sys.executable,

        "-m",

        "wxbox_utils.post.plot_cycle_surface2m",

        str(yamlfile),
    ]

    print(
        "[RUN]",
        " ".join(cmd)
    )

    subprocess.run(
        cmd,
        check=True,
    )

# =====================================================
# Summary
# =====================================================

def run_summary(cfg):

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

    df = generate_summary_plots(

        cfg["experiment_dir"],

        summary_dir,
    )

    print()

    print(
        f"Summary written to "
        f"{summary_dir}"
    )

    return df


# =====================================================
# Movies
# =====================================================

def run_movies(cfg):

    summary_dir = (

        Path(
            cfg["experiment_dir"]
        )

        / "post"

    )

    build_standard_movies(

        summary_dir,

        fps=
        cfg["post"]
        ["movies"]
        ["fps"],
    )


# =====================================================
# Main
# =====================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(

        "command",

        choices=[

            "check",

            "render",

            "run",

            "summary",

            "movie",
        ],
    )

    parser.add_argument(
        "config"
    )

    args = parser.parse_args()

    cfg = load_yaml(
        args.config
    )

    cycles = get_cycles(
        cfg
    )
    
    if args.command == "check":

        for cycle in cycles:

            check_cycle(
                cfg,
                cycle,
            )

    elif args.command == "render":

        for cycle in cycles:

            if check_cycle(
                cfg,
                cycle,
            ):

                render_cycle(
                    cfg,
                    cycle,
                )

    elif args.command == "run":

        for cycle in cycles:

            if check_cycle(
                cfg,
                cycle,
            ):

                run_cycle(
                    cfg,
                    cycle,
                )

    elif args.command == "summary":

        run_summary(
            cfg
        )

    elif args.command == "movie":

        run_movies(
            cfg
        )


if __name__ == "__main__":
    main()
