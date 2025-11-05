# 🧠 Brain Art - Muse S Athena

**Interactive EEG-powered art generation with brainwaves**

Create colorful visualizations using attention (beta) or relaxation (alpha) states.

---

## ⚡ Quick Start (3 minutes)

### 1. (Optional) Create Virtual Environment

**Recommended:** Use venv to isolate project dependencies:

```bash
# Windows
python -m venv venv
# or if you want a specific Python version
py -3.12 -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

**Option A: Editable install (recommended for development):**
```bash
pip install -e .
```

**Option B: Production install:**
```bash
pip install .
```

### 3. Find Your Muse S
Power on Muse S (blue LED) and run:
```bash
OpenMuse find
```
Note the MAC address (e.g., `00:55:DA:B9:FB:2C`)

### 4. Run
**Terminal 1:**
```bash
# Recommended: EEG only (saves battery)
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
```

**Terminal 2:**
```bash
python main.py
```

Optional **Terminal 3:**
```bash
# EEG signals visualization
OpenMuse view
```

### 5. Done! 🎨
- **Calibration**: 10 seconds with eyes closed
- **Create**: Experiment with closing eyes and concentration!

**Full installation guide:** See [docs/eng/INSTALLATION.md](docs/eng/INSTALLATION.md)

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `SPACE` | Clear screen |
| `1` | Relaxation mode (Alpha) - warm colors |
| `2` | Attention mode (Beta) - dynamic effects |
| `3` | Mixed mode |
| `S` | Screenshot |
| `Q` | Check signal quality |
| `M` | Toggle motion features |
| `ESC` | Exit |

**Head gestures (if motion enabled):**
- 👍 **Nod** (forward-down-forward) → Change mode
- 👎 **Shake** (left-right-left) → Clear screen
- 🔄 **Tilt** → Particle direction

---

## 💡 How It Works

### Visualization Modes:

**🔵 Alpha Mode (Relaxation)**
- How: Close eyes, deep breathing
- Effect: Warm colors (violet → blue), slow motion

**🔴 Beta Mode (Attention)**  
- How: Concentrate (counting, thinking)
- Effect: Bright colors (red → yellow), fast particles

**⭐ Mixed Mode**
- Combination of both - most spectacular!

### Technical:
- **EEG**: 4 channels (TP9, AF7, AF8, TP10) @ 256 Hz
- **FFT**: Frequency band analysis (Alpha: 8-13 Hz, Beta: 13-30 Hz)
- **LSL**: Streaming via OpenMuse (dedicated for Muse S Athena)

---

## 🔋 Battery Optimization

**Use preset `p20` - EEG4 only, no optics:**
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
```

**What p20 disables:**
- ❌ **Optics** (PPG/fNIRS) - 16 optical channels ← **biggest savings!**
- ❌ **Red LED** - bright red LEDs

**What p20 keeps:**
- ✅ **EEG4** - 4 main EEG channels @ 256 Hz (sufficient for Brain Art!)
- ✅ **ACC/GYRO** - accelerometer and gyroscope
- ✅ **Full functionality** of Brain Art

**Effect:** Battery life increased by **100-150%** (from ~2-3h to ~5-6h)! 🎉

📚 **Details:** [OpenMuse Presets Table](https://github.com/DominiqueMakowski/OpenMuse#presets) | [docs/BATTERY_SAVING.md](docs/BATTERY_SAVING.md)

---

## 📊 EEG Monitor

Besides the Brain Art window, you can open a **second window with EEG signal preview**:

**Monitor shows:**
- 📈 Raw EEG traces (4 channels - TP9, AF7, AF8, TP10) - if turn on in config, but I recommend to use `OpenMuse view` for that
- 🧠 Alpha/Beta topomaps (activity of all electrodes)
- 📊 Real-time visualization

```bash
python main.py
# Select "y" when asked about EEG monitor
```

Auto-start: Set `SHOW_EEG_MONITOR = True` in `config.py`

---

## 📚 Documentation

- **[INSTALLATION.md](docs/eng/INSTALLATION.md)** - Installation, OpenMuse, configuration, troubleshooting
- **[USER_GUIDE.md](docs/eng/USER_GUIDE.md)** - User manual with controls and features
- **[BATTERY_SAVING.md](docs/eng/BATTERY_SAVING.md)** - Battery optimization tips and preset guide
- **[DEVELOPMENT.md](docs/eng/DEVELOPMENT.md)** - Developer documentation

---

## 📋 Requirements

**Hardware:**
- Muse S Athena
- Laptop with Windows 11 (built-in Bluetooth is enough!)
- Optional: Large monitor/TV (HDMI)

**Software:**
- Python 3.12 (tested only on this version)
- OpenMuse (will install from `requirements.txt`)

---

## 📂 Project Structure

```
Brain_Art/
├── main.py                 # Main application entry point
├── config.py               # Central configuration
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Package configuration
│
├── src/                   # Core modules
│   ├── muse_connector.py   # Muse S connection (LSL streaming)
│   ├── eeg_processor.py    # EEG signal processing (FFT, band analysis)
│   ├── brain_visualizer.py # Particle system visualization
│   ├── eeg_visualizer.py   # Optional EEG monitor window
│   ├── motion_processor.py # Head gesture detection (ACC/GYRO)
│   ├── signal_quality.py   # Signal quality metrics
│   └── performance_optimizer.py # Performance optimization
│
├── utils/                 # Utility tools
│   └── find_muse.py       # Device discovery
│
├── tests/                 # Test suite
│   ├── test_system.py     # System integration tests
│   ├── test_eeg_visualizer.py
│   └── ... 
│
├── docs/                  # Documentation
│   ├── eng/               # English documentation
│   │   ├── INSTALLATION.md
│   │   ├── USER_GUIDE.md
│   │   └── BATTERY_SAVING.md
│   ├── INSTALLATION.md      # Installation guide (Polish)
│   ├── FESTIVAL.md        # Festival setup guide (Polish)
│   ├── DEVELOPMENT.md          # Developer documentation (Polish)
│   └── ...                # Additional docs (Polish)
│
└── screenshots/           # Saved screenshots
```

---

## 🙏 Credits

- **OpenMuse**: https://github.com/DominiqueMakowski/OpenMuse
- **Pygame**: https://www.pygame.org/
- **MNE-LSL**: https://mne.tools/mne-lsl/
- **SciPy**: Signal processing

---

## 📄 License

Open-source - use and modify as you like!

