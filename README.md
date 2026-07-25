# FastSteerNet Self-Driving Simulator

## Overview

FastSteerNet is a Python-based self-driving car simulator built with Pygame. The simulator supports both autonomous and manual driving modes and uses a TorchScript steering model for auto driving.

## Repository Structure

- `main.py` — simulator entry point and main loop
- `car.py` — vehicle physics, steering, throttle, and brake logic
- `road.py` — track rendering and road generation
- `camera.py` — capture simulator frames for model input
- `model.py` — TorchScript model wrapper and prediction logic
- `hud.py` — heads-up display rendering
- `track.py` — track layout and update utilities
- `training/DL_Project.ipynb` — training notebook for model development
- `Faststeernet.mp4` — demo video file

## Requirements

- Python 3.8 or newer
- `pygame`
- `torch`

## Setup

1. Create a virtual environment:
   ```powershell
   python -m venv venv
   ```
2. Activate the environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install pygame torch
   ```
4. Place the pretrained model file `faststeernet_torchscript.pt` in the project root.

## Run the simulator

```powershell
python main.py
```

## Controls

- `F1` — switch to auto mode
- `F2` — switch to manual mode
- `W` / `S` — throttle / brake
- `A` / `D` — steer left / right in manual mode
- `Q` — quit the simulator

## Demo video

<video controls width="720">
  <source src="Faststeernet.mp4" type="video/mp4">
  Your browser does not support HTML5 video.
</video>

[Download the demo video](Faststeernet.mp4)

## Notes

- The pretrained model file is not included in this repository.
- The model file must be placed in the project root before running `main.py`.
- The training notebook is located at `training/DL_Project.ipynb`.
