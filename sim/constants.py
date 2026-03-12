from typing import Final

import pint
from uncertainties import ufloat

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# --- Source voltage ---
V_SOURCE: Final = 5.0 * ureg.V  # DC supply

# --- Component values with manufacturer tolerances ---
RESISTANCE: Final = ufloat(1.0, 0.05) * ureg.kohm  # 1.0 kOhm ±5%, generic thick film
CAPACITANCE: Final = ufloat(10.0, 1.0) * ureg.uF  # 10 uF ±10%, generic MLCC

# --- Derived: time constant with propagated uncertainty ---
TAU: Final = (RESISTANCE * CAPACITANCE).to(ureg.ms)  # RC time constant
