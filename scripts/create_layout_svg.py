# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate an SVG comparing Zarr V2, V3, and V3+sharding file layouts
in a three-column layout sized for an 8.5x11 portrait page."""

# ── Page & layout constants ───────────────────────────────────────────────────
# Target ~7in usable width at 96 dpi ≈ 672px.  We'll use a bit more and let
# the SVG scale via viewBox.

PAGE_W = 720
COL_W = 220
COL_GAP = 20
MARGIN_X = (PAGE_W - 3 * COL_W - 2 * COL_GAP) / 2

FONT = "Helvetica, Arial, sans-serif"
FONT_SIZE = 11
FONT_SMALL = 9.5

# Icon sizes (compact for columns)
FOLDER_W, FOLDER_H = 80, 34
FILE_W, FILE_H = 72, 38
FOLD = 8
ITEM_GAP = 6  # vertical gap between stacked items
BRACKET_GAP = 22  # vertical space for bracket connectors

# Colours
BLUE = "#4285F4"
YELLOW_META = "#FBBC04"
YELLOW_META_LIGHT = "#FFF9E6"
GREEN = "#34A853"
SHARD_GREEN = "#0D652D"
WHITE = "#FFFFFF"
GREY = "#5F6368"

ARRAYS = ["lat", "lon", "time", "temperature", "precipitation"]
COORD_ARRAYS = {"lat", "lon", "time"}


# ── SVG primitives ────────────────────────────────────────────────────────────


def folder_svg(x: float, y: float, w: float, h: float, label: str, fill: str) -> str:
    tab_w = w * 0.35
    tab_h = 7
    return (
        f'<g>'
        f'<path d="M{x},{y + tab_h} L{x},{y + h} L{x + w},{y + h} L{x + w},{y + tab_h}'
        f' L{x + tab_w + 4},{y + tab_h} L{x + tab_w},{y} L{x},{y} Z"'
        f' fill="{fill}" stroke="{fill}" stroke-width="1" rx="2"/>'
        f'<text x="{x + w / 2}" y="{y + tab_h + (h - tab_h) / 2 + 4}"'
        f' font-family="{FONT}" font-size="{FONT_SIZE}" fill="{WHITE}"'
        f' text-anchor="middle">{label}</text>'
        f'</g>'
    )


def file_svg(
    x: float, y: float, w: float, h: float, label: str, fill: str,
    text_fill: str = GREY, font_size: float = FONT_SMALL,
) -> str:
    return (
        f'<g>'
        f'<path d="M{x},{y} L{x + w - FOLD},{y} L{x + w},{y + FOLD} L{x + w},{y + h}'
        f' L{x},{y + h} Z"'
        f' fill="{fill}" stroke="{GREY}" stroke-width="0.6"/>'
        f'<path d="M{x + w - FOLD},{y} L{x + w - FOLD},{y + FOLD} L{x + w},{y + FOLD} Z"'
        f' fill="{GREY}" opacity="0.2"/>'
        f'<text x="{x + w / 2}" y="{y + h / 2 + 4}"'
        f' font-family="{FONT}" font-size="{font_size}" fill="{text_fill}"'
        f' text-anchor="middle">{label}</text>'
        f'</g>'
    )


def bracket_svg(
    parent_cx: float, parent_bottom: float,
    child_centers: list[float], child_top: float,
) -> str:
    mid_y = (parent_bottom + child_top) / 2
    lines: list[str] = []
    lines.append(
        f'<line x1="{parent_cx}" y1="{parent_bottom}"'
        f' x2="{parent_cx}" y2="{mid_y}" stroke="{GREY}" stroke-width="1"/>'
    )
    if len(child_centers) > 1:
        left, right = min(child_centers), max(child_centers)
        lines.append(
            f'<line x1="{left}" y1="{mid_y}"'
            f' x2="{right}" y2="{mid_y}" stroke="{GREY}" stroke-width="1"/>'
        )
    for cx in child_centers:
        lines.append(
            f'<line x1="{cx}" y1="{mid_y}"'
            f' x2="{cx}" y2="{child_top}" stroke="{GREY}" stroke-width="1"/>'
        )
    return "\n".join(lines)


def dots_svg(x: float, y: float) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="14" fill="{GREY}"'
        f' text-anchor="middle" font-weight="bold">...</text>'
    )


def title_svg(x: float, y: float, text: str) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="15"'
        f' font-weight="bold" fill="{GREY}" text-anchor="middle">{text}</text>'
    )


# ── Column builders ──────────────────────────────────────────────────────────


def build_v2_column(ox: float, oy: float) -> tuple[str, float]:
    """Build V2 tree within a column. Returns (svg, max_y)."""
    parts: list[str] = []
    cx = ox + COL_W / 2  # column center

    # Root folder
    root_x = cx - FOLDER_W / 2
    parts.append(folder_svg(root_x, oy, FOLDER_W, FOLDER_H, "Root", BLUE))
    root_bottom = oy + FOLDER_H

    # Row 1: root metadata files + array folders
    row1_y = root_bottom + BRACKET_GAP

    # Layout: meta files on left side, array folders spread across
    # We'll stack root meta vertically on the left, arrays across the middle
    meta_files = [(".zmetadata", YELLOW_META_LIGHT), (".zgroup", YELLOW_META), (".zattrs", YELLOW_META)]
    meta_x = ox + 2
    meta_cy = meta_x + FILE_W / 2

    child_centers_root: list[float] = []

    # Root meta stacked vertically
    my = row1_y
    for name, fill in meta_files:
        parts.append(file_svg(meta_x, my, FILE_W, FILE_H, name, fill))
        child_centers_root.append(meta_cy)
        my += FILE_H + ITEM_GAP

    # Array folders in a column to the right of meta
    arr_x = meta_x + FILE_W + 12
    arr_cx = arr_x + FOLDER_W / 2
    folder_ys: dict[str, float] = {}
    ay = row1_y
    for arr_name in ARRAYS:
        folder_ys[arr_name] = ay
        parts.append(folder_svg(arr_x, ay, FOLDER_W, FOLDER_H, arr_name, BLUE))
        child_centers_root.append(arr_cx)
        ay += FOLDER_H + ITEM_GAP

    # Bracket from root
    parts.append(bracket_svg(cx, root_bottom, child_centers_root, row1_y))

    # Row 2: per-array contents (indented under each folder)
    content_x = arr_x + FOLDER_W + 10
    content_cx = content_x + FILE_W / 2
    max_y = ay

    for arr_name in ARRAYS:
        fy = folder_ys[arr_name]
        folder_cx = arr_x + FOLDER_W / 2
        folder_bottom = fy + FOLDER_H

        child_centers: list[float] = []

        # .zarray
        cy = folder_bottom + BRACKET_GAP
        parts.append(file_svg(content_x, cy, FILE_W, FILE_H, ".zarray", YELLOW_META))
        child_centers.append(content_cx)
        cy += FILE_H + ITEM_GAP

        # .zattrs
        parts.append(file_svg(content_x, cy, FILE_W, FILE_H, ".zattrs", YELLOW_META))
        child_centers.append(content_cx)
        cy += FILE_H + ITEM_GAP

        # chunks
        if arr_name in COORD_ARRAYS:
            parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "0", GREEN))
            child_centers.append(content_cx)
            cy += FILE_H + ITEM_GAP
        else:
            parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "0.0.0", GREEN))
            child_centers.append(content_cx)
            cy += FILE_H + ITEM_GAP
            parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "0.0.1", GREEN))
            child_centers.append(content_cx)
            cy += FILE_H + 2
            parts.append(dots_svg(content_cx, cy + 8))
            cy += 16

        parts.append(bracket_svg(folder_cx, folder_bottom, child_centers,
                                  folder_bottom + BRACKET_GAP))
        max_y = max(max_y, cy)

    return "\n".join(parts), max_y


def build_v3_column(ox: float, oy: float) -> tuple[str, float]:
    """Build V3 tree within a column."""
    parts: list[str] = []
    cx = ox + COL_W / 2

    # Root folder
    root_x = cx - FOLDER_W / 2
    parts.append(folder_svg(root_x, oy, FOLDER_W, FOLDER_H, "Root", BLUE))
    root_bottom = oy + FOLDER_H

    row1_y = root_bottom + BRACKET_GAP
    child_centers_root: list[float] = []

    # zarr.json on left
    meta_x = ox + 2
    meta_cx = meta_x + FILE_W / 2
    parts.append(file_svg(meta_x, row1_y, FILE_W, FILE_H, "zarr.json", YELLOW_META))
    child_centers_root.append(meta_cx)

    # Array folders
    arr_x = meta_x + FILE_W + 12
    arr_cx = arr_x + FOLDER_W / 2
    folder_ys: dict[str, float] = {}
    ay = row1_y
    for arr_name in ARRAYS:
        folder_ys[arr_name] = ay
        parts.append(folder_svg(arr_x, ay, FOLDER_W, FOLDER_H, arr_name, BLUE))
        child_centers_root.append(arr_cx)
        ay += FOLDER_H + ITEM_GAP

    parts.append(bracket_svg(cx, root_bottom, child_centers_root, row1_y))

    # Per-array contents
    content_x = arr_x + FOLDER_W + 10
    content_cx = content_x + FILE_W / 2
    max_y = ay

    for arr_name in ARRAYS:
        fy = folder_ys[arr_name]
        folder_cx = arr_x + FOLDER_W / 2
        folder_bottom = fy + FOLDER_H

        child_centers: list[float] = []
        cy = folder_bottom + BRACKET_GAP

        # zarr.json
        parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "zarr.json", YELLOW_META))
        child_centers.append(content_cx)
        cy += FILE_H + ITEM_GAP

        # chunks
        if arr_name in COORD_ARRAYS:
            parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "c/0", GREEN))
            child_centers.append(content_cx)
            cy += FILE_H + ITEM_GAP
        else:
            parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "c/0/0/0", GREEN))
            child_centers.append(content_cx)
            cy += FILE_H + ITEM_GAP
            parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "c/0/0/1", GREEN))
            child_centers.append(content_cx)
            cy += FILE_H + 2
            parts.append(dots_svg(content_cx, cy + 8))
            cy += 16

        parts.append(bracket_svg(folder_cx, folder_bottom, child_centers,
                                  folder_bottom + BRACKET_GAP))
        max_y = max(max_y, cy)

    return "\n".join(parts), max_y


def build_v3s_column(ox: float, oy: float) -> tuple[str, float]:
    """Build V3+sharding tree within a column."""
    parts: list[str] = []
    cx = ox + COL_W / 2

    # Root folder
    root_x = cx - FOLDER_W / 2
    parts.append(folder_svg(root_x, oy, FOLDER_W, FOLDER_H, "Root", BLUE))
    root_bottom = oy + FOLDER_H

    row1_y = root_bottom + BRACKET_GAP
    child_centers_root: list[float] = []

    # zarr.json on left
    meta_x = ox + 2
    meta_cx = meta_x + FILE_W / 2
    parts.append(file_svg(meta_x, row1_y, FILE_W, FILE_H, "zarr.json", YELLOW_META))
    child_centers_root.append(meta_cx)

    # Array folders
    arr_x = meta_x + FILE_W + 12
    arr_cx = arr_x + FOLDER_W / 2
    folder_ys: dict[str, float] = {}
    ay = row1_y
    for arr_name in ARRAYS:
        folder_ys[arr_name] = ay
        parts.append(folder_svg(arr_x, ay, FOLDER_W, FOLDER_H, arr_name, BLUE))
        child_centers_root.append(arr_cx)
        ay += FOLDER_H + ITEM_GAP

    parts.append(bracket_svg(cx, root_bottom, child_centers_root, row1_y))

    # Per-array contents
    content_x = arr_x + FOLDER_W + 10
    content_cx = content_x + FILE_W / 2
    max_y = ay

    for arr_name in ARRAYS:
        fy = folder_ys[arr_name]
        folder_cx = arr_x + FOLDER_W / 2
        folder_bottom = fy + FOLDER_H

        child_centers: list[float] = []
        cy = folder_bottom + BRACKET_GAP

        # zarr.json
        parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "zarr.json", YELLOW_META))
        child_centers.append(content_cx)
        cy += FILE_H + ITEM_GAP

        # chunk / shard
        if arr_name in COORD_ARRAYS:
            parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "c/0", GREEN))
            child_centers.append(content_cx)
            cy += FILE_H + ITEM_GAP
        else:
            parts.append(file_svg(content_x, cy, FILE_W, FILE_H, "c/0/0/0",
                                   SHARD_GREEN, text_fill=WHITE))
            child_centers.append(content_cx)
            cy += FILE_H + 2
            parts.append(
                f'<text x="{content_cx}" y="{cy + 10}"'
                f' font-family="{FONT}" font-size="{FONT_SMALL}" fill="{GREY}"'
                f' text-anchor="middle" font-style="italic">(shard)</text>'
            )
            cy += 18

        parts.append(bracket_svg(folder_cx, folder_bottom, child_centers,
                                  folder_bottom + BRACKET_GAP))
        max_y = max(max_y, cy)

    return "\n".join(parts), max_y


# ── Legend ────────────────────────────────────────────────────────────────────


def build_legend(x: float, y: float) -> str:
    parts: list[str] = []
    items = [
        ("Group", BLUE, "folder"),
        ("JSON metadata", YELLOW_META, "file"),
        ("Chunk", GREEN, "file"),
        ("Shard", SHARD_GREEN, "file"),
    ]
    lx = x
    for label, fill, kind in items:
        if kind == "folder":
            parts.append(folder_svg(lx, y, 50, 26, "", fill))
        else:
            tfill = WHITE if fill == SHARD_GREEN else GREY
            parts.append(file_svg(lx, y, 50, 26, "", fill, text_fill=tfill, font_size=FONT_SMALL))
        parts.append(
            f'<text x="{lx + 58}" y="{y + 17}"'
            f' font-family="{FONT}" font-size="{FONT_SMALL}" fill="{GREY}">{label}</text>'
        )
        lx += 140
    return "\n".join(parts)


# ── Assemble ──────────────────────────────────────────────────────────────────


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
        parts.append(title_svg(col_starts[i] + COL_W / 2, title_y, t))

    # Separator line under titles
    parts.append(
        f'<line x1="{MARGIN_X}" y1="34" x2="{PAGE_W - MARGIN_X}" y2="34"'
        f' stroke="{GREY}" stroke-width="0.5" opacity="0.4"/>'
    )

    # Build columns
    builders = [build_v2_column, build_v3_column, build_v3s_column]
    max_y = col_top
    for i, builder in enumerate(builders):
        svg, bottom = builder(col_starts[i], col_top)
        parts.append(svg)
        max_y = max(max_y, bottom)

    # Vertical separators between columns
    for i in range(2):
        sep_x = col_starts[i] + COL_W + COL_GAP / 2
        parts.append(
            f'<line x1="{sep_x}" y1="10" x2="{sep_x}" y2="{max_y}"'
            f' stroke="{GREY}" stroke-width="0.5" stroke-dasharray="4,3" opacity="0.3"/>'
        )

    # Legend at bottom
    max_y += 20
    parts.append(build_legend(MARGIN_X + 20, max_y))
    max_y += 40

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
    out = Path(__file__).resolve().parent.parent / "figures" / "zarr_v2_v3_layout.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg)
    print(f"Written to {out}")
