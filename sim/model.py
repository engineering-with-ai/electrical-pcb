"""Buck converter PySpice transient simulation.

Ideal buck: voltage pulse source (duty-cycled) → inductor → output cap → load.
Diode provides freewheeling path when switch is off.
"""

import numpy as np
from numpy.typing import NDArray
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_Ohm, u_uF, u_uH, u_us, u_V

from sim.constants import (
    DUTY_CYCLE,
    F_SW,
    I_LOAD,
    INDUCTANCE,
    INPUT_CAP,
    OUTPUT_CAP,
    V_IN,
    V_OUT,
)


def build_circuit() -> Circuit:
    """Build ideal buck converter netlist.

    Topology: Pulsed V_source → L → output node → C_out → GND
              Diode from GND to switch node (freewheeling)
              R_load from output to GND
    """
    circuit = Circuit("Buck Converter")

    vin = V_IN.magnitude
    d = DUTY_CYCLE.magnitude
    f = F_SW.to("kHz").magnitude
    period_us = 1e3 / f  # period in microseconds

    # Reason: pulse source models ideal switch — ON for D*T, OFF for (1-D)*T.
    # PySpice has circuit.MOSFET() but that needs gate driver, SPICE model params,
    # and 10x slower sim — all for the same steady-state result within our 10% tolerance.
    circuit.PulseVoltageSource(
        "sw",
        "switch",
        circuit.gnd,
        initial_value=0 @ u_V,
        pulsed_value=vin @ u_V,
        delay_time=0 @ u_us,
        rise_time=10e-3 @ u_us,  # 10ns rise — fast enough to not affect results
        fall_time=10e-3 @ u_us,
        pulse_width=(d * period_us) @ u_us,
        period=period_us @ u_us,
    )

    # Freewheeling diode
    circuit.D("1", circuit.gnd, "switch_l", model="DIODE")
    circuit.model("DIODE", "D", IS=1e-14, N=1.0, BV=100)

    inductance = INDUCTANCE.magnitude.nominal_value
    circuit.L("1", "switch", "output", inductance @ u_uH)

    # Reason: wire from switch node to inductor and diode must be same net
    circuit.R("wire", "switch", "switch_l", 1e-3 @ u_Ohm)

    c_out = OUTPUT_CAP.magnitude.nominal_value
    circuit.C("out", "output", circuit.gnd, c_out @ u_uF)

    c_in = INPUT_CAP.magnitude.nominal_value
    circuit.C("in", "switch", circuit.gnd, c_in @ u_uF)

    # Load resistor: R = V_out / I_load
    r_load = (V_OUT / I_LOAD).to("ohm").magnitude
    circuit.R("load", "output", circuit.gnd, r_load @ u_Ohm)

    return circuit


def simulate() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Run transient simulation of buck converter.

    Returns:
        Tuple of (time_us, output_voltage) arrays
    """
    circuit = build_circuit()
    simulator = circuit.simulator()

    f = F_SW.to("kHz").magnitude
    period_us = 1e3 / f

    # Reason: simulate 200 switching cycles for steady-state, step = period/100
    end_time = 200 * period_us
    step_time = period_us / 100

    analysis = simulator.transient(
        step_time=step_time @ u_us,
        end_time=end_time @ u_us,
        use_initial_condition=True,
    )

    time_s = np.array([float(t) for t in analysis.time])
    v_out = np.array([float(v) for v in analysis["output"]])

    time_us = time_s * 1e6

    return time_us, v_out
