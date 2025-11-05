# Brain Art - Development Documentation

**For developers and contributors**

---

## 📐 System Architecture

### Data Flow

```
┌──────────┐    BLE     ┌──────────┐    LSL     ┌──────────┐
│ Muse S   │ ────────▶  │ OpenMuse │ ────────▶  │ Python   │
│ Athena   │            │  stream  │            │   App    │
└──────────┘            └──────────┘            └──────────┘
                                                      │
                        ┌─────────────────────────────┤
                        │                             │
                   ┌────▼────┐                  ┌────▼────┐
                   │   EEG   │                  │  Brain  │
                   │Processor│                  │  Viz    │
                   └────┬────┘                  └────┬────┘
                        │                             │
                        └─────────────┬───────────────┘
                                      │
                                  ┌───▼───┐
                                  │Display│
                                  └───────┘
```

### Modules

#### 1. `muse_connector.py` - Data Acquisition

**Responsibilities:**
- Connection to Muse S via LSL
- EEG streaming (256 Hz, 4 channels)
- Signal quality monitoring

**API:**
```python
connector = MuseConnector(mode='lsl', enable_motion=True)
connector.connect()

# Get data
data = connector.get_eeg_data(duration=1.0)  # ndarray [samples, channels]
quality = connector.get_signal_quality()     # list [n_channels] (0-100%)

connector.disconnect()
```

**Implementation:**
- Uses `mne_lsl.lsl` (StreamInlet)
- Fallback to `pylsl` if mne_lsl unavailable
- Dynamic data retrieval (duration parameter in `get_eeg_data()`)
- Timeout: 5s on connect
- Signal quality monitoring via `SignalQualityChecker`
- Motion data (ACC/GYRO) handling via `get_motion_data()`

#### 2. `eeg_processor.py` - Signal Processing

**Responsibilities:**
- FFT and frequency power analysis
- Notch filtering (50Hz/60Hz - power line interference)
- Calibration (baseline)
- Metrics computation (attention, relaxation)

**API:**
```python
processor = EEGProcessor()  # Parameters from config.py (SAMPLE_RATE, WINDOW_SIZE)

# Add data
processor.add_data(eeg_array)  # [samples, 4] - uses only first 4 channels

# Calibration
# NOTE: In main.py calibration is performed manually, does not use processor.calibrate()
# In main.py: collects data for config.CALIBRATION_TIME seconds, then sets baseline
processor.baseline = powers.copy()  # Manual baseline setting
processor.is_calibrated = True

# Processing
powers = processor.compute_band_powers()  # dict {band: power} - averaged across channels
powers_per_ch = processor.compute_band_powers_per_channel()  # dict {band: [ch0, ch1, ch2, ch3]}
attention = processor.compute_attention()      # float 0-1
relaxation = processor.compute_relaxation()    # float 0-1
```

**Implementation:**
- **Frequency bands (computed):**
  - Delta: 1-4 Hz (deep sleep) - **computed, but not used for visualization**
  - Theta: 4-8 Hz (meditation, drowsiness) - **used in relaxation (20%)**
  - Alpha: 8-13 Hz (relaxation) - **main indicator for relaxation (80%)**
  - Beta: 13-30 Hz (attention) - **main indicator for attention (70%)**
  - Gamma: 30-44 Hz (processing) - **used in attention (30%)**

- **Note:** The program computes all 5 bands, but uses **only 4 bands** (alpha, beta, gamma, theta) for visualization. Delta is computed and available in `band_powers`, but is not used in attention/relaxation metrics.
  
- **Metrics (used for visualization):**
  - `attention = 0.7 * (beta / beta_baseline) + 0.3 * (gamma / gamma_baseline)`
    - Uses: **beta (70%) + gamma (30%)**
    - Normalization relative to baseline, clip to [0, 2], scaling to [0, 1]
  - `relaxation = 0.8 * (alpha / alpha_baseline) + 0.2 * (theta / theta_baseline)`
    - Uses: **alpha (80%) + theta (20%)**
    - Normalization relative to baseline, clip to [0, 2], scaling to [0, 1]
  - Smoothing: rolling average (5 samples in `metric_history`)

- **Signal processing:**
  - Detrend (trend removal)
  - Notch filter 50Hz/60Hz (power line interference) - `scipy.signal.iirnotch`
  - Hanning window (smoothing before FFT)
  - FFT (Fast Fourier Transform) - direct frequency analysis
  - **NOTE:** Butterworth filters are created in `_create_filters()`, but are not used in `compute_band_powers()` - FFT is used directly

