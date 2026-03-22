# electrical-base

![](https://img.shields.io/gitlab/pipeline-status/engineering-with-ai/electrical-base?branch=main&logo=gitlab)
![](https://gitlab.com/engineering-with-ai/electrical-base/badges/main/coverage.svg)

Buck converter (12V→3.3V, 500kHz) — showcases the full EE toolchain: theory derivation, SPICE simulation, SKiDL schematic generation, and KiCad PCB export.

The analytical CCM solution (D = Vout/Vin, L = Vout(1-D)/(fsw×ΔI)) provides exact expected values. The PySpice/ngspice switching simulation solves the same circuit numerically. Agreement validates the model and toolchain.

## Schematic

```mermaid
graph LR
    VIN["V_IN<br/>12V DC"] --> SW["MOSFET<br/>Switch"]
    SW --> L["L1<br/>22 uH +/-10%"]
    L --> VOUT["V_OUT<br/>3.3V"]
    SW --> D["D1<br/>SS14"]
    D --> GND["GND"]
    VOUT --> COUT["C_out<br/>22 uF +/-20%"]
    COUT --> GND
    VIN --> CIN["C_in<br/>10 uF +/-20%"]
    CIN --> GND

    style VIN fill:#4a9,stroke:#333
    style SW fill:#a49,stroke:#333
    style L fill:#49a,stroke:#333
    style D fill:#94a,stroke:#333
    style VOUT fill:#4a9,stroke:#333
    style GND fill:#666,stroke:#333
    style COUT fill:#a94,stroke:#333
    style CIN fill:#a94,stroke:#333
```

## Workflow

```
theory.ipynb (sympy + pint) -> cad/model.py (SKiDL -> netlist) -> sim/ (PySpice transient) -> pytest (assert sim matches theory)
```

1. `theory.ipynb` derives D, L, C symbolically, plugs in component values with pint + uncertainties
2. `cad/model.py` defines the circuit in SKiDL, generates KiCad netlist
3. `sim/model.py` builds PySpice netlist and runs switching transient simulation
4. `sim/test_run.py` asserts steady-state output voltage matches D×Vin within tolerance

## Quick Start

```bash
uv sync
uv run poe checks       # ruff format + lint
uv run poe notebook      # execute theory.ipynb
uv run poe build         # SKiDL -> KiCad netlist
uv run poe sim           # pytest
uv run poe inspect       # open schematic in KiCad
uv run poe export        # SVG + PDF to spec/drawings/
uv run poe validate      # KiCad ERC
```

## Structure

- `theory.ipynb` — sympy derivation, pint + uncertainties, expected values
- `sim/constants.py` — buck converter parameters with units, tolerances, and sources
- `sim/model.py` — PySpice switching transient simulation
- `sim/test_run.py` — pytest assertion: output voltage vs D×Vin
- `cad/model.py` — SKiDL circuit definition → KiCad netlist
- `spec/drawings/` — exported schematic SVG/PDF
