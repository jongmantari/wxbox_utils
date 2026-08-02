#!/usr/bin/env python3

import os
import sys
import shutil

import yaml
import numpy as np
import netCDF4 as nc

# =====================================================
# YAML
# =====================================================

def load_yaml(filename):

    with open(filename, "r") as f:

        return yaml.safe_load(f)

# =====================================================
# Balanced T-q perturbation
# =====================================================

def apply_balanced_tq_blob(

        T,
        q,

        amplitude,

        levels,

        decay_scale,

        sigma_i,
        sigma_j,

        q_per_kelvin,

        random_center=False):

    #
    # Temperature grid
    #
    nyT = T.shape[2]
    nxT = T.shape[3]

    blobT, cx, cy = build_blob(

        nxT,
        nyT,

        sigma_i,
        sigma_j,

        random_center
    )

    #
    # Moisture grid
    #
    nyQ = q.shape[2]
    nxQ = q.shape[3]

    blobQ, _, _ = build_blob(

        nxQ,
        nyQ,

        sigma_i,
        sigma_j,

        random_center
    )

    ksurf = (
        T.shape[1] - 1
    )

    for kk in range(levels):

        k = (
            ksurf - kk
        )

        if k < 0:
            break

        weight = np.exp(
            -kk / decay_scale
        )

        #
        # Temperature perturbation
        #
        dT = (
            amplitude
            * weight
            * blobT
        )

        #
        # Correlated moisture perturbation
        #
        dq = (
            q_per_kelvin
            * amplitude
            * weight
            * blobQ
        )

        T[
            0,
            k,
            :,
            :
        ] += dT

        q[
            0,
            k,
            :,
            :
        ] += dq

    return (
        T,
        q,
        cx,
        cy
    )

# =====================================================
# Random or centered blob
# =====================================================

def build_blob(
        nx,
        ny,
        sigma_i,
        sigma_j,
        random_center=False):

    if random_center:

        cx = np.random.randint(
            nx
        )

        cy = np.random.randint(
            ny
        )

    else:

        cx = nx // 2
        cy = ny // 2

    x = np.arange(nx)
    y = np.arange(ny)

    X, Y = np.meshgrid(
        x,
        y
    )

    blob = np.exp(
        -0.5 * (
            ((X - cx) / sigma_i) ** 2
            +
            ((Y - cy) / sigma_j) ** 2
        )
    )

    return blob, cx, cy


# =====================================================
# Gaussian centered at domain center
# =====================================================

def build_centered_blob(
        nx,
        ny,
        sigma_i,
        sigma_j):

    cx = nx // 2
    cy = ny // 2

    x = np.arange(nx)
    y = np.arange(ny)

    X, Y = np.meshgrid(
        x,
        y
    )

    blob = np.exp(
        -0.5 * (
            ((X - cx) / sigma_i) ** 2
            +
            ((Y - cy) / sigma_j) ** 2
        )
    )

    return blob, cx, cy


# =====================================================
# Apply perturbation
# =====================================================

def apply_centered_gaussian_blob(
        field,
        amplitude,
        levels,
        decay_scale,
        sigma_i,
        sigma_j):

    if field.ndim != 4:

        raise ValueError(
            f"Expected 4D field "
            f"shape={field.shape}"
        )

    ny = field.shape[2]
    nx = field.shape[3]

    blob, cx, cy = build_centered_blob(
        nx,
        ny,
        sigma_i,
        sigma_j
    )

    ksurf = field.shape[1] - 1

    for kk in range(levels):

        k = ksurf - kk

        if k < 0:
            break

        weight = np.exp(
            -kk / decay_scale
        )

        field[
            0,
            k,
            :,
            :
        ] += (
            amplitude
            * weight
            * blob
        )

    return field, cx, cy