#### 3. `brain_visualizer.py` - Visualization

**Responsibilities:**
- Particle system
- 3 modes: Alpha, Beta, Mixed
- Rendering (pygame)
- HUD/info

**API:**
```python
viz = BrainVisualizer()  # Parameters from config.py (WINDOW_WIDTH, WINDOW_HEIGHT, FULLSCREEN)

# Set metrics
viz.set_metrics(attention=0.75, relaxation=0.5, motion_metrics=None)  # motion_metrics optional

# Change mode
viz.set_mode('mixed')  # 'alpha', 'beta', 'mixed'

# Render frame
viz.run_frame()  # One frame @ TARGET_FPS (default 30 FPS from config)

# Screenshot
viz.save_screenshot()

# Cleanup
viz.close()
```

**Implementation:**

- **Particle System:**
  ```python
  class Particle:
      position: (x, y)
      velocity: (vx, vy)
      color: (r, g, b)
      size: float
      lifetime: float  # seconds
  ```

- **Spawning:**
  - Rate depends on attention/relaxation
  - Position: random (beta mode) or center (alpha)
  - Color: from palette appropriate for mode
  - Size: 8-40 px

- **Rendering:**
  - Fade effect: alpha blend
  - Draw particles: pygame.draw.circle (with cache for performance)
  - Particle cache: pre-rendered surfaces for better FPS
  - HUD: FPS, metrics, mode, motion status
  - Auto-optimization: adjustment of MAX_PARTICLES and FPS target based on actual FPS

- **Motion Effects (optional):**
  - Head tilt affects particle direction (95% influence with strong tilt)
  - Motion intensity affects particle count (if `MOTION_INTENSITY_SCALING=True` in config, default: False)
  - Gestures: nod (change mode), shake (clear screen)

#### 4. `main.py` - Main Application

**Flow:**
```python
1. Setup
   - Connect to Muse (MuseConnector)
   - Initialize EEG processor (EEGProcessor)
   - Initialize motion processor (MotionProcessor, optional)
   - Initialize performance optimizer (PerformanceOptimizer, optional)
   - Initialize brain visualizer (BrainVisualizer)
   - Initialize EEG monitor (EEGVisualizer, optional)

2. Calibration
   - Collect data for config.CALIBRATION_TIME seconds (default 5s)
   - Display instructions and progress
   - Manually set baseline: processor.baseline = powers.copy()
   - Set processor.is_calibrated = True
   # NOTE: Does NOT use processor.calibrate() - collects data manually

3. Main Loop
   while running:
       # Motion data (every 100ms - more frequent than EEG)
       if motion_enabled:
           - Get motion data (ACC/GYRO)
           - Add to motion_processor
           - Detect gestures (nod → cycle_mode, shake → clear_screen)
       
       # EEG data (every UPDATE_INTERVAL ms, default 500ms = 2Hz)
       if time_to_update_eeg:
           - Get EEG data
           - Process (async in thread if optimizer enabled)
           - Compute band powers, attention, relaxation
           - Update brain visualizer
           - Update EEG monitor (if enabled)
       
       # Render
       - Render visualization frame
       - Update EEG monitor plots (if in same process)
       - Handle events (keyboard, mouse)

4. Cleanup
   - Disconnect Muse
   - Close visualizers
   - Cleanup optimizer (threads, processes)
```

#### 5. `motion_processor.py` - Motion Processing

**Responsibilities:**
- Processing ACC/GYRO data from Muse S
- Gesture detection (nod, shake)
- Head tilt detection
- Motion metrics computation

**API:**
```python
processor = MotionProcessor(sample_rate=52)  # 52 Hz for ACC/GYRO

# Add data
processor.add_data(acc_data, gyro_data)  # acc: [X, Y, Z] g, gyro: [X, Y, Z] deg/s

# Gesture detection
if processor.detect_nod():      # Head nod (forward-down)
    # Change visualization mode
if processor.detect_shake():    # Head shake (left-right)
    # Clear screen

# Head tilt
tilt_lr, tilt_fb = processor.get_head_tilt()  # -1 to 1

# Metrics
metrics = processor.get_metrics()  # dict with tilt, motion_intensity, etc.
```

