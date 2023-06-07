Part of preparations to capture metadata into the product.

- `chumash/` –  Contains metadata attributes for the Chumash Heritage NMS products.
    - `globalAttributes.json`
    - `variableAttributes.json`

- `mars/` – Contains metadata attributes for MARS.
    - `globalAttributes.json`
    - `variableAttributes.json`


TODO NOTE:

If explicitly adding `"units": "seconds"` for `"effort"` in `variableAttributes.json`,
then the saving of the NetCDF would make xarray complain with:
```
ValueError: failed to prevent overwriting existing key units in attrs on variable 'effort'.
   This is probably an encoding field used by xarray to describe how a variable is serialized.
    To proceed, remove this key from the variable's attributes manually.
```
