"""CM4 carrier board schematic generation via kicad-sch-api.

Layout driven by cad/layout_spec.yaml. Six functional blocks placed
on A4 sheet with power at top, GND at bottom, signal flow L->R.
"""

import kicad_sch_api as ksa
import yaml

SCHEMATIC_PATH = "cad/cm4_carrier.kicad_sch"
SPEC_PATH = "cad/layout_spec.yaml"

# Reason: unique power symbol counter avoids ref collisions
_pwr_idx = 0


def _pwr_ref() -> str:
    global _pwr_idx
    _pwr_idx += 1
    return f"#PWR{_pwr_idx:02d}"


def build_schematic() -> None:
    """Generate schematic from layout_spec.yaml."""
    global _pwr_idx
    _pwr_idx = 0

    with open(SPEC_PATH) as f:
        spec = yaml.safe_load(f)

    ksa.use_grid_units(True)
    sch = ksa.create_schematic("CM4_Carrier")
    sch.set_title_block(title=spec["title"], company="Engineering With AI")

    blocks = spec["blocks"]
    _place_power(sch, blocks["power"])
    _place_cm4(sch, blocks["cm4"])
    _place_rs485(sch, blocks["rs485"])
    _place_usb_uart(sch, blocks["usb_uart"])
    _place_decoupling(sch, blocks["decoupling"])
    _place_io_headers(sch, blocks["io_headers"])

    sch.save(SCHEMATIC_PATH)


def _bp(block: dict, dx: int, dy: int) -> tuple[int, int]:
    """Block-relative position from layout_spec origin."""
    bx, by = block["position"]
    return (bx + dx, by + dy)


def _add_rail(sch, block: dict, dx: int = 0) -> None:
    """Add power rail symbol at top of block."""
    rail = block.get("power_rail")
    if rail:
        lib = f"power:{rail}"
        sch.components.add(lib, _pwr_ref(), rail, position=_bp(block, dx, -5))


def _add_gnd(sch, block: dict, dy_offset: int = 35, dx: int = 0) -> None:
    """Add GND symbol at bottom of block."""
    if block.get("ground"):
        sch.components.add(
            "power:GND", _pwr_ref(), "GND", position=_bp(block, dx, dy_offset)
        )


def _add_labels(sch, block: dict, side: str, spacing: int = 4) -> None:
    """Add net labels on block boundary."""
    labels = block.get("labels", {}).get(side, [])
    dx = -8 if side == "left" else 30
    for i, name in enumerate(labels):
        sch.add_label(name, position=_bp(block, dx, i * spacing))


def _place_power(sch, block: dict) -> None:
    """Power: connector -> polyfuse -> MOSFET -> bulk caps."""
    p = lambda dx, dy: _bp(block, dx, dy)

    sch.components.add("power:+5V", _pwr_ref(), "+5V", position=p(0, -5))
    sch.components.add("power:PWR_FLAG", "#FLG01", "PWR_FLAG", position=p(-4, 0))
    sch.components.add(
        "power:PWR_FLAG", "#FLG02", "PWR_FLAG", position=p(-4, 35), rotation=180
    )
    _add_gnd(sch, block, dy_offset=40)

    j = sch.components.add(
        "Connector_Generic:Conn_01x02", "J1", "5V_IN", position=p(0, 16)
    )
    j.footprint = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"

    f = sch.components.add("Device:Polyfuse", "F1", "2A", position=p(14, 8))
    f.footprint = "Fuse:Fuse_1812_4532Metric"

    q = sch.components.add("Device:Q_PMOS", "Q1", "SI2301", position=p(28, 8))
    q.footprint = "Package_TO_SOT_SMD:SOT-23"

    c1 = sch.components.add("Device:C", "C1", "100uF", position=p(38, 16))
    c1.footprint = "Capacitor_SMD:C_1210_3225Metric"
    c2 = sch.components.add("Device:C", "C2", "10uF", position=p(46, 16))
    c2.footprint = "Capacitor_SMD:C_0805_2012Metric"

    sch.add_label("5V_RAIL", position=p(38, 4))


def _place_cm4(sch, block: dict) -> None:
    """CM4 connector with net labels."""
    p = lambda dx, dy: _bp(block, dx, dy)

    j = sch.components.add(
        "Connector_Generic:Conn_02x20_Odd_Even", "J2", "CM4", position=p(12, 5)
    )
    j.footprint = "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical"

    # Reason: labels every 4 grid units to avoid overlap with pin numbers
    _add_labels(sch, block, "left", spacing=4)
    _add_gnd(sch, block, dy_offset=55)


