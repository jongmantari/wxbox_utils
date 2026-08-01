#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess

from pathlib import Path
from datetime import datetime, timedelta

import yaml

from jinja2 import (
    Environment,
    FileSystemLoader,
)

# =============================================================================
# YAML
# =============================================================================

def load_yaml(filename):

    with open(filename, "r") as f:
        return yaml.safe_load(f)


# =============================================================================
# Cycle Utilities
# =============================================================================

def parse_cycle(cycle):

    return datetime.strptime(
        cycle,
        "%Y%m%dT%HZ"
    )


def format_cycle(dt):

    return dt.strftime(
        "%Y%m%dT%HZ"
    )


# =============================================================================
# Paths
# =============================================================================

def get_cycle_dir(cfg, cycle):

    return (
        Path(
            cfg["experiment_dir"]
        )
        / cycle
    )


# =============================================================================
# Observation Handling
# =============================================================================

def find_obs_file(cfg, cycle):

    obs_dir = (
        Path(
            cfg["obsdb_dir"]
        )
        / cycle
    )

    if not obs_dir.exists():

        raise FileNotFoundError(
            f"Missing obs directory: {obs_dir}"
        )

    files = sorted(
        obs_dir.glob("*.nc4")
    )

    if not files:

        raise FileNotFoundError(
            f"No obs files found: {obs_dir}"
        )

    return files[0]


def build_diag_file(cycle_dir, obsfile):

    return (
        cycle_dir
        / "letkf"
        / f"diag_{obsfile.name}"
    )


# =============================================================================
# Restart Files
# =============================================================================

def find_coupler_file(cycle_dir):

    restart_dir = (
        cycle_dir
        / "fv3_restart"
    )

    matches = sorted(
        restart_dir.glob("*.coupler.res")
    )

    if not matches:

        raise FileNotFoundError(
            f"No coupler file found in {restart_dir}"
        )

    return matches[0].name


# =============================================================================
# Cycle Discovery
# =============================================================================

def discover_cycles(cfg):

    exp_dir = Path(
        cfg["experiment_dir"]
    )

    obs_root = Path(
        cfg["obsdb_dir"]
    )

    cycles = []

    if not exp_dir.exists():
        return cycles

    for d in sorted(
        exp_dir.iterdir()
    ):

        if not d.is_dir():
            continue

        cycle = d.name

        if "T" not in cycle:
            continue

        obs_dir = obs_root / cycle

        if not obs_dir.exists():
            continue

        if not list(
            obs_dir.glob("*.nc4")
        ):
            continue

        cycles.append(cycle)

    return cycles


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


def get_cycles(cfg, args):

    if args.cycle:
        return [args.cycle]

    mode = (
        cfg["cycling"]["mode"]
        .lower()
    )

    if mode == "discover":

        cycles = discover_cycles(cfg)

    elif mode == "range":

        cycles = range_cycles(
            cfg["cycling"]["start"],
            cfg["cycling"]["end"],
            cfg["cycling"]["frequency_hours"],
        )

    elif mode == "explicit":

        cycles = (
            cfg["cycling"]["cycles"]
        )

    else:

        raise ValueError(
            f"Unknown cycling mode: {mode}"
        )

    if args.start:

        cycles = [
            c for c in cycles
            if c >= args.start
        ]

    if args.end:

        cycles = [
            c for c in cycles
            if c <= args.end
        ]

    if args.last:

        cycles = cycles[
            -args.last:
        ]

    return cycles


# =============================================================================
# Check
# =============================================================================

