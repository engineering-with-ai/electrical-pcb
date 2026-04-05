"""Place PCB footprints from layout_spec.yaml pcb_placement config.

Uses pcbnew Python API to position footprints and draw board outline.
Usage: python3 cad/drawing/place_pcb.py
"""

import sys
from pathlib import Path

import pcbnew
import yaml

LAYOUT_SPEC = Path("cad/layout_spec.yaml")
PCB_PATH = Path("cad/cm4_carrier.kicad_pcb")


def place_footprints() -> None:
    """Place all footprints per pcb_placement config and draw board outline."""
    spec = yaml.safe_load(LAYOUT_SPEC.read_text())
    placement = spec["pcb_placement"]
    ox, oy = placement["board_origin"]
    bw, bh = placement["board_size"]

    board = pcbnew.LoadBoard(str(PCB_PATH))

    # Reason: place each component at its configured position
    placed = 0
    for block_name, block in placement["blocks"].items():
        for ref, (x, y, rot) in block["components"].items():
            fp = board.FindFootprintByReference(ref)
            if fp is None:
                print(f"WARNING: {ref} not found on board")
                continue
            fp.SetPosition(
                pcbnew.VECTOR2I(pcbnew.FromMM(ox + x), pcbnew.FromMM(oy + y))
            )
            fp.SetOrientationDegrees(rot)
            placed += 1

    # Reason: draw board outline on Edge.Cuts if not present
    has_outline = any(
        s.GetLayer() == pcbnew.Edge_Cuts for s in board.GetDrawings()
    )
    if not has_outline:
        _draw_outline(board, ox, oy, bw, bh)
        print(f"Drew {bw}x{bh}mm board outline")

    board.Save(str(PCB_PATH))
    print(f"Placed {placed} footprints, saved {PCB_PATH}")


def _draw_outline(board, ox: float, oy: float, w: float, h: float) -> None:
    """Draw rectangular board outline on Edge.Cuts layer."""
    corners = [
        ((ox, oy), (ox + w, oy)),
        ((ox + w, oy), (ox + w, oy + h)),
        ((ox + w, oy + h), (ox, oy + h)),
        ((ox, oy + h), (ox, oy)),
    ]
    for (x1, y1), (x2, y2) in corners:
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.1))
        board.Add(seg)


if __name__ == "__main__":
    place_footprints()
