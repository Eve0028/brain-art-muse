"""
Muse S Accelerometer and Gyroscope Data Processing.

Gesture detection and interactive effects.
"""

from collections import deque
from typing import Optional, Tuple, Dict, Deque
import time

import numpy as np


class MotionProcessor:
    """
    Processes ACC/GYRO data into gestures and visual effects.
    """

    def __init__(self, sample_rate: int = 52) -> None:
        """
        Initialize motion processor.

        :param sample_rate: ACC/GYRO sampling frequency (52 Hz for Muse S)
        """
        self.sample_rate = sample_rate

        # Data buffers (last 2 seconds)
        buffer_size = sample_rate * 2
        self.acc_buffer: Deque[np.ndarray] = deque(maxlen=buffer_size)
        self.gyro_buffer: Deque[np.ndarray] = deque(maxlen=buffer_size)
        self.time_buffer: Deque[float] = deque(maxlen=buffer_size)

        # Current values
        self.current_acc = np.zeros(3)   # [X, Y, Z]
        self.current_gyro = np.zeros(3)  # [X, Y, Z]

        # Gesture detection
        self.last_nod_time: float = 0.0
        self.last_shake_time: float = 0.0
        self.last_tilt_time: float = 0.0

        # Gesture parameters (thresholds) - tuned based on test_motion_axes.py
        self.nod_threshold = 0.8      # g - nod in ACC X (test showed 1.4g)
        self.shake_threshold = 150    # deg/s - shake in GYRO Z (test: 245°/s)
        self.tilt_threshold = 0.3     # g - head tilt

        # Cooldown between gestures (seconds)
        self.gesture_cooldown = 1.5  # Increased to avoid false detections

        # Motion metrics
        self.motion_intensity = 0.0   # 0-1
        self.is_still = True          # Whether user is still

    def add_data(self, acc_data: np.ndarray, gyro_data: np.ndarray, timestamp: Optional[float] = None) -> None:
        """
        Add new ACC/GYRO data.

        :param acc_data: [X, Y, Z] acceleration in g
        :param gyro_data: [X, Y, Z] angular velocity in deg/s
        :param timestamp: Timestamp (optional)
        """
        if timestamp is None:
            timestamp = time.time()

        # Add to buffers
        self.acc_buffer.append(acc_data)
        self.gyro_buffer.append(gyro_data)
        self.time_buffer.append(timestamp)

        # Update current values
        self.current_acc = np.array(acc_data)
        self.current_gyro = np.array(gyro_data)

        # Compute motion metrics
        self._update_motion_metrics()

    def _update_motion_metrics(self) -> None:
        """
        Update motion metrics (intensity, whether still).
        """
        if len(self.acc_buffer) < 10:
            return

        # Last 0.5s of data
        window_size = min(int(self.sample_rate * 0.5), len(self.acc_buffer))
        recent_acc = np.array(list(self.acc_buffer)[-window_size:])
        recent_gyro = np.array(list(self.gyro_buffer)[-window_size:])

        # Motion intensity = standard deviation of acceleration + angular velocity
        acc_std = np.std(recent_acc, axis=0).mean()
        gyro_std = np.std(recent_gyro, axis=0).mean()

        # Normalize to 0-1
        self.motion_intensity = np.clip((acc_std / 0.5 + gyro_std / 50) / 2, 0, 1)

        # Still if intensity < 0.1
        self.is_still = self.motion_intensity < 0.1

    def get_head_tilt(self) -> Tuple[float, float]:
        """
        Return head tilt.

        :return: (tilt_lr, tilt_fb) tuple:
                 - tilt_lr: Left-right tilt (-1 = left, +1 = right)
                 - tilt_fb: Forward-backward tilt (-1 = forward, +1 = backward)
        """
        if len(self.acc_buffer) == 0:
            return (0.0, 0.0)

        # Use gravity (acceleration) to determine orientation
        current_acc = self.current_acc

        # Left-right tilt (Roll) - Y axis (not X!)
        # INVERTED SIGN (no minus) - test showed it was reversed
        tilt_lr = np.clip(current_acc[1], -1, 1)

        # Forward-backward tilt (Pitch) - X axis (not Y!)
        # INVERTED SIGN (with minus) - test showed it was reversed
        tilt_fb = np.clip(-current_acc[0], -1, 1)

        return (tilt_lr, tilt_fb)

    def detect_nod(self) -> bool:
        """
        Detect head nod (YES) - bow forward.

        Movement: front → down → front.

        :return: True if nod detected
        """
        current_time = time.time()

        # Cooldown
        if current_time - self.last_nod_time < self.gesture_cooldown:
            return False

        if len(self.acc_buffer) < int(self.sample_rate * 0.5):  # Minimum 0.5s data
            return False

        # FIXED: Check last 0.8 seconds of data
        window_size = int(self.sample_rate * 0.8)
        window = np.array(list(self.acc_buffer)[-window_size:])
        acc_x = window[:, 0]  # X axis (front-back)

        # Check range of motion in X axis
        x_max = np.max(acc_x)
        x_min = np.min(acc_x)
        x_range = x_max - x_min

        # Nod: large change in X axis (test showed 1.4g)
        # Threshold 0.6g should catch most nods
        if x_range > self.nod_threshold:
            # Check if there was movement (extremum is in middle of interval, not at ends)
            min_idx = np.argmin(acc_x)
            max_idx = np.argmax(acc_x)
            # Extremum should be between 20%-80% of window
            if (0.2 * window_size < min_idx < 0.8 * window_size) or \
               (0.2 * window_size < max_idx < 0.8 * window_size):
                self.last_nod_time = current_time
                return True

        return False

    def detect_shake(self) -> bool:
        """
        Detect head shake (NO).

        Movement: left-right-left quickly.

        :return: True if shake detected
        """
        current_time = time.time()

        # Cooldown
        if current_time - self.last_shake_time < self.gesture_cooldown:
            return False

        if len(self.gyro_buffer) < self.sample_rate:
            return False

        # Check angular velocity around Z axis (head rotation)
        window = np.array(list(self.gyro_buffer)[-self.sample_rate:])
        angular_velocity_z = window[:, 2]

        # Maximum angular velocity
        max_speed = np.max(np.abs(angular_velocity_z))

        # Shake: very fast rotation
        if max_speed > self.shake_threshold:
            # Check if there were oscillations (left-right-left)
            zero_crossings = np.sum(np.diff(np.sign(angular_velocity_z)) != 0)

            # At least 2 direction changes within a second
            if zero_crossings >= 2:
                self.last_shake_time = current_time
                return True

        return False

    def detect_tilt_change(self) -> Optional[str]:
        """
        Detect significant head tilt change.

        :return: 'left', 'right', 'forward', 'backward' or None
        """
        current_time = time.time()

        # Cooldown
        if current_time - self.last_tilt_time < 0.5:  # Shorter cooldown
            return None

        tilt_lr, tilt_fb = self.get_head_tilt()

        # Detect significant tilt
        if abs(tilt_lr) > self.tilt_threshold:
            self.last_tilt_time = current_time
            return 'left' if tilt_lr < 0 else 'right'

        if abs(tilt_fb) > self.tilt_threshold:
            self.last_tilt_time = current_time
            return 'forward' if tilt_fb > 0 else 'backward'

        return None

    def get_motion_intensity(self) -> float:
        """
        Return motion intensity (0-1).

        Can be used to modify visualization intensity.

        :return: Motion intensity 0-1
        """
        return self.motion_intensity

    def is_user_still(self) -> bool:
        """
        Check if user is still (flow state).

        :return: True if user is still
        """
        return self.is_still

    def get_rotation_speed(self) -> float:
        """
        Return head rotation speed (deg/s).

        Can be used to rotate visual effects.

        :return: Rotation speed in deg/s
        """
        if len(self.gyro_buffer) == 0:
            return 0.0

        # Sum of angular velocities (magnitude)
        current_gyro = self.current_gyro
        return float(np.linalg.norm(current_gyro).item())

    def get_metrics(self) -> Dict:
        """
        Return all motion metrics.

        :return: Dictionary with metrics
        """
        tilt_lr, tilt_fb = self.get_head_tilt()

        return {
            'tilt_left_right': tilt_lr,
            'tilt_forward_backward': tilt_fb,
            'motion_intensity': self.motion_intensity,
            'is_still': self.is_still,
            'rotation_speed': self.get_rotation_speed(),
            'acc': self.current_acc.tolist(),
            'gyro': self.current_gyro.tolist(),
        }

    def reset(self) -> None:
        """
        Reset buffers.
        """
        self.acc_buffer.clear()
        self.gyro_buffer.clear()
        self.time_buffer.clear()
        self.current_acc = np.zeros(3)
        self.current_gyro = np.zeros(3)


