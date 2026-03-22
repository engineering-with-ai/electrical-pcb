"""Buck converter schematic generation via SKiDL.

Generates KiCad netlist from Python circuit definition.
Components are parameterized from sim/constants.py.
"""

import os

# Reason: SKiDL checks version-specific env vars for KiCad symbol libraries
_SYM_DIR = "/usr/share/kicad/symbols"
for v in ("KICAD_SYMBOL_DIR", "KICAD6_SYMBOL_DIR", "KICAD7_SYMBOL_DIR", "KICAD8_SYMBOL_DIR", "KICAD9_SYMBOL_DIR"):
    os.environ[v] = _SYM_DIR

from skidl import *  # noqa: E402

from sim.constants import (
    INDUCTANCE,
    INPUT_CAP,
    OUTPUT_CAP,
    ureg,
)

NETLIST_PATH = "cad/buck_converter.net"


def build_schematic() -> None:
    """Define buck converter circuit and generate netlist."""

    # Nets
    vin = Net("VIN")
    sw = Net("SW")
    vout = Net("VOUT")
    gnd = Net("GND")

    # Input connector (2-pin header for power input)
    j_in = Part("Connector_Generic", "Conn_01x02", footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    j_in.value = "VIN"
    vin += j_in[1]
    gnd += j_in[2]

    # Input capacitor
    c_in_val = f"{INPUT_CAP.magnitude.nominal_value:.0f}uF"
    c_in = Part("Device", "C", value=c_in_val, footprint="Capacitor_SMD:C_0805_2012Metric")
    vin += c_in[1]
    gnd += c_in[2]

    # Reason: using a generic NMOS as the high-side switch for simplicity
    # In a real design this would be an integrated buck IC (e.g. TPS54331)
    q_sw = Part("Device", "Q_NMOS", footprint="Package_TO_SOT_SMD:SOT-23")
    q_sw.value = "SW"
    vin += q_sw["D"]
    sw += q_sw["S"]

    # Gate drive placeholder — net label only
    gate = Net("GATE")
    gate += q_sw["G"]

    # Freewheeling diode
    d1 = Part("Device", "D_Schottky", footprint="Diode_SMD:D_SOD-123")
    d1.value = "SS14"
    gnd += d1["A"]
    sw += d1["K"]

    # Inductor
    l_val = f"{INDUCTANCE.magnitude.nominal_value:.0f}uH"
    l1 = Part("Device", "L", value=l_val, footprint="Inductor_SMD:L_1210_3225Metric")
    sw += l1[1]
    vout += l1[2]

    # Output capacitor
    c_out_val = f"{OUTPUT_CAP.magnitude.nominal_value:.0f}uF"
    c_out = Part("Device", "C", value=c_out_val, footprint="Capacitor_SMD:C_0805_2012Metric")
    vout += c_out[1]
    gnd += c_out[2]

    # Output connector
    j_out = Part("Connector_Generic", "Conn_01x02", footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    j_out.value = "VOUT"
    vout += j_out[1]
    gnd += j_out[2]

    generate_netlist(file_=NETLIST_PATH, tool=KICAD8)


if __name__ == "__main__":
    build_schematic()
    print(f"Netlist generated: {NETLIST_PATH}")
