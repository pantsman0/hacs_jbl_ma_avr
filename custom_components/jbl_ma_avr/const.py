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
