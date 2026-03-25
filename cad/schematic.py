"""CM4 carrier board schematic generation via kicad-sch-api.

Places components in functional groups and wires them using
connect_pins_with_wire for auto-routing between pins.
"""

import kicad_sch_api as ksa

SCHEMATIC_PATH = "cad/cm4_carrier.kicad_sch"


def build_schematic() -> None:
    """Generate visual schematic (.kicad_sch)."""
    ksa.use_grid_units(True)
    sch = ksa.create_schematic("CM4_Carrier")
    sch.set_title_block(
        title="CM4 Carrier Board",
        company="Engineering With AI",
    )

    def p(dx: int, dy: int) -> tuple[int, int]:
        """Grid position relative to drawing origin."""
        return (25 + dx, 20 + dy)

    # --- Power section (left side) ---
    _place_power(sch, p)

    # --- CM4 connector (center) ---
    _place_cm4(sch, p)

    # --- RS-485 (upper right) ---
    _place_rs485(sch, p)

    # --- USB-UART (lower right) ---
    _place_usb_uart(sch, p)

    # --- I/O headers (far right) ---
    _place_io_headers(sch, p)

    sch.save(SCHEMATIC_PATH)


def _place_power(sch: ksa.core.schematic.Schematic, p) -> None:
    """Place power input components: connector, polyfuse, MOSFET, caps."""
    # +5V power symbol
    sch.components.add("power:+5V", "#PWR01", "+5V", position=p(0, 0))
    sch.components.add("power:GND", "#PWR02", "GND", position=p(0, 20))

    # Screw terminal
    j = sch.components.add(
        "Connector_Generic:Conn_01x02", "J1", "5V_IN", position=p(0, 10)
    )
    j.footprint = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"

    # Polyfuse
    f = sch.components.add("Device:Polyfuse", "F1", "2A", position=p(8, 5))
    f.footprint = "Fuse:Fuse_1812_4532Metric"

    # P-MOSFET reverse polarity
    q = sch.components.add(
        "Device:Q_PMOS", "Q1", "SI2301", position=p(16, 5)
    )
    q.footprint = "Package_TO_SOT_SMD:SOT-23"

    # Bulk caps
    c1 = sch.components.add("Device:C", "C1", "100uF", position=p(22, 10))
    c1.footprint = "Capacitor_SMD:C_1210_3225Metric"
    c2 = sch.components.add("Device:C", "C2", "10uF", position=p(26, 10))
    c2.footprint = "Capacitor_SMD:C_0805_2012Metric"

    # PWR_FLAG for ERC
    sch.components.add("power:PWR_FLAG", "#FLG01", "PWR_FLAG", position=p(-2, 2))
    sch.components.add(
        "power:PWR_FLAG", "#FLG02", "PWR_FLAG", position=p(-2, 20), rotation=180
    )

    # Labels
    sch.add_label("5V_RAIL", position=p(22, 5))


def _place_cm4(sch: ksa.core.schematic.Schematic, p) -> None:
    """Place CM4 connector in center of schematic."""
    j = sch.components.add(
        "Connector_Generic:Conn_02x20_Odd_Even", "J2", "CM4", position=p(35, 10)
    )
    j.footprint = (
        "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical"
    )

    # Net labels on CM4 pins
    sch.add_label("5V_RAIL", position=p(33, 6))
    sch.add_label("3V3", position=p(33, 8))
    sch.add_label("SDA", position=p(33, 10))
    sch.add_label("SCL", position=p(33, 12))
    sch.add_label("UART_TX", position=p(33, 14))
    sch.add_label("UART_RX", position=p(33, 16))
    sch.add_label("RS485_TX", position=p(33, 22))
    sch.add_label("RS485_RX", position=p(33, 24))


