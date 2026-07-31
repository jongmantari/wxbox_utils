#!/usr/bin/env python3

import numpy as np

from scipy.spatial import cKDTree


class HRRRSampler:

    def __init__(
        self,
        hrrr_lon,
        hrrr_lat,

        mass_lon,
        mass_lat,

        u_lon,
        u_lat,

        v_lon,
        v_lat,
    ):

        self.hrrr_lon = hrrr_lon
        self.hrrr_lat = hrrr_lat

        self.mass_lon = mass_lon
        self.mass_lat = mass_lat

        self.u_lon = u_lon
        self.u_lat = u_lat

        self.v_lon = v_lon
        self.v_lat = v_lat

        print()
        print("=" * 60)
        print("HRRR SAMPLER")
        print("=" * 60)

        print(
            "HRRR:",
            hrrr_lon.shape
        )

        print(
            "Mass:",
            mass_lon.shape
        )

        print(
            "U:",
            u_lon.shape
        )

        print(
            "V:",
            v_lon.shape
        )

        #
        # source point cloud
        #
        src_points = np.column_stack(
            (
                hrrr_lon.ravel(),
                hrrr_lat.ravel(),
            )
        )

        self.tree = cKDTree(
            src_points
        )

    # --------------------------------------------------
    # nearest-4 IDW interpolation
    # --------------------------------------------------

    def _sample(
        self,
        field,
        lon_dst,
        lat_dst,
    ):

        dst_points = np.column_stack(
            (
                lon_dst.ravel(),
                lat_dst.ravel(),
            )
        )

        dist, idx = self.tree.query(
            dst_points,
            k=4,
        )

        values = field.ravel()[idx]

        w = 1.0 / (
            dist + 1.0e-12
        )

        out = (
            np.sum(
                values * w,
                axis=1,
            )
            /
            np.sum(
                w,
                axis=1,
            )
        )

        return out.reshape(
            lon_dst.shape
        )

    # --------------------------------------------------
    # interpolate last two dimensions
    # --------------------------------------------------

    def _sample_field(
        self,
        data,
        lon_dst,
        lat_dst,
    ):

        #
        # 2-D field
        #
        if data.ndim == 2:

            return self._sample(
                data,
                lon_dst,
                lat_dst,
            )

        #
        # N-D field
        #
        lead = data.shape[:-2]

        out = np.empty(
            (
                *lead,
                *lon_dst.shape
            ),
            dtype=np.float32,
        )

        for idx in np.ndindex(*lead):

            out[idx] = self._sample(
                data[idx],
                lon_dst,
                lat_dst,
            )

        return out

    # --------------------------------------------------
    # mass grid
    # --------------------------------------------------

    def mass(
        self,
        field,
    ):

        return self._sample_field(
            field,
            self.mass_lon,
            self.mass_lat,
        )

    # --------------------------------------------------
    # u grid
    # --------------------------------------------------

    def u(
        self,
        field,
    ):

        return self._sample_field(
            field,
            self.u_lon,
            self.u_lat,
        )

    # --------------------------------------------------
    # v grid
    # --------------------------------------------------

    def v(
        self,
        field,
    ):

        return self._sample_field(
            field,
            self.v_lon,
            self.v_lat,
        )

    # --------------------------------------------------
    # surface fields
    # --------------------------------------------------

    def surface(
        self,
        field,
    ):

        return self.mass(
            field
        )

    # --------------------------------------------------
    # compatibility wrapper
    # --------------------------------------------------

    def wind(
        self,
        field,
    ):

        return self.u(
            field
        )
