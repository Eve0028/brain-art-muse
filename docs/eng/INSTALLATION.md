# Installation and Setup - Brain Art

## 📋 Requirements

**Hardware:**
- Muse S Athena
- Laptop with Windows 11 (built-in Bluetooth is sufficient)
- Optional: USB dongle BLED112 (backup)

**Software:**
- Python 3.12 (tested only on this version)
- ~200 MB disk space

---

## 🔧 Step-by-Step Installation

### 1. Check Python

```bash
python --version
```

If you don't have Python 3.12:
- Download from https://www.python.org/downloads/

### 2. (Optional) Create Virtual Environment

**Recommended:** Use venv to isolate project dependencies:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

After activation, the prompt should show `(venv)`.

**Deactivation:**
```bash
deactivate
```

### 3. Install Dependencies

**Option A: Editable install:**

```bash
cd Brain_Art
pip install -e .
```

This installs the package in editable mode (code changes are immediately visible) and all dependencies:
- **OpenMuse** - dedicated support for Muse S Athena
- **MNE-LSL** - Lab Streaming Layer
- **pygame, numpy, scipy** - visualization and processing

**Option B: Production install (non-editable):**

```bash
cd Brain_Art
pip install .
```

This installs the package normally (copies to site-packages) - imports work the same from any directory, but code changes require reinstallation.

**Option C: Traditional install (dependencies only):**

```bash
cd Brain_Art
pip install -r requirements.txt
```

⚠️ **Note:** Option C does not install the `brain-art` package, so imports from `src.*` will require `sys.path` modification in tests.

### 4. Test Installation

```bash
python -c "import pygame, numpy, scipy, OpenMuse; print('✅ All OK!')"
```

---

## ✨ OpenMuse - Why and How?

### Why OpenMuse?

