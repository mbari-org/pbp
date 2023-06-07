Part of preparations to capture metadata into the product.

- `chumash/` –  Contains metadata attributes for the Chumash Heritage NMS products.
    - `globalAttributes.json`
    - `variableAttributes.json`

- `mars/` – Contains metadata attributes for MARS.
    - `globalAttributes.json`
    - `variableAttributes.json`


NOTE regarding "effort" variable units:

- If explicitly setting `"units": "seconds"`:
    - If also setting `np.timedelta64` for the array elements, xarray would complain when saving the NetCDF:
      ```
      ValueError: failed to prevent overwriting existing key units in attrs on variable 'effort'.
         This is probably an encoding field used by xarray to describe how a variable is serialized.
          To proceed, remove this key from the variable's attributes manually.
      ```
    - If setting `np.float32` (and probably other types as well), no errors are raised.
- If not setting any `"units"` attribute:
    - no problem setting either `np.timedelta64` or `np.float32`.
      The former will show:
      ```
      In [34]: mars.effort.values
      Out[34]:
      array([60000000000, 60000000000, 60000000000, 60000000000, 60000000000,
             .....
             60000000000, 60000000000, 60000000000, 60000000000, 60000000000],
            dtype='timedelta64[ns]')
      ```
      The latter:
      ```
      In [36]: mars.effort.values
      Out[36]:
      array([60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60.,
             60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60.,
             60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60.,
             60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60., 60.,
             60., 60., 60., 60., 60., 60., 60., 60.], dtype=float32)
      ```
