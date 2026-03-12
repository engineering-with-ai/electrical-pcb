## Methodologies

### Implementation Methodology
When presented with a request YOU MUST:
1. Use context7 mcp server or websearch tool to get the latest related documentation. Understand the API deeply and all of its nuances and options
2. Use TDD Approach: Derive the expected value in `theory.ipynb` first, then write the sim assertion in `run.py` that fails, then build the model until it passes
3. Start with the simplest hand calc — back-of-envelope before simulation
4. See the assertion fail against the notebook's expected value
5. Make the smallest change to the model
6. Check if `uv run poe checks` and `uv run poe cover` pass
7. Repeat steps 5-6 until the assertion passes
8. You MUST NOT move on until assertions pass

### Debugging Methodology

#### Phase I: Information Gathering
1. Understand the error
2. Read the relevant source code: try local `.venv`
3. Look at any relevant github issues for the library

#### Phase II: Testing Hypothesis
4. Develop a hypothesis that resolves the root cause of the problem. Must only chase root cause possible solutions. Think hard to decide if its root cause or NOT.
5. Add debug logs to determine hypothesis
6. If not successful, YOU MUST clean up any artifact or code attempts in this debug cycle. Then repeat steps 1-5

#### Phase III: Weigh Tradeoffs
7. If successful and fix is straightforward. Apply fix
8. If not straightforward, weigh the tradeoffs and provide a recommendation


## Units & Dimensional Analysis — Non-Negotiable

Bare floats are the `Any` of engineering. Every physical value MUST have a pint unit.

- **No bare floats for physical quantities.** `velocity = 3.5` is NEVER ALLOWED. `velocity = 3.5 * ureg.m / ureg.s` is correct.
- **No manual unit conversions.** Let pint `.to()` handle all conversions. Manual conversion factors are the equivalent of `# type: ignore` — they bypass the guardrail.
- **No `float` annotations for physical quantities.** Use `pint.Quantity` in type hints.
  - NOT: `def calc_force(mass: float, accel: float) -> float:`
  - CORRECT: `def calc_force(mass: Quantity, accel: Quantity) -> Quantity:`
- **Use domain-conventional units, not SI base units everywhere.** kA not A for fault current, bar not Pa for hydraulic pressure, AWG not m² for wire gauge. Let pint handle the conversion to SI when computation requires it.


## Uncertainty & Precision

- **No results without uncertainty.** If you can't state the error band, the result is incomplete. Use the `uncertainties` library to propagate error through calculations.
- **No false precision.** If your input is +/-5%, your output cannot have 7 significant figures. Report results to the number of significant figures justified by your inputs.
- **Never round intermediate results.** Carry full precision through the calculation chain. Round only in the final reporting cell.


## Constants & Physical Parameters

Every constant needs a name, a unit, and a source. A magic `0.85` in engineering could be a safety factor, a derating, an efficiency, or a power factor — getting it wrong can mean a fire.

- **All physical constants at module level in SCREAMING_SNAKE_CASE** with `Final` annotation, pint unit, and source comment
  ```python
  FUSE_DERATING: Final = 0.80 * ureg.dimensionless  # UL 248 Table 1
  GRAVITY: Final = 9.80665 * ureg.m / ureg.s**2  # ISO 80000-3
  ```
- **No inline physical constants.** Never write `force = mass * 9.81`. Define it once, name it, source it.
- **Standards references must include edition, table, and clause.** "Per IEEE 1547" is meaningless. "Per IEEE 1547-2018 Table 1, Category III" is a reference.


## Assumptions

AI silently assumes ideal conditions — zero wire resistance, no temperature derating, negligible contact resistance, lossless transmission. Every one of these is an engineering `Any`.

- **Every assumption must be stated explicitly** in the notebook's assumptions cell before any derivation
- **If you can't name the assumption, you can't validate the result**
- **When the sim disagrees with theory, the first place to look is the assumptions cell** — did an assumption break, or did the sim break?
- **No idealized defaults.** Real systems have parasitics, losses, and tolerances. State which you are neglecting and why.