[OpenMuse](https://github.com/DominiqueMakowski/OpenMuse) is **the only solution with full support for Muse S Athena**:

**Find Muse:**
```bash
OpenMuse find
```

Output:
```
Found device: MuseS-FB2C
MAC Address: 00:55:DA:B9:FB:2C
```

**Stream:**
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C
```

**Presets (optional):**
```bash
# ⚡ RECOMMENDED: EEG only (saves battery!)
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
# or
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p21

# All sensors (default - higher battery consumption)
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p1041
```

**🔋 Battery Saving:**

According to [OpenMuse official documentation](https://github.com/DominiqueMakowski/OpenMuse#presets):

| Preset | EEG | Optics (PPG/fNIRS) | ACC/GYRO | Red LED | Battery Consumption |
|--------|-----|-------------------|----------|---------|---------------------|
| **`p20`/`p21`** | **EEG4** | **—** (none) | ✅ | off | 🟢 **Lowest** |
| `p1041` (default) | EEG8 | Optics16 | ✅ | bright | 🔴 **Highest** |

💡 **Recommendation for Brain Art:** Use `p20`!
- ✅ **EEG4** (4 main channels) - completely sufficient
- ❌ No optical sensors (PPG/fNIRS) - **biggest savings!**
- ❌ No bright LED
- **Effect:** Battery life **2-3x longer** (from ~2-3h to ~5-6h)! 🎉

**Recording:**
```bash
OpenMuse record --address 00:55:DA:B9:FB:2C --duration 60 --outfile session.txt
```

**Live visualization:**
```bash
OpenMuse view
```

---

## 🚀 First Run

### Step 1: Prepare Muse S

**Charging:**
- Full charge: ~2 hours
- Battery: ~10 hours of operation
- Red LED = charging, off = charged

**Wearing:**
- Front sensors (AF7, AF8) on forehead above eyebrows
- Rear sensors (TP9, TP10) behind ears
- Headband comfortable but snug

**Signal quality:**
- **Wet the sensors!** (most important)
- Water, conductive gel
- Sensors must touch skin
- Move hair away

### Step 2: Find MAC Address

```bash
# Turn on Muse (press button - blue LED)
OpenMuse find
# Note the displayed MAC address
```

### Step 3: Start Stream

**Terminal 1:**
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
# Wait for "Streaming data..."
```

### Step 4: Run Application

**Terminal 2:**
```bash
python main.py
```

### Step 5: Calibration

- Automatic (10 seconds)
- **Sit still with eyes closed**
- Breathe normally
- Don't think about anything

### Step 6: Experiment! 🎨

- Close/open eyes
- Focus on counting
- Relax
- See how colors change!

---

## 🔧 Troubleshooting

### OpenMuse find doesn't find device

**Check:**
1. Muse is on (blue LED)
2. Bluetooth active in Windows
3. Muse NOT connected to phone (close Muse app!)
4. Within range (~2-3m)

**Solution:**
```bash
# Restart Muse (hold 5s, wait, turn on)
# Restart Bluetooth
Get-Service bthserv | Restart-Service
# Try again
OpenMuse find
```

### Stream connects but app doesn't see it

```bash
# Check if stream is working
OpenMuse view

# Check LSL streams
python -c "from mne_lsl.lsl import resolve_streams; print(resolve_streams())"
```

### Import errors

```bash
# Check installation
pip list | findstr "OpenMuse pygame numpy brain-art"

# If using editable install:
pip install -e .  # Reinstall package (dependencies not reinstalled if already present)

# If using requirements.txt:
pip uninstall OpenMuse mne-lsl -y
pip install -r requirements.txt

# Check Python
python -c "import sys; print(sys.executable)"

# Check if package is installed
python -c "from src.muse_connector import MuseConnector; print('✅ Import OK')"
```

### Poor signal quality

**Symptoms:**
- Unstable colors
- No reaction to closing eyes
- During calibration: quality below 60%

**Quality check:**
```bash
# During app operation press 'Q' key
# You'll see detailed report:
# - Quality of each channel (TP9, AF7, AF8, TP10)
# - Metrics: variance, amplitude, alpha power, interference
# - Specific warnings and recommendations
```

**Solution:**
1. **Wet the sensors** (most important!)
2. Adjust headband
3. Move hair away from sensors
4. Minimize interference (phone, WiFi)
5. Minimize head movement
6. Check if sensors touch skin (not hair)

---

## ⚙️ Configuration

### File `config.py`

**Basic settings:**
```python
# EEG
SAMPLE_RATE = 256          # Don't change (Muse S spec)
WINDOW_SIZE = 64           # FFT window (64/128/256)
CALIBRATION_TIME = 10      # Calibration seconds

# Visualization
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FULLSCREEN = False         # True for production
TARGET_FPS = 30

# Particles
PARTICLE_LIFETIME = 2.0
MAX_PARTICLES = 150
PARTICLE_SIZE_MAX = 40

# Debug
DEBUG = True               # False for production
SHOW_FPS = True
```

**Colors:**
```python
COLOR_PALETTES = {
    'alpha': [
        (138, 43, 226),   # Violet
        (75, 0, 130),     # Indigo
        (0, 0, 255),     # Blue
    ],
    'beta': [
        (255, 0, 0),     # Red
        (255, 165, 0),   # Orange
        (255, 255, 0),   # Yellow
    ],
}
```

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `SPACE` | Clear screen |
| `1` | Alpha mode (relaxation) |
| `2` | Beta mode (attention) |
| `3` | Mixed mode |
| `S` | Screenshot |
| `Q` | Check signal quality (detailed report) |
| `ESC` | Exit |

## 📊 EEG Monitor (Optional)

When starting, you can open a **second window with EEG preview**:
- **Raw EEG** - all Muse S Athena channels (4-8 in real-time)
- **Topomaps** - visualization of **all electrodes** activity
- **Advanced** - uses MNE-Python library

Auto-start in `config.py`:
```python
SHOW_EEG_MONITOR = True
```

---

## 📚 Next Steps

- **Usage:** See README.md
- **Battery saving:** See [BATTERY_SAVING.md](BATTERY_SAVING.md)
- **User guide:** See [USER_GUIDE.md](USER_GUIDE.md)
