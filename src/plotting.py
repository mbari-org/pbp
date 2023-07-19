import matplotlib.dates as md
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pvlib
import xarray as xr
from matplotlib import gridspec


def plot_dataset_summary(
    ds: xr.Dataset, jpeg_filename: str, dpi: int = 200
):  # pylint: disable=R0915  too-many-statements
    """
    Generate a summary plot from the given dataset.
    Code by RYJO, with minor formatting/variable naming adjustments.
    :param ds: Dataset to plot.
    :param jpeg_filename: Filename to save the plot to.
    :param dpi: DPI to use for the plot.
    """
    # Transpose psd array for plotting
    da = xr.DataArray.transpose(ds.psd)

    # get solar elevation
    # Estimate the solar position with a specific SPA defined with the argument 'method'
    solpos = pvlib.solarposition.get_solarposition(ds.time, 36.7128, -122.186, 0)
    se = solpos.elevation  # isolate solar elevation
    # map elevation to gray scale
    seg = 0 * se  # 0 covers nighttime (black)
    # day (white)
    d = np.squeeze(np.where(se > 0))
    seg[d] = 1
    # dusk / dawn (gray range)
    d = np.squeeze(np.where(np.logical_and(se <= 0, se >= -12)))
    seg[d] = 1 - abs(se[d] / max(abs(se[d])))
    # Get the indices of the min and max
    seg1 = pd.Series.to_numpy(solpos.elevation)
    minidx = np.squeeze(np.where(seg1 == min(seg1)))
    maxidx = np.squeeze(np.where(seg1 == max(seg1)))

    seg3 = np.tile(seg, (50, 1))

    # plotting variables
    psdlabl = r'Spectrum level (dB re 1 " r"$\mu$Pa$\mathregular{^{2}}$ Hz$\mathregular{^{-1}}$)'
    freqlabl = "Frequency (Hz)"
    titl = "MBARI MARS Cabled Observatory   Monterey Bay, California, USA   36.713 \xb0N, 122.186 \xb0W"

    # define percentiles
    pctlev = np.array([1, 10, 25, 50, 75, 90, 99])
    # initialize output array
    pctls = np.empty((pctlev.size, ds.frequency.size))
    # get percentiles
    np.nanpercentile(ds.psd, pctlev, axis=0, out=pctls)

    # create a figure
    fig = plt.figure()
    fig.set_figheight(6)
    fig.set_figwidth(12)
    spec = gridspec.GridSpec(
        ncols=2,
        nrows=2,
        width_ratios=[2.5, 1],
        wspace=0.02,
        height_ratios=[0.045, 0.95],
        hspace=0.09,
    )

    # Use more of the available plotting space
    plt.subplots_adjust(left=0.06, right=0.94, bottom=0.12, top=0.89)

    # Spectrogram
    ax0 = fig.add_subplot(spec[2])
    sg = plt.pcolormesh(
        ds.time, ds.frequency, da, shading="nearest", cmap="rainbow", vmin=32, vmax=108
    )
    plt.yscale("log")
    plt.ylim(10, 100000)
    plt.ylabel(freqlabl)
    xl = ax0.get_xlim()
    ax0.set_xticks([])
    # plt.colorbar(location='left', shrink = 0.25, fraction = 0.05)

    # Percentile
    pplabels = ["L99", "L90", "L75", "L50", "L25", "L10", "L1"]
    ax1 = fig.add_subplot(spec[3])
    ax1.yaxis.tick_right()
    ax1.yaxis.set_label_position("right")
    plt.plot(pctls.T, ds.frequency, linewidth=1)
    plt.yscale("log")
    plt.ylim([10, 100000])
    plt.xlabel(psdlabl)
    plt.ylabel(freqlabl)
    plt.legend(loc="lower left", labels=pplabels)

    # day night
    ax3 = fig.add_subplot(spec[0])
    ax3.pcolormesh(seg3, shading="flat", cmap="gray")
    ax3.annotate("Day", (maxidx, 25), weight="bold", ha="center", va="center")
    ax3.annotate(
        "Night", (minidx, 25), weight="bold", color="white", ha="center", va="center"
    )
    ax3.set_xticks([])
    ax3.set_yticks([])

    # colorbar for spectrogram
    r = np.concatenate(np.squeeze(ax0.get_position()))
    cb_ax = fig.add_axes([r[0] + 0.09, r[1] - 0.025, r[2] - 0.25, 0.015])
    q = fig.colorbar(sg, orientation="horizontal", cax=cb_ax)
    q.set_label(psdlabl)

    # time axes for the day/night panel
    # create a dummy time / zero range variable
    timax = fig.add_axes(ax3.get_position(), frameon=False)
    timax.plot(solpos.elevation * 0, "k")
    timax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
    timax.set_ylim(0, 100)
    timax.set_yticks([])
    timax.set_xlim(xl)
    timax.xaxis.set_major_formatter(
        md.ConciseDateFormatter(timax.xaxis.get_major_locator())
    )

    plt.gcf().text(0.5, 0.955, titl, fontsize=14, horizontalalignment="center")
    plt.gcf().text(0.65, 0.91, "UTC")

    plt.savefig(jpeg_filename, dpi=dpi)
    # plt.show()


def plot_summary_for_file(nc_filename: str, dpi: int = 200) -> str:
    """
    Generate a summary plot from the given netcdf file.
    :param nc_filename:
        netcdf file to plot
    :param dpi:
        DPI to use for the plot.
    :return:
        filename of the generated jpeg
    """
    jpeg_filename = nc_filename.replace(".nc", ".jpg")
    ds = xr.open_dataset(nc_filename)
    plot_dataset_summary(ds, jpeg_filename, dpi=dpi)
    return jpeg_filename


if __name__ == "__main__":
    import sys

    nc_f = sys.argv[1]
    dpi_ = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    print(f"plotting {nc_f} at {dpi_} dpi")
    jpeg_f = plot_summary_for_file(nc_f, dpi_)
    print(f"   done: {jpeg_f}")
