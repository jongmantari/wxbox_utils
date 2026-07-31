#!/usr/bin/env python3

"""
hrrr_vertical.py

FV3 Hybrid Vertical Coordinate Utilities

Functions:

    pint(ps)
    pmid(ps)
    delp(ps)

    interpolate()

    dewpoint_to_sphum()

Test:

    python hrrr_vertical.py \
        Data/inputs/lam_akbk/INPUT/akbk65.nc
"""

import sys
import numpy as np
import xarray as xr

from scipy.interpolate import interp1d


class FV3VerticalGrid:

    def __init__(self, akbk_file):

        ds = xr.open_dataset(
            akbk_file
        )

        self.ak = (
            ds["ak"]
            .isel(Time=0)
            .values
        )

        self.bk = (
            ds["bk"]
            .isel(Time=0)
            .values
        )

        self.nlev = (
            len(self.ak) - 1
        )

    # --------------------------------------------------
    # Interface pressure
    # --------------------------------------------------

    def pint(self, ps):

        return (

            self.ak[:, None, None]

            +

            self.bk[:, None, None]
            * ps[None, :, :]
        )

    # --------------------------------------------------
    # Midpoint pressure
    # --------------------------------------------------

    def pmid(self, ps):

        pint = self.pint(ps)

        return 0.5 * (

            pint[:-1]

            +

            pint[1:]
        )

    # --------------------------------------------------
    # DELP
    # --------------------------------------------------

    def delp(self, ps):

        pint = self.pint(ps)

        return (

            pint[1:]

            -

            pint[:-1]
        )

    # --------------------------------------------------
    # Pressure-level interpolation
    # --------------------------------------------------

    def interpolate(
        self,
        field,
        hrrr_pressure,
        ps,
    ):
        """
        field:
            (nz, ny, nx)

        hrrr_pressure:
            hPa

        ps:
            Pa
        """

        fv3_pmid = (
            self.pmid(ps)
            / 100.0
        )

        #
        # detect wind grid
        #
        _, ny_field, nx_field = field.shape

        _, ny_mass, nx_mass = fv3_pmid.shape

        if ny_field != ny_mass:

            fv3_pmid = np.pad(
                fv3_pmid,
                (
                    (0, 0),
                    (0, 1),
                    (0, 0),
                ),
                mode="edge"
            )

        nz_out, ny_out, nx_out = (
            fv3_pmid.shape
        )

        out = np.empty(
            (
                nz_out,
                ny_out,
                nx_out,
            ),
            dtype=np.float32,
        )

        psrc = np.asarray(
            hrrr_pressure
        )

        for j in range(ny_out):

            for i in range(nx_out):

                jj = min(
                    j,
                    field.shape[1] - 1
                )

                fint = interp1d(
                    psrc,
                    field[:, jj, i],
                    kind="linear",
                    bounds_error=False,
                    fill_value="extrapolate",
                )

                out[:, j, i] = fint(
                    fv3_pmid[:, j, i]
                )

        return out
    # --------------------------------------------------
    # Saturation vapor pressure
    # --------------------------------------------------

    @staticmethod
    def saturation_vapor_pressure(
        td_k
    ):

        td_c = (
            td_k - 273.15
        )

        return (

            611.2

            *

            np.exp(

                17.67
                * td_c

                /

                (
                    td_c
                    + 243.5
                )
            )
        )

    # --------------------------------------------------
    # Dewpoint -> specific humidity
    # --------------------------------------------------

    def dewpoint_to_sphum(

        self,

        dewpoint,

        pressure,
    ):

        """
        dewpoint: K

        pressure: Pa
        """

        e = (
            self
            .saturation_vapor_pressure(
                dewpoint
            )
        )

        q = (

            0.622
            * e

            /

            (
                pressure
                - 0.378 * e
            )
        )

        return q

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    def summary(self):

        print()

        print(
            "=" * 60
        )

        print(
            "FV3 Vertical Grid"
        )

        print(
            "=" * 60
        )

        print(
            f"Layers: "
            f"{self.nlev}"
        )

        print(
            f"Interfaces: "
            f"{len(self.ak)}"
        )

        print()

        print(
            "Top AK = "
            f"{self.ak[0]}"
        )

        print(
            "Bottom AK = "
            f"{self.ak[-1]}"
        )

        print()


# ======================================================
# Tests
# ======================================================

def run_tests(

    akbk_file
):

    fv3 = FV3VerticalGrid(
        akbk_file
    )

    fv3.summary()

    #
    # Sample PS
    #
    ps = np.full(

        (
            158,
            142,
        ),

        100000.0,
    )

    pint = fv3.pint(ps)

    pmid = fv3.pmid(ps)

    delp = fv3.delp(ps)

    print(
        "PINT:",
        pint.shape
    )

    print(
        "PMID:",
        pmid.shape
    )

    print(
        "DELP:",
        delp.shape
    )

    assert pint.shape == (
        66,
        158,
        142,
    )

    assert pmid.shape == (
        65,
        158,
        142,
    )

    assert delp.shape == (
        65,
        158,
        142,
    )

    #
    # Fake HRRR field
    #
    hrrr_levels = np.array([

        1000,
        925,
        850,
        700,
        500,
        300,
        250

    ])

    T = np.random.rand(

        7,
        158,
        142,
    )

    T65 = fv3.interpolate(

        T,

        hrrr_levels,

        ps,
    )

    print()

    print(
        "Interpolated T:"
    )

    print(
        T65.shape
    )

    assert T65.shape == (
        65,
        158,
        142,
    )

    #
    # Humidity test
    #
    td = np.full(

        (
            158,
            142,
        ),

        293.15
    )

    q = fv3.dewpoint_to_sphum(

        td,

        100000.0,
    )

    print()

    print(
        "Specific Humidity:"
    )

    print(
        q.min(),
        q.max(),
    )

    print()

    print(
        "=" * 60
    )

    print(
        "ALL TESTS PASSED"
    )

    print(
        "=" * 60
    )

    print()


# ======================================================
# Main
# ======================================================

def main():

    if len(sys.argv) != 2:

        print()

        print(
            "Usage:"
        )

        print(

            "python "
            "hrrr_vertical.py "
            "Data/inputs/lam_akbk/INPUT/akbk65.nc"
        )

        print()

        sys.exit(1)

    run_tests(
        sys.argv[1]
    )


if __name__ == "__main__":
    main()
