---
name: generate-schematic
description: Generate professional KiCad schematic from SKiDL netlist + declarative layout spec. Two-phase: deterministic placement then visual refinement.
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob
---

# Generate Professional KiCad Schematic

Read `cad/layout_spec.yaml` and the SKiDL netlist to generate a professional `.kicad_sch` file using kicad-sch-api.

## Phase 1: Deterministic Placement

1. **Read layout spec** — `cad/layout_spec.yaml` defines functional blocks, positions, signal flow, and components
2. **Read netlist** — parse the `.net` file or `cad/model.py` for component list and connections
3. **Generate schematic** — use kicad-sch-api with these rules:
   - Each block occupies its declared position region — no overlap
   - ICs centered in their block
   - Decoupling caps directly below their IC's power pins
   - Power symbols (+5V, 3V3) at TOP of each block
   - GND symbols at BOTTOM of each block
   - Signal inputs on LEFT edge of block, outputs on RIGHT
   - Net labels at block boundaries connect signals across blocks
   - Wire routing via `auto_route_pins(strategy="manhattan")` — orthogonal only
   - Minimum 8 grid units between components within a block
   - Use hierarchical sheets for blocks with >8 components
4. **Set title block** — `sch.set_title_block(title=..., company="Engineering With AI")`
5. **Run ERC** — `kicad-cli sch erc cad/*.kicad_sch` must pass with 0 violations

## Phase 2: Visual Review Loop (max 5 iterations)

After Phase 1, iterate on visual quality:

1. **Export SVG** — `kicad-cli sch export svg cad/*.kicad_sch -b -e -n -o /tmp/`
2. **Convert to PNG** — `rsvg-convert -w 2400 /tmp/*.svg -o /tmp/schematic_review.png`
3. **Read and inspect the PNG** — look for:
   - Labels overlapping component references or values
   - Wires crossing through component bodies
   - Unbalanced spacing between sections
   - Text too small or illegible at this resolution
   - Signal flow not reading left-to-right
   - Components too close together
4. **If issues found**: adjust positions in the schematic generation code, regenerate, re-export
5. **If clean**: done — run final ERC and export deliverables

After converging, update `cad/layout_spec.yaml` with the refined positions so future runs start from the optimized layout.

## Output

- `cad/<project>.kicad_sch` — generated schematic
- `spec/drawings/<project>.svg` — schematic SVG (circuit only, no border)
- `spec/drawings/<project>.pdf` — schematic PDF (with drawing sheet + title block)
- ERC report confirming 0 violations

## Layout Spec Format Reference

```yaml
sheet_size: A4
title: "Project Title"

blocks:
  block_name:
    position: [x, y]              # grid units from sheet origin
    components: [R1, U1, C1]      # reference designators
    signal_flow: left_to_right    # or right_to_left, top_to_bottom
    power_rail: "+5V"             # power symbol name (placed at top)
    ground: true                  # add GND symbol at bottom
    labels:
      left: [NET_A, NET_B]       # input net labels
      right: [NET_C]             # output net labels

layout_rules:
  min_component_spacing: 8
  power_symbol_position: top
  ground_symbol_position: bottom
  decoupling_near_ic: true
  routing: manhattan
```
