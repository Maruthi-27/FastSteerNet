# main.py — FastSteerNet Self-Driving Simulator
# Run: python main.py
# Controls: A=Auto  M=Manual  W/S/A/D=Drive  Q=Quit

import pygame
import sys
import os

from road   import RoadRenderer
from car    import Car
from model  import SteerModel
from camera import capture_frame
from hud    import draw_hud, draw_model_inset

# ── Config ────────────────────────────────────────────────────────
MODEL_PATH   = 'faststeernet_torchscript.pt'
WIN_W, WIN_H = 800, 600
FPS          = 30
# ─────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption('FastSteerNet — Self Driving Simulator')
    clock    = pygame.time.Clock()
    font     = pygame.font.SysFont('monospace', 15, bold=True)
    font_sm  = pygame.font.SysFont('monospace', 12)

    renderer = RoadRenderer(WIN_W, WIN_H)
    car      = Car()

    # ── Check model file exists ────────────────────────────────────
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model file not found: {MODEL_PATH}")
        print(f"   Make sure faststeernet_torchscript.pt is in: {os.getcwd()}")
        pygame.quit()
        sys.exit(1)

    model      = SteerModel(MODEL_PATH, device='cpu')
    auto_drive = True

    # Control state
    steering = 0.0
    throttle = 0.35
    brake    = 0.0

    # Manual key steering accumulator (self-centering)
    manual_steer = 0.0

    print("=" * 52)
    print("  FastSteerNet Self-Driving Simulator  v2")
    print("=" * 52)
    print("  A = AUTO mode  (model drives)")
    print("  M = MANUAL mode  (WASD keys)")
    print("  W = throttle   S = brake")
    print("  A/D = steer left/right  (manual only)")
    print("  Q = quit")
    print("=" * 52)

    while True:
        dt = clock.tick(FPS) / 33.0    # normalised so 30 FPS = 1.0

        # ── Events ────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_a and not auto_drive:
                    # Only switch via 'a' key when in manual (avoid conflict with steer-left)
                    pass
                if event.key == pygame.K_F1:
                    auto_drive = True
                    model._ema_steer    = 0.0
                    model._ema_throttle = 0.35
                    print("🤖 AUTO — model is driving")
                if event.key == pygame.K_F2:
                    auto_drive = False
                    manual_steer = 0.0
                    print("🕹  MANUAL — WASD to drive")

        # Simpler toggle keys that don't conflict with WASD
        keys = pygame.key.get_pressed()
        if keys[pygame.K_F1]:
            auto_drive = True
        if keys[pygame.K_F2]:
            auto_drive = False

        # ── Control inputs ────────────────────────────────────────
        if auto_drive:
            # Capture road view and run model
            frame = capture_frame(screen)
            try:
                steering, throttle, brake = model.predict(frame)
            except Exception as e:
                print(f"⚠️  Model error: {e}")
                steering, throttle, brake = 0.0, 0.3, 0.0
        else:
            # Manual WASD
            if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
                manual_steer -= 0.06 * dt
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                manual_steer += 0.06 * dt
            else:
                manual_steer *= 0.80    # self-centre

            manual_steer = max(-1.0, min(1.0, manual_steer))
            steering     = manual_steer
            throttle     = 0.55 if (keys[pygame.K_UP]   or keys[pygame.K_w]) else 0.0
            brake        = 0.70 if (keys[pygame.K_DOWN]  or keys[pygame.K_s]) else 0.0

            if throttle == 0.0 and brake == 0.0:
                throttle = 0.15   # idle creep

        # ── Update car ────────────────────────────────────────────
        car.set_controls(steering, throttle, brake)
        car.update(dt)

        # ── Render road ───────────────────────────────────────────
        renderer.render(screen, car.position, car.steering)

        # ── Capture frame for model inset ─────────────────────────
        model_frame = capture_frame(screen)

        # ── HUD ───────────────────────────────────────────────────
        draw_hud(screen, font, font_sm,
                 car, car.steering, throttle, brake,
                 auto_drive, WIN_W, WIN_H)
        draw_model_inset(screen, font_sm, model_frame, WIN_W, WIN_H)

        pygame.display.flip()


if __name__ == '__main__':
    main()