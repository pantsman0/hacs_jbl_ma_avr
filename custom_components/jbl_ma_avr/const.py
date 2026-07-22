DOMAIN = "jbl_ma_avr"

DEFAULT_PORT = 50000

MODEL_NAMES = {
    0x01: "MA510",
    0x02: "MA710",
    0x03: "MA7100HP",
    0x04: "MA9100HP",
}

MODEL_NAMES_INV = {v:k for k,v in MODEL_NAMES.items()}

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

IR_COMMANDS = {
    "POWER": bytearray.fromhex("010E03"),
    "UP": bytearray.fromhex("010E99"),
    "DOWN": bytearray.fromhex("010E59"),
    "LEFT": bytearray.fromhex("010E83"),
    "RIGHT": bytearray.fromhex("010E43"),
    "OK": bytearray.fromhex("010E21"),
    "MENU": bytearray.fromhex("010ECA"),
    "BACK": bytearray.fromhex("010EA1"),
    "DIM": bytearray.fromhex("010EC9"),
    "VOL_PLUS": bytearray.fromhex("010EE3"),
    "VOL_MINUS": bytearray.fromhex("010E13"),
    "SOURCE_PLUS": bytearray.fromhex("010E8C"),
    "SOURCE_MINUS": bytearray.fromhex("010E0C"),
    "SURROUND_PLUS": bytearray.fromhex("010EF4"),
    "SURROUND_MINUS": bytearray.fromhex("010E74"),
    "MUTE": bytearray.fromhex("010EC3"),
    "MAIN_ZONE_POWER_ON": bytearray.fromhex("010ED9"),
    "MAIN_ZONE_POWER_OFF": bytearray.fromhex("010EF9"),
    "ZONE2_PARTY_MODE_ON": bytearray.fromhex("010E73"),
    "ZONE2_PARTY_MODE_OFF": bytearray.fromhex("010E8B"),
    "ZONE2_PARTY_MODE_VOL_UP": bytearray.fromhex("010E39"),
    "ZONE2_PARTY_MODE_VOL_DOWN": bytearray.fromhex("010EB9"),
    "MAIN_ZONE_TV_INPUT": bytearray.fromhex("010E71"),
    "MAIN_ZONE_HDMI1_INPUT": bytearray.fromhex("010E11"),
    "MAIN_ZONE_HDMI2_INPUT": bytearray.fromhex("010E91"),
    "MAIN_ZONE_HDMI3_INPUT": bytearray.fromhex("010E51"),
    "MAIN_ZONE_HDMI4_INPUT": bytearray.fromhex("010ED1"),
    "MAIN_ZONE_HDMI5_INPUT": bytearray.fromhex("010E31"),
    "MAIN_ZONE_HDMI6_INPUT": bytearray.fromhex("010EB1"),
    "MAIN_ZONE_COAX_INPUT": bytearray.fromhex("010E81"),
    "MAIN_ZONE_OPTICAL_INPUT": bytearray.fromhex("010EDB"),
    "MAIN_ZONE_ANALOG1_INPUT": bytearray.fromhex("010E23"),
    "MAIN_ZONE_ANALOG2_INPUT": bytearray.fromhex("010E33"),
    "MAIN_ZONE_PHONO_INPUT": bytearray.fromhex("010E0B"),
    "MAIN_ZONE_BLUETOOTH_INPUT": bytearray.fromhex("010E53"),
    "MAIN_ZONE_NETWORK_INPUT": bytearray.fromhex("010ED3")
}