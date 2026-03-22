"""Buck converter parameters with units and tolerances."""

from typing import Final

import pint
from uncertainties import ufloat

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# --- Input / Output spec ---
V_IN: Final = 12.0 * ureg.V  # DC input supply
V_OUT: Final = 3.3 * ureg.V  # target output voltage
I_LOAD: Final = 1.0 * ureg.A  # max load current

# --- Switching ---
F_SW: Final = 500.0 * ureg.kHz  # switching frequency, typical for integrated buck ICs

# --- Ripple specs ---
# Reason: 1% output voltage ripple and 30% inductor current ripple are common targets
DELTA_V_OUT: Final = 0.033 * ureg.V  # 1% of V_OUT
RIPPLE_RATIO: Final = 0.30 * ureg.dimensionless  # peak-to-peak ΔI / I_LOAD

# --- Derived: duty cycle ---
# D = V_OUT / V_IN (ideal, CCM)
DUTY_CYCLE: Final = (V_OUT / V_IN).to(ureg.dimensionless)

# --- Component values ---
# L = V_OUT * (1 - D) / (f_sw * ΔI_L)
# ΔI_L = RIPPLE_RATIO * I_LOAD
DELTA_I_L: Final = (RIPPLE_RATIO * I_LOAD).to(ureg.A)
INDUCTANCE: Final = ufloat(22.0, 2.2) * ureg.uH  # 22 uH ±10%, shielded power inductor
# Reason: calculated minimum ~18.2 uH, 22 uH is next standard value (E12)

# C_OUT = ΔI_L / (8 * f_sw * ΔV_OUT)
OUTPUT_CAP: Final = ufloat(22.0, 4.4) * ureg.uF  # 22 uF ±20%, MLCC X5R
# Reason: calculated minimum ~5.7 uF, 22 uF provides margin for DC bias derating

INPUT_CAP: Final = ufloat(10.0, 2.0) * ureg.uF  # 10 uF ±20%, MLCC X5R
# Reason: input cap sized for RMS ripple current handling
