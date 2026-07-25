# track.py — Track layout definition
# All segment data lives here so road.py stays clean.

def build_track():
    """
    Returns a list of segment dicts:
        curve : lateral curvature  (+right, -left)
        hill  : vertical change    (+up, -down)
    """
    segs = []

    def add(n, curve=0.0, hill=0.0):
        for _ in range(n):
            segs.append({'curve': curve, 'hill': hill, 'idx': len(segs)})

    # ── Layout ────────────────────────────────────────────────────
    add(100)                        # long straight start
    add(40,  curve= 1.8)            # gentle right
    add(40,  curve=-1.8)            # gentle left
    add(60)                         # straight
    add(30,  curve= 3.2)            # sharp right
    add(20)
    add(30,  curve=-3.2)            # sharp left
    add(50,  hill= 0.6)             # uphill
    add(30,  hill=-0.6)             # downhill
    add(80)                         # long straight
    add(35,  curve= 2.5)
    add(35,  curve=-2.5)
    add(60)
    add(25,  curve= 1.2,  hill=0.4)
    add(25,  curve=-1.2,  hill=-0.4)
    add(80)
    # ── Track repeats seamlessly ──────────────────────────────────
    return segs


TRACK  = build_track()
N_SEGS = len(TRACK)