def _place_rs485(sch: ksa.core.schematic.Schematic, p) -> None:
    """Place MAX3485 transceiver with termination and bias."""
    u = sch.components.add(
        "Interface_UART:MAX3485", "U1", "MAX3485", position=p(55, 5)
    )
    u.footprint = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"

    # Termination
    r_t = sch.components.add(
        "Device:R", "R1", "120", position=p(65, 5), rotation=90
    )
    r_t.footprint = "Resistor_SMD:R_0805_2012Metric"

    # Bias resistors
    r_a = sch.components.add("Device:R", "R2", "560", position=p(68, 2))
    r_a.footprint = "Resistor_SMD:R_0603_1608Metric"
    r_b = sch.components.add("Device:R", "R3", "560", position=p(68, 8))
    r_b.footprint = "Resistor_SMD:R_0603_1608Metric"

    # Header
    j = sch.components.add(
        "Connector_Generic:Conn_01x04", "J3", "RS485", position=p(75, 5)
    )
    j.footprint = (
        "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )

    # Decoupling
    c = sch.components.add("Device:C", "C3", "100nF", position=p(55, 15))
    c.footprint = "Capacitor_SMD:C_0402_1005Metric"

    # Labels
    sch.add_label("RS485_TX", position=p(50, 7))
    sch.add_label("RS485_RX", position=p(50, 3))
    sch.add_label("3V3", position=p(55, 0))


def _place_usb_uart(sch: ksa.core.schematic.Schematic, p) -> None:
    """Place CP2102N USB-UART bridge."""
    u = sch.components.add(
        "Interface_USB:CP2102N-Axx-xQFN20", "U2", "CP2102N",
        position=p(55, 25),
    )
    u.footprint = (
        "Package_DFN_QFN:QFN-20-1EP_4x4mm_P0.5mm_EP2.5x2.5mm"
    )

    # USB connector
    j = sch.components.add(
        "Connector:USB_B_Micro", "J4", "USB_DEBUG", position=p(45, 30)
    )
    j.footprint = "Connector_USB:USB_Micro-B_Molex_47346-0001"

    # Decoupling
    c = sch.components.add("Device:C", "C4", "100nF", position=p(55, 35))
    c.footprint = "Capacitor_SMD:C_0402_1005Metric"

    # Labels
    sch.add_label("UART_TX", position=p(50, 27))
    sch.add_label("UART_RX", position=p(50, 23))
    sch.add_label("3V3", position=p(55, 20))


def _place_io_headers(sch: ksa.core.schematic.Schematic, p) -> None:
    """Place I2C, SPI, GPIO headers with pull-ups."""
    # I2C pull-ups
    r_sda = sch.components.add("Device:R", "R4", "2.2k", position=p(80, 2))
    r_sda.footprint = "Resistor_SMD:R_0603_1608Metric"
    r_scl = sch.components.add("Device:R", "R5", "2.2k", position=p(84, 2))
    r_scl.footprint = "Resistor_SMD:R_0603_1608Metric"

    # I2C header
    j_i2c = sch.components.add(
        "Connector_Generic:Conn_01x04", "J5", "I2C", position=p(88, 5)
    )
    j_i2c.footprint = (
        "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )

    # SPI header
    j_spi = sch.components.add(
        "Connector_Generic:Conn_01x06", "J6", "SPI", position=p(88, 15)
    )
    j_spi.footprint = (
        "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
    )

    # GPIO header
    j_gpio = sch.components.add(
        "Connector_Generic:Conn_01x08", "J7", "GPIO", position=p(88, 28)
    )
    j_gpio.footprint = (
        "Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical"
    )

    # Labels
    sch.add_label("SDA", position=p(80, 5))
    sch.add_label("SCL", position=p(84, 5))
    sch.add_label("3V3", position=p(80, 0))
    sch.add_label("MOSI", position=p(85, 16))
    sch.add_label("MISO", position=p(85, 18))
    sch.add_label("SCK", position=p(85, 20))
    sch.add_label("SPI_CS0", position=p(85, 22))

    # CM4 decoupling caps
    for i in range(4):
        c = sch.components.add(
            "Device:C", f"C{5 + i}", "100nF", position=p(30 + i * 4, 40)
        )
        c.footprint = "Capacitor_SMD:C_0402_1005Metric"


if __name__ == "__main__":
    build_schematic()
    print(f"Schematic: {SCHEMATIC_PATH}")