if __name__ == "__main__":
    print("=== Test MotionProcessor ===\n")

    processor = MotionProcessor()

    # Simulate a head nod
    print("📊 Test 1: Head nod simulation...")
    for i in range(52):  # 1 sec @ 52 Hz
        t = i / 52
        # Nod: Y changes from 0 → -1 → 0 → 1 → 0
        acc_y = np.sin(t * 4 * np.pi) * 1.5
        acc = np.array([0.0, acc_y, 1.0])
        gyro = np.array([0.0, 0.0, 0.0])

        processor.add_data(acc, gyro)

        if processor.detect_nod():
            print("  ✅ Head nod detected!")

    # Simulate a head shake
    print("\n📊 Test 2: Head shake simulation...")
    processor.reset()
    for i in range(52):
        t = i / 52
        # Shake: Z oscillates quickly
        gyro_z = np.sin(t * 8 * np.pi) * 200
        acc = np.array([0.0, 0.0, 1.0])
        gyro = np.array([0.0, 0.0, gyro_z])

        processor.add_data(acc, gyro)

        if processor.detect_shake():
            print("  ✅ Head shake detected!")

    # Test head tilt
    print("\n📊 Test 3: Head tilt...")
    processor.reset()

    # Left
    processor.add_data(np.array([-0.5, 0.0, 1.0]), np.zeros(3))
    tilt = processor.detect_tilt_change()
    if tilt:
        print(f"  ✅ Head tilt detected: {tilt}")

    # Right
    processor.add_data(np.array([0.5, 0.0, 1.0]), np.zeros(3))
    time.sleep(0.6)  # Cooldown
    tilt = processor.detect_tilt_change()
    if tilt:
        print(f"  ✅ Head tilt detected: {tilt}")

    print("\n✅ Test completed!")