## Notebook Discipline

`theory.ipynb` is a calculation document, not a tutorial.

- **Notebook structure:** Assumptions cell -> Derivation cells -> Expected value cell
- **The expected value cell is your type signature.** It defines what correct looks like before you simulate: `# Peak fault current: 4.2kA +/- 10%`
- **No tutorial-style prose between cells.** Brief `# Reason:` comments for non-obvious steps. The derivation speaks for itself.
- **Every notebook must be re-runnable.** No cells that depend on manual execution order.


## Simulation Validation

Never trust simulation output. Validate it.

### Order-of-Magnitude First
- Before running any sim, the notebook must have a hand calc that gets you within 2-5x of the answer
- If the sim is 10x off from the hand calc, one of them is wrong — figure out which before proceeding
- This is the engineering "see the test fail" step

### Conservation Law Checks
- Energy in = energy out + losses
- Mass flow in = mass flow out
- Current into a node = current out
- If conservation doesn't hold, the model is wrong — not the physics

### Convergence is Not Optional
- **Mesh convergence for FEM** — refine until the result stops changing within tolerance
- **Timestep convergence for transient sims** — halve the timestep and verify the result holds
- **Solver tolerance must be justified, not defaulted.** "It ran without errors" is not validation.


## Derating & Safety Factors

- **Components have temperature derating, altitude derating, aging factors.** These are not optional.
- **Safety factors must be explicit and sourced** — never assumed or buried in a calculation
- **Worst-case analysis is the default.** Nominal-case results are supplementary, not primary.


## Code Structure & Modularity

- **Write the most minimal code to get the job done**
- **Get to root of the problem.** Never write hacky workarounds. You are done when the assertions pass.
- **Never create a file longer than 200 lines of code.** If a file approaches this limit, refactor by splitting it into modules.


## Testing & Reliability

- **Fail fast, fail early.** Detect errors as early as possible and halt execution. Rely on the runtime to handle the error and provide a stack trace. You MUST NOT write random error handling for no good reason.
- **Use AAA (Arrange, Act, Assert) pattern for tests:**
  - **Arrange**: Set up the necessary context and inputs
  - **Act**: Execute the simulation or calculation
  - **Assert**: Verify the outcome matches the notebook's expected value within tolerance
- **Use `pytest.approx` with `rel` tolerance for physical quantity assertions**
  ```python
  assert actual_current.magnitude == pytest.approx(expected_current.magnitude, rel=0.10)
  ```


## Style

- **Constants in code:** Write top level declarations in SCREAMING_SNAKE_CASE with `Final` annotation
- **Use explicit type hints ALWAYS.** No `Any`. No bare `float` for physical quantities.
- **Prefer Pydantic models over dicts for structured data**
- **Use proper logging, not print() debugging**
- **Write concise Google Style Docstrings for an LLM to consume**


## Anti-Bias Rules

| AI Bias | Correct Practice |
|---|---|
| Uses ideal/textbook models by default | Real systems have parasitics, losses, tolerances — state which you're neglecting and why |
| Writes tutorial-style notebooks with markdown explanations between every cell | Notebook is a calculation document — derivation, numbers, expected value. Not a teaching tool |
| Presents single-point results as definitive | Every result has a tolerance band. If you can't state the band, you don't understand the result |
| Defaults to SI base units everywhere | Use domain-conventional units — kA for fault current, bar for hydraulic pressure, AWG for wire gauge |
| Rounds intermediate results | Never round until final reporting. Carry full precision through the calculation chain |
| Skips derating and safety factors | Components have temperature derating, altitude derating, aging factors. These are not optional |
| Cites standards without edition/table/clause | "Per IEEE 1547" is meaningless — "Per IEEE 1547-2018 Table 1, Category III" is a reference |
| Uses default solver settings without justification | Timestep, mesh density, tolerance — all must be explicit choices with stated rationale |
| Trusts simulation output without sanity checks | Conservation law check and order-of-magnitude hand calc before accepting any result |


