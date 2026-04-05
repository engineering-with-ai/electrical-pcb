---
name: place-pcb
description: Place PCB footprints from layout_spec.yaml block definitions using pcbnew Python API, then visual review loop.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
---

# Place PCB Components

Place footprints on the KiCad PCB board programmatically from `layout_spec.yaml` block definitions, then refine via visual review.

## Prerequisites

- `cad/*.kicad_pcb` must exist (from "Update PCB from Schematic" in pcbnew)
- `cad/layout_spec.yaml` must define blocks with component references
- Footprints must be assigned in the schematic

## Phase 1: Define PCB Placement in layout_spec.yaml

Add a `pcb_placement` section to `layout_spec.yaml` that maps functional blocks to board regions. Positions are in mm from the board origin (top-left corner).

```yaml
pcb_placement:
  board_size: [100, 80]  # mm
  board_origin: [100, 80]  # mm offset in pcbnew coordinate space

  blocks:
    power:
      zone: [5, 5, 30, 35]  # x, y, width, height in mm
      components:
        J1: [10, 20, 0]     # x, y, rotation_degrees
        F1: [20, 15, 0]
        Q1: [20, 25, 0]
        C1: [28, 15, 0]
        C2: [28, 25, 0]

    cm4:
      zone: [30, 15, 40, 50]
      components:
        J2: [50, 40, 0]     # CM4 connector centered

    rs485:
      zone: [70, 5, 28, 35]
      components:
        U1: [80, 20, 0]
        R1: [90, 12, 0]
        R2: [90, 18, 0]
        R3: [90, 24, 0]
        J3: [95, 20, 270]   # edge connector, rotated
        C3: [75, 12, 0]

    usb_uart:
      zone: [5, 45, 30, 30]
      components:
        U2: [15, 60, 0]
        J4: [5, 55, 90]     # USB connector on edge
        C4: [25, 55, 0]

    io_headers:
      zone: [70, 45, 28, 30]
      components:
        R4: [75, 55, 0]
        R5: [75, 60, 0]
        J5: [85, 50, 0]
        J6: [85, 58, 0]
        J7: [85, 66, 0]

    decoupling:
      zone: [35, 5, 30, 10]
      components:
        C5: [40, 8, 0]
        C6: [48, 8, 0]
        C7: [56, 8, 0]
        C8: [64, 8, 0]
```

## Phase 2: Run Placement Script

```bash
python3 cad/drawing/place_pcb.py
```

The script:
1. Loads `layout_spec.yaml` pcb_placement section
2. Loads `cad/*.kicad_pcb` via pcbnew API
3. For each block, places each component at specified position + rotation:

```python
import pcbnew
import yaml

board = pcbnew.LoadBoard("cad/cm4_carrier.kicad_pcb")
spec = yaml.safe_load(open("cad/layout_spec.yaml"))
placement = spec["pcb_placement"]
ox, oy = placement["board_origin"]

for block_name, block in placement["blocks"].items():
    for ref, (x, y, rot) in block["components"].items():
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            print(f"WARNING: {ref} not found on board")
            continue
        fp.SetPosition(pcbnew.VECTOR2I(
            pcbnew.FromMM(ox + x),
            pcbnew.FromMM(oy + y),
        ))
        fp.SetOrientationDegrees(rot)
        print(f"Placed {ref} at ({x}, {y}) rot={rot}")

board.Save("cad/cm4_carrier.kicad_pcb")
```

4. Draws board outline on Edge.Cuts if not present

## Phase 3: Visual Review (max 5 iterations)

1. Open board: `uv run poe inspect-asm`
2. Check:
   - Components not overlapping
   - Decoupling caps near IC power pins
   - Connectors accessible from board edges
   - Adequate spacing for trace routing
   - Silkscreen readable
3. If issues: adjust positions in `layout_spec.yaml`, re-run placement script
4. After placement converges, proceed to `/route-pcb` for trace routing

## Phase 4: Board Outline

If Edge.Cuts is empty, add the outline programmatically:

```python
import pcbnew

board = pcbnew.LoadBoard("cad/cm4_carrier.kicad_pcb")
ox, oy = 100, 80  # board origin in mm
w, h = 100, 80    # board size in mm

for start, end in [
    ((ox, oy), (ox + w, oy)),
    ((ox + w, oy), (ox + w, oy + h)),
    ((ox + w, oy + h), (ox, oy + h)),
    ((ox, oy + h), (ox, oy)),
]:
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(start[0]), pcbnew.FromMM(start[1])))
    seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(end[0]), pcbnew.FromMM(end[1])))
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(pcbnew.FromMM(0.1))
    board.Add(seg)

board.Save("cad/cm4_carrier.kicad_pcb")
```

## Placement Rules

- **Power input** (screw terminal, polyfuse, MOSFET): near board edge for cable access
- **CM4 connector**: centered — it has the most connections
- **Decoupling caps**: within 5mm of their IC power pin
- **Connectors/headers**: on board edges, pins facing outward
- **ICs**: oriented so pin 1 is consistent (top-left convention)
- **Signal flow**: power enters one side, signals fan out toward headers
- **Clearance**: minimum 1mm between component courtyards
