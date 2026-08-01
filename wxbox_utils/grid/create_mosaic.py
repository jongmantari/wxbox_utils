#!/usr/bin/env python3

import sys
import yaml
import shutil

from netCDF4 import Dataset
from netCDF4 import stringtochar

import numpy as np


def write_char_string(nc, varname, text):

    v = nc.variables[varname]

    strlen = v.shape[1]

    arr = stringtochar(
        np.array(
            [text.ljust(strlen)],
            dtype=f"S{strlen}"
        )
    )

    v[:] = arr


def main():

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "python create_mosaic.py c1667.yaml"
        )

        sys.exit(1)

    with open(sys.argv[1], "r") as f:

        cfg = yaml.safe_load(f)

    grid = cfg["grid"]

    mosaic = grid["mosaic"]

    shutil.copy(
        mosaic["template"],
        mosaic["output"]
    )

    with Dataset(
        mosaic["output"],
        "r+"
    ) as nc:

        #
        # derive automatically
        #
        grid_file = (
            grid["output"]["grid_file"]
            .split("/")[-1]
        )

        grid_path = (
            "/".join(
                grid["output"]["grid_file"]
                .split("/")[:-2]
            )
        )

        write_char_string(
            nc,
            "gridfiles",
            grid_file
        )

        write_char_string(
            nc,
            "gridfiles_path",
            grid_path
        )

        write_char_string(
            nc,
            "gridtiles",
            "tile7"
        )

    print()
    print(
        f"Created {mosaic['output']}"
    )


if __name__ == "__main__":
    main()
