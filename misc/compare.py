import matplotlib.pyplot as plt
import xarray as xr


fig, ax = plt.subplots()

# John's netcdf:
minutes0to19_file = "/Volumes/PAM_Analysis/pypam-space/InputMinutes/pypamASA_MARS_20220902_minutes0to19.nc"
minutes0to19_ds = xr.open_dataset(minutes0to19_file)
# minutes0to19_ds['millidecade_bands'][0].plot()

# My netcdf:
minute0_file = (
    "/Volumes/PAM_Analysis/pypam-space/test_output/milli_psd_20220902_000000.nc"
)
minute0_ds = xr.open_dataset(minute0_file)
# minute0_ds['__xarray_dataarray_variable__'][0].plot()

# difference:
diff = (
    minutes0to19_ds["millidecade_bands"][0]
    - minute0_ds["__xarray_dataarray_variable__"][0]
)

diff.plot()  # type: ignore[missing-argument]
# perhaps a future xarray version will have more complete type stubs
plt.show()
