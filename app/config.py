"""
Centralized configuration for the YT Mixtape application.

All paths, audio settings, video settings, and defaults live here
so nothing is hard-coded elsewhere.
"""

import os

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIXTAPE_DIR = os.path.join(BASE_DIR, "mixtape")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ── Audio Settings ───────────────────────────────────────────────────
TRANSITION_MS = 6000          # cross-fade overlap in milliseconds
CHANNELS = 2                  # stereo
FRAME_RATE = 44100            # 44.1 kHz
AUDIO_FORMATS = (".mp3", ".wav")
LOW_PASS_FREQ = 4000          # Hz – smooths the cross-fade zone

# ── Video Settings ───────────────────────────────────────────────────
VIDEO_RESOLUTION = (1280, 720)  # 720p
FPS = 1                         # low fps = smaller file for static image
PRESET = "ultrafast"            # ffmpeg encoding preset
AUDIO_BITRATE = "192k"         # AAC output bitrate
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

# ── Description Defaults ────────────────────────────────────────────
DEFAULT_HASHTAGS = [
    "#AfroHouse", "#HouseMusic", "#EDM", "#DanceMusic", "#Mixtape",
    "#ElectronicMusic", "#DJMix", "#PartyMusic", "#DeepHouse",
    "#AfroHouseVibes",
]
