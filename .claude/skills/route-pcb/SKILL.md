---
name: route-pcb
description: Autoroute a KiCad PCB using Freerouting, then visual review loop for placement and DRC cleanup.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
---

# Route PCB via Freerouting

Autoroute a KiCad PCB board using Freerouting's headless CLI, then iterate on placement and DRC.

## Prerequisites

- `cad/*.kicad_pcb` must exist with footprints placed (from schematic import)
- `java` available (OpenJDK 21+)
- `~/tools/freerouting.jar` — download if missing:
  ```bash
  mkdir -p ~/tools && curl -L -o ~/tools/freerouting.jar \
    "https://github.com/freerouting/freerouting/releases/download/v2.0.1/freerouting-2.0.1.jar"
  ```

## Phase 1: Component Placement

Before routing, components must be placed sensibly. If footprints are piled in a corner:

1. Open in pcbnew: `uv run poe inspect-asm`
2. Place components following these rules:
   - Power input components near one board edge
   - Main IC (CM4 connector) centered — it's the hub
   - Decoupling caps adjacent to their IC power pins
   - Connectors/headers on board edges
   - Signal flow: power enters one side, signals fan out
3. Draw board outline on Edge.Cuts layer (100x80mm rectangle)
4. Save the `.kicad_pcb`

If placement is already done, skip to Phase 2.

## Phase 2: Autoroute

Run the full pipeline programmatically:

```bash
# 1. Export DSN from KiCad
python3 -c "
import pcbnew
board = pcbnew.LoadBoard('cad/cm4_carrier.kicad_pcb')
pcbnew.ExportSpecctraDSN(board, '/tmp/cm4_carrier.dsn')
print('DSN exported')
"

# 2. Run Freerouting headless (single-threaded to avoid DRC violations)
java -jar ~/tools/freerouting.jar \
  -de /tmp/cm4_carrier.dsn \
  -do /tmp/cm4_carrier.ses \
  -mp 20 -mt 1 2>&1

# 3. Import routed session back into KiCad
python3 -c "
import pcbnew
board = pcbnew.LoadBoard('cad/cm4_carrier.kicad_pcb')
pcbnew.ImportSpecctraSES(board, '/tmp/cm4_carrier.ses')
board.Save('cad/cm4_carrier.kicad_pcb')
print('SES imported and board saved')
"
```

**IMPORTANT flags:**
- `-mt 1` — single thread. Multi-threaded optimization is broken and generates clearance violations
- `-mp 20` — max 20 routing passes (usually completes in 1-3)

## Phase 3: DRC Validation

```bash
uv run poe validate-asm
```

Check the DRC report:
```bash
cat cm4_carrier-drc.rpt
```

**Expected results:**
- `0 unconnected pads` — all nets routed
- Board outline violation is OK if Edge.Cuts not drawn yet
- Clearance violations need manual fixes in pcbnew

## Phase 4: Visual Review + Cleanup (max 5 iterations)

1. Open board: `uv run poe inspect-asm`
2. Inspect for:
   - Traces crossing unnecessarily (reroute shorter path)
   - Missing ground pour (Add zone → GND net → draw rectangle → press B to fill)
   - Power traces too thin (5V should be 0.5-1mm width, signals 0.25mm)
   - Components too close to board edge
   - Silkscreen overlapping pads
3. If issues found: fix in pcbnew, save, re-run DRC
4. If clean: proceed to final export

## Phase 5: Final Export

```bash
uv run poe generate-asm
```

This produces gerbers, drill files, BOM, CPL, STEP, and PCB SVG.

## Ground Pour Checklist

After routing, add ground pour on both layers:
1. Select copper zone tool (right toolbar)
2. Set net to GND
3. Draw rectangle around entire board on F.Cu
4. Repeat on B.Cu
5. Press `B` to fill zones
6. Re-run DRC

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Freerouting leaves unrouted nets | Try `-us hybrid` strategy, or route remaining manually |
| Clearance violations after import | Use `-mt 1` (multi-thread is broken). If persists, fix manually |
| "Board outline malformed" DRC | Draw rectangle on Edge.Cuts layer in pcbnew |
| Freerouting hangs | Kill and retry with fewer passes (`-mp 5`) |
| Power nets routed as thin traces | Exclude from autoroute (`-inc GND,+5V`), route manually with wider traces |
