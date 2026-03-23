"""UI constants for Phase 05 Board Rendering."""

# Colors (from D-01, D-04, D-14, D-15)
BOARD_BG = "#7BA05B"           # green felt background
GRID_COLOR = "#2D5A1B"          # dark green grid lines
RED_FILL = "#CC2200"            # red piece fill
BLACK_FILL = "#1A1A1A"          # black piece fill
PIECE_TEXT_COLOR = "#FFFFFF"    # white text on pieces
PIECE_STROKE_COLOR = "#FFFFFF"  # white border around all pieces
RIVER_TEXT_COLOR = "#2D5A1B"   # "楚河"/"漢界" fill (same as grid)
COORD_TEXT_COLOR = "#2D5A1B"    # row/col labels

# Derived size ratios (D-12, font size ratios from UI-SPEC)
CELL_RATIO = 0.80           # piece diameter / cell
PIECE_FONT_RATIO = 0.56     # piece char font size / cell
RIVER_FONT_RATIO = 0.28     # river text font / cell (with floor)
COORD_FONT_RATIO = 0.22     # coordinate label font / cell

# Window sizes (D-08, D-09, D-10, D-11)
DEFAULT_SIZE = (480, 600)
MIN_SIZE = (360, 450)
MAX_SIZE = (720, 900)
