# 📝 Changelog - Brain Art

## v1.0.0 - Initial Release (2025-11-05)

### 🎉 First Public Release

**Brain Art** - Real-time EEG visualization and interaction system for Muse S Athena headbands. Transform your brain activity into dynamic visual art.

---

## ✨ Core Features

### 🧠 EEG Signal Processing
- **4-channel support for Muse S Athena**: Primary channels (TP9, AF7, AF8, TP10)
- **OpenMuse compatibility**: Works with 4 or 8 channel streams (uses first 4 channels)
- **Signal Quality Assessment**: Real-time quality metrics with 6 assessment criteria
- **Detailed quality reports**: Press 'Q' for diagnostic information
- **50Hz/60Hz Notch Filtering**: Automatic power line noise removal (IIR, Q=30)
- **Band Power Analysis**: Alpha, Beta, Gamma, Theta, Delta frequency bands

### 🎨 Visualization Modes
- **3 Visualization Modes**: 
  - Alpha mode (Relaxation) - Warm, calm colors
  - Beta mode (Attention) - Dynamic, energetic colors
  - Mixed mode - Combination of both
- **Dynamic mode switching**: Press 1, 2, 3 or use gesture control
- **Particle System**: Beautiful particle effects driven by EEG activity
- **Real-time rendering**: Optimized pygame-based visualization

### 📊 EEG Monitor (Optional)
- **Raw EEG traces**: Real-time signal visualization
- **Per-channel topomaps**: Spatial distribution of band powers
- **Topographic maps**: MNE-Python based scalp plots
- **Separate process architecture**: Runs in separate process for better performance
- **5-second buffer**: Smooth scrolling visualization

### 🎮 Motion Features (Optional)
- **Gesture Detection**:
  - **Nod** (forward-down-forward) → Changes visualization mode
  - **Shake** (left-right-left) → Clears screen
- **Motion-reactive Effects**:
  - **Head tilt** influences particle direction
  - **Motion intensity** modifies particle count (0.5x - 2.0x scaling)
  - **Flow state** - stillness reduces particle count
- **Toggle with 'M' key**: Enable/disable motion features during runtime

### 🔌 Connection Methods
- **LSL (Lab Streaming Layer)**: Recommended method
  - Support for MNE-LSL (OpenMuse) and pylsl (legacy)
  - Automatic stream detection
- **Bluetooth Low Energy**: Experimental direct connection
  - MAC address configuration
  - Requires bleak library

---

## 🏗️ Project Structure

### 🔧 Core Modules

#### `src/muse_connector.py`
- LSL streaming with 4 channels (TP9, AF7, AF8, TP10)
- Uses first 4 channels from OpenMuse stream (even if 8 channels are available)
- Motion data streaming (ACC/GYRO) with preset support
- Signal quality monitoring integration
- Bluetooth connection support (experimental)

#### `src/eeg_processor.py`
- Fast Fourier Transform (FFT) with configurable window size
- Per-channel band power computation
- Attention and relaxation metrics
- Baseline calibration system
- Optional FFT cache (`ENABLE_FFT_CACHE`) for faster repeated computations
- Hash-based cache for identical data windows (max 100 entries, FIFO)
- Automatic cache clearing on processor reset

#### `src/brain_visualizer.py`
- Particle system with dynamic properties
- Color palette switching per mode
- Motion-reactive effects
- Performance-optimized rendering
- Configurable particle cache (`ENABLE_PARTICLE_CACHE`) for faster rendering
- Manual cache management via `Particle.clear_cache()` method

#### `src/eeg_visualizer.py`
- Real-time EEG trace visualization
- Topographic maps using MNE-Python
- Per-channel band power visualization
- Scalp map generation with spatial interpolation

#### `src/motion_processor.py`
- Accelerometer and gyroscope data processing
- Gesture detection (nod, shake)
- Tilt computation (left/right, forward/backward)
- Motion intensity calculation

#### `src/signal_quality.py`
- 6 quality metrics:
  - Variance analysis
  - Amplitude checking
  - Alpha power detection
  - Line noise assessment
  - Artifact detection (kurtosis, gradient)
  - Stationarity analysis
