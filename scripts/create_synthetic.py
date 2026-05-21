# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "xarray",
#     "zarr==3.1.6",
#     "numpy",
# ]
# ///
"""Create a synthetic xarray dataset with lat/lon/time coordinates and
temperature/precipitation data variables, then write it as Zarr V2, V3,
and V3 with sharding. Print the object listing for each."""

import shutil
from pathlib import Path

import numpy as np
import xarray as xr

output_dir = Path(__file__).resolve().parent.parent / "examples" / "zarr_synthetic"
if output_dir.exists():
    shutil.rmtree(output_dir)
output_dir.mkdir(parents=True)

# Build a small synthetic dataset
np.random.seed(42)
nlat, nlon, ntime = 8, 8, 12

ds = xr.Dataset(
    {
        "temperature": (["time", "lat", "lon"], np.random.rand(ntime, nlat, nlon).astype("float32")),
        "precipitation": (["time", "lat", "lon"], np.random.rand(ntime, nlat, nlon).astype("float32")),
    },
    coords={
        "lat": ("lat", np.linspace(-90, 90, nlat, dtype="float64")),
        "lon": ("lon", np.linspace(-180, 180, nlon, dtype="float64")),
        "time": ("time", np.arange(ntime, dtype="int64")),
    },
)

print("Dataset:")
print(ds)
print()

# ── V2 ──
v2_path = output_dir / "v2.zarr"
ds.to_zarr(v2_path, zarr_format=2)

# ── V3 ──
v3_path = output_dir / "v3.zarr"
ds.to_zarr(v3_path, zarr_format=3)

# ── V3 with sharding ──
v3s_path = output_dir / "v3_sharded.zarr"

# Write with sharding: chunks = inner chunk size, shards = outer shard size
encoding = {}
for var in ["temperature", "precipitation"]:
    encoding[var] = {
        "chunks": (4, 4, 4),              # inner chunk size
        "shards": (ntime, nlat, nlon),    # shard size = full array
    }
for coord in ["lat", "lon", "time"]:
    shape = ds[coord].shape[0]
    encoding[coord] = {
        "chunks": (shape,),   # inner chunk = full coord
        "shards": (shape,),   # shard = full coord
    }

ds.to_zarr(v3s_path, zarr_format=3, encoding=encoding)
