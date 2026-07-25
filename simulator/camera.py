# camera.py — Capture the rendered road view for model inference
# The model was trained on 160x320 RGB images (YUV after preprocessing).
# We grab the full road surface and resize to match.

import numpy as np
import cv2
import pygame

CAM_W = 320
CAM_H = 160


def capture_frame(surface):
    """
    Capture the pygame surface as a numpy RGB array (160, 320, 3).
    This is what gets passed to model.preprocess().
    """
    raw  = pygame.surfarray.array3d(surface)      # shape: (W, H, 3)
    raw  = np.transpose(raw, (1, 0, 2))            # → (H, W, 3)
    view = cv2.resize(raw, (CAM_W, CAM_H),
                      interpolation=cv2.INTER_AREA)
    return view   # RGB numpy array