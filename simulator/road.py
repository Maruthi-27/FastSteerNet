import pygame
import math

# ── Palette (matches Udacity track colours) ───────────────────────
SKY_TOP      = ( 95, 140, 200)
SKY_BOT      = (180, 210, 235)
HILL_DARK    = ( 50,  80,  42)
HILL_MID     = ( 70, 110,  48)
GRASS_A      = ( 48, 128,  48)
GRASS_B      = ( 38, 112,  38)
ROAD_A       = ( 92,  92,  92)
ROAD_B       = ( 80,  80,  80)
CURB_WHITE   = (240, 240, 240)
CURB_RED     = (200,  30,  30)
LANE_WHITE   = (255, 255, 255)
TREE_TRUNK   = ( 90,  55,  25)
TREE_LEAF_A  = ( 32, 115,  42)
TREE_LEAF_B  = ( 20,  85,  30)
MOUNTAIN     = ( 90, 110,  80)

SEGMENTS_PER_COLOR = 4


# ── Track definition ──────────────────────────────────────────────
class Segment:
    def __init__(self, idx, curve=0.0, hill=0.0, tree_l=False, tree_r=False):
        self.idx    = idx
        self.curve  = curve
        self.hill   = hill
        self.tree_l = tree_l
        self.tree_r = tree_r


def build_track():
    segs = []

    def add(n, curve=0.0, hill=0.0, trees=False):
        for i in range(n):
            tl = trees and (i % 8 == 0)
            tr = trees and (i % 8 == 4)
            segs.append(Segment(len(segs), curve, hill, tl, tr))

    add(80)
    add(50,  curve= 2.0, trees=True)
    add(40,  curve=-2.0, trees=True)
    add(80,  trees=True)
    add(40,  curve= 3.2, hill= 0.5, trees=True)
    add(40,  curve=-3.2, hill=-0.5, trees=True)
    add(60,  hill= 0.7,  trees=True)
    add(40,  hill=-0.7,  trees=True)
    add(80,  trees=True)
    add(50,  curve= 2.5, trees=True)
    add(50,  curve=-2.5, trees=True)
    add(60)
    return segs


TRACK     = build_track()
TRACK_LEN = len(TRACK)

# Road half-width in pixels at depth=1
ROAD_W_PX = 420
DRAW_DIST = 220        # segments ahead to render
HORIZON_F = 0.40       # horizon fraction of screen height (lower = more road)