## Electrical Engineering Best Practices


### EE-Conventional Units

Use the units that appear on datasheets and schematics, not SI base units.

| Quantity | Use | Not |
|---|---|---|
| Resistance | kOhm, MOhm | Ohm (for large values) |
| Capacitance | pF, nF, uF | F |
| Inductance | nH, uH, mH | H |
| Signal current | mA, uA | A |
| Fault / bus current | kA | A |
| Wire gauge | AWG | m² |
| Frequency | kHz, MHz | Hz (for large values) |
| Time constants | us, ms | s (when sub-second) |
| PCB trace width | mil, mm | m |

Let pint `.to()` handle conversion to SI when computation requires it.


### Component Tolerance Conventions

Always state tolerance source — don't guess.

| Component | Typical Tolerance | Source |
|---|---|---|
| Thick film resistor | +/-1%, +/-5% | Datasheet series (E96, E24) |
| Thin film resistor | +/-0.1%, +/-0.5% | Datasheet |
| MLCC (C0G/NP0) | +/-5% | Datasheet, stable over temp |
| MLCC (X5R/X7R) | +/-10%, +/-20% | Datasheet — derate for DC bias and temp |
| Electrolytic | +/-20% | Datasheet — derate for ESR aging |
| Inductor | +/-10%, +/-20% | Datasheet — check saturation current |

When building `ufloat` values, the uncertainty is the tolerance from the datasheet:
```python
RESISTANCE: Final = ufloat(1.0, 0.05) * ureg.kohm   # 1.0 kOhm +/-5%, generic thick film
CAPACITANCE: Final = ufloat(10.0, 1.0) * ureg.uF     # 10 uF +/-10%, generic MLCC X7R
```


### pint + uncertainties Access Pattern

pint wraps ufloat. Strip unit first (`.magnitude`), then strip uncertainty (`.nominal_value`).

```python
TAU = (RESISTANCE * CAPACITANCE).to(ureg.ms)

TAU.magnitude                # → ufloat (e.g. 10.0+/-1.12)
TAU.magnitude.nominal_value  # → float (e.g. 10.0)
TAU.magnitude.std_dev        # → float (e.g. 1.12)
```

**WRONG:** `TAU.nominal_value.magnitude` — pint Quantity has no `.nominal_value`.


### PySpice / ngspice Conventions

#### Circuit Construction
- Use PySpice unit decorators for netlist values: `v0 @ u_V`, `r @ u_kOhm`, `c @ u_uF`
- Strip pint units and uncertainty before passing to PySpice — it needs plain floats with its own unit system
- Name nodes semantically: `"input"`, `"output"`, `"bus"`, `"fault_point"` — not `"n1"`, `"n2"`

```python
# Correct: strip pint unit, strip uncertainty, apply PySpice unit
r = RESISTANCE.magnitude.nominal_value
circuit.R(1, "input", "output", r @ u_kOhm)
```

#### Transient Simulation
- **Always use `use_initial_condition=True`** for charging/discharging circuits. Without it, SPICE computes a DC operating point first — capacitors start charged, inductors start at steady-state current. This is the #1 PySpice gotcha.
- Choose `step_time` and `end_time` relative to the circuit's time constant — 5*tau is a reasonable end time for steady state
- Justify timestep: `step_time` should be at least 100x smaller than the fastest time constant

```python
analysis = simulator.transient(
    step_time=10 @ u_us,       # Reason: tau ~10ms, step = tau/1000
    end_time=50 @ u_ms,        # Reason: 5*tau for steady state
    use_initial_condition=True, # Reason: start capacitor at 0V
)
```

