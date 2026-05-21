# Zarr V2 vs V3 Differences

A side-by-side reference for the differences between the Zarr V2 storage spec and the Zarr V3 core spec, with scripts that produce small example stores and explanatory figures.

## Contents

- [`zarr-v2-vs-v3.md`](zarr-v2-vs-v3.md), the main reference document, tables comparing metadata layout, data types, chunk grids, chunk-key encoding, codecs, fill values, extension points, and more.
- `scripts/`, self-contained scripts (each declares its own dependencies as PEP 723 inline metadata, runnable via `uv run`):
  - `create_examples.py`, writes a 4x4 array as V2, V3, and V3+sharding, then prints the on-disk file trees and metadata.
  - `create_synthetic.py`, builds a synthetic `xarray.Dataset` with `lat`/`lon`/`time` coords and `temperature`/`precipitation` variables, then writes it as V2, V3, and V3+sharding.
  - `create_layout_svg.py`, renders `figures/zarr_v2_v3_layout.svg`, a three-column tree view of how V2, V3, and V3+sharding lay out files on a filesystem.
  - `create_objstore_svg.py`, renders `figures/zarr_v2_v3_objstore.svg`, the same three configurations shown as flat object listings, with an object-count badge for each.
- `figures/`, generated SVGs plus a PNG export of the object-store figure.
- `examples/`, where the two `create_*.py` scripts write their `.zarr` stores. The store dirs themselves (`zarr_examples/`, `zarr_synthetic/`) are gitignored since they are regenerable.

## Regenerating everything

From any directory:

```sh
uv run scripts/create_examples.py     # writes examples/zarr_examples/
uv run scripts/create_synthetic.py    # writes examples/zarr_synthetic/
uv run scripts/create_layout_svg.py   # writes figures/zarr_v2_v3_layout.svg
uv run scripts/create_objstore_svg.py # writes figures/zarr_v2_v3_objstore.svg
```

Each script resolves its output path relative to its own location, so the CWD does not matter.

## License

MIT, see [`LICENSE`](LICENSE).
