# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "zarr==3.1.6",
#     "numpy",
# ]
# ///
"""Create example Zarr arrays to illustrate V2 vs V3 and sharding."""

import shutil
from pathlib import Path

import numpy as np
import zarr

output_dir = Path(__file__).resolve().parent.parent / "examples" / "zarr_examples"
if output_dir.exists():
    shutil.rmtree(output_dir)
output_dir.mkdir(parents=True)

data = np.arange(16, dtype=np.float64).reshape(4, 4)

# V2: 4 chunks, no sharding
store = zarr.storage.LocalStore(output_dir / "v2_no_sharding.zarr")
arr = zarr.create_array(
    store,
    shape=(4, 4),
    chunks=(2, 2),
    dtype="float64",
    zarr_format=2,
)
arr[:] = data

# V3: 4 chunks, no sharding
store = zarr.storage.LocalStore(output_dir / "v3_no_sharding.zarr")
arr = zarr.create_array(
    store,
    shape=(4, 4),
    chunks=(2, 2),
    dtype="float64",
    zarr_format=3,
)
arr[:] = data

# V3: 4 inner chunks with sharding (1 shard containing all 4 inner chunks)
store = zarr.storage.LocalStore(output_dir / "v3_sharding.zarr")
arr = zarr.create_array(
    store,
    shape=(4, 4),
    chunks=(2, 2),
    shards=(4, 4),
    dtype="float64",
    zarr_format=3,
)
arr[:] = data

# Print the resulting file trees
print("=== V2: 4 chunks, no sharding ===")
for p in sorted((output_dir / "v2_no_sharding.zarr").rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(output_dir)}")

print("\n=== V3: 4 chunks, no sharding ===")
for p in sorted((output_dir / "v3_no_sharding.zarr").rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(output_dir)}")

print("\n=== V3: 4 chunks, sharding ===")
for p in sorted((output_dir / "v3_sharding.zarr").rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(output_dir)}")

# Print metadata contents
print("\n\n=== Metadata contents ===")
for name in ["v2_no_sharding.zarr", "v3_no_sharding.zarr", "v3_sharding.zarr"]:
    print(f"\n--- {name} ---")
    meta_paths = list((output_dir / name).rglob("*.json")) + list(
        (output_dir / name).rglob(".z*")
    )
    for meta in sorted(meta_paths):
        print(f"\n  {meta.relative_to(output_dir / name)}:")
        print(f"  {meta.read_text()}")
