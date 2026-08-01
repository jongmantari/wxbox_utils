#!/usr/bin/env python3

"""
hrrr_horizontal.py

Horizontal interpolation utilities for:

    HRRR
        ↓
    FV3 C1667

Mass grid:

    ny=158
    nx=142

Wind grid:

    ny=159
    nx=142

Test:

    python hrrr_horizontal.py
"""

import numpy as np

from scipy.ndimage import zoom


class HorizontalInterpolator:

    """
    HRRR -> C1667

    Mass:
        158 x 142

    Wind:
        159 x 142
    """

    def __init__(self):

        #
        # C1667 dimensions
        #
        self.mass_ny = 158
        self.mass_nx = 142

        self.wind_ny = 159
        self.wind_nx = 142

    # --------------------------------------------------
    # Generic interpolation
    # --------------------------------------------------

    @staticmethod
    def _interp2d(
        field,
        ny_new,
        nx_new,
        order=1,
    ):

        zy = ny_new / field.shape[-2]
        zx = nx_new / field.shape[-1]

        return zoom(
            field,
            (zy, zx),
            order=order,
        )

    # --------------------------------------------------
    # Interpolate final two dimensions
    # --------------------------------------------------

    def _interp_field(
        self,
        data,
        ny_new,
        nx_new,
        order=1,
    ):

        shape = data.shape

        #
        # 2D field
        #
        if len(shape) == 2:

            return self._interp2d(
                data,
                ny_new,
                nx_new,
                order,
            )

        #
        # ND field
        #
        lead_shape = shape[:-2]

        out = np.empty(

            (*lead_shape,
             ny_new,
             nx_new),

            dtype=np.float32
        )

        for idx in np.ndindex(*lead_shape):

            out[idx] = self._interp2d(

                data[idx],

                ny_new,
                nx_new,

                order,
            )

        return out

    # --------------------------------------------------
    # Mass grid
    # --------------------------------------------------

    def mass(
        self,
        field,
        order=1,
    ):

        return self._interp_field(

            field,

            self.mass_ny,
            self.mass_nx,

            order,
        )

    # --------------------------------------------------
    # Wind grid
    # --------------------------------------------------

    def wind(
        self,
        field,
        order=1,
    ):

        return self._interp_field(

            field,

            self.wind_ny,
            self.wind_nx,

            order,
        )

    # --------------------------------------------------
    # Surface grid
    # --------------------------------------------------

    def surface(
        self,
        field,
        order=1,
    ):

        return self.mass(
            field,
            order,
        )


# ======================================================
# Test Mode
# ======================================================

def run_tests():

    h = HorizontalInterpolator()

    print()
    print("=" * 60)
    print("HRRR Horizontal Interpolator Test")
    print("=" * 60)

    #
    # Surface field
    #
    surface = np.random.rand(
        1059,
        1799,
    )

    out = h.surface(surface)

    print()

    print(
        "Surface:"
    )

    print(
        f"  Input  : {surface.shape}"
    )

    print(
        f"  Output : {out.shape}"
    )

    assert out.shape == (
        158,
        142,
    )

    #
    # Pressure-level field
    #
    T = np.random.rand(

        7,
        1059,
        1799,
    )

    out = h.mass(T)

    print()

    print(
        "Mass Field:"
    )

    print(
        f"  Input  : {T.shape}"
    )

    print(
        f"  Output : {out.shape}"
    )

    assert out.shape == (
        7,
        158,
        142,
    )

    #
    # Wind field
    #
    U = np.random.rand(

        7,
        1059,
        1799,
    )

    out = h.wind(U)

    print()

    print(
        "Wind Field:"
    )

    print(
        f"  Input  : {U.shape}"
    )

    print(
        f"  Output : {out.shape}"
    )

    assert out.shape == (
        7,
        159,
        142,
    )

    #
    # FV3-style field
    #
    fv3 = np.random.rand(

        65,
        1059,
        1799,
    )

    out = h.mass(fv3)

    print()

    print(
        "FV3 65-Level Field:"
    )

    print(
        f"  Input  : {fv3.shape}"
    )

    print(
        f"  Output : {out.shape}"
    )

    assert out.shape == (
        65,
        158,
        142,
    )

    print()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    print()


# ======================================================
# Main
# ======================================================

if __name__ == "__main__":

    run_tests()