def _place_rs485(sch, block: dict) -> None:
    """MAX3485 with termination and bias."""
    p = lambda dx, dy: _bp(block, dx, dy)

    _add_rail(sch, block, dx=12)
    _add_gnd(sch, block, dy_offset=42, dx=12)

    u = sch.components.add(
        "Interface_UART:MAX3485", "U1", "MAX3485", position=p(12, 10)
    )
    u.footprint = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"

    r_t = sch.components.add(
        "Device:R", "R1", "120", position=p(30, 10), rotation=90
    )
    r_t.footprint = "Resistor_SMD:R_0805_2012Metric"

    r_a = sch.components.add("Device:R", "R2", "560", position=p(36, 3))
    r_a.footprint = "Resistor_SMD:R_0603_1608Metric"
    r_b = sch.components.add("Device:R", "R3", "560", position=p(36, 17))
    r_b.footprint = "Resistor_SMD:R_0603_1608Metric"

    j = sch.components.add(
        "Connector_Generic:Conn_01x04", "J3", "RS485", position=p(48, 10)
    )
    j.footprint = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"

    c = sch.components.add("Device:C", "C3", "100nF", position=p(12, 28))
    c.footprint = "Capacitor_SMD:C_0402_1005Metric"

    _add_labels(sch, block, "left", spacing=8)


def _place_usb_uart(sch, block: dict) -> None:
    """CP2102N USB-UART bridge."""
    p = lambda dx, dy: _bp(block, dx, dy)

    _add_rail(sch, block, dx=22)
    _add_gnd(sch, block, dy_offset=42, dx=22)

    u = sch.components.add(
        "Interface_USB:CP2102N-Axx-xQFN20", "U2", "CP2102N", position=p(22, 10)
    )
    u.footprint = "Package_DFN_QFN:QFN-20-1EP_4x4mm_P0.5mm_EP2.5x2.5mm"

    j = sch.components.add(
        "Connector:USB_B_Micro", "J4", "USB_DEBUG", position=p(0, 16)
    )
    j.footprint = "Connector_USB:USB_Micro-B_Molex_47346-0001"

    c = sch.components.add("Device:C", "C4", "100nF", position=p(22, 30))
    c.footprint = "Capacitor_SMD:C_0402_1005Metric"

    _add_labels(sch, block, "left", spacing=8)


def _place_decoupling(sch, block: dict) -> None:
    """CM4 decoupling caps."""
    p = lambda dx, dy: _bp(block, dx, dy)

    _add_rail(sch, block)
    _add_gnd(sch, block, dy_offset=16)

    for i in range(4):
        c = sch.components.add(
            "Device:C", f"C{5 + i}", "100nF", position=p(i * 10, 5)
        )
        c.footprint = "Capacitor_SMD:C_0402_1005Metric"


def _place_io_headers(sch, block: dict) -> None:
    """I2C (with pull-ups), SPI, GPIO headers."""
    p = lambda dx, dy: _bp(block, dx, dy)

    _add_rail(sch, block, dx=5)

    # I2C pull-ups
    r_sda = sch.components.add("Device:R", "R4", "2.2k", position=p(5, 4))
    r_sda.footprint = "Resistor_SMD:R_0603_1608Metric"
    r_scl = sch.components.add("Device:R", "R5", "2.2k", position=p(14, 4))
    r_scl.footprint = "Resistor_SMD:R_0603_1608Metric"

    j_i2c = sch.components.add(
        "Connector_Generic:Conn_01x04", "J5", "I2C", position=p(26, 8)
    )
    j_i2c.footprint = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"

    sch.add_label("SDA", position=p(5, 10))
    sch.add_label("SCL", position=p(14, 10))
    _add_gnd(sch, block, dy_offset=22, dx=26)

    # SPI header
    j_spi = sch.components.add(
        "Connector_Generic:Conn_01x06", "J6", "SPI", position=p(26, 30)
    )
    j_spi.footprint = "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"

    sch.add_label("3V3", position=p(16, 28))
    sch.add_label("MOSI", position=p(16, 32))
    sch.add_label("MISO", position=p(16, 36))
    sch.add_label("SCK", position=p(16, 40))
    sch.add_label("SPI_CS0", position=p(16, 44))
    _add_gnd(sch, block, dy_offset=48, dx=26)

    # GPIO header
    j_gpio = sch.components.add(
        "Connector_Generic:Conn_01x08", "J7", "GPIO", position=p(26, 56)
    )
    j_gpio.footprint = "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"

    sch.add_label("3V3", position=p(16, 54))
    _add_gnd(sch, block, dy_offset=74, dx=26)


if __name__ == "__main__":
    build_schematic()
    print(f"Schematic: {SCHEMATIC_PATH}")