# ── Main renderer ─────────────────────────────────────────────────
class RoadRenderer:
    def __init__(self, width=800, height=600):
        self.W   = width
        self.H   = height
        self.HZ  = int(height * HORIZON_F)
        self._sky = self._make_sky()

    # ── Pre-built sky gradient ────────────────────────────────────
    def _make_sky(self):
        sky = pygame.Surface((self.W, self.HZ))
        for y in range(self.HZ):
            t = y / max(self.HZ - 1, 1)
            c = tuple(int(SKY_TOP[i] * (1-t) + SKY_BOT[i] * t) for i in range(3))
            pygame.draw.line(sky, c, (0, y), (self.W, y))
        return sky

    @staticmethod
    def _quad(surf, color, x1, y1, w1, x2, y2, w2):
        y1, y2 = int(y1), int(y2)
        if y1 == y2 or (w1 == 0 and w2 == 0):
            return
        pts = [(x1-w1, y1), (x1+w1, y1), (x2+w2, y2), (x2-w2, y2)]
        pygame.draw.polygon(surf, color, pts)

    def _tree(self, surf, cx, cy, scale):
        th = int(90 * scale)
        tw = int(32 * scale)
        if th < 5 or tw < 2:
            return
        pygame.draw.rect(surf, TREE_TRUNK,
                         (cx - tw//5, cy - th, tw//2, th//2 + 2))
        pygame.draw.circle(surf, TREE_LEAF_B, (cx,           cy - th),           tw)
        pygame.draw.circle(surf, TREE_LEAF_A, (cx,           cy - th - tw//3),   int(tw * 0.80))
        pygame.draw.circle(surf, TREE_LEAF_A, (cx - tw//3,   cy - th + tw//5),   int(tw * 0.60))
        pygame.draw.circle(surf, TREE_LEAF_A, (cx + tw//3,   cy - th + tw//5),   int(tw * 0.60))

    def render(self, surf, position, steering=0.0):
        W, H, HZ = self.W, self.H, self.HZ

        # ── Sky ───────────────────────────────────────────────────
        surf.blit(self._sky, (0, 0))

        # ── Mountain silhouette ───────────────────────────────────
        pts_mt = [(0, HZ)]
        for mx in range(0, W + 1, 14):
            mh = int(22 * math.sin(mx * 0.009 + position * 0.004)
                     + 14 * math.sin(mx * 0.021 + position * 0.006 + 1.0))
            pts_mt.append((mx, HZ - 28 - mh))
        pts_mt.append((W, HZ))
        pygame.draw.polygon(surf, MOUNTAIN, pts_mt)

        # ── Rolling hills ─────────────────────────────────────────
        for color, amp1, freq1, amp2, freq2, phase, offset in [
            (HILL_DARK, 16, 0.014, 8,  0.030, 0.0,  0),
            (HILL_MID,   9, 0.019, 5,  0.038, 0.8, -5),
        ]:
            pts = [(0, HZ)]
            for hx in range(0, W + 1, 12):
                hy = (HZ + offset
                      - int(amp1 * math.sin(hx * freq1 + position * 0.018 + phase))
                      - int(amp2 * math.sin(hx * freq2 + position * 0.012)))
                pts.append((hx, hy))
            pts.append((W, HZ))
            pygame.draw.polygon(surf, color, pts)

        # ── Ground base (overdrawn by road strips below) ──────────
        pygame.draw.rect(surf, GRASS_A, (0, HZ, W, H - HZ))

        # ── Project all segments ──────────────────────────────────
        #
        # THE FIX:  sy = HZ + (H - HZ) / depth
        #
        #   depth = i  where  i=1 → nearest (sy ≈ H, bottom of screen)
        #                     i=DRAW_DIST → farthest (sy ≈ HZ, horizon)
        #
        # Previously: sy = horizon + y_off * scale * H * 0.1
        # That made every flat segment land exactly on the horizon line!
        #
        base  = int(position) % TRACK_LEN
        x_off = 0.0
        y_off = 0.0

        projected = []   # (sx, sy, rw, road_scale, idx, seg)

        for i in range(DRAW_DIST, 0, -1):
            idx  = (base + i) % TRACK_LEN
            seg  = TRACK[idx]

            depth = float(i)

            # Core projection
            sy         = HZ + (H - HZ) / depth
            rw         = ROAD_W_PX / depth
            # Steer shifts vanishing point (camera lean into the curve)
            steer_px   = steering * 55.0 * (1.0 - depth / DRAW_DIST)
            sx         = W / 2.0 - x_off + steer_px
            # Hill displaces sy vertically
            sy        += y_off / (depth + 1e-6) * H * 0.10

            road_scale = 1.0 / depth

            projected.append((sx, sy, rw, road_scale, idx, seg))

            # Accumulate curve & hill offsets
            # Far segments bend very little; near ones bend more
            x_off += seg.curve * (DRAW_DIST / depth) ** 0.50 * 0.09
            y_off += seg.hill  * 0.14

        # Draw back-to-front (index 0 = farthest)
        for k in range(len(projected) - 1):
            sx2, sy2, rw2, sc2, idx2, seg2 = projected[k]       # far
            sx1, sy1, rw1, sc1, idx1, seg1 = projected[k + 1]   # near

            # Skip strips above the horizon
            if sy1 < HZ and sy2 < HZ:
                continue
            sy1c = max(sy1, float(HZ))
            sy2c = max(sy2, float(HZ))

            alt    = (idx1 // SEGMENTS_PER_COLOR) % 2
            grass_c = GRASS_A   if alt else GRASS_B
            road_c  = ROAD_A    if alt else ROAD_B
            curb_c  = CURB_WHITE if alt else CURB_RED

            # Grass strip (full width)
            y_top = min(sy1c, sy2c)
            y_bot = max(sy1c, sy2c)
            if y_bot > y_top:
                pygame.draw.rect(surf, grass_c,
                                 (0, int(y_top), W, int(y_bot - y_top) + 1))

            # Outer curb
            self._quad(surf, curb_c,
                       sx1, sy1c, rw1 * 1.24,
                       sx2, sy2c, rw2 * 1.24)

            # Road surface
            self._quad(surf, road_c,
                       sx1, sy1c, rw1,
                       sx2, sy2c, rw2)

            # White edge lines (draw thin lane over road, then road inside it)
            self._quad(surf, LANE_WHITE,
                       sx1, sy1c, rw1 * 1.02,
                       sx2, sy2c, rw2 * 1.02)
            self._quad(surf, road_c,
                       sx1, sy1c, rw1 * 0.975,
                       sx2, sy2c, rw2 * 0.975)

            # Dashed centre line (every other alt block)
            if alt:
                self._quad(surf, LANE_WHITE,
                           sx1, sy1c, rw1 * 0.028,
                           sx2, sy2c, rw2 * 0.028)

            # Trees
            if rw1 > 8:
                if seg1.tree_r:
                    self._tree(surf,
                               int(sx1 + rw1 * 1.65), int(sy1c),
                               max(0.08, sc1 * 48))
                if seg1.tree_l:
                    self._tree(surf,
                               int(sx1 - rw1 * 1.65), int(sy1c),
                               max(0.08, sc1 * 48))

        # ── Car sprite ────────────────────────────────────────────
        self._draw_car(surf, steering)

    def _draw_car(self, surf, steering):
        W, H = self.W, self.H
        cx   = W // 2 + int(steering * 22)
        cy   = H - 58
        cw, ch = 130, 72

        # Drop shadow
        shadow = pygame.Surface((cw - 10, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), (0, 0, cw - 10, 20))
        surf.blit(shadow, (cx - (cw - 10)//2, cy + ch//2 - 8))

        body = pygame.Surface((cw, ch), pygame.SRCALPHA)

        # Main body
        pygame.draw.rect(body, (28, 28, 34),
                         (8, 22, cw - 16, ch - 28), border_radius=12)
        # Roof
        pygame.draw.polygon(body, (22, 22, 28),
                            [(26, 22), (cw-26, 22), (cw-16, 8), (16, 8)])
        # Windshield
        pygame.draw.polygon(body, (140, 195, 228, 200),
                            [(28, 21), (cw-28, 21), (cw-20, 9), (20, 9)])
        # Rear window
        pygame.draw.polygon(body, (100, 150, 195, 170),
                            [(18, 22), (36, 9), (cw-36, 9), (cw-18, 22)])
        # Wheels
        for wx, wy, ww, wh in [
            (5,  34, 24, 16), (cw-29, 34, 24, 16),
            (5,  50, 24, 14), (cw-29, 50, 24, 14),
        ]:
            pygame.draw.ellipse(body, (12, 12, 12),    (wx,   wy,   ww,   wh))
            pygame.draw.ellipse(body, (55, 55, 60),    (wx+3, wy+3, ww-6, wh-6))
            pygame.draw.ellipse(body, (120, 120, 125), (wx+6, wy+5, ww-12, wh-10))
        # Headlights
        for lx in [14, cw - 32]:
            pygame.draw.ellipse(body, (255, 245, 190), (lx,   ch-18, 18, 10))
            pygame.draw.ellipse(body, (255, 255, 230), (lx+3, ch-16, 12,  6))
        # Tail lights
        for lx in [12, cw - 28]:
            pygame.draw.ellipse(body, (180, 15,  15),  (lx,   ch-12, 14,  7))
            pygame.draw.ellipse(body, (220, 50,  50),  (lx+2, ch-11,  8,  4))
        # Hood line
        pygame.draw.line(body, (40, 40, 48), (12, 22), (cw - 12, 22), 1)

        surf.blit(body, (cx - cw//2, cy - ch//2))