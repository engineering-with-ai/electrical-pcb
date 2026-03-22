"""Assert buck converter simulation matches analytical expected values."""

import numpy as np
import pytest

from sim.constants import DUTY_CYCLE, V_IN, ureg
from sim.model import simulate


def _expected_output_voltage() -> float:
    """Ideal buck: V_out = D * V_in."""
    return DUTY_CYCLE.magnitude * V_IN.to(ureg.V).magnitude


class TestBuckConverter:
    """Assertions against theory.ipynb expected values."""

    def test_output_voltage(self) -> None:
        """Steady-state output voltage matches D * V_in within 10%."""
        # arrange
        expected_v = _expected_output_voltage()

        # act
        time_us, v_out = simulate()
        # Reason: use last 10% of sim for steady-state average
        steady = v_out[int(len(v_out) * 0.9) :]
        actual_v = steady.mean()

        # assert
        assert actual_v == pytest.approx(expected_v, rel=0.10)
