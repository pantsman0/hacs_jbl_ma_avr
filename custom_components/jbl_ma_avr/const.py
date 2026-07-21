DOMAIN = "jbl_ma_avr"

DEFAULT_PORT = 50000

SOURCES = {
    0x01: "TV(ARC)",
    0x02: "HDMI 1",
    0x03: "HDMI 2",
    0x04: "HDMI 3",
    0x05: "HDMI 4",
    0x06: "HDMI 5",
    0x07: "HDMI 6",
    0x08: "Coax",
    0x09: "Optical",
    0x0A: "Analog1",
    0x0B: "Analog2",
    0x0C: "Phono",
    0x0D: "Bluetooth",
    0x0E: "Network"
}

SOURCES_INV = {v: k for k, v in SOURCES.items()}

# Surround modes (0x08)
SURROUND_MODES = {
    0x01: "Dolby Surround",
    0x02: "DTS Neural:X",
    0x03: "Stereo 2.0",
    0x04: "Stereo 2.1",
    0x05: "All Stereo",
    0x06: "Native",
    0x07: "Dolby ProLogic II",
}
SURROUND_MODES_INV = {v: k for k, v in SURROUND_MODES.items()}

# Display dim levels (0x01)
DISPLAY_DIM_MODES = {
    0x00: "Full",
    0x01: "50%",
    0x02: "25%",
    0x03: "Off",
}
DISPLAY_DIM_MODES_INV = {v: k for k, v in DISPLAY_DIM_MODES.items()}

# Room EQ modes (0x0D)
ROOM_EQ_MODES = {
    0x00: "Disabled",
    0x01: "EZ Set EQ",
    0x02: "Dirac Live",
}
ROOM_EQ_MODES_INV = {v: k for k, v in ROOM_EQ_MODES.items()}

# Dolby audio modes (0x0F)
DOLBY_MODES = {
    0x00: "Off",
    0x01: "Music",
    0x02: "Movie",
    0x03: "Night",
}
DOLBY_MODES_INV = {v: k for k, v in DOLBY_MODES.items()}

# Streaming server names (0x11 Data1)
STREAMING_SERVERS = {
    0: "Unknown",
    1: "Airable",
    4: "USB Storage",
    6: "VTuner",
    9: "TuneIn",
    10: "UPnP",
    11: "QPlay",
    12: "Bluetooth",
    13: "AirPlay",
    15: "Spotify",
    16: "Google Cast",
    17: "Airable Radios",
    18: "Airable Podcasts",
    19: "Napster",
    20: "Qobuz",
    21: "Deezer",
    22: "Tidal",
    23: "Roon",
    26: "Amazon Music",
    33: "Pandora",
}

STREAMING_PLAY_STATES = {
    0x00: "Stopped",
    0x01: "Playing",
    0x02: "Paused",
}