def check_cycle(cfg, cycle):

    try:

        cycle_dir = get_cycle_dir(
            cfg,
            cycle,
        )

        ensemble_dir = (
            cycle_dir
            / "ensemble"
        )

        restart_dir = (
            cycle_dir
            / "fv3_restart"
        )

        if not cycle_dir.exists():

            raise RuntimeError(
                f"Missing cycle: {cycle_dir}"
            )

        if not ensemble_dir.exists():

            raise RuntimeError(
                f"Missing ensemble: {ensemble_dir}"
            )

        if not restart_dir.exists():

            raise RuntimeError(
                f"Missing fv3_restart: {restart_dir}"
            )

        obsfile = find_obs_file(
            cfg,
            cycle,
        )

        coupler = (
            find_coupler_file(
                cycle_dir
            )
        )

        nmembers = len(
            list(
                ensemble_dir.glob(
                    "mem*"
                )
            )
        )

        print(
            f"[OK] {cycle}"
        )

        print(
            f"     members : {nmembers}"
        )

        print(
            f"     obs     : {obsfile.name}"
        )

        print(
            f"     coupler : {coupler}"
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


# =============================================================================
# Render
# =============================================================================

def render_cycle(cfg, cycle):

    cycle_dir = get_cycle_dir(
        cfg,
        cycle,
    )

    letkf_dir = (
        cycle_dir
        / "letkf"
    )

    letkf_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    obsfile = find_obs_file(
        cfg,
        cycle,
    )

    diagfile = build_diag_file(
        cycle_dir,
        obsfile,
    )

    coupler_file = (
        find_coupler_file(
            cycle_dir
        )
    )

    analysis_dt = (
        parse_cycle(cycle)
    )

    analysis_time = (
        analysis_dt.strftime(
            "%Y-%m-%dT%H:00:00Z"
        )
    )

    window_begin = (
        analysis_dt
        - timedelta(
            hours=1
        )
    ).strftime(
        "%Y-%m-%dT%H:00:00Z"
    )

    observer = (
        cfg["observations"]
        ["observers"][0]
    )

    env = Environment(
        loader=FileSystemLoader(
            "configs/templates"
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template(
        "letkf.yaml.j2"
    )

    rendered = template.render(

        # paths

        fms_namelist=
        cfg["paths"]["fms_namelist"],

        field_table=
        cfg["paths"]["field_table"],

        akbk_file=
        cfg["paths"]["akbk_file"],

        fv3_namelist=
        cfg["paths"]["fv3_namelist"],

        # analysis

        cycle=
        cycle,

        cycle_dir=
        str(cycle_dir),

        analysis_time=
        analysis_time,

        window_begin=
        window_begin,

        # files

        obsfile=
        str(obsfile),

        diagfile=
        str(diagfile),

        coupler_file=
        coupler_file,

        # background

        nmembers=
        cfg["nmembers"],

        # observations

        obs_name=
        observer["name"],

        obs_operator=
        observer["operator"],

        obs_correction=
        observer["correction"],

        simulated_variables=
        observer["simulated_variables"],

        diagnostics=
        observer["diagnostics"],

        distribution_name=
        observer["distribution"]["name"],

        halo_size=
        observer["distribution"]["halo_size"],

        covariance_model=
        observer["error"]
        ["covariance_model"],

        perturbation_amplitude=
        observer["error"]
        ["perturbation_amplitude"],

        perturbation_seed=
        observer["error"]
        ["perturbation_seed"],

        # letkf

        solver=
        cfg["letkf"]["solver"],

        rtps=
        cfg["letkf"]["inflation"]["rtps"],

        rtpp=
        cfg["letkf"]["inflation"]["rtpp"],

        mult=
        cfg["letkf"]["inflation"]["mult"],

        localization_lengthscale=
        cfg["letkf"]
        ["localization"]
        ["lengthscale"],

        max_nobs=
        cfg["letkf"]
        ["localization"]
        ["max_nobs"],
    )

    outfile = (
        letkf_dir
        / "letkf.yaml"
    )

    with open(
        outfile,
        "w",
    ) as f:

        f.write(
            rendered
        )

    print(
        f"[RENDER] {outfile}"
    )

# =============================================================================
# Run
# =============================================================================

def get_project_root():

    return (
        Path(__file__)
        .resolve()
        .parents[1]
    )

def prepare_output_dirs(cfg, cycle):

    cycle_dir = get_cycle_dir(
        cfg,
        cycle,
    )

    letkf_dir = (
        cycle_dir
        / "letkf"
    )

    analysis_dir = (
        letkf_dir
        / "analysis"
    )

    increment_dir = (
        letkf_dir
        / "increment"
    )

    analysis_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    increment_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for member in range(
        1,
        cfg["nmembers"] + 1,
    ):

        memdir = (
            analysis_dir
            / f"mem{member:03d}"
        )

        memdir.mkdir(
            parents=True,
            exist_ok=True,
        )

    print(
        f"[PREP] {cycle}"
    )

def run_cycle(
    cfg,
    cycle,
    dry_run=False,
):

    project_root = get_project_root()

    render_cycle(
        cfg,
        cycle,
    )

    prepare_output_dirs(
        cfg,
        cycle,
    )

    cycle_dir = get_cycle_dir(
        cfg,
        cycle,
    )

    letkf_dir = (
        cycle_dir
        / "letkf"
    )

    yaml_file = (
        letkf_dir
        / "letkf.yaml"
    )

    logfile = (
        letkf_dir
        / f"letkf_{cycle}.log"
    )

    jedi_root = os.getenv(
        "JEDI_BUNDLE_ROOT"
    )

    if not jedi_root:

        raise RuntimeError(
            "JEDI_BUNDLE_ROOT not set"
        )

    executable = (
        Path(jedi_root)
        / "bin"
        / "fv3jedi_letkf.x"
    )

    if not executable.exists():

        raise RuntimeError(
            f"Missing executable: {executable}"
        )

    #
    # IMPORTANT:
    # execute from repository root
    #
    project_root = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    cmd = [

        "mpiexec",

        "--allow-run-as-root",

        "-n",

        str(
            cfg["mpi"]["ranks"]
        ),

        str(executable),

        str(yaml_file),
    ]

    print()
    print(
        "[RUN]",
        " ".join(cmd)
    )
    print(
        f"[LOG] {logfile}"
    )
    print()

    if dry_run:
        return

    with open(
        logfile,
        "w",
    ) as log:

        subprocess.run(
            cmd,
            cwd=project_root,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )

# =============================================================================
# Clean
# =============================================================================

def clean_cycle(
    cfg,
    cycle,
):

    letkf_dir = (
        get_cycle_dir(
            cfg,
            cycle,
        )
        / "letkf"
    )

    if not letkf_dir.exists():
        return

    targets = []

    targets.extend(
        letkf_dir.glob(
            "*.yaml"
        )
    )

    targets.extend(
        letkf_dir.glob(
            "*.log"
        )
    )

    targets.extend(
        letkf_dir.glob(
            "diag_*.nc4"
        )
    )

    targets.append(
        letkf_dir
        / "analysis"
    )

    targets.append(
        letkf_dir
        / "increment"
    )

    for target in targets:

        if target.is_dir():

            shutil.rmtree(
                target,
                ignore_errors=True,
            )

        elif target.exists():

            target.unlink()

    print(
        f"[CLEAN] {cycle}"
    )


# =============================================================================
# Main
# =============================================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command",
        choices=[
            "check",
            "render",
            "run",
            "clean",
        ]
    )

    parser.add_argument(
        "config"
    )

    parser.add_argument(
        "--cycle"
    )

    parser.add_argument(
        "--start"
    )

    parser.add_argument(
        "--end"
    )

    parser.add_argument(
        "--last",
        type=int,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = (
        parser.parse_args()
    )

    cfg = load_yaml(
        args.config
    )

    cycles = get_cycles(
        cfg,
        args,
    )

    if not cycles:

        print(
            "No cycles found"
        )
        return

    if args.command == "check":

        success = 0

        for cycle in cycles:

            if check_cycle(
                cfg,
                cycle,
            ):
                success += 1

        print()
        print(
            f"Validation passed "
            f"{success}/{len(cycles)} cycles"
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

        completed = 0

        for cycle in cycles:

            valid = check_cycle(
                cfg,
                cycle,
            )

            if not valid:
                continue

            run_cycle(
                cfg,
                cycle,
                dry_run=args.dry_run,
            )

            completed += 1

        print()
        print(
            f"Completed "
            f"{completed}/{len(cycles)} cycles"
        )

    elif args.command == "clean":

        for cycle in cycles:

            clean_cycle(
                cfg,
                cycle,
            )


if __name__ == "__main__":
    main()
