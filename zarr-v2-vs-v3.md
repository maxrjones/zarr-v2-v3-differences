# Differences Between Zarr V2 and Zarr V3

This document summarizes all significant differences between the Zarr Storage Specification Version 2 and the Zarr Core Specification Version 3 (current version: 3.1).

## Metadata File Layout

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Array metadata** | `.zarray` | `zarr.json` |
| **Group metadata** | `.zgroup` | `zarr.json` |
| **User attributes** | `.zattrs` (separate file) | `attributes` field inside `zarr.json` |
| **Node type indicator** | Implicit (determined by which dot-file exists) | Explicit `node_type` field (`"array"` or `"group"`) |

In V2, array metadata, group metadata, and user attributes are stored in three separate files. In V3, everything is consolidated into a single `zarr.json` document per node. This reduces the number of storage operations needed to read or write a node and eliminates race conditions between metadata and attribute files.

### V2 example (3 files)

`.zarray`:
```json
{
    "zarr_format": 2,
    "shape": [10000, 10000],
    "chunks": [1000, 1000],
    "dtype": "<f8",
    "compressor": {"id": "blosc", "cname": "lz4", "clevel": 5, "shuffle": 1},
    "fill_value": "NaN",
    "order": "C",
    "filters": [{"id": "delta", "dtype": "<f8", "astype": "<f4"}]
}
```

`.zattrs`:
```json
{"foo": 42, "bar": "apples"}
```

### V3 example (1 file)

`zarr.json`:
```json
{
    "zarr_format": 3,
    "node_type": "array",
    "shape": [10000, 1000],
    "data_type": "float64",
    "chunk_grid": {
        "name": "regular",
        "configuration": {"chunk_shape": [1000, 100]}
    },
    "chunk_key_encoding": {
        "name": "default",
        "configuration": {"separator": "/"}
    },
    "codecs": [
        {"name": "bytes", "configuration": {"endian": "little"}}
    ],
    "fill_value": "NaN",
    "attributes": {"foo": 42, "bar": "apples"}
}
```

## Group Metadata

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **File** | `.zgroup` | `zarr.json` |
| **Content** | Only `zarr_format` | `zarr_format`, `node_type`, optional `attributes` |
| **Attributes** | Separate `.zattrs` file | Inline `attributes` field |
| **Ancestor creation** | Ancestors must be explicitly created | Ancestors must be explicitly created (implicit groups were removed) |

