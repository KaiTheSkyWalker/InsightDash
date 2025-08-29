from itertools import cycle, islice

# Base palette for charts
base_palette = [
    '#E73489',  # Bright Pink
    '#7E32A8',  # Purple
    '#49319B',  # Dark Blue
    '#3B63C4',  # Medium Blue
    '#45B4D3',  # Light Blue
]


def color_map_from_list(keys, palette=base_palette):
    """Return a stable color map for the given keys using the palette."""
    extended_palette = list(islice(cycle(palette), len(keys)))
    return dict(zip(keys, extended_palette))


# Consistent colors for performance tiers across the app
TIER_COLOR_MAP = {
    'HIGH_PERFORMER': '#16a34a',      # Green
    'GOOD_PERFORMER': '#2563eb',      # Blue
    'AVERAGE_PERFORMER': '#f59e0b',   # Amber
    'NEEDS_IMPROVEMENT': '#dc2626',   # Red
}

def tier_color_map():
    return dict(TIER_COLOR_MAP)
