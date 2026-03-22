"""Buck converter schematic and netlist generation.

SKiDL defines the circuit topology → KiCad netlist (for PySpice + PCB).
kicad-sch-api generates the visual schematic (.kicad_sch) for drawings.
Components are parameterized from sim/constants.py.
"""

import os

_SYM_DIR = "/usr/share/kicad/symbols"
for v in ("KICAD_SYMBOL_DIR", "KICAD6_SYMBOL_DIR", "KICAD7_SYMBOL_DIR", "KICAD8_SYMBOL_DIR", "KICAD9_SYMBOL_DIR"):
    os.environ[v] = _SYM_DIR

import skidl  # noqa: E402
import kicad_sch_api as ksa  # noqa: E402

from sim.constants import INDUCTANCE, INPUT_CAP, OUTPUT_CAP, ureg  # noqa: E402

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

    j_in = skidl.Part("Connector_Generic", "Conn_01x02", footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    j_in.value = "VIN"
    vin += j_in[1]
    gnd += j_in[2]

    c_in = skidl.Part("Device", "C", value=vals["c_in"], footprint="Capacitor_SMD:C_0805_2012Metric")
    vin += c_in[1]
    gnd += c_in[2]

    q_sw = skidl.Part("Device", "Q_NMOS", footprint="Package_TO_SOT_SMD:SOT-23")
    q_sw.value = "SW"
    vin += q_sw["D"]
    sw += q_sw["S"]
    gate += q_sw["G"]

    d1 = skidl.Part("Device", "D_Schottky", footprint="Diode_SMD:D_SOD-123")
    d1.value = "SS14"
    gnd += d1["A"]
    sw += d1["K"]

    l1 = skidl.Part("Device", "L", value=vals["l"], footprint="Inductor_SMD:L_1210_3225Metric")
    sw += l1[1]
    vout += l1[2]

    c_out = skidl.Part("Device", "C", value=vals["c_out"], footprint="Capacitor_SMD:C_0805_2012Metric")
    vout += c_out[1]
    gnd += c_out[2]

    j_out = skidl.Part("Connector_Generic", "Conn_01x02", footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    j_out.value = "VOUT"
    vout += j_out[1]
    gnd += j_out[2]

    skidl.generate_netlist(file_=NETLIST_PATH, tool=skidl.KICAD8)


def build_schematic() -> None:
    """Generate visual schematic (.kicad_sch) via kicad-sch-api."""
    vals = _vals()
    ksa.use_grid_units(True)

    sch = ksa.create_schematic("Buck_Converter")

    def p(dx, dy):
        return (20 + dx, 20 + dy)

    # Power symbols
    sch.components.add("power:+12V", "#PWR01", "+12V", position=p(0, 0))
    sch.components.add("power:GND", "#PWR02", "GND", position=p(0, 20))
    sch.components.add("power:GND", "#PWR03", "GND", position=p(15, 20))
    sch.components.add("power:GND", "#PWR04", "GND", position=p(35, 20))

    # Components
    sch.components.add("Device:C", "C1", vals["c_in"], position=p(0, 10))
    sch.components.add("Device:Q_NMOS", "Q1", "SW", position=p(10, 6))
    sch.components.add("Device:D_Schottky", "D1", "SS14", position=p(15, 12))
    sch.components.add("Device:L", "L1", vals["l"], position=p(25, 4), rotation=90)
    sch.components.add("Device:C", "C2", vals["c_out"], position=p(35, 10))

    # Junctions
    sch.junctions.add(position=p(0, 4))
    sch.junctions.add(position=p(15, 4))
    sch.junctions.add(position=p(35, 4))

    # VIN rail
    sch.add_wire(start=p(0, 0), end=p(0, 4))
    sch.add_wire(start=p(0, 4), end=p(0, 7))
    sch.add_wire(start=p(0, 4), end=p(8, 4))

    # SW node
    sch.add_wire(start=p(12, 4), end=p(15, 4))
    sch.add_wire(start=p(15, 4), end=p(15, 9))
    sch.add_wire(start=p(15, 4), end=p(22, 4))

    # VOUT rail
    sch.add_wire(start=p(28, 4), end=p(35, 4))
    sch.add_wire(start=p(35, 4), end=p(35, 7))

    # GND
    sch.add_wire(start=p(0, 13), end=p(0, 20))
    sch.add_wire(start=p(15, 15), end=p(15, 20))
    sch.add_wire(start=p(35, 13), end=p(35, 20))

    # Gate
    sch.add_wire(start=p(5, 6), end=p(8, 6))

    # Labels
    sch.add_label("VIN", position=p(4, 4))
    sch.add_label("SW", position=p(17, 4))
    sch.add_label("VOUT", position=p(30, 4))
    sch.add_label("GATE", position=p(5, 6))

    sch.add_text("Buck Converter 12V to 3.3V", position=p(10, -5), size=1.27)

    sch.save(SCHEMATIC_PATH)


if __name__ == "__main__":
    build_netlist()
    print(f"Netlist: {NETLIST_PATH}")
    build_schematic()
    print(f"Schematic: {SCHEMATIC_PATH}")
