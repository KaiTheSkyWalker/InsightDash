from itertools import cycle, islice

# Base palette for charts (high‑contrast blue family)
# Ordered from darkest → lightest for good separation when cycled.
base_palette = [
    '#0B2E4E',  # Deep Navy
    '#1E3A8A',  # Indigo 800
    '#1D4ED8',  # Blue 700
    '#2563EB',  # Blue 600
    '#3B82F6',  # Blue 500
    '#60A5FA',  # Blue 400
    '#0EA5E9',  # Sky 500
    '#38BDF8',  # Sky 400
    '#0891B2',  # Cyan 700 (blue-leaning)
    '#06B6D4',  # Cyan 500 (blue-leaning)
    '#93C5FD',  # Blue 300
    '#BFDBFE',  # Blue 200
]


def color_map_from_list(keys, palette=base_palette):
    """Return a stable color map for the given keys using the palette."""
    extended_palette = list(islice(cycle(palette), len(keys)))
    return dict(zip(keys, extended_palette))


# Consistent colors for performance tiers across the app (well‑separated blues)
TIER_COLOR_MAP = {
    'HIGH_PERFORMER': '#1E3A8A',   # Dark indigo
    'GOOD_PERFORMER': '#2563EB',   # Strong blue
    'AVERAGE_PERFORMER': '#0EA5E9',# Sky / cyan (blue‑leaning)
    'NEEDS_IMPROVEMENT': '#93C5FD' # Light blue
}

def tier_color_map():
    return dict(TIER_COLOR_MAP)
