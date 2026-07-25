# model.py — Load TorchScript model and run inference
# Includes EMA smoothing on steering so the car doesn't oscillate.

import torch
import numpy as np
import cv2


class SteerModel:
    def __init__(self, model_path, device='cpu'):
        self.device = torch.device(device)
        self.model  = torch.jit.load(model_path, map_location=self.device)
        self.model.eval()
        print(f"✅ Model loaded: {model_path}")

        # Exponential moving average for steering smoothness
        self._ema_steer    = 0.0
        self._ema_throttle = 0.35
        self._ema_brake    = 0.0
        self._alpha        = 0.30   # smoothing factor (lower = smoother)

    # ── Preprocessing (matches training pipeline exactly) ─────────
    def preprocess(self, frame_rgb):
        """
        frame_rgb : numpy (160, 320, 3) uint8  RGB
        Returns   : torch tensor (1, 3, 66, 200) on self.device
        """
        img = frame_rgb.copy()
        # Crop sky (top 55px) and hood (bottom 20px) from 160-tall image
        img = img[55 : img.shape[0] - 20, :]
        img = cv2.resize(img, (200, 66))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
        img = img.astype(np.float32) / 255.0
        tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)
        return tensor.to(self.device)

    def _curve_features(self):
        """Dummy curve features — zeros when no Hough detection available."""
        return torch.zeros(1, 6, device=self.device)

    # ── Inference ─────────────────────────────────────────────────
    def predict(self, frame_rgb):
        """
        Returns smoothed (steering, throttle, brake) floats.
        steering : -1.0 (full left) .. +1.0 (full right)
        throttle :  0.0 .. 1.0
        brake    :  0.0 .. 1.0
        """
        with torch.no_grad():
            img   = self.preprocess(frame_rgb)
            curve = self._curve_features()

            # Try two-input model first (image + curve features)
            try:
                out = self.model(img, curve)
            except Exception:
                out = self.model(img)

            # Unpack output — could be tuple or single tensor
            if isinstance(out, (tuple, list)):
                raw_steer    = float(out[0].squeeze())
                raw_throttle = float(out[1].squeeze()) if len(out) > 1 else 0.35
                raw_brake    = float(out[2].squeeze()) if len(out) > 2 else 0.0
            else:
                raw_steer    = float(out[0, 0])
                raw_throttle = float(out[0, 1]) if out.shape[1] > 1 else 0.35
                raw_brake    = float(out[0, 2]) if out.shape[1] > 2 else 0.0

        # Clamp raw outputs
        raw_steer    = max(-1.0, min(1.0,  raw_steer))
        raw_throttle = max(0.0,  min(1.0,  raw_throttle))
        raw_brake    = max(0.0,  min(1.0,  raw_brake))

        # EMA smoothing
        a = self._alpha
        self._ema_steer    = self._ema_steer    * (1 - a) + raw_steer    * a
        self._ema_throttle = self._ema_throttle * (1 - a) + raw_throttle * a
        self._ema_brake    = self._ema_brake    * (1 - a) + raw_brake    * a

        # Clamp final outputs
        steer    = max(-1.0, min(1.0,  self._ema_steer))
        throttle = max(0.18, min(0.70, self._ema_throttle))
        brake    = max(0.0,  min(1.0,  self._ema_brake))

        return steer, throttle, brake