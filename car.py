# car.py — Car state and physics

class Car:
    def __init__(self):
        self.position  = 0.0    # track scroll position (segment units)
        self.speed     = 0.0    # current speed
        self.max_speed = 6.0
        self.steering  = 0.0   # smoothed steering output (-1..+1)

        # Smoothing factors
        self._steer_smooth = 0.25   # lower = more smoothing (range 0..1)
        self._speed_smooth = 0.15

        # Target values set by controller
        self._target_steer    = 0.0
        self._target_throttle = 0.0
        self._target_brake    = 0.0

    def set_controls(self, steering, throttle, brake):
        """Feed raw control inputs; car physics will smooth them."""
        self._target_steer    = max(-1.0, min(1.0, float(steering)))
        self._target_throttle = max(0.0,  min(1.0, float(throttle)))
        self._target_brake    = max(0.0,  min(1.0, float(brake)))

    def update(self, dt=1.0):
        """Step physics forward."""
        α = self._steer_smooth
        self.steering = self.steering * (1 - α) + self._target_steer * α

        accel = self._target_throttle * 0.28
        decel = self._target_brake    * 0.55
        self.speed += accel * dt
        self.speed -= decel * dt
        self.speed *= (1.0 - 0.04 * dt)          # rolling friction
        self.speed  = max(0.0, min(self.speed, self.max_speed))

        self.position += self.speed * 0.5 * dt

    @property
    def speed_kmh(self):
        return self.speed * 25.0