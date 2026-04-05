---
name: layout-pcb
description: Place footprints, autoroute traces, and validate a KiCad PCB. One-shot pipeline with human review at the end.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
---

# Layout PCB

Place footprints from `layout_spec.yaml`, autoroute via Freerouting, run DRC, and export review images. Human reviews at the end.

## Prerequisite (human, one-time)

"Update PCB from Schematic" is GUI-only — no CLI or Python API exists for this.

1. Open pcbnew: `uv run poe inspect-asm`
2. Press **F8** (Tools → Update PCB from Schematic)
3. Click **Update PCB** — footprints appear piled at origin
4. Save and close

This only needs to happen once per schematic change. After footprints are on the board, this skill handles everything else.

## Phase 1: Place Footprints

Run the placement script:
```bash
python3 cad/drawing/place_pcb.py
```

This reads `pcb_placement` from `layout_spec.yaml` and positions each footprint via the pcbnew Python API. It also draws the board outline on Edge.Cuts if missing.

### Placement config format in layout_spec.yaml

```yaml
pcb_placement:
  board_size: [100, 80]      # mm
  board_origin: [100, 80]    # mm offset in pcbnew coordinate space
  blocks:
    power:
      components:
        J1: [3, 20, 0]       # x, y (mm from board origin), rotation (degrees)
        F1: [15, 12, 0]
```

### Placement rules
- Power input near board edge for cable access
- Main connector (CM4) centered — most connections radiate from it
- Decoupling caps within 5mm of their IC power pins
- Headers on board edges, pins facing outward
- Minimum 1mm between component courtyards

## Phase 2: Autoroute

Export DSN, route with Freerouting, import result:

```bash
# Export
python3 -c "
import pcbnew
board = pcbnew.LoadBoard('cad/cm4_carrier.kicad_pcb')
pcbnew.ExportSpecctraDSN(board, '/tmp/cm4_carrier.dsn')
print('DSN exported')
"

# Route (single-threaded — multi-thread is broken)
java -jar ~/tools/freerouting.jar \
  -de /tmp/cm4_carrier.dsn \
  -do /tmp/cm4_carrier.ses \
  -mp 20 -mt 1

# Import
python3 -c "
import pcbnew
board = pcbnew.LoadBoard('cad/cm4_carrier.kicad_pcb')
pcbnew.ImportSpecctraSES(board, '/tmp/cm4_carrier.ses')
board.Save('cad/cm4_carrier.kicad_pcb')
print('SES imported and board saved')
"
```

### Freerouting prerequisites
```bash
# Install if missing
mkdir -p ~/tools && curl -L -o ~/tools/freerouting.jar \
  "https://github.com/freerouting/freerouting/releases/download/v2.0.1/freerouting-2.0.1.jar"
```

## Phase 3: DRC Validation

```bash
uv run poe validate-asm
cat cm4_carrier-drc.rpt
```

Target: **0 errors** (warnings OK). Common results:
- `0 unconnected` = all nets routed
- `copper_edge_clearance` = trace too close to board edge → adjust placement in yaml
- `silk_edge_clearance` = cosmetic warning, OK to ship

## Phase 4: Visual Review (max 5 iterations)

Export the board as SVG for inspection:

```bash
kicad-cli pcb export svg cad/cm4_carrier.kicad_pcb \
  -l F.Cu,B.Cu,Edge.Cuts,F.Silkscreen \
  --black-and-white --exclude-drawing-sheet \
  --page-size-mode 2 --mode-single \
  -o /tmp/pcb_review.svg
rsvg-convert -w 2400 --background-color white /tmp/pcb_review.svg -o /tmp/pcb_review.png
```

Read the PNG and check:
- All traces connected (no floating ratsnest lines)
- Power traces adequately wide
- No traces crossing board edge
- Components not overlapping
- Logical grouping (power section, comms section, headers)

**If DRC errors or visual issues:**
1. Adjust component positions in `layout_spec.yaml` `pcb_placement` section
2. Re-run from Phase 1 (place → route → DRC → review)

**If clean:** proceed to Phase 5.

## Phase 5: Ground Pour (manual in pcbnew)

After routing converges, add ground copper fill:
1. Open board: `uv run poe inspect-asm`
2. Select copper zone tool (right toolbar)
3. Set net to GND, layer to F.Cu
4. Draw rectangle around entire board → press B to fill
5. Repeat on B.Cu
6. Save → re-run `uv run poe validate-asm`

## Phase 6: Final Export

```bash
uv run poe generate-asm
```

Produces: gerbers, drill files, BOM, CPL, PCB STEP, PCB SVG.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Freerouting leaves unrouted nets | Try `-us hybrid`, or route remaining manually |
| Edge clearance violations | Move component inward in yaml, re-run |
| Freerouting hangs | Kill, retry with `-mp 5` |
| Components overlap after placement | Increase spacing in yaml positions |
| "Board outline malformed" | Ensure `place_pcb.py` ran (draws Edge.Cuts) |
