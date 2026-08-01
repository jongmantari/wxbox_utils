#!/usr/bin/env python3

import sys
import numpy as np
import cfgrib


class HRRRReader:

    #
    # Levels discovered from HRRR inventory
    #
    T_LEVELS = np.array([
        1000,
         925,
         850,
         700,
         500,
    ])

    UV_LEVELS = np.array([
        1000,
         925,
         850,
         700,
         500,
         300,
         250,
    ])

    def __init__(self, grib_file):

        self.grib_file = grib_file

    # --------------------------------------------------
    # Read
    # --------------------------------------------------

    def read(self):

        have_coords = False

        datasets = cfgrib.open_datasets(
            self.grib_file,
            indexpath=""
        )

        fields = {}

        print()
        print("=" * 60)
        print("HRRR Reader")
        print("=" * 60)

        for i, ds in enumerate(datasets):

            vars_ = set(ds.data_vars)

            #
            # grab coordinates once
            #
            if (
                not have_coords
                and
                "latitude" in ds.coords
                and
                "longitude" in ds.coords
            ):

                fields["lat"] = (
                    ds["latitude"].values
                )

                fields["lon"] = (
                    ds["longitude"].values
                )

                have_coords = True

                print(
                    f"Dataset {i}: coordinates"
                )

                print(
                    "   lat/lon:",
                    fields["lat"].shape
                )

            #
            # Dataset 13
            #
            if "t2m" in vars_:

                print(
                    f"Dataset {i}: 2m fields"
                )

                for var in [

                    "t2m",
                    "d2m",
                    "sh2",
                    "r2",

                ]:

                    if var in ds:

                        fields[var] = (
                            ds[var].values
                        )

            #
            # Dataset 15
            #
            elif "u10" in vars_:

                print(
                    f"Dataset {i}: 10m winds"
                )

                fields["u10"] = (
                    ds["u10"].values
                )

                fields["v10"] = (
                    ds["v10"].values
                )

            #
            # Dataset 23
            #
            elif {

                "t",
                "dpt",

            }.issubset(vars_):

                print(
                    f"Dataset {i}: "
                    "pressure temperature"
                )

                fields["t"] = (
                    ds["t"].values
                )

                fields["dpt"] = (
                    ds["dpt"].values
                )

                fields["pressure_t"] = (
                    self.T_LEVELS
                )

            #
            # Dataset 24
            #
            elif {

                "u",
                "v",

            }.issubset(vars_):

                print(
                    f"Dataset {i}: "
                    "pressure winds"
                )

                fields["u"] = (
                    ds["u"].values
                )

                fields["v"] = (
                    ds["v"].values
                )

                fields["pressure_uv"] = (
                    self.UV_LEVELS
                )

            #
            # Dataset 42
            #
            elif "sp" in vars_:

                print(
                    f"Dataset {i}: "
                    "surface pressure"
                )

                fields["sp"] = (
                    ds["sp"].values
                )

        print()
        print("=" * 60)
        print("FIELDS")
        print("=" * 60)

        for k in sorted(fields):

            try:

                print(
                    f"{k:<15}"
                    f"{fields[k].shape}"
                )

            except Exception:

                print(
                    f"{k:<15}"
                    f"{fields[k]}"
                )

        print()

        return fields