#### Extracting Results
- Analysis node names match your circuit node names: `analysis["output"]`
- Time is in seconds — convert to ms for readability: `time_ms = time_s * 1e3`
- Convert to numpy arrays for assertion: `np.array([float(v) for v in analysis["output"]])`


### KiCad Workflow

- Schematics live in `cad/` directory with `.kicad_sch` extension
- Open for editing: `eeschema cad/<name>.kicad_sch`
- Export to SVG: `kicad-cli sch export svg cad/<name>.kicad_sch -o cad/drawings/`
- Export to PDF: `kicad-cli sch export pdf cad/<name>.kicad_sch -o cad/drawings/`
- Run ERC: `kicad-cli sch erc cad/<name>.kicad_sch`
- Schematic should match the netlist in `sim/model.py` — same topology, same node names, same component values

#### Export Formats
Two export targets — one for web/readme, one for documentation:
- **SVG (web/readme):** `kicad-cli sch export svg <file> -e -n -o cad/drawings/` — strips drawing sheet border and background for clean embedding
- **PDF (documentation):** `kicad-cli sch export pdf <file> -o cad/drawings/<name>.pdf` — keeps the professional drawing sheet border with title block

#### Presentable Schematics
- Center the circuit on the schematic sheet — not crammed in the upper-left corner. For A4 paper, center is approximately (148.5, 105.0) mm
- Keep the circuit compact — minimize wire lengths, align components on 2.54mm grid

#### Visual Review After Generation — Non-Negotiable
After generating or modifying a KiCad schematic, you MUST visually review it:
1. Export SVG: `kicad-cli sch export svg <file> -t engineering -e -n -o cad/drawings/`
2. Convert to PNG: `rsvg-convert -w 1600 cad/drawings/<name>.svg -o /tmp/<name>_review.png`
3. Read the PNG with the Read tool and inspect for:
   - Labels overlapping component references or values
   - Components too close together (need ~20mm between centers for horizontal chains)
   - Circuit not centered on the page
   - Wires crossing through component bodies
4. Fix any issues and re-export before proceeding


### KiCad Schematic Generation (.kicad_sch)

KiCad schematics are s-expression files. You can generate them programmatically.

**File structure:**
```
(kicad_sch
  (version 20230121)
  (generator "claude")
  (uuid "<sheet-uuid>")
  (paper "A4")
  (lib_symbols ...)     ← embedded copies of symbols used
  (wire ...)            ← wires connecting pins
  (label ...)           ← net labels (must match sim/model.py node names)
  (symbol ...)          ← placed component instances
  (sheet_instances ...)
)
```

**Symbol libraries — where to find them:**
- Standard symbols: `/usr/share/kicad/symbols/`
- Passive components (R, C, L): `Device.kicad_sym` → lib_id `"Device:R"`, `"Device:C"`, `"Device:L"`
- SPICE sources and ground: `Simulation_SPICE.kicad_sym` → lib_id `"Simulation_SPICE:VDC"`, `"Simulation_SPICE:0"`
- Power symbols (VCC, GND): `power.kicad_sym` → lib_id `"power:GND"`, `"power:VCC"`

**Extracting symbol definitions for lib_symbols:**
Each schematic must embed copies of the symbols it uses. Extract them from the `.kicad_sym` files by parsing the s-expression — find the top-level `(symbol "NAME" ...)` block, prefix with library name for `lib_symbols`.

**Placing a component instance:**
```
(symbol (lib_id "Device:R") (at 144.78 55.88 90) (unit 1)
  (in_bom yes) (on_board yes) (dnp no)
  (uuid "<component-uuid>")
  (property "Reference" "R1" (at 144.78 52.07 90)
    (effects (font (size 1.27 1.27)))
  )
  (property "Value" "1k" (at 144.78 54.13 90)
    (effects (font (size 1.27 1.27)))
  )
  (property "Footprint" "" (at ...) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "~" (at ...) (effects (font (size 1.27 1.27)) hide))
  (pin "1" (uuid "<pin-uuid>"))
  (pin "2" (uuid "<pin-uuid>"))
  (instances
    (project "<project-name>"
      (path "/<sheet-uuid>" (reference "R1") (unit 1))
    )
  )
)
```

