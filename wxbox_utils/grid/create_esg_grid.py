#!/usr/bin/env python3

import sys
import yaml
import numpy as np
import xarray as xr

EARTH_RADIUS = 6371229.0


class ESGGrid:

    def __init__(
        self,
        target_lon,
        target_lat,
        idim,
        jdim,
        delx_deg,
        dely_deg,
        halo=3,
    ):

        self.target_lon = target_lon
        self.target_lat = target_lat

        self.idim = idim
        self.jdim = jdim

        self.delx = delx_deg
        self.dely = dely_deg

        self.halo = halo

        #
        # ESG sizing convention
        #
        self.nx = 2 * idim + 12
        self.ny = 2 * jdim + 12

        self.nxp = self.nx + 1
        self.nyp = self.ny + 1

    def generate_latlon(self):

        i = np.arange(self.nxp)
        j = np.arange(self.nyp)

        ii, jj = np.meshgrid(i, j)

        xoff = ii - self.nxp // 2
        yoff = jj - self.nyp // 2

        eta = xoff / np.max(np.abs(xoff))
        xi = yoff / np.max(np.abs(yoff))

        #
        # Mantari mapping
        #
        eta2 = eta + 0.10 * eta**3

        lon = (
            self.target_lon
            + eta2 * (self.nxp // 2) * self.delx
        )

        lat = (
            self.target_lat
            + xi * (self.nyp // 2) * self.dely
        )

        lat = lat + 0.05 * (1.0 - eta**2)
        lat = lat - 0.05

        lon = (lon + 360.0) % 360.0

        return lon, lat

    def compute_metrics(self, lon, lat):

        lonr = np.radians(lon)
        latr = np.radians(lat)

        dx = np.zeros((self.nyp, self.nx))

        dx[:] = (
            EARTH_RADIUS
            * np.cos(latr[:, :-1])
            * np.abs(lonr[:, 1:] - lonr[:, :-1])
        )

        dy = np.zeros((self.ny, self.nxp))

        dy[:] = (
            EARTH_RADIUS
            * np.abs(latr[1:, :] - latr[:-1, :])
        )

        area = np.zeros((self.ny, self.nx))

        area[:] = (
            dx[:-1, :]
            * dy[:, :-1]
        )

        angle_dx = np.zeros((self.nyp, self.nxp))
        angle_dy = np.zeros((self.nyp, self.nxp))

        return dx, dy, area, angle_dx, angle_dy

    def write(self, outfile):

        lon, lat = self.generate_latlon()

        dx, dy, area, angle_dx, angle_dy = (
            self.compute_metrics(lon, lat)
        )

        ds = xr.Dataset(

            data_vars={

                "x": (
                    ("nyp", "nxp"),
                    lon,
                    {
                        "standard_name": "geographic_longitude",
                        "units": "degree_east",
                        "hstagger": "C",
                    },
                ),

                "y": (
                    ("nyp", "nxp"),
                    lat,
                    {
                        "standard_name": "geographic_latitude",
                        "units": "degree_north",
                        "hstagger": "C",
                    },
                ),

                "area": (
                    ("ny", "nx"),
                    area,
                    {
                        "standard_name": "grid_cell_area",
                        "units": "m2",
                        "hstagger": "H",
                    },
                ),

                "dx": (
                    ("nyp", "nx"),
                    dx,
                    {
                        "standard_name": "dx",
                        "units": "m",
                        "hstagger": "H",
                    },
                ),

                "dy": (
                    ("ny", "nxp"),
                    dy,
                    {
                        "standard_name": "dy",
                        "units": "m",
                        "hstagger": "H",
                    },
                ),

                "angle_dx": (
                    ("nyp", "nxp"),
                    angle_dx,
                    {
                        "standard_name": "angle_dx",
                        "units": "deg",
                        "hstagger": "C",
                    },
                ),

                "angle_dy": (
                    ("nyp", "nxp"),
                    angle_dy,
                    {
                        "standard_name": "angle_dy",
                        "units": "deg",
                        "hstagger": "C",
                    },
                ),
            }
        )

        ds.attrs.update(
            {
                "history": "gnomonic_ed",
                "source": "FV3GFS",
                "grid": "akappa",

                "plat": self.target_lat,
                "plon": self.target_lon,
                "pazi": 0.0,

                "delx": self.delx,
                "dely": self.dely,

                "lx": -71,
                "ly": -51,

                "a": 0.15966819226997153,
                "k": -0.3052578534551481,
            }
        )

        ds.to_netcdf(outfile)

        print(f"Wrote {outfile}")


def main():

    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "python create_esg_grid.py c1667.yaml"
        )
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        cfg = yaml.safe_load(f)

    g = cfg["grid"]

    grid = ESGGrid(
        target_lon=g["target_lon"],
        target_lat=g["target_lat"],
        idim=g["idim"],
        jdim=g["jdim"],
        delx_deg=g["delx"],
        dely_deg=g["dely"],
        halo=g.get("halo", 3),
    )

    grid.write(
        cfg["grid"]["output"]["grid_file"]
    )


if __name__ == "__main__":
    main()
