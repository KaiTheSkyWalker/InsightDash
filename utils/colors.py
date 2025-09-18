from itertools import cycle, islice

# Base palette for charts (high‑contrast blue family)
# Ordered from darkest → lightest for good separation when cycled.
base_palette = [
    "#0B2E4E",  # Deep Navy
    "#1E3A8A",  # Indigo 800
    "#1D4ED8",  # Blue 700
    "#2563EB",  # Blue 600
    "#3B82F6",  # Blue 500
    "#60A5FA",  # Blue 400
    "#0EA5E9",  # Sky 500
    "#38BDF8",  # Sky 400
    "#0891B2",  # Cyan 700 (blue-leaning)
    "#06B6D4",  # Cyan 500 (blue-leaning)
    "#93C5FD",  # Blue 300
    "#BFDBFE",  # Blue 200
]

# High-contrast categorical palette for scatter plots (more differentiable)
diverse_palette = [
    "#2563EB",  # Blue
    "#D97706",  # Amber 700
    "#059669",  # Emerald 600
    "#7C3AED",  # Violet 600
    "#DC2626",  # Red 600
    "#0EA5E9",  # Sky 500
    "#F59E0B",  # Amber 500
    "#10B981",  # Emerald 500
    "#8B5CF6",  # Violet 500
    "#EF4444",  # Red 500
]

# (Removed several unused experimental palettes to keep API lean.)

# Brand palette from user (Lush Aqua, Jungle Book Green, Dewberry, Harissa Red, Moscow Papyrus, Bright Orange, Pale Narcissus)
brand_palette = [
    "#004365",
    "#366A51",
    "#8D5489",
    "#A52A2A",
    "#947D05",
    "#FF6F30",
    "#FAF3E0",
]

# Consistent category colors (A/B/C/D) across all tabs
CATEGORY_COLOR_MAP = {
    "A": "#004365",  # Lush Aqua
    "B": "#366A51",  # Jungle Book Green
    "C": "#8D5489",  # Dewberry
    "D": "#FF6F30",  # Bright Orange
}


def category_color_map():
    return dict(CATEGORY_COLOR_MAP)


def color_map_from_list(keys, palette=base_palette):
    """Return a stable color map for the given keys using the palette."""
    extended_palette = list(islice(cycle(palette), len(keys)))
    return dict(zip(keys, extended_palette))


# Consistent colors for performance tiers across the app (well‑separated blues)
TIER_COLOR_MAP = {
    "HIGH_PERFORMER": "#1E3A8A",  # Dark indigo
    "GOOD_PERFORMER": "#2563EB",  # Strong blue
    "AVERAGE_PERFORMER": "#0EA5E9",  # Sky / cyan (blue‑leaning)
    "NEEDS_IMPROVEMENT": "#93C5FD",  # Light blue
}


def tier_color_map():
    return dict(TIER_COLOR_MAP)
