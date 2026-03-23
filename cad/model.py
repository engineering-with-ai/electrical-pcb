"""Buck converter schematic and netlist generation.

SKiDL defines the circuit topology → KiCad netlist (for PySpice + PCB).
kicad-sch-api generates the visual schematic (.kicad_sch) for drawings.
Components are parameterized from sim/constants.py.
"""

import os

_SYM_DIR = "/usr/share/kicad/symbols"
for v in (
    "KICAD_SYMBOL_DIR",
    "KICAD6_SYMBOL_DIR",
    "KICAD7_SYMBOL_DIR",
    "KICAD8_SYMBOL_DIR",
    "KICAD9_SYMBOL_DIR",
):
    os.environ[v] = _SYM_DIR

import skidl  # noqa: E402
import kicad_sch_api as ksa  # noqa: E402

from sim.constants import INDUCTANCE, INPUT_CAP, OUTPUT_CAP  # noqa: E402

NETLIST_PATH = "cad/buck_converter.net"
SCHEMATIC_PATH = "cad/buck_converter.kicad_sch"


def _vals() -> dict[str, str]:
    return {
        "c_in": f"{INPUT_CAP.magnitude.nominal_value:.0f}uF",
        "c_out": f"{OUTPUT_CAP.magnitude.nominal_value:.0f}uF",
        "l": f"{INDUCTANCE.magnitude.nominal_value:.0f}uH",
    }


