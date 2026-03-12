import numpy as np
from numpy.typing import NDArray
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_V, u_kOhm, u_ms, u_uF, u_us

from sim.constants import CAPACITANCE, RESISTANCE, V_SOURCE


def build_circuit() -> Circuit:
    """Build RC charging circuit netlist.

    Topology: V_source -> R -> C -> GND

    Returns:
        PySpice Circuit ready for simulation
    """
    circuit = Circuit("RC Charging")

    v0 = V_SOURCE.magnitude
    circuit.V(1, "input", circuit.gnd, v0 @ u_V)

    r = RESISTANCE.magnitude.nominal_value
    circuit.R(1, "input", "output", r @ u_kOhm)

    c = CAPACITANCE.magnitude.nominal_value
    circuit.C(1, "output", circuit.gnd, c @ u_uF)

    return circuit


def simulate() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Simulate RC circuit charging transient using PySpice/ngspice.

    Returns:
        Tuple of (time_ms, capacitor_voltage) arrays
    """
    circuit = build_circuit()
    simulator = circuit.simulator()

    # Reason: use_initial_condition=True starts capacitor at 0V (skip DC operating point)
    analysis = simulator.transient(
        step_time=10 @ u_us,
        end_time=50 @ u_ms,
        use_initial_condition=True,
    )

    time_s = np.array([float(t) for t in analysis.time])
    v_cap = np.array([float(v) for v in analysis["output"]])

    time_ms = time_s * 1e3

    return time_ms, v_cap
