from argparse import ArgumentParser, RawTextHelpFormatter

from pbp.plot_const import (
    DEFAULT_DPI,
    DEFAULT_LAT_LON_FOR_SOLPOS,
    DEFAULT_TITLE,
    DEFAULT_YLIM,
    DEFAULT_CMLIM,
)
from pbp import get_pbp_version


def parse_arguments():
    description = "Generate summary plots for given netcdf files."

    parser = ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)

    parser.add_argument(
        "--version",
        action="version",
        version=get_pbp_version(),
    )

    parser.add_argument(
        "--latlon",
        type=float,
        nargs=2,
        default=DEFAULT_LAT_LON_FOR_SOLPOS,
        metavar=("lat", "lon"),
        help="Lat/Lon for solar position calculation . Default: %(default)s",
    )

    parser.add_argument(
        "--title",
        type=str,
        default=f"'{DEFAULT_TITLE}'",
        metavar="string",
        help="Title for the plot. Default: %(default)s",
    )

    parser.add_argument(
        "--ylim",
        type=int,
        nargs=2,
        default=DEFAULT_YLIM,
        metavar=("lower", "upper"),
        help="Limits for the y-axis. Default: %(default)s",
    )

    parser.add_argument(
        "--cmlim",
        type=int,
        nargs=2,
        default=DEFAULT_CMLIM,
        metavar=("vmin", "vmax"),
        help="Parameters passed to pcolormesh. Default: %(default)s",
    )

    parser.add_argument(
        "--dpi",
        type=float,
        default=DEFAULT_DPI,
        metavar="value",
        help="DPI to use for the plot. Default: %(default)s",
    )

    parser.add_argument(
        "--show",
        default=False,
        action="store_true",
        help="Also show the plot",
    )

    parser.add_argument(
        "--only-show",
        default=False,
        action="store_true",
        help="Only show the plot (do not generate .jpg files)",
    )

    parser.add_argument("netcdf", nargs="+", help="netcdf file(s) to plot")

    return parser.parse_args()


def main():
    opts = parse_arguments()
    # pylint: disable=import-outside-toplevel
    import xarray as xr

    from pbp.plotting import plot_dataset_summary

    show = opts.show or opts.only_show
    for nc_filename in opts.netcdf:
        print(f"plotting {nc_filename} at {opts.dpi} dpi")
        ds = xr.open_dataset(nc_filename)
        jpeg_filename = None if opts.only_show else nc_filename.replace(".nc", ".jpg")
        plot_dataset_summary(
            ds,
            lat_lon_for_solpos=opts.latlon,
            title=opts.title,
            ylim=opts.ylim,
            cmlim=opts.cmlim,
            dpi=opts.dpi,
            jpeg_filename=jpeg_filename,
            show=show,
        )
        if jpeg_filename is not None:
            print(f"   done: {jpeg_filename}")


if __name__ == "__main__":
    main()