def build_netlist() -> None:
    """Define buck converter in SKiDL and generate KiCad netlist."""
    vals = _vals()

    vin = skidl.Net("VIN")
    sw = skidl.Net("SW")
    vout = skidl.Net("VOUT")
    gnd = skidl.Net("GND")
    gate = skidl.Net("GATE")

    j_in = skidl.Part(
        "Connector_Generic",
        "Conn_01x02",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    )
    j_in.value = "VIN"
    vin += j_in[1]
    gnd += j_in[2]

    c_in = skidl.Part(
        "Device", "C", value=vals["c_in"], footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    vin += c_in[1]
    gnd += c_in[2]

    q_sw = skidl.Part("Transistor_FET", "2N7002", footprint="Package_TO_SOT_SMD:SOT-23")
    q_sw.value = "2N7002"
    vin += q_sw["D"]
    sw += q_sw["S"]
    gate += q_sw["G"]

    d1 = skidl.Part("Device", "D_Schottky", footprint="Diode_SMD:D_SOD-123")
    d1.value = "SS14"
    gnd += d1["A"]
    sw += d1["K"]

    l1 = skidl.Part(
        "Device", "L", value=vals["l"], footprint="Inductor_SMD:L_1210_3225Metric"
    )
    sw += l1[1]
    vout += l1[2]

    c_out = skidl.Part(
        "Device", "C", value=vals["c_out"], footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    vout += c_out[1]
    gnd += c_out[2]

    j_out = skidl.Part(
        "Connector_Generic",
        "Conn_01x02",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    )
    j_out.value = "VOUT"
    vout += j_out[1]
    gnd += j_out[2]

    skidl.generate_netlist(file_=NETLIST_PATH, tool=skidl.KICAD8)


def build_schematic() -> None:
    """Generate visual schematic (.kicad_sch) via kicad-sch-api."""
    vals = _vals()
    ksa.use_grid_units(True)

    sch = ksa.create_schematic("Buck_Converter")
    sch.set_title_block(
        title="Buck Converter 12V to 3.3V",
        company="Engineering With AI",
    )

    # Reason: origin offset from top-left of drawing area, with margin for border + grid markers
    def p(dx, dy):
        return (30 + dx, 25 + dy)

    # Reason: pin offsets (grid units) from component position:
    #   Q_NMOS:     Gate(-4,0)  Drain(+2,-4)  Source(+2,+4)
    #   D_Schottky: K(-3,0)     A(+3,0)
    #   C:          Pin1(0,-3)  Pin2(0,+3)
    #   L (rot 90): Pin1(-3,0)  Pin2(+3,0)
    #   +12V/GND:   pin at component position

    # Power symbols
    sch.components.add("power:+12V", "#PWR01", "+12V", position=p(0, 0))
    sch.components.add("power:GND", "#PWR02", "GND", position=p(0, 16))
    sch.components.add("power:GND", "#PWR03", "GND", position=p(18, 16))
    sch.components.add("power:GND", "#PWR04", "GND", position=p(35, 16))
    # Reason: PWR_FLAG satisfies ERC "power pin not driven" for connector-fed designs
    sch.components.add("power:PWR_FLAG", "#FLG01", "PWR_FLAG", position=p(-2, 2))
    sch.components.add(
        "power:PWR_FLAG", "#FLG02", "PWR_FLAG", position=p(-2, 16), rotation=180
    )

    # Components — pin positions noted for wiring
    # Footprints must match build_netlist() for PCB import
    # C1 at p(0,10):   Pin1=p(0,7)   Pin2=p(0,13)
    c1 = sch.components.add("Device:C", "C1", vals["c_in"], position=p(0, 10))
    c1.footprint = "Capacitor_SMD:C_0805_2012Metric"
    # Q1 at p(10,6):   Gate=p(6,6)   Drain=p(12,2)  Source=p(12,10)
    q1 = sch.components.add("Transistor_FET:2N7002", "Q1", "2N7002", position=p(10, 6))
    q1.footprint = "Package_TO_SOT_SMD:SOT-23"
    # D1 at p(15,14):  K=p(12,14)    A=p(18,14)
    d1 = sch.components.add("Device:D_Schottky", "D1", "SS14", position=p(15, 14))
    d1.footprint = "Diode_SMD:D_SOD-123"
    # L1 at p(25,4):   Pin1=p(22,4)  Pin2=p(28,4)
    l1 = sch.components.add("Device:L", "L1", vals["l"], position=p(25, 4), rotation=90)
    l1.footprint = "Inductor_SMD:L_1210_3225Metric"
    # C2 at p(35,10):  Pin1=p(35,7)  Pin2=p(35,13)
    c2 = sch.components.add("Device:C", "C2", vals["c_out"], position=p(35, 10))
    c2.footprint = "Capacitor_SMD:C_0805_2012Metric"

    # Junctions
    sch.junctions.add(position=p(0, 2))
    sch.junctions.add(position=p(12, 10))
    sch.junctions.add(position=p(35, 4))

    # VIN rail: +12V -> C1.Pin1 and -> Q1.Drain
    sch.add_wire(start=p(0, 0), end=p(0, 2))
    sch.add_wire(start=p(0, 2), end=p(0, 7))
    sch.add_wire(start=p(0, 2), end=p(12, 2))
    # PWR_FLAG connections
    sch.add_wire(start=p(-2, 2), end=p(0, 2))
    sch.add_wire(start=p(-2, 16), end=p(0, 16))

    # Reason: gate is driven by external PWM controller (not modeled)
    # no_connects.add doesn't respect use_grid_units — pass mm directly
    gate_pos = p(6, 6)
    sch.no_connects.add(position=(gate_pos[0] * 1.27, gate_pos[1] * 1.27))

    # SW node: Q1.Source -> D1.K and -> L1.Pin1
    sch.add_wire(start=p(12, 10), end=p(12, 14))
    sch.add_wire(start=p(12, 10), end=p(12, 4))
    sch.add_wire(start=p(12, 4), end=p(22, 4))

    # VOUT rail: L1.Pin2 -> C2.Pin1
    sch.add_wire(start=p(28, 4), end=p(35, 4))
    sch.add_wire(start=p(35, 4), end=p(35, 7))

    # GND: C1.Pin2, D1.A, C2.Pin2 -> GND symbols
    sch.add_wire(start=p(0, 13), end=p(0, 16))
    sch.add_wire(start=p(18, 14), end=p(18, 16))
    sch.add_wire(start=p(35, 13), end=p(35, 16))

    # Labels — must land exactly on wire endpoints or mid-wire
    sch.add_label("SW", position=p(14, 4))
    sch.add_label("VOUT", position=p(30, 4))

    sch.save(SCHEMATIC_PATH)


if __name__ == "__main__":
    build_netlist()
    print(f"Netlist: {NETLIST_PATH}")
    build_schematic()
    print(f"Schematic: {SCHEMATIC_PATH}")
