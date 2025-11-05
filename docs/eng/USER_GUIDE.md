# Brain Art - User Guide

**Basic application usage**

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `SPACE` | Clear screen |
| `1` | Alpha mode (relaxation) |
| `2` | Beta mode (attention) |
| `3` | Mixed mode |
| `S` | Screenshot |
| `Q` | Check signal quality |
| `M` | Toggle motion features (on/off) |
| `ESC` | Exit |

---

## 🎨 Visualization Modes

### Mode 1: Alpha (Relaxation)

**How to achieve:**
- Close eyes
- Deep, slow breathing
- Don't think about anything specific
- Imagine a peaceful place

**Visual effect:**
- Warm colors: violet → indigo → blue
- Large, slow particles
- Center of screen
- Calm, meditative effect

### Mode 2: Beta (Attention)

**How to achieve:**
- Open eyes
- Focus (counting, reading)
- Active thinking
- React to stimuli

**Visual effect:**
- Bright colors: red → orange → yellow
- Small, fast particles
- Full screen
- Dynamic, energetic effect

### Mode 3: Mixed

**Visual effect:**
- Pastel: magenta, cyan, white
- Medium particles
- Most spectacular!
- Combination of both modes

---

## 🎮 Motion Features (Optional)

**New feature - interactive effects based on head movement!**

### What is it?

Motion features use **accelerometer and gyroscope** from Muse S Athena to detect movement and head gestures that affect visualization in real-time.

### Requirements

- `ENABLE_MOTION = True` in `config.py` (enabled by default)
- OpenMuse stream with preset containing ACC/GYRO:
  - ✅ `p20` (recommended - EEG4 + ACC/GYRO, saves battery)
  - ✅ `p1041` (all sensors, high consumption)

### How it works?

#### 1. **Head gestures**
- **Nod** (forward-down-forward) → **Changes visualization mode** (Alpha/Beta/Mixed)
- **Shake** (left-right-left) → **Clears screen**

#### 2. **Head tilt affects particle direction**
- Tilt head **left** → particles flow left
- Tilt **right** → particles right
- Tilt **forward/backward** → particles forward/backward

#### 3. **Movement intensity affects particle count**
- More movement = more particles (0.5x - 2.0x)
- Stillness → fewer particles (flow state)

### Controls

| Action | Effect |
|--------|--------|
| Key `M` | Toggle motion features (on/off) |
| Nod | Change mode (Alpha → Beta → Mixed → Alpha...) |
| Shake | Clear screen |
| Tilt head | Particle direction |
| Head movement | More particles |

### Configuration

In `config.py`:

```python
# === MOTION FEATURES ===
ENABLE_MOTION = True              # Enable/disable motion features
MOTION_GESTURE_CONTROL = True     # Gestures (nod, shake)
MOTION_TILT_EFFECTS = True        # Tilt affects visualization
MOTION_INTENSITY_SCALING = False  # Movement intensity → particle count (disabled by default)
```

### Tips

- **Best effects:** Light head movements during visualization
- **Flow state:** Sit still → visualization based only on EEG
- **Disable motion:** If you want only EEG, press `M` or set `ENABLE_MOTION = False`
- **Battery saving:** Use `p20` instead of `p1041` (longer battery life!)

---

## ⚙️ Configuration

### File `config.py` - Main Settings

**EEG:**
```python
SAMPLE_RATE = 256          # Hz (don't change - Muse S spec)
WINDOW_SIZE = 64           # Samples for FFT (64/128/256)
CALIBRATION_TIME = 10      # Calibration seconds
```

**Visualization:**
```python
WINDOW_WIDTH = 1280        # Resolution
WINDOW_HEIGHT = 720
FULLSCREEN = False         # True for production
TARGET_FPS = 30            # Target FPS
UPDATE_INTERVAL = 500      # ms between EEG updates
```

**Particles:**
```python
PARTICLE_LIFETIME = 2.0    # How long they live (seconds)
PARTICLE_SIZE_MIN = 8      # Minimum size
PARTICLE_SIZE_MAX = 40     # Maximum size
MAX_PARTICLES = 150        # Limit on screen
```

**Debug:**
```python
DEBUG = True               # False for production
SHOW_FPS = True            # Show FPS
SHOW_SIGNAL_QUALITY = True # Show signal quality
```

### Custom Colors

In `config.py` change palettes:
```python
COLOR_PALETTES = {
    'alpha': [
        (138, 43, 226),   # Violet
        (75, 0, 130),     # Indigo
        (0, 0, 255),      # Blue
        (0, 128, 128),    # Teal
    ],
    'beta': [
        (255, 0, 0),      # Red
        (255, 165, 0),    # Orange
        (255, 255, 0),    # Yellow
        (0, 255, 0),      # Green
    ],
    'mixed': [
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Cyan
        (255, 255, 255),  # White
        (255, 192, 203),  # Pink
    ],
}
```

---

## 🔧 Performance Tuning

### Application Runs Slowly (< 30 FPS)

**Edit `config.py`:**
```python
# Reduce load:
WINDOW_SIZE = 64          # Faster FFT
UPDATE_INTERVAL = 500     # Less frequent EEG processing
MAX_PARTICLES = 300       # Fewer particles
PARTICLE_LIFETIME = 1.0   # Shorter lifetime
TARGET_FPS = 60           # Target FPS
```

Or close other applications.

### Too Few Particles on Screen

**Edit `config.py`:**
```python
MAX_PARTICLES = 1000        # More
PARTICLE_LIFETIME = 3.0     # Longer lifetime
PARTICLE_SIZE_MAX = 50      # Larger
```

### Too Many Particles

```python
MAX_PARTICLES = 200         # Fewer
PARTICLE_LIFETIME = 0.5     # Shorter lifetime
```

### No Reaction to State Changes

**Causes:**
1. Poor calibration
2. Poor signal quality
3. Too much smoothing

**Solution:**
```bash
# 1. Restart application
# 2. During calibration REALLY be calm
# 3. Check signal quality (wet sensors!)
```

In `eeg_processor.py` you can change smoothing:
```python
self.metric_history = {
    'attention': deque(maxlen=2),     # was 5
    'relaxation': deque(maxlen=2),    # was 5
}
```

---

## 📊 Result Interpretation

### Frequency Bands

| Band | Hz | State | Brain Art |
|------|-----|-------|-----------|
| **Delta** | 1-4 | Deep sleep | Not used |
| **Theta** | 4-8 | Meditation, drowsiness | Small influence |
| **Alpha** | 8-13 | **Relaxation** | **Main indicator** |
| **Beta** | 13-30 | **Attention** | **Main indicator** |
| **Gamma** | 30-44 | Processing | Additional |

## 🔗 More Information

- **Installation:** See [INSTALLATION.md](INSTALLATION.md)
- **Battery saving:** See [BATTERY_SAVING.md](BATTERY_SAVING.md)

