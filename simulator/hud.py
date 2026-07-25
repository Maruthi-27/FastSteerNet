# hud.py — Dashboard overlay
import pygame
import math


def draw_hud(surf, font, font_sm, car, steering, throttle, brake, auto, W, H):
    """Draw all HUD elements onto surf."""

    # ── Semi-transparent bottom panel ────────────────────────────
    panel_h = 115
    panel   = pygame.Surface((W, panel_h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 170))
    surf.blit(panel, (0, H - panel_h))

    # ── Steering wheel ────────────────────────────────────────────
    cx, cy = W // 2, H - 58
    # Outer ring
    pygame.draw.circle(surf, (55, 55, 55),   (cx, cy), 42)
    pygame.draw.circle(surf, (210, 210, 210),(cx, cy), 42, 3)
    # Hub
    pygame.draw.circle(surf, (100, 100, 100),(cx, cy), 12)
    # Needle
    angle = math.radians(steering * -115)    # ±115° range
    nx = int(cx + 36 * math.sin(angle))
    ny = int(cy - 36 * math.cos(angle))
    pygame.draw.line(surf, (255, 215, 0), (cx, cy), (nx, ny), 5)
    pygame.draw.circle(surf, (255, 215, 0),  (nx, ny), 4)

    # ── Speed dial ────────────────────────────────────────────────
    sdx, sdy = W - 80, H - 60
    spd_kmh  = car.speed_kmh
    pct      = min(spd_kmh / 120.0, 1.0)
    # dial background
    pygame.draw.circle(surf, (35, 35, 35),   (sdx, sdy), 48)
    pygame.draw.circle(surf, (200, 200, 200),(sdx, sdy), 48, 2)
    # arc ticks
    for t in range(0, 11):
        a   = math.radians(-130 + t * 26)
        r0, r1 = 35, 44
        pygame.draw.line(surf, (150,150,150),
                         (int(sdx + r0*math.cos(a)), int(sdy + r0*math.sin(a))),
                         (int(sdx + r1*math.cos(a)), int(sdy + r1*math.sin(a))), 1)
    # needle
    spd_ang = math.radians(-130 + pct * 260)
    ex = int(sdx + 38 * math.cos(spd_ang))
    ey = int(sdy + 38 * math.sin(spd_ang))
    pygame.draw.line(surf, (255, 60, 60), (sdx, sdy), (ex, ey), 3)
    # text
    spd_lbl = font.render(f"{spd_kmh:.0f}", True, (255, 255, 255))
    surf.blit(spd_lbl, spd_lbl.get_rect(center=(sdx, sdy - 2)))
    kmh_lbl = font_sm.render("km/h", True, (160, 160, 160))
    surf.blit(kmh_lbl, kmh_lbl.get_rect(center=(sdx, sdy + 16)))

    # ── Throttle / Brake bars ─────────────────────────────────────
    bx = 18
    for label, val, col, by in [
        ("THR", throttle, (0, 200, 80),  H - 105),
        ("BRK", brake,    (210, 40, 40), H -  75),
    ]:
        lbl_s = font_sm.render(label, True, (180, 180, 180))
        surf.blit(lbl_s, (bx, by - 14))
        pygame.draw.rect(surf, (50, 50, 50),   (bx, by, 130, 13), border_radius=4)
        if val > 0:
            pygame.draw.rect(surf, col, (bx, by, int(130 * val), 13), border_radius=4)

    # ── Mode badge ────────────────────────────────────────────────
    mode_col  = (0, 210, 255) if auto else (255, 170, 0)
    mode_text = "AUTO" if auto else "MANUAL"
    badge_bg  = pygame.Surface((90, 24), pygame.SRCALPHA)
    badge_bg.fill((*mode_col, 40))
    surf.blit(badge_bg, (14, H - panel_h + 6))
    pygame.draw.rect(surf, mode_col, (14, H - panel_h + 6, 90, 24), 1, border_radius=3)
    badge_lbl = font.render(mode_text, True, mode_col)
    surf.blit(badge_lbl, badge_lbl.get_rect(center=(59, H - panel_h + 18)))

    # ── Steer value ───────────────────────────────────────────────
    steer_txt = font_sm.render(f"Steer  {steering:+.3f}", True, (220, 220, 220))
    surf.blit(steer_txt, steer_txt.get_rect(center=(W // 2, H - panel_h + 14)))

    # ── Keyboard hint (top-left) ──────────────────────────────────
    hint = font_sm.render("A=Auto   M=Manual   WASD=Drive   Q=Quit", True, (130, 130, 130))
    surf.blit(hint, (10, 8))


def draw_model_inset(surf, font_sm, frame_rgb, W, H):
    """Show the model's camera input as a small inset (top-right)."""
    import numpy as np
    import cv2
    import pygame

    small      = cv2.resize(frame_rgb, (160, 80))
    s          = pygame.surfarray.make_surface(np.transpose(small, (1, 0, 2)))
    ix, iy     = W - 172, 28
    surf.blit(s, (ix, iy))
    pygame.draw.rect(surf, (0, 240, 100), (ix, iy, 160, 80), 2)
    lbl = font_sm.render("Model Input  320×160", True, (0, 240, 100))
    surf.blit(lbl, (ix, iy + 82))