- Overall quality scoring (0-100)
- Per-channel quality reports

#### `src/performance_optimizer.py`
- Multithreading for EEG computations
- Separate process for EEG visualizer
- GPU acceleration support
- Process and thread pools

---

## 📚 Documentation

Comprehensive documentation in `docs/`:

### Main Guides
- **[INSTALLATION.md](docs/eng/INSTALLATION.md)**: Detailed installation and troubleshooting guide (English)
- **[USER_GUIDE.md](docs/eng/USER_GUIDE.md)**: User manual with controls and features (English)
- **FESTIVAL.md**: Festival usage guide (Polish only - see [docs/FESTIVAL.md](docs/FESTIVAL.md))
- **[DEVELOPMENT.md](docs/eng/DEVELOPMENT.md)**: Technical documentation (English)

### Technical Documentation
- **EEG_MONITOR.md**: EEG monitor window documentation (Polish only - see [docs/EEG_MONITOR.md](docs/EEG_MONITOR.md))
- **QUALITY_METRICS.md**: Signal quality metrics explained (Polish only - see [docs/QUALITY_METRICS.md](docs/QUALITY_METRICS.md))
- **OPTIMIZATION.md**: Performance optimization guide (Polish only - see [docs/OPTIMIZATION.md](docs/OPTIMIZATION.md))
- **[BATTERY_SAVING.md](docs/eng/BATTERY_SAVING.md)**: Battery optimization tips and preset guide (English)
- **OPENMUSE_PRESETS.md**: OpenMuse preset information (Polish only - see [docs/OPENMUSE_PRESETS.md](docs/OPENMUSE_PRESETS.md))
- **FILTERING.md**: Signal filtering documentation (Polish only - see [docs/FILTERING.md](docs/FILTERING.md))
- **MOTION_AXES.md**: Motion sensor axes reference (Polish only - see [docs/MOTION_AXES.md](docs/MOTION_AXES.md))

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

- **test_system.py**: Comprehensive component testing with synthetic data
  - Tests all core modules (MuseConnector, EEGProcessor, BrainVisualizer)
  - Validates imports and dependencies
  - Optional OpenMuse connection test
  - No device required (uses synthetic data)

- **test_eeg_visualizer.py**: EEG monitor window functionality test
  - Tests EEG visualizer standalone
  - Validates visualization components

- **test_performance.py**: Performance optimization tests
  - CPU information
  - Threading and multiprocessing
  - Pygame FPS testing
  - Configuration recommendations

