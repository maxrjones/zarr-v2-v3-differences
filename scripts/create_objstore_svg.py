# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate an SVG comparing Zarr V2, V3, and V3+sharding as flat objects
in an object store, in a three-column layout sized for 8.5x11 portrait."""

PAGE_W = 720
COL_W = 210
COL_GAP = 20
MARGIN_X = (PAGE_W - 3 * COL_W - 2 * COL_GAP) / 2

FONT = "Helvetica, Arial, sans-serif"
FONT_SIZE = 11
FONT_SMALL = 9.5
FONT_MONO = "'SF Mono', 'Menlo', 'Consolas', monospace"

BLUE = "#4285F4"
YELLOW_META = "#FBBC04"
GREEN = "#34A853"
SHARD_GREEN = "#0D652D"
WHITE = "#FFFFFF"
GREY = "#5F6368"

OBJ_H = 24
OBJ_GAP = 3
BUCKET_PAD = 10

ARRAYS = ["lat", "lon", "time", "temperature", "precipitation"]
COORD_ARRAYS = {"lat", "lon", "time"}


def object_row(x: float, y: float, w: float, key: str, fill: str,
               text_fill: str = GREY) -> str:
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{OBJ_H}" rx="3"'
        f' fill="{fill}" stroke="{GREY}" stroke-width="0.4" opacity="0.85"/>'
        f'<text x="{x + 8}" y="{y + OBJ_H / 2 + 4}"'
        f' font-family="{FONT_MONO}" font-size="{FONT_SMALL}" fill="{text_fill}"'
        f'>{key}</text>'
        f'</g>'
    )


def count_badge(x: float, y: float, count: int) -> str:
    label = f"{count} objects"
    tw = len(label) * 7.5 + 14
    return (
        f'<rect x="{x - tw / 2}" y="{y}" width="{tw}" height="22" rx="11"'
        f' fill="{BLUE}" opacity="0.9"/>'
        f'<text x="{x}" y="{y + 15}"'
        f' font-family="{FONT}" font-size="{FONT_SIZE}" fill="{WHITE}"'
        f' text-anchor="middle" font-weight="bold">{label}</text>'
    )


def build_object_list_v2() -> list[tuple[str, str]]:
    objects: list[tuple[str, str]] = []
    objects.append((".zmetadata", YELLOW_META))
    objects.append((".zgroup", YELLOW_META))
    objects.append((".zattrs", YELLOW_META))
    for arr in ARRAYS:
        objects.append((f"{arr}/.zarray", YELLOW_META))
        objects.append((f"{arr}/.zattrs", YELLOW_META))
        if arr in COORD_ARRAYS:
            objects.append((f"{arr}/0", GREEN))
        else:
            objects.append((f"{arr}/0.0.0", GREEN))
            objects.append((f"{arr}/0.0.1", GREEN))
            objects.append((f"{arr}/0.0.2", GREEN))
            objects.append((f"{arr}/0.0.3", GREEN))
    return objects


def build_object_list_v3() -> list[tuple[str, str]]:
    objects: list[tuple[str, str]] = []
    objects.append(("zarr.json", YELLOW_META))
    for arr in ARRAYS:
        objects.append((f"{arr}/zarr.json", YELLOW_META))
        if arr in COORD_ARRAYS:
            objects.append((f"{arr}/c/0", GREEN))
        else:
            objects.append((f"{arr}/c/0/0/0", GREEN))
            objects.append((f"{arr}/c/0/0/1", GREEN))
            objects.append((f"{arr}/c/0/0/2", GREEN))
            objects.append((f"{arr}/c/0/0/3", GREEN))
    return objects


def build_object_list_v3_sharded() -> list[tuple[str, str]]:
    objects: list[tuple[str, str]] = []
    objects.append(("zarr.json", YELLOW_META))
    for arr in ARRAYS:
        objects.append((f"{arr}/zarr.json", YELLOW_META))
        if arr in COORD_ARRAYS:
            objects.append((f"{arr}/c/0", GREEN))
        else:
            objects.append((f"{arr}/c/0/0/0", SHARD_GREEN))
    return objects


def render_column(
    objects: list[tuple[str, str]], ox: float, oy: float, col_w: float,
) -> tuple[str, float]:
    """Render one column: dashed bucket with objects inside. Returns (svg, bottom_y)."""
    parts: list[str] = []
    inner_w = col_w - 2 * BUCKET_PAD
    bucket_h = len(objects) * (OBJ_H + OBJ_GAP) + 2 * BUCKET_PAD - OBJ_GAP

    # Dashed bucket outline
    parts.append(
        f'<rect x="{ox}" y="{oy}" width="{col_w}" height="{bucket_h}" rx="8"'
        f' fill="none" stroke="{GREY}" stroke-width="1.2" stroke-dasharray="5,3"/>'
    )

    # Objects
    row_y = oy + BUCKET_PAD
    for key, fill in objects:
        tfill = WHITE if fill == SHARD_GREEN else GREY
        parts.append(object_row(ox + BUCKET_PAD, row_y, inner_w, key, fill, text_fill=tfill))
        row_y += OBJ_H + OBJ_GAP

    # Count badge
    badge_y = oy + bucket_h + 10
    parts.append(count_badge(ox + col_w / 2, badge_y, len(objects)))

    return "\n".join(parts), badge_y + 30


def make_svg() -> str:
    title_y = 24
    col_top = 50

    col_starts = [
        MARGIN_X,
        MARGIN_X + COL_W + COL_GAP,
        MARGIN_X + 2 * (COL_W + COL_GAP),
    ]

    parts: list[str] = []

    # Column titles
    titles = ["Zarr V2", "Zarr V3", "Zarr V3 + Sharding"]
    for i, t in enumerate(titles):
        parts.append(
            f'<text x="{col_starts[i] + COL_W / 2}" y="{title_y}"'
            f' font-family="{FONT}" font-size="15" font-weight="bold"'
            f' fill="{GREY}" text-anchor="middle">{t}</text>'
        )

    # Separator line under titles
    parts.append(
        f'<line x1="{MARGIN_X}" y1="34" x2="{PAGE_W - MARGIN_X}" y2="34"'
        f' stroke="{GREY}" stroke-width="0.5" opacity="0.4"/>'
    )

    # Build columns
    lists = [build_object_list_v2(), build_object_list_v3(), build_object_list_v3_sharded()]
    max_y = col_top
    for i, objs in enumerate(lists):
        svg, bottom = render_column(objs, col_starts[i], col_top, COL_W)
        parts.append(svg)
        max_y = max(max_y, bottom)

    # Vertical separators
    for i in range(2):
        sep_x = col_starts[i] + COL_W + COL_GAP / 2
        parts.append(
            f'<line x1="{sep_x}" y1="10" x2="{sep_x}" y2="{max_y - 10}"'
            f' stroke="{GREY}" stroke-width="0.5" stroke-dasharray="4,3" opacity="0.3"/>'
        )

    # Legend row at bottom
    max_y += 10
    legend_items = [
        ("JSON metadata", YELLOW_META, GREY),
        ("Chunk", GREEN, GREY),
        ("Shard", SHARD_GREEN, WHITE),
    ]
    lx = MARGIN_X + 30
    for label, fill, tfill in legend_items:
        parts.append(
            f'<rect x="{lx}" y="{max_y}" width="40" height="18" rx="3"'
            f' fill="{fill}" stroke="{GREY}" stroke-width="0.4"/>'
        )
        parts.append(
            f'<text x="{lx + 48}" y="{max_y + 13}"'
            f' font-family="{FONT}" font-size="{FONT_SMALL}" fill="{GREY}">{label}</text>'
        )
        lx += 150
    max_y += 34

    content = "\n".join(parts)
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {PAGE_W} {max_y}"
     width="{PAGE_W}" height="{max_y}">
  <rect width="100%" height="100%" fill="white"/>
{content}
</svg>"""


if __name__ == "__main__":
    from pathlib import Path
    svg = make_svg()
    out = Path(__file__).resolve().parent.parent / "figures" / "zarr_v2_v3_objstore.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg)
    print(f"Written to {out}")