**Implementation:**
- **Gesture detection:**
  - Nod: large change in ACC X (threshold: 0.8g, test: 1.4g)
  - Shake: fast rotation GYRO Z (threshold: 150°/s, test: 245°/s)
  - Cooldown: 1.5s between gestures

- **Head tilt:**
  - Tilt left-right: ACC Y (roll)
  - Tilt forward-backward: ACC X (pitch)
  - Used to modify particle direction

- **Motion metrics:**
  - `motion_intensity`: 0-1 (based on std dev ACC/GYRO)
  - `tilt_left_right`: -1 (left) to +1 (right)
  - `tilt_forward_backward`: -1 (forward) to +1 (backward)

#### 6. `eeg_visualizer.py` - EEG Monitor

**Responsibilities:**
- EEG signal visualization in separate window
- Topomaps (topographic activity maps)
- Raw EEG traces (optional)
- Power spectrogram

**API:**
```python
# Factory function
viz = create_eeg_visualizer(use_advanced=True, buffer_duration=5.0)

# Setup
viz.setup_window()

# Update data
viz.update_data(eeg_data, band_powers, band_powers_per_channel)

# Render (in main loop)
viz.update_plots()

# Cleanup
viz.close()
```

**Implementation:**
- Uses matplotlib (TkAgg backend)
- Requires MNE for topomaps (fallback: SimpleEEGVisualizer)
- Can run in separate process (`EEGVisualizerProcess`) for better FPS
- Per-channel band powers for more accurate topomaps

#### 7. `performance_optimizer.py` - Performance Optimization

**Responsibilities:**
- Multithreading for EEG computations
- Multiprocessing for EEG monitor
- GPU acceleration
- Cache management

**API:**
```python
optimizer = PerformanceOptimizer(processor=eeg_processor)

# Async processing
optimizer.process_eeg_async(eeg_data)

# Get results (non-blocking)
results = optimizer.get_eeg_results()  # dict or None
if results:
    band_powers = results['band_powers']
    attention = results['attention']
    relaxation = results['relaxation']

# Cleanup
optimizer.cleanup()
```