In both V2 and V3, creating an array at path `foo/bar/baz` requires ensuring group metadata exists at `foo/bar`, `foo`, and the root. An earlier V3 draft supported implicit groups, but this was removed (see [PR #292](https://github.com/zarr-developers/zarr-specs/pull/292)).

## Data Types

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Field name** | `dtype` | `data_type` |
| **Format** | NumPy typestr format (e.g., `"<f8"`, `">i4"`, `"\|b1"`) | Named identifiers (e.g., `"float64"`, `"int32"`, `"bool"`) |
| **Byte order** | Embedded in dtype string | Handled by the `bytes` codec |
| **Structured/compound dtypes** | Supported via nested lists | Not in core; available via extensions |
| **Datetime/timedelta** | `datetime64` and `timedelta64` built-in | Not in core; available via extensions |
| **Strings** | Fixed-length strings (`\|S12`) and unicode (`\|U12`) | Not in core; available via extensions |

### V3 core data types

`bool`, `int8`, `int16`, `int32`, `int64`, `uint8`, `uint16`, `uint32`, `uint64`, `float16` (optional), `float32`, `float64`, `complex64`, `complex128`, `r*` (raw bits, optional)

V3 data types are language-agnostic identifiers rather than NumPy-specific format strings. Endianness is no longer part of the data type and is instead specified through the `bytes` codec. The `data_type` field is an extension point, so new data types can be added without modifying the core spec.

## Chunks and Chunk Grid

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Field name** | `chunks` (array of ints) | `chunk_grid` (named object with configuration) |
| **Grid types** | Only regular (uniform) grids | Regular grid in core; rectilinear and others via extensions |
| **Specification** | Flat array: `[1000, 1000]` | Object: `{"name": "regular", "configuration": {"chunk_shape": [1000, 100]}}` |

The chunk grid is an extension point in V3, enabling future grid types (e.g., rectilinear grids with non-uniform chunk sizes) without changing the core spec.

## Chunk Key Encoding

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Field** | `dimension_separator` (optional) | `chunk_key_encoding` (required) |
| **Default separator** | `.` | `/` |
| **Key prefix** | None | `c` |
| **Example key** | `0.0` or `0/0` | `c/0/0` or `c.0.0` |
| **0-d array key** | N/A | `c` |

V3 introduces a `c` prefix to chunk keys by default, which separates chunk data from metadata in the key namespace. The default separator changed from `.` to `/` (matching N5's convention), which produces a directory-like hierarchy that reduces the number of entries per directory on filesystem-based stores.

V3 also defines a backward-compatible `v2` chunk key encoding (`"chunk_key_encoding": {"name": "v2"}`) that preserves the old key format (no `c` prefix, `.` separator by default). This allows migrating existing V2 datasets to V3 metadata without renaming chunk files on disk.

## Compression and Codecs

This is one of the most significant architectural changes.

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Fields** | Separate `filters` and `compressor` | Single `codecs` list |
| **Pipeline** | Filters applied first, then single compressor | Ordered codec chain with typed stages |
| **Codec types** | Untyped (all are "id"-based) | Three types: `array -> array`, `array -> bytes`, `bytes -> bytes` |
| **Memory layout** | `order` field (`"C"` or `"F"`) | `transpose` codec (array -> array) |
| **Byte serialization** | Implicit (via NumPy memory layout + dtype endianness) | Explicit `bytes` codec with `endian` parameter |
| **Minimum codecs** | `compressor` can be `null`, `filters` can be `null` | Must have at least one `array -> bytes` codec |
| **Sharding** | Not supported | Supported via sharding codec (ZEP0002) |

### V2 compression model

```json
{
    "filters": [{"id": "delta", "dtype": "<f8"}],
    "compressor": {"id": "blosc", "cname": "lz4", "clevel": 5, "shuffle": 1},
    "order": "C"
}
```

Filters are applied in order, then the single compressor is applied.

### V3 codec pipeline

```json
{
    "codecs": [
        {"name": "transpose", "configuration": {"order": [1, 0]}},
        {"name": "bytes", "configuration": {"endian": "little"}},
        {"name": "blosc", "configuration": {"cname": "lz4", "clevel": 5, "shuffle": "noshuffle"}}
    ]
}
```

The pipeline is strictly ordered: zero or more `array -> array` codecs, then exactly one `array -> bytes` codec, then zero or more `bytes -> bytes` codecs.

### Key implications

- **Memory layout (`order`)** is no longer a top-level metadata field. It is handled by the `transpose` codec if non-default ordering is desired.
- **Byte serialization** is explicit. The `bytes` codec specifies endianness, making chunk data self-describing regardless of the data type field.
- **Sharding** (ZEP0002) is an `array -> bytes` codec that groups multiple logical chunks ("inner chunks") into a single storage object ("shard"), with an embedded index for random access to individual inner chunks.

## Fill Value

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Required** | Yes, but can be `null` | Yes, always required (no `null`) |
| **NaN/Infinity** | String encodings: `"NaN"`, `"Infinity"`, `"-Infinity"` | Same string encodings, plus hex byte representation (e.g., `"0x7fc00000"`) |
| **Boolean** | Integer `0` or `1` | JSON `true` or `false` |
| **Complex numbers** | Not specified | Two-element array: `[real, imag]` |
| **Binary/byte strings** | Base64-encoded | Array of integers in `[0, 255]` (for `r*` types) |
| **Default behavior** | `null` means contents of uninitialized chunks are undefined | Implementations may choose a default, but it must be recorded in metadata |

## Memory Layout (`order`)

| **V2** | **V3** |
|----|----|
| Top-level `order` field: `"C"` or `"F"` | No `order` field; use the `transpose` codec instead |

In V2, `"C"` means row-major (last dimension varies fastest) and `"F"` means column-major (first dimension varies fastest). In V3, the default is C order; column-major or other orderings are achieved by inserting a `transpose` codec into the codec chain.

## Extension Points

V2 has no formal extension mechanism. Unrecognized keys in metadata should be ignored.

V3 defines five explicit extension points:

| **Extension Point** | **Description** |
|-----------------|-------------|
| **Data types** | Custom data types beyond core (e.g., variable-length strings, datetime) |
| **Chunk grids** | Custom grid layouts (e.g., rectilinear) |
| **Chunk key encodings** | Custom chunk-to-key mappings |
| **Codecs** | Custom codecs for encoding/decoding |
| **Storage transformers** | Intercept and modify storage operations (e.g., caching, sharding) |

Each extension is identified by a registered name (e.g., `zstd`, `blosc`). Extensions use a consistent object format:

```json
{
    "name": "<extension-name>",
    "configuration": { ... }
}
```

Short-hand names (just a string) can be used when no configuration is needed.

### `must_understand` semantics

V3 introduces a `must_understand` field for extensions. By default, all extensions have `must_understand: true`, meaning implementations must fail if they encounter an unrecognized extension. Extensions can set `must_understand: false` to indicate they can be safely ignored. This replaces V2's implicit "ignore unknown keys" behavior with explicit, per-extension compatibility signaling.

## Storage Transformers

V3 introduces storage transformers, a concept absent in V2. Storage transformers sit between the codec pipeline and the store, intercepting and modifying storage operations at the array level (as opposed to codecs which operate per-chunk). They can be stacked. Use cases include caching, data reorganization, and encryption.

## Store Interface

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Interface definition** | Informal: read, write, delete | Formal abstract interface with three capability sets |
| **Capabilities** | Not categorized | readable, writeable, listable |
| **Partial I/O** | Not specified | `get_partial_values` and `set_partial_values` operations |
| **Listing** | Not specified | `list`, `list_prefix`, `list_dir` operations |
| **Bulk operations** | Not specified | `erase_values`, `erase_prefix` |

V3 formalizes the store interface to enable modular, interchangeable store implementations and explicitly supports partial reads/writes for efficient access to subsets of chunks (important for sharding).

## Node Names

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Character set** | Any ASCII string | Unicode with constraints |
| **Reserved prefixes** | Dot-files (`.zarray`, `.zgroup`, `.zattrs`) | `__` prefix reserved for Zarr internal use |
| **Constraints** | Normalized paths, no `.` or `..` segments | No `/`, no empty strings, no `.`/`..`-only strings, no `__` prefix |

## Dimension Names

| **V2** | **V3** |
|----|----|
| Not part of spec (handled by conventions like xarray's `_ARRAY_DIMENSIONS`) | Optional `dimension_names` field in array metadata |

V3 natively supports naming dimensions (e.g., `["x", "y", "z"]`), removing the need for convention-based workarounds.

## Hierarchy Model

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Root node** | Must be a group | Can be a group or an array |
| **Implicit groups** | Not supported | Removed after initial draft; ancestors must be explicitly created |

V3 allows a hierarchy to consist of a single root array, which simplifies the single-array use case. An early V3 draft supported implicit groups (ancestors inferred from descendants without explicit metadata), but this was removed in [PR #292](https://github.com/zarr-developers/zarr-specs/pull/292).

## Versioning and Stability Policy

| **Aspect** | **V2** | **V3** |
|--------|----|----|
| **Version format** | Single integer (`2`) | `MAJOR.MINOR` (e.g., `3.1`) |
| **Compatibility** | Not formally specified | Minor versions add features only; breaking changes require major version bump |
| **Metadata version** | `zarr_format: 2` | `zarr_format: 3` (major version only; minor features are auto-discovered) |

## Summary of Field Name Changes

| **V2 Field** | **V3 Field** |
|----------|----------|
| `dtype` | `data_type` |
| `chunks` | `chunk_grid` |
| `compressor` | `codecs` (combined) |
| `filters` | `codecs` (combined) |
| `order` | Removed (use `transpose` codec) |
| `dimension_separator` | `chunk_key_encoding` |
| (N/A) | `node_type` (new) |
| (N/A) | `dimension_names` (new) |
| (N/A) | `storage_transformers` (new) |
| (`.zattrs` file) | `attributes` (inline) |