**Key rules:**
- All coordinates on 2.54mm grid
- Rotation: 0 = default orientation, 90 = rotated (e.g. horizontal resistor)
- Every element needs a unique UUID (use `uuid.uuid4()`)
- Wire endpoints must land exactly on pin positions
- `(label "node_name" ...)` creates named nets — use these to match `sim/model.py` node names
- Validate with: `kicad-cli sch export svg <file> -o /tmp/` — if it exports, the format is valid

**Pin offsets from component origin (at default rotation 0):**

| Symbol | Pin 1 offset | Pin 2 offset |
|---|---|---|
| Device:R | (0, -3.81) top | (0, +3.81) bottom |
| Device:C | (0, -3.81) top | (0, +3.81) bottom |
| Device:L | (0, -3.81) top | (0, +3.81) bottom |
| Simulation_SPICE:VDC | (0, -5.08) positive | (0, +5.08) negative |
| Simulation_SPICE:0 | (0, 0) single pin | — |
| power:PWR_FLAG | (0, 0) single pin | — |

When rotated 90 degrees, swap x/y offsets. When rotated 180, negate offsets.

**Power symbol connection rule:** Wire endpoints must land exactly on power symbol pin positions. Split long wires into segments that pass through each power pin location — spatial overlap alone does not create a connection.

**PWR_FLAG rule:** Every net with a `power_in` pin (like `Simulation_SPICE:0`) needs a `power:PWR_FLAG` on the same net to satisfy ERC. Place it on the same wire, rotated 180 so it points down toward the wire.


### schemdraw for Documentation

Use schemdraw for quick circuit diagrams in notebooks and readmes when a full KiCad schematic is overkill:
```python
import schemdraw
import schemdraw.elements as elm

with schemdraw.Drawing() as d:
    d += elm.SourceV().label("V_s")
    d += elm.Resistor().right().label("R")
    d += elm.Capacitor().down().label("C")
    d += elm.Line().left()
```


### SPICE Gotchas

| Gotcha | Symptom | Fix |
|---|---|---|
| Missing `use_initial_condition=True` | Capacitor starts charged, inductor has steady-state current | Add `use_initial_condition=True` to `.transient()` |
| Floating node | Simulation fails or gives nonsense | Every node must have a DC path to ground |
| Timestep too large | Waveform looks jagged or misses transients | `step_time` should be 100-1000x smaller than fastest tau |
| Node name mismatch | `KeyError` when extracting results | Use exact node name string from circuit definition |
| Convergence failure | ngspice reports `no convergence` | Add `.options(reltol=0.01)` or check for unrealistic component values |


### EE Anti-Bias Rules

| AI Bias | Correct Practice |
|---|---|
| Ignores ESR on capacitors | Electrolytic ESR matters for ripple current and loop stability — state if neglected and why |
| Assumes ideal op-amps | Real op-amps have offset voltage, bias current, slew rate, GBW — state which limits apply |
| Skips decoupling capacitors | Every IC power pin needs local decoupling — not optional in real designs |
| Uses unrealistic component values | Check that values exist in standard series (E24, E96). 1.37 kOhm is not a real resistor |
| Ignores temperature coefficients | MLCC X7R loses 50%+ capacitance at rated voltage and high temp — derate or use C0G |
| Treats wire as zero impedance | At high frequency or high current, wire/trace impedance matters — state when neglected |
| Assumes instantaneous switching | Real switches have rise/fall time, dead time, ringing — matters for EMI and loss calculations |
| Defaults to DC analysis | Most real circuits have AC behavior that matters — check if transient or frequency analysis is needed |


