# See MODULES.md for the repository module map before editing.
from __future__ import annotations

# Shared semantic colors for workstation chat surfaces.
# This module intentionally contains palette tokens only.

ACTIVE_AREA_FRAME = "#46515d" # dark grey
INACTIVE_AREA_FRAME = "#2b333d" # near black

PAGE_BACKGROUND = "#10151b" # black
ACTIVE_AREA_BACKGROUND = "#171e26" # slightly lighter black
INACTIVE_AREA_BACKGROUND = "#121920" # slightly lighter black

ACTIVE_TEXT_A_COLOR = "#eef3f7" # light beige
INACTIVE_TEXT_A_COLOR = "#7d8894" # dull gold

ACTIVE_TEXT_B_COLOR = "#e7c86b"
# e.g. Chat Prompt Placeholder, Activity
ACTIVE_TEXT_C_COLOR = "#5da8ff"  # light blue
# e.g. Status
ACTIVE_TEXT_D_COLOR = "#d8e1ea"  # yellow
ACTIVE_TEXT_F_COLOR = "#a7b3bf"  # light grey
ACTIVE_TEXT_G_COLOR = "#7d8894"  # dull gold

SUBJECT_CONTROL_TEXT_COLOR = "#171c22" # slightly lighter black
SUBJECT_CONTROL_BACKGROUND = "#1c6b46" # mid green
SUBJECT_CONTROL_ACTIVE_BACKGROUND = "#a8efc2" # light cyan green
SUBJECT_CONTROL_DISABLED_BACKGROUND = "#4f5964" # dull gold

__all__ = [
    "ACTIVE_AREA_BACKGROUND",
    "ACTIVE_AREA_FRAME",
    "ACTIVE_TEXT_A_COLOR",
    "ACTIVE_TEXT_B_COLOR",
    "ACTIVE_TEXT_C_COLOR",
    "ACTIVE_TEXT_D_COLOR",
    "ACTIVE_TEXT_F_COLOR",
    "ACTIVE_TEXT_G_COLOR",
    "INACTIVE_AREA_BACKGROUND",
    "INACTIVE_AREA_FRAME",
    "INACTIVE_TEXT_A_COLOR",
    "PAGE_BACKGROUND",
    "SUBJECT_CONTROL_ACTIVE_BACKGROUND",
    "SUBJECT_CONTROL_BACKGROUND",
    "SUBJECT_CONTROL_DISABLED_BACKGROUND",
    "SUBJECT_CONTROL_TEXT_COLOR",
]