# =====================================================
# CONFIG
# =====================================================
def generate_ensembles(cfg):

    cycles_root = (
        cfg["cycles"]["root"]
    )

    background_subdir = (
        cfg["background"]["directory"]
    )

    ensemble_subdir = (
        cfg["ensemble"]["directory"]
    )

    members = (
        cfg["ensemble"]["members"]
    )

    copy_files = (
        cfg["files"]["copy"]
    )

    perturbations = (
        cfg["perturbations"]
    )

    # =====================================================
    # DISCOVER CYCLES
    # =====================================================

    cycles = []

    for d in sorted(
        os.listdir(cycles_root)
    ):

        cycle_path = os.path.join(
            cycles_root,
            d
        )

        if (
            os.path.isdir(cycle_path)
            and
            os.path.isdir(
                os.path.join(
                    cycle_path,
                    background_subdir
                )
            )
        ):

            cycles.append(d)

    print()
    print("=" * 70)
    print("Creating Synthetic Ensembles")
    print("=" * 70)

    print()

    print(
        f"Cycles discovered: "
        f"{len(cycles)}"
    )

    # =====================================================
    # PROCESS CYCLES
    # =====================================================

    for cycle in cycles:

        print()
        print("=" * 70)
        print(
            f"Cycle: {cycle}"
        )
        print("=" * 70)

        cycle_dir = os.path.join(
            cycles_root,
            cycle
        )

        bkg_dir = os.path.join(
            cycle_dir,
            background_subdir
        )

        ens_root = os.path.join(
            cycle_dir,
            ensemble_subdir
        )

        os.makedirs(
            ens_root,
            exist_ok=True
        )

        # --------------------------------------------
        # Members
        # --------------------------------------------

        for mem, delta in members.items():

            memdir = os.path.join(
                ens_root,
                mem
            )

            if os.path.exists(memdir):

                shutil.rmtree(memdir)

            os.makedirs(memdir)

            #
            # Copy restart package
            #
            for fname in copy_files:

                src = os.path.join(
                    bkg_dir,
                    fname
                )

                dst = os.path.join(
                    memdir,
                    fname
                )

                shutil.copy2(
                    src,
                    dst
                )

            #
            # Always copy coupler file
            #
            for fname in os.listdir(
                bkg_dir
            ):

                if fname.endswith(
                    ".coupler.res"
                ):

                    shutil.copy2(

                        os.path.join(
                            bkg_dir,
                            fname
                        ),

                        os.path.join(
                            memdir,
                            fname
                        )
                    )

            print()
            print(
                f"{mem} "
                f"delta={delta:+.2f}"
            )

            # ------------------------------------
            # Apply perturbations
            # ------------------------------------

            for pert in perturbations:

                mode = pert["mode"]

                # --------------------------------
                # Balanced T-q perturbation
                # --------------------------------

                if mode == "balanced_tq":

                    core_file = os.path.join(
                        memdir,
                        pert["temperature_file"]
                    )

                    tracer_file = os.path.join(
                        memdir,
                        pert["tracer_file"]
                    )

                    core = nc.Dataset(
                        core_file,
                        "r+"
                    )

                    tracer = nc.Dataset(
                        tracer_file,
                        "r+"
                    )

                    T = core[
                        pert[
                            "temperature_variable"
                        ]
                    ][:]

                    q = tracer[
                        pert[
                            "tracer_variable"
                        ]
                    ][:]

                    T, q, cx, cy = (
                        apply_balanced_tq_blob(

                            T=T,

                            q=q,

                            amplitude=delta,

                            levels=int(
                                pert["levels"]
                            ),

                            decay_scale=float(
                                pert.get(
                                    "decay_scale",
                                    2.0
                                )
                            ),

                            sigma_i=float(
                                pert["sigma_i"]
                            ),

                            sigma_j=float(
                                pert["sigma_j"]
                            ),

                            q_per_kelvin=float(
                                pert.get(
                                    "q_per_kelvin",
                                    0.05
                                )
                            ),

                            random_center=bool(
                                pert.get(
                                    "random_center",
                                    False
                                )
                            )
                        )
                    )

                    core[
                        pert[
                            "temperature_variable"
                        ]
                    ][:] = T

                    tracer[
                        pert[
                            "tracer_variable"
                        ]
                    ][:] = q

                    core.close()
                    tracer.close()

                    print(
                        f"  balanced_tq"
                        f" center=({cy},{cx})"
                        f" amp={delta:+.3f}"
                    )

                # --------------------------------
                # Legacy Gaussian perturbation
                # --------------------------------

                else:

                    filename = os.path.join(
                        memdir,
                        pert["file"]
                    )

                    variable = (
                        pert["variable"]
                    )

                    ds = nc.Dataset(
                        filename,
                        "r+"
                    )

                    field = ds[
                        variable
                    ][:]

                    amp = delta

                    if (
                        "scale_factor"
                        in pert
                    ):

                        amp *= float(
                            pert[
                                "scale_factor"
                            ]
                        )

                    field, cx, cy = (
                        apply_centered_gaussian_blob(

                            field=field,

                            amplitude=amp,

                            levels=int(
                                pert["levels"]
                            ),

                            decay_scale=float(
                                pert.get(
                                    "decay_scale",
                                    2.0
                                )
                            ),

                            sigma_i=float(
                                pert["sigma_i"]
                            ),

                            sigma_j=float(
                                pert["sigma_j"]
                            ),
                        )
                    )

                    ds[
                        variable
                    ][:] = field

                    ds.close()

                    print(
                        f"  {variable:8s}"
                        f" center=({cy},{cx})"
                        f" amp={amp:+.3f}"
                    )

    # =====================================================
    # DONE
    # =====================================================

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)

    print()

    for mem, delta in members.items():

        print(
            f"{mem}: "
            f"{delta:+.2f}"
        )
        
# =====================================================
# CLI
# =====================================================

def main():

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "config",
        nargs="?",
        default="ensemble_c1667.yaml",
    )

    args = parser.parse_args()

    cfg = load_yaml(
        args.config
    )

    generate_ensembles(
        cfg
    )


if __name__ == "__main__":

    main()
