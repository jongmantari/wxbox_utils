#!/usr/bin/env python3

import sys
import yaml
import pathlib
import datetime as dt

import numpy as np
import netCDF4 as nc

# =====================================================
# CONFIG
# =====================================================

if len(sys.argv) > 1:
    cfgfile = sys.argv[1]
else:
    cfgfile = "asos_concat.yaml"

with open(cfgfile) as f:
    cfg = yaml.safe_load(f)

start = dt.datetime.strptime(
    cfg["cycles"]["start"],
    "%Y%m%dT%HZ"
)

end = dt.datetime.strptime(
    cfg["cycles"]["end"],
    "%Y%m%dT%HZ"
)

cycle_step = dt.timedelta(
    hours=cfg["cycles"]["interval_hours"]
)

before_hours = cfg["window"]["before_hours"]
after_hours = cfg["window"]["after_hours"]

outroot = pathlib.Path(
    cfg["output"]["root"]
)

KEEP_GROUPS = [
    "MetaData",
    "ObsValue",
    "DerivedObsValue",
    "PreQC"
]

# =====================================================
# HELPERS
# =====================================================

def copy_global_attributes(src, dst):

    for att in src.ncattrs():

        dst.setncattr(
            att,
            src.getncattr(att)
        )


# =====================================================
# MAIN
# =====================================================

for obs_type in cfg["obs_types"]:

    obs_cfg = cfg["obs"][obs_type]

    input_dir = pathlib.Path(
        obs_cfg["input_dir"]
    )

    file_pattern = (
        obs_cfg["file_pattern"]
    )

    output_pattern = (
        obs_cfg["output_pattern"]
    )

    obs_errors = (
        obs_cfg["obserror"]
    )

    current = start

    while current <= end:

        cycle_dir = current.strftime(
            "%Y%m%dT%HZ"
        )

        outfile_name = current.strftime(
            output_pattern
        )

        outdir = (
            outroot
            / obs_type
            / cycle_dir
        )

        outdir.mkdir(
            parents=True,
            exist_ok=True
        )

        outfile = (
            outdir
            / outfile_name
        )

        # -------------------------------------------------
        # gather files in window
        # -------------------------------------------------

        infiles = []

        for dh in range(
            -before_hours,
            after_hours + 1
        ):

            t = (
                current
                + dt.timedelta(
                    hours=dh
                )
            )

            fname = t.strftime(
                file_pattern
            )

            fpath = (
                input_dir
                / fname
            )

            if fpath.exists():

                infiles.append(
                    fpath
                )

        if len(infiles) == 0:

            print(
                "No files:",
                cycle_dir
            )

            current += cycle_step
            continue

        print()
        print(
            "Cycle:",
            cycle_dir
        )

        print(
            "Files:",
            len(infiles)
        )

        # -------------------------------------------------
        # sample file
        # -------------------------------------------------

        sample = nc.Dataset(
            infiles[0]
        )

        total_locations = 0

        for f in infiles:

            ds = nc.Dataset(f)

            total_locations += len(
                ds.dimensions[
                    "Location"
                ]
            )

            ds.close()

        # -------------------------------------------------
        # create output
        # -------------------------------------------------

        out = nc.Dataset(
            outfile,
            "w"
        )

        copy_global_attributes(
            sample,
            out
        )

        out.createDimension(
            "Location",
            total_locations
        )

        locvar = out.createVariable(
            "Location",
            "i8",
            ("Location",)
        )

        locvar[:] = np.arange(
            total_locations
        )

        # -------------------------------------------------
        # create schema
        # -------------------------------------------------

        for gname in KEEP_GROUPS:

            if gname not in sample.groups:
                continue

            gsrc = sample.groups[gname]

            gout = out.createGroup(
                gname
            )

            for vname in gsrc.variables:

                srcvar = (
                    gsrc.variables[
                        vname
                    ]
                )

                dtype = srcvar.dtype

                fill_value = None

                if (
                    "_FillValue"
                    in srcvar.ncattrs()
                ):
                    fill_value = (
                        srcvar.getncattr(
                            "_FillValue"
                        )
                    )

                if (
                    str(dtype)
                    .startswith(
                        "<class 'str'"
                    )
                ):

                    outvar = (
                        gout.createVariable(
                            vname,
                            str,
                            ("Location",)
                        )
                    )

                else:

                    outvar = (
                        gout.createVariable(
                            vname,
                            dtype,
                            ("Location",),
                            fill_value=fill_value
                        )
                    )

                for att in (
                    srcvar.ncattrs()
                ):

                    if att == "_FillValue":
                        continue

                    outvar.setncattr(
                        att,
                        srcvar.getncattr(att)
                    )

        sample.close()

        # -------------------------------------------------
        # concatenate
        # -------------------------------------------------

        offset = 0

        for f in infiles:

            ds = nc.Dataset(f)

            nloc = len(
                ds.dimensions[
                    "Location"
                ]
            )

            sl = slice(
                offset,
                offset + nloc
            )

            for gname in KEEP_GROUPS:

                if gname not in ds.groups:
                    continue

                gsrc = ds.groups[gname]
                gout = out.groups[gname]

                for vname in gout.variables:

                    if (
                        vname
                        not in
                        gsrc.variables
                    ):
                        continue

                    gout.variables[
                        vname
                    ][sl] = (
                        gsrc.variables[
                            vname
                        ][:]
                    )

            offset += nloc

            ds.close()

        # -------------------------------------------------
        # ObsError
        # -------------------------------------------------

        if (
            "ObsError"
            not in out.groups
        ):
            out.createGroup(
                "ObsError"
            )

        gerr = out.groups[
            "ObsError"
        ]

        for varname, err in (
            obs_errors.items()
        ):

            if (
                "ObsValue"
                not in out.groups
            ):
                continue

            if (
                varname
                not in
                out.groups[
                    "ObsValue"
                ].variables
            ):
                continue

            v = gerr.createVariable(
                varname,
                np.float32,
                ("Location",)
            )

            v[:] = np.full(
                total_locations,
                err,
                dtype=np.float32
            )

            try:

                v.units = (
                    out.groups[
                        "ObsValue"
                    ]
                    .variables[
                        varname
                    ]
                    .units
                )

            except Exception:
                pass

            v.long_name = (
                "observation error "
                f"for {varname}"
            )

        out.close()

        print(
            "Created:",
            outfile
        )

        current += cycle_step

print()
print("DONE")
