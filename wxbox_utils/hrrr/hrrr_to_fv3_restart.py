#!/usr/bin/env python3

import shutil
import yaml
import numpy as np
import xarray as xr

from pathlib import Path

from wxbox_utils.hrrr.hrrr_reader import HRRRReader
from wxbox_utils.hrrr.hrrr_horizontal_sample import HRRRSampler
from wxbox_utils.hrrr.hrrr_vertical import FV3VerticalGrid


class HRRRToFV3Restart:

    def __init__(self, cfgfile):

        with open(cfgfile) as f:
            self.cfg = yaml.safe_load(f)

        #
        # Cycle-driven workflow
        #
        self.cycles_root = Path(
            self.cfg["cycles"]["root"]
        )

        self.output_root = Path(
            self.cfg["output"]["root"]
        )

        #
        # Build horizontal sampler later
        #
        self.horizontal = None

        self.vertical = FV3VerticalGrid(
            self.cfg["grid"]["akbk"]
        )

        #
        # FV3 target grid
        #
        self.grid_file = (
            self.cfg["grid"]["grid_file"]
        )

        self.template_dir = Path(
            self.cfg["grid"]["template_dir"]
        )

        #
        # Load FV3 coordinates once
        #
        grid = xr.open_dataset(
            self.grid_file
        )

        lonc = grid["x"].values
        latc = grid["y"].values

        #
        # Mass grid
        #
        self.mass_lon = 0.25 * (
            lonc[:-1, :-1]
            + lonc[1:, :-1]
            + lonc[:-1, 1:]
            + lonc[1:, 1:]
        )

        self.mass_lat = 0.25 * (
            latc[:-1, :-1]
            + latc[1:, :-1]
            + latc[:-1, 1:]
            + latc[1:, 1:]
        )

        #
        # U grid
        #
        self.u_lon = 0.5 * (
            lonc[:, :-1]
            + lonc[:, 1:]
        )

        self.u_lat = 0.5 * (
            latc[:, :-1]
            + latc[:, 1:]
        )

        #
        # V grid
        #
        self.v_lon = 0.5 * (
            lonc[:-1, :]
            + lonc[1:, :]
        )

        self.v_lat = 0.5 * (
            latc[:-1, :]
            + latc[1:, :]
        )

        print()
        print("=" * 60)
        print("FV3 TARGET GRID")
        print("=" * 60)

        print("Mass:", self.mass_lon.shape)
        print("U   :", self.u_lon.shape)
        print("V   :", self.v_lon.shape)

        print()

    # --------------------------------------------------
    # Discover cycles
    # --------------------------------------------------

    def discover_cycles(self):

        cycles = []

        for d in sorted(
            self.cycles_root.iterdir()
        ):

            if d.is_dir():

                cycles.append(d)

        return cycles

    # --------------------------------------------------
    # Copy template restart package
    # --------------------------------------------------

    def copy_templates(
        self,
        outdir
    ):

        outdir.mkdir(
            parents=True,
            exist_ok=True
        )

        files = [

            self.cfg["templates"]["core"],
            self.cfg["templates"]["tracer"],
            self.cfg["templates"]["sfcw"],
            self.cfg["templates"]["sfcd"],

        ]

        for f in files:

            shutil.copy(
                self.template_dir / f,
                outdir / f
            )

        #
        # copy coupler file
        #
        coupler = list(
            self.template_dir.glob(
                "*.coupler.res"
            )
        )

        if coupler:

            shutil.copy(
                coupler[0],
                outdir / coupler[0].name
            )

    # --------------------------------------------------
    # Update coupler time
    # --------------------------------------------------

    def update_coupler_time(
        self,
        outdir,
        cycle_tag
    ):

        year = int(cycle_tag[0:4])
        month = int(cycle_tag[4:6])
        day = int(cycle_tag[6:8])

        hour = int(
            cycle_tag.split("T")[1]
            .replace("Z", "")
        )

        couplers = list(
            outdir.glob(
                "*.coupler.res"
            )
        )

        if len(couplers) != 1:

            raise RuntimeError(
                f"{outdir}: expected one coupler file"
            )

        coupler = couplers[0]

        with open(coupler, "r") as f:
            lines = f.readlines()

        print()
        print("Original coupler:")
        print(lines[1].rstrip())
        print(lines[2].rstrip())

        lines[1] = (
            f"{year:6d}"
            f"{month:6d}"
            f"{day:6d}"
            f"{hour:6d}"
            f"{0:6d}"
            f"{0:6d}"
            "        Model start time:   year, month, day, hour, minute, second\n"
        )

        lines[2] = (
            f"{year:6d}"
            f"{month:6d}"
            f"{day:6d}"
            f"{hour:6d}"
            f"{0:6d}"
            f"{0:6d}"
            "        Current model time: year, month, day, hour, minute, second\n"
        )

        with open(coupler, "w") as f:
            f.writelines(lines)

        with open(coupler, "r") as f:
            verify = f.readlines()

        print()
        print("Updated coupler:")
        print(verify[1].rstrip())
        print(verify[2].rstrip())

            
    # --------------------------------------------------
    # Process one cycle
    # --------------------------------------------------

    def process_cycle(
        self,
        cycle_dir
    ):

        cycle_tag = cycle_dir.name

        print()
        print("=" * 80)
        print(f"Processing Cycle {cycle_tag}")
        print("=" * 80)

        gribs = list(
            cycle_dir.glob(
                "*.grib2"
            )
        )

        if len(gribs) != 1:

            raise RuntimeError(
                f"{cycle_tag}: "
                f"expected exactly one grib2 file"
            )

        grib_file = str(
            gribs[0]
        )

        outdir = (
            self.output_root
            / cycle_tag
            / "fv3_restart"
        )

        self.copy_templates(
            outdir
        )

        self.update_coupler_time(
            outdir,
            cycle_tag
        )
        
        #
        # Read HRRR
        #
        reader = HRRRReader(
            grib_file
        )

        fields = reader.read()

        #
        # Build sampler
        #
        self.horizontal = HRRRSampler(

            fields["lon"],
            fields["lat"],

            self.mass_lon,
            self.mass_lat,

            self.u_lon,
            self.u_lat,

            self.v_lon,
            self.v_lat,
        )

        #
        # Horizontal interpolation
        #
        ps = self.horizontal.mass(
            fields["sp"]
        )

        T_h = self.horizontal.mass(
            fields["t"]
        )

        U_h = self.horizontal.wind(
            fields["u"]
        )

        V_h = self.horizontal.wind(
            fields["v"]
        )

        U10 = self.horizontal.wind(
            fields["u10"]
        )

        V10 = self.horizontal.wind(
            fields["v10"]
        )

        #
        # Vertical interpolation
        #
        T65 = self.vertical.interpolate(
            T_h,
            fields["pressure_t"],
            ps
        )

        UA65 = self.vertical.interpolate(
            U_h,
            fields["pressure_uv"],
            ps
        )

        VA65 = self.vertical.interpolate(
            V_h,
            fields["pressure_uv"],
            ps
        )

        DELP = self.vertical.delp(
            ps
        )

        #
        # MVP moisture
        #

        q2 = self.horizontal.u(
            fields["sh2"]
        )

        t2m = self.horizontal.u(
            fields["t2m"]
        )        

        sphum = np.repeat(
            q2[None, :, :],
            65,
            axis=0
        )

        #
        # fv_core
        #
        core = xr.load_dataset(
            outdir /
            self.cfg["templates"]["core"]
        )

        if "ua" in core:
            core["ua"][0] = UA65

        if "va" in core:
            core["va"][0] = VA65

        core["T"][0] = T65
        core["DELP"][0] = DELP

        core.to_netcdf(
            outdir /
            "hrrr.fv_core.res.tile1.nc"
        )

        #
        # fv_tracer
        #
        tracer = xr.load_dataset(
            outdir /
            self.cfg["templates"]["tracer"]
        )

        tracer["sphum"][0] = sphum

        tracer.to_netcdf(
            outdir /
            "hrrr.fv_tracer.res.tile1.nc"
        )

        #
        # fv_srf_wnd
        #
        sfcw = xr.load_dataset(
            outdir /
            self.cfg["templates"]["sfcw"]
        )

        if "u_srf" in sfcw:
            sfcw["u_srf"][0, 0] = U10

        if "v_srf" in sfcw:
            sfcw["v_srf"][0, 0] = V10

        sfcw.to_netcdf(
            outdir /
            "hrrr.fv_srf_wnd.res.tile1.nc"
        )

        #
        # sfc_data
        #
        sfcd = xr.load_dataset(
            outdir /
            self.cfg["templates"]["sfcd"]
        )

        if "t2m" in sfcd:

            sfcd["t2m"][0, 0] = t2m

        sfcd.to_netcdf(
            outdir /
            "hrrr.sfc_data.nc"
        )

        print()
        print(
            f"Finished cycle {cycle_tag}"
        )

    # --------------------------------------------------
    # Driver
    # --------------------------------------------------

    def run(self):

        cycles = self.discover_cycles()

        print()
        print("=" * 80)
        print(
            f"Cycles discovered: {len(cycles)}"
        )
        print("=" * 80)

        for cycle_dir in cycles:

            self.process_cycle(
                cycle_dir
            )


def main():

    import sys

    if len(sys.argv) != 2:

        print()
        print(
            "Usage:\n"
            "python "
            "hrrr_to_fv3_restart.py "
            "hrrr_fv3_c1667.yaml"
        )
        print()

        sys.exit(1)

    app = HRRRToFV3Restart(
        sys.argv[1]
    )

    app.run()


if __name__ == "__main__":
    main()