**Implementation:**
- `EEGComputeThread`: separate thread for FFT computations (doesn't block main loop)
- `EEGVisualizerProcess`: separate process for EEG monitor (significant FPS boost)
- Thread pools and process pools for parallel computations

#### 8. `signal_quality.py` - Signal Quality Assessment

**Responsibilities:**
- EEG signal quality assessment
- Per-channel and overall metrics
- Artifact and interference detection

**API:**
```python
checker = SignalQualityChecker(sample_rate=256)

# Assessment
result = checker.assess_quality(eeg_data)  # dict with metrics, warnings, etc.
# result['overall_quality']: 0-100
# result['channel_quality']: [0-100] per channel
# result['warnings']: list of warnings

# Quick check (for main loop)
quality = quick_quality_check(eeg_data)  # 0-100
```

**Implementation:**
- **Metrics:**
  - Variance (signal variance)
  - Amplitude (peak-to-peak amplitude)
  - Alpha power (alpha wave presence)
  - Line noise (50Hz/60Hz interference)
  - Artifacts (kurtosis, gradient analysis)
  - Stationarity (signal stability)

- **Weights:**
  - Variance: 30%
  - Amplitude: 20%
  - Alpha power: 15%
  - Line noise: 15%
  - Artifacts: 15%
  - Stationarity: 5%

#### 9. `config.py` - Configuration

**Sections:**
```python
# Muse Connection
CONNECTION_MODE = 'lsl'  # 'lsl' (recommended) or 'bluetooth'
MUSE_ADDRESS = '00:55:DA:B9:FB:2C'  # MAC address (for Bluetooth mode)
MUSE_NAME = 'Muse-S'  # Device name (for muselsl stream)

# EEG Processing
SAMPLE_RATE = 256
WINDOW_SIZE = 64
CALIBRATION_TIME = 5

# Visualization
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FULLSCREEN = False
TARGET_FPS = 30  # Default target FPS
UPDATE_INTERVAL = 500  # ms - how often to update EEG data (2 Hz)

# Particles
PARTICLE_LIFETIME = 2.0
PARTICLE_SIZE_MIN = 8
PARTICLE_SIZE_MAX = 40
PARTICLE_SPEED_MIN = 30
PARTICLE_SPEED_MAX = 100
MAX_PARTICLES = 150  # Default (auto-optimized based on FPS)

# Colors
COLOR_PALETTES = {...}

# Debug
DEBUG = True
SHOW_FPS = True
SHOW_SIGNAL_QUALITY = True
SHOW_EEG_MONITOR = False  # Auto-open EEG monitor window
EEG_MONITOR_SHOW_RAW_TRACES = False  # Show raw traces in monitor
DEBUG_MOTION = False  # Show detailed motion data

# Motion Features
ENABLE_MOTION = True  # Enable motion features (requires preset with ACC/GYRO)
MOTION_GESTURE_CONTROL = True  # Gestures: nod (change mode), shake (clear)
MOTION_TILT_EFFECTS = True  # Head tilt affects particle direction
MOTION_INTENSITY_SCALING = False  # Motion intensity affects particle count
```

---

## 🔬 Algorithms

### FFT (Fast Fourier Transform)

**Goal:** Transform time-domain signal → frequency-domain

```python
from scipy.fft import fft, fftfreq

# Input: signal [256 samples]
n = len(signal)
fft_vals = fft(signal)
fft_freqs = fftfreq(n, 1/sample_rate)

# Only positive frequencies
pos_mask = fft_freqs > 0
freqs = fft_freqs[pos_mask]

# Power spectrum (normalized by N)
power_spectrum = (np.abs(fft_vals[pos_mask]) / n) ** 2

# Power in band [f1, f2]
band_mask = (freqs >= f1) & (freqs <= f2)
power = np.mean(power_spectrum[band_mask])
```

### Normalization

**Goal:** Relative changes vs baseline

```python
# During calibration (in main.py)
powers = processor.compute_band_powers()
processor.baseline = powers.copy()  # Set baseline

# During use
normalized_power = current_power / baseline_power  # Relative normalization

# For attention/relaxation metrics:
# 1. Normalization relative to baseline
beta_norm = beta / beta_baseline
gamma_norm = gamma / gamma_baseline

# 2. Weighted combination
attention_value = 0.7 * beta_norm + 0.3 * gamma_norm

# 3. Clip to [0, 2] and scale to [0, 1]
attention_value = np.clip(attention_value, 0, 2) / 2.0

# 4. Smoothing (rolling average)
metric_history['attention'].append(attention_value)
attention_smooth = np.mean(metric_history['attention'])
```

### Smoothing

**Goal:** Noise reduction, smooth changes

```python
from collections import deque

history = deque(maxlen=5)  # Rolling window
history.append(new_value)
smoothed = np.mean(history)
```

---

## ⚙️ Parameters and Tuning

### Performance

**If FPS < 30:**
```python
WINDOW_SIZE = 64           # ↓ Faster FFT
UPDATE_INTERVAL = 500      # ↑ Less frequent EEG
MAX_PARTICLES = 300        # ↓ Fewer particles
PARTICLE_LIFETIME = 1.0    # ↓ Shorter lifetime
```

**If CPU > 80%:**
- Increase `UPDATE_INTERVAL`
- Decrease `MAX_PARTICLES`
- Disable `DEBUG`

### Responsiveness

**If response too slow:**
```python
# eeg_processor.py
self.metric_history = {
    'attention': deque(maxlen=2),    # was 5
    'relaxation': deque(maxlen=2),
}
```

**If too fast (unstable):**
```python
maxlen=10  # More smoothing
```

### Visual Density

**Too few particles:**
```python
MAX_PARTICLES = 1000
PARTICLE_LIFETIME = 3.0
PARTICLE_SIZE_MAX = 50
```

**Too many:**
```python
MAX_PARTICLES = 200
PARTICLE_LIFETIME = 0.5
```

---

## 🚀 Extensions

### 1. EEG Data Recording

```python
# In main.py
import csv

csv_file = open('eeg_recording.csv', 'w', newline='')
writer = csv.writer(csv_file)
writer.writerow(['time', 'TP9', 'AF7', 'AF8', 'TP10', 'attention', 'relaxation'])

# In main loop
writer.writerow([time.time(), *eeg_data[-1], attention, relaxation])

# Cleanup
csv_file.close()
```

### 2. Recorded Data Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load
df = pd.read_csv('eeg_recording.csv')

# Plot
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# EEG
df.plot(x='time', y=['TP9', 'AF7', 'AF8', 'TP10'], ax=axes[0])
axes[0].set_title('Raw EEG')

# Metrics
df.plot(x='time', y=['attention', 'relaxation'], ax=axes[1])
axes[1].set_title('Computed Metrics')

plt.tight_layout()
plt.show()
```

### 3. Music from EEG

```python
import numpy as np
import pygame.mixer

pygame.mixer.init(frequency=22050, size=-16, channels=1)

def generate_tone(frequency, duration, volume):
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples)
    wave = np.sin(2 * np.pi * frequency * t) * volume
    wave = (wave * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(wave)

# In main loop
freq = 200 + attention * 400  # 200-600 Hz
volume = relaxation * 0.5
tone = generate_tone(freq, 0.1, volume)
tone.play()
```

### 4. OSC to Tablet

```python
from pythonosc import udp_client

# Setup
osc_client = udp_client.SimpleUDPClient("192.168.1.100", 5005)

# In loop
osc_client.send_message("/brain/attention", attention)
osc_client.send_message("/brain/relaxation", relaxation)
osc_client.send_message("/brain/alpha", alpha_power)
osc_client.send_message("/brain/beta", beta_power)
```

**On tablet (TouchOSC/Processing):**
```processing
import oscP5.*;

OscP5 osc;

void setup() {
  osc = new OscP5(this, 5005);
}

void oscEvent(OscMessage msg) {
  if (msg.checkAddrPattern("/brain/attention")) {
    float attention = msg.get(0).floatValue();
    // Draw something...
  }
}
```

### 5. Custom Visualizations

**Lines instead of particles:**
```python
# In brain_visualizer.py
def _draw_lines(self):
    if random.random() < 0.1:
        start = (random.randint(0, self.width), 0)
        end = (random.randint(0, self.width), self.height)
        color = self._get_color_for_mode()
        thickness = int(5 + self.attention * 10)
        pygame.draw.line(self.canvas, color, start, end, thickness)
```

**Fractals:**
```python
def draw_fractal_tree(surface, x, y, angle, length, attention):
    if length < 5:
        return

    end_x = x + length * np.cos(np.radians(angle))
    end_y = y + length * np.sin(np.radians(angle))

    color = (255 * attention, 100, 255 * (1 - attention))
    pygame.draw.line(surface, color, (x, y), (end_x, end_y), 2)

    draw_fractal_tree(surface, end_x, end_y, angle - 20, length * 0.7, attention)
    draw_fractal_tree(surface, end_x, end_y, angle + 20, length * 0.7, attention)
```

### 6. Multiplayer (2 Muse)

```python
# Two connectors
muse1 = MuseConnector(address='00:55:DA:B9:FB:2C')
muse2 = MuseConnector(address='00:55:DA:B9:XX:XX')

# Two processors
proc1 = EEGProcessor()
proc2 = EEGProcessor()

# In loop
att1 = proc1.compute_attention()
att2 = proc2.compute_attention()

# Modes:
# 1. Cooperation: avg_attention = (att1 + att2) / 2
# 2. Competition: winner = "P1" if att1 > att2 else "P2"
# 3. Duel: each controls half of the screen
```

---

## 🧪 Testing

### Running Tests

All tests are located in the `tests/` directory. Run them individually:

```bash
# Comprehensive system test (recommended first)
python tests/test_system.py

# EEG monitor functionality test
python tests/test_eeg_visualizer.py

# Performance optimization tests
python tests/test_performance.py

# Motion gesture tests (requires active OpenMuse stream)
python tests/gestures/test_motion.py
python tests/gestures/test_motion_axes.py
python tests/gestures/test_tilt.py
```

### Test Suites

- **test_system.py**: Comprehensive component test with synthetic data
  - Tests all main modules (MuseConnector, EEGProcessor, BrainVisualizer)
  - Verifies imports and dependencies
  - Optional OpenMuse connection test
  - Does not require device (uses synthetic data)

- **test_eeg_visualizer.py**: EEG monitor window functionality test
  - Tests standalone EEG visualizer
  - Verifies visualization components

- **test_performance.py**: Performance optimization tests
  - CPU information
  - Threading and multiprocessing
  - Pygame FPS tests
  - Configuration recommendations

- **gestures/** - Motion feature tests:
  - `test_motion.py`: Gesture detection tests (nod, shake)
  - `test_motion_axes.py`: Accelerometer/gyroscope axis identification
  - `test_tilt.py`: Head tilt detection tests
  - **Note**: Require active OpenMuse stream with motion data (preset p20, p21, p1041)

- **debug_channels.py**: LSL stream analysis and channel inspection
  - Displays available LSL streams
  - Shows channel names and their order
  - Useful for troubleshooting connection issues

### Unit Tests

Example unit test structure:

```python
# test_eeg_processor.py
import unittest
import numpy as np
from eeg_processor import EEGProcessor

class TestEEGProcessor(unittest.TestCase):
    def setUp(self):
        self.proc = EEGProcessor()

    def test_add_data(self):
        data = np.random.randn(256, 4)
        self.proc.add_data(data)
        self.assertEqual(self.proc.buffer.shape[0], 256)

    def test_compute_band_powers(self):
        # Simulate alpha wave (10 Hz)
        t = np.linspace(0, 1, 256)
        signal = np.sin(2 * np.pi * 10 * t)
        data = np.tile(signal, (4, 1)).T

        self.proc.add_data(data)
        powers = self.proc.compute_band_powers()

        # Alpha should be dominant
        self.assertGreater(powers['alpha'], powers['beta'])
```

### Integration Tests

```bash
# test_system.py (already exists)
python tests/test_system.py
```

### Manual Testing Checklist

- [ ] Connection to Muse
- [ ] Signal quality > 70%
- [ ] Calibration (5s default)
- [ ] Close eyes → more alpha → warm colors
- [ ] Open eyes + counting → more beta → bright colors
- [ ] Motion gestures work (nod → mode change, shake → clear)
- [ ] Head tilt affects particle direction
- [ ] EEG monitor works (if enabled)
- [ ] Screenshots save correctly
- [ ] FPS > 30 (or adjusted to PERFORMANCE_MODE)
- [ ] No memory leaks (long session)

---

## 📊 Metrics and Monitoring

### Performance Metrics

```python
# In main.py
import time

frame_times = []

while running:
    start = time.time()

    # ... main loop ...

    frame_time = time.time() - start
    frame_times.append(frame_time)

    if len(frame_times) > 100:
        avg_fps = 1.0 / np.mean(frame_times)
        print(f"Avg FPS: {avg_fps:.1f}")
        frame_times = []
```

### Signal Quality Monitoring

```python
# In muse_connector.py
from src.signal_quality import SignalQualityChecker

# Initialization
self.quality_checker = SignalQualityChecker(sample_rate=256)

# Quality update (in _update_signal_quality)
quality_result = self.quality_checker.assess_quality(eeg_data)
self.signal_quality = quality_result['channel_quality']  # [0-100] per channel
self.overall_quality = quality_result['overall_quality']  # 0-100
self.quality_warnings = quality_result['warnings']  # List of warnings

# Get quality
quality_list = connector.get_signal_quality()  # [0-100] per channel
overall = connector.get_overall_quality()  # 0-100
warnings = connector.get_quality_warnings()  # List of strings
```

**Quality metrics:**
- Variance: 30% (signal variance)
- Amplitude: 20% (peak-to-peak)
- Alpha power: 15% (alpha wave presence)
- Line noise: 15% (50Hz/60Hz interference)
- Artifacts: 15% (movements, blinking)
- Stationarity: 5% (stability)

---

## 🐛 Debugging

### Enable Debug Mode

```python
# config.py
DEBUG = True
SHOW_FPS = True
SHOW_SIGNAL_QUALITY = True
LOG_LEVEL = 'DEBUG'
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('brain_art.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.debug("This is a debug message")
```

### Common Issues

**FFT errors:**
```python
# Check window size
assert len(signal) == WINDOW_SIZE
# Check for NaN
assert not np.any(np.isnan(signal))
```

**LSL connection:**
```python
# Test resolve
from mne_lsl.lsl import resolve_streams
streams = resolve_streams(timeout=5)
print(f"Found {len(streams)} streams")
```

---

## 📚 Resources

### Documentation
- **OpenMuse:** https://github.com/DominiqueMakowski/OpenMuse
- **MNE-LSL:** https://mne.tools/mne-lsl/
- **Pygame:** https://www.pygame.org/docs/
- **SciPy Signal:** https://docs.scipy.org/doc/scipy/reference/signal.html

### Scientific
- **EEG Bands:** https://en.wikipedia.org/wiki/Electroencephalography
- **BCI:** https://www.frontiersin.org/journals/human-neuroscience
- **FFT:** https://en.wikipedia.org/wiki/Fast_Fourier_transform

### Inspirations
- NeuroSky MindWave
- InteraXon Muse Apps
- BCI Art Projects