- **gestures/** - Motion feature testing:
  - `test_motion.py`: Gesture detection testing (nod, shake)
  - `test_motion_axes.py`: Accelerometer/gyroscope axis identification
  - `test_tilt.py`: Head tilt detection testing
  - **Note**: These require active OpenMuse stream with motion data (preset p20, p21, p1041)

### Debugging Tools
- **debug_channels.py**: LSL stream analysis and channel inspection
  - Useful for troubleshooting connection issues
  - Lists available LSL streams and channels

---

## ⚙️ Configuration

### Key Settings (`config.py`)

#### Connection
- `CONNECTION_MODE`: 'lsl' (recommended) or 'bluetooth'
- `MUSE_ADDRESS`: MAC address for Bluetooth mode
- `SAMPLE_RATE`: 256 Hz (Muse S default)

#### Visualization
- `WINDOW_WIDTH` / `WINDOW_HEIGHT`: Display resolution
- `TARGET_FPS`: Target frames per second (30 default)
- `UPDATE_INTERVAL`: EEG data update frequency (500ms)
- `MAX_PARTICLES`: Maximum particle count (150 default)

#### Motion Features
- `ENABLE_MOTION`: Enable motion features
- `MOTION_GESTURE_CONTROL`: Enable gesture detection
- `MOTION_TILT_EFFECTS`: Enable tilt-based effects
- `MOTION_INTENSITY_SCALING`: Scale particles by motion intensity

#### Performance
- `USE_THREADING`: Multithreaded EEG processing
- `EEG_VISUALIZER_SEPARATE_PROCESS`: Run monitor in separate process
- `USE_GPU_ACCELERATION`: Enable hardware acceleration
- `ENABLE_PARTICLE_CACHE`: Cache pre-rendered particles for faster rendering (default: True)
  - Can be disabled to save memory at cost of performance
  - Manual cache management available via `Particle.clear_cache()`
- `ENABLE_FFT_CACHE`: Cache FFT results for identical data windows (default: False)
  - Hash-based caching for faster repeated computations
  - Particularly useful during calibration (multiple computations on same data)
  - Automatic memory management (max 100 entries, FIFO)

---

## 📦 Dependencies

### Required
- **Python 3.12 (tested only on this version)**
- **numpy**: Numerical computations
- **scipy**: Signal processing (FFT, filtering)
- **pygame**: Visualization rendering
- **matplotlib**: Plotting (for EEG monitor)

### EEG Streaming
- **OpenMuse**: `git+https://github.com/DominiqueMakowski/OpenMuse.git`
- **mne-lsl**: MNE-LSL for OpenMuse support
- **pylsl**: Alternative LSL library (legacy support)

### Optional
- **bleak**: Bluetooth Low Energy support
- **mne**: Advanced EEG analysis (for topomaps)

---

## 🎯 Hardware Support

### Primary Device
- **Muse S Athena**: Main supported device
  - 4 main channels: TP9, AF7, AF8, TP10
  - Accelerometer and gyroscope (with presets p20, p21, p1041)

### Optional Hardware
- **BLED112-V1**: Bluetooth 4.0 dongle (for direct BLE connection)

### Tested Platforms
- **Windows 11**: Fully tested and confirmed
- **Linux**: Should work (untested)
- **macOS**: Should work (untested)

---

## 🚀 Getting Started

1. **(Optional) Create virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   # Recommended: Editable install
   pip install -e .
   
   # Or production install
   pip install .
   ```

3. **Find your Muse S device**:
   ```bash
   OpenMuse find
   ```
   Note the MAC address (e.g., `00:55:DA:B9:FB:2C`)

4. **Start OpenMuse stream** (Terminal 1):
   ```bash
   # Recommended: EEG only (saves battery)
   OpenMuse stream --address <YOUR_MAC> --preset p20
   ```

5. **Run Brain Art** (Terminal 2):
   ```bash
   python main.py
   ```

6. **Optional: View EEG signals** (Terminal 3):
   ```bash
   OpenMuse view
   ```

7. **Calibrate**: Sit still for 10 seconds with eyes closed

8. **Enjoy**: Watch your brain activity transform into art!

**Full installation guide:** See [docs/eng/INSTALLATION.md](docs/eng/INSTALLATION.md)

---

## ⌨️ Controls

- **SPACE**: Clear screen
- **1**: Relaxation mode (Alpha)
- **2**: Attention mode (Beta)
- **3**: Mixed mode
- **S**: Save screenshot
- **Q**: Check signal quality report
- **M**: Toggle motion features (if enabled)
- **ESC**: Exit

---

## 🐛 Known Issues & Limitations

- Bluetooth direct connection is experimental - LSL is recommended
- Motion features require OpenMuse preset with ACC/GYRO (p20, p21, p1041)
- Topomaps show frontal-temporal region only (4 electrodes limitation)
- Windows console emoji support may require encoding fixes

---

## 🙏 Acknowledgments

- **OpenMuse**: For Muse device support
- **MNE-Python**: For EEG analysis tools
- **pylsl / mne-lsl**: For LSL streaming capabilities

---

## 📄 License

See LICENSE file for details.

---

## 🔜 Future Roadmap

Potential features for future releases:
- [ ] Session recording to file
- [ ] Replay recorded sessions
- [ ] Additional visualization modes
- [ ] Per-user calibration profiles
- [ ] Web interface (optional)
- [ ] VR/AR visualization modes
- [ ] Advanced machine learning features

---

## 📞 Support

For issues, questions, or contributions:
- Check documentation in `docs/` folder
- Review troubleshooting guides
- Open an issue on GitHub (if applicable)

---

**Enjoy creating art with your brain! 🧠🎨**
