import numpy as np
import pytest

from sim.constants import TAU, V_SOURCE
from sim.model import simulate


def _extract_time_constant(t_ms: np.ndarray, v_cap: np.ndarray) -> float:
    """Extract time constant from simulated data.

    At t = tau, voltage reaches ~63.2% of final value (1 - 1/e).

    Args:
        t_ms: Time array in milliseconds
        v_cap: Capacitor voltage array

    Returns:
        Simulated time constant in milliseconds
    """
    v_final = V_SOURCE.magnitude
    v_at_tau = v_final * (1 - np.exp(-1))
    idx = np.argmin(np.abs(v_cap - v_at_tau))
    return float(t_ms[idx])


class TestRCCircuit:
    """Assertions against theory.ipynb expected values."""

    def test_time_constant(self) -> None:
        """SPICE tau matches analytical tau within propagated uncertainty."""
        # arrange
        expected_tau_ms = TAU.magnitude.nominal_value
        tolerance = TAU.magnitude.std_dev / TAU.magnitude.nominal_value

        # act
        t_ms, v_cap = simulate()
        actual_tau_ms = _extract_time_constant(t_ms, v_cap)

        # assert
        assert actual_tau_ms == pytest.approx(expected_tau_ms, rel=tolerance)

    def test_final_voltage(self) -> None:
        """Capacitor charges to source voltage at steady state."""
        # arrange
        expected_v = V_SOURCE.magnitude

        # act
        _t_ms, v_cap = simulate()
        actual_v = v_cap[-1]

        # assert
        assert actual_v == pytest.approx(expected_v, rel=0.01)

    def test_initial_voltage(self) -> None:
        """Capacitor starts at zero volts."""
        # act
        _, v_cap = simulate()

        # assert
        assert v_cap[0] == pytest.approx(0.0, abs=0.1)
