"""
Brain Art Application Configuration.
"""

# === MUSE CONNECTION ===
# Muse S MAC address (fill after running muselsl list)
MUSE_ADDRESS = "00:55:DA:B9:FB:2C"  # e.g. "00:55:DA:B9:FB:2C"

# Muse device name (if using muselsl stream)
MUSE_NAME = "Muse-S"  # or "MuseS-FB2C" (from muselsl list)

# Connection mode: 'lsl' (recommended) or 'bluetooth'
CONNECTION_MODE = 'lsl'

# COM port for BLED112 USB dongle (if using)
BLED112_PORT = "COM3"  # Change if your dongle is on different port

# === EEG PARAMETERS ===
# Muse S sampling frequency
SAMPLE_RATE = 256  # Hz

# Window size for analysis (in samples)
WINDOW_SIZE = 64  # 0.25 seconds - faster FFT

# Frequency bands
BANDS = {
    'delta': (1, 4),      # Deep sleep
    'theta': (4, 8),      # Meditation, drowsiness
    'alpha': (8, 13),     # Relaxation, eyes closed
    'beta': (13, 30),     # Active attention, concentration
    'gamma': (30, 44),    # Cognitive processing
}

# Channels for analysis (Muse S has: TP9, AF7, AF8, TP10)
CHANNELS = ['TP9', 'AF7', 'AF8', 'TP10']

# Power line noise filtering
# 50Hz in Europe/Asia/Africa/Australia
# 60Hz in USA/Canada/Japan/South Korea
POWER_LINE_FREQ = 50  # Hz - change to 60 if you're in 60Hz region

# Calibration time (seconds)
CALIBRATION_TIME = 5  # Faster calibration for better UX

# === VISUALIZATION ===
# Window resolution
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# Fullscreen?
FULLSCREEN = False

# FPS
TARGET_FPS = 30

# How often to update EEG data (ms)
UPDATE_INTERVAL = 500  # 2 Hz - less frequent = faster (EEG processing is slow)

# === VISUAL PARAMETERS ===
# Visualization modes
MODES = {
    'alpha': 'Relaxation',
    'beta': 'Attention',
    'mixed': 'Mixed'
}

# Color palettes
COLOR_PALETTES = {
    'alpha': [  # Warm, calm colors
        (138, 43, 226),   # Violet
        (75, 0, 130),     # Indigo
        (0, 0, 255),      # Blue
        (0, 128, 128),    # Teal
    ],
    'beta': [  # Dynamic, energetic colors
        (255, 0, 0),      # Red
        (255, 165, 0),    # Orange
        (255, 255, 0),    # Yellow
        (0, 255, 0),      # Green
    ],
    'mixed': [  # Combination
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Cyan
        (255, 255, 255),  # White
        (255, 192, 203),  # Pink
    ]
}

# Particle parameters
PARTICLE_LIFETIME = 2.0  # seconds - longer life = more on screen
PARTICLE_SIZE_MIN = 8
PARTICLE_SIZE_MAX = 40  # Larger for better effect
PARTICLE_SPEED_MIN = 30
PARTICLE_SPEED_MAX = 100
MAX_PARTICLES = 150  # Increased for 12-core CPU (was 80)

# === PERFORMANCE OPTIMIZATION ===
PERFORMANCE_MODE = "auto"  # "high" (60fps target), "balanced" (30fps), "low" (15fps), "auto"
                           # "auto" will adapt to actual FPS

# === ADVANCED OPTIMIZATION ===
# Threading and multicore
USE_THREADING = True  # Use separate threads for EEG computations
USE_PROCESS_POOL = True  # Use process pool for heavy computations (FFT)
MAX_THREADS = None  # Maximum worker threads (None = auto-detect CPU cores)
                    # Auto-detect will find 12 cores on your system!

# EEG Visualizer in separate process
EEG_VISUALIZER_SEPARATE_PROCESS = True  # Run EEG monitor in separate process (recommended!)

# GPU Acceleration
USE_GPU_ACCELERATION = True  # Try to use GPU for rendering
PYGAME_USE_OPENGL = False  # Use OpenGL for pygame (experimental, may be unstable)
                            # If False, will use standard hardware-accelerated rendering

# Optimization cache
ENABLE_PARTICLE_CACHE = True  # Cache pre-rendered particles (large FPS increase)
ENABLE_FFT_CACHE = False  # Cache FFT results (may increase RAM usage)

# === PATHS ===
SCREENSHOTS_DIR = "screenshots"

# === DEBUG ===
DEBUG = True
SHOW_FPS = True
SHOW_SIGNAL_QUALITY = True
SHOW_EEG_MONITOR = False  # Automatically open EEG monitor window (True/False)
EEG_MONITOR_SHOW_RAW_TRACES = False  # Show raw EEG signals in monitor (True/False)
                                      # If False, monitor will show only scalp maps (topomaps)
                                      # Use "OpenMuse view" to preview raw signals
DEBUG_MOTION = False  # Show detailed motion data (ACC/GYRO values)

# === MOTION FEATURES (ACC/GYRO) ===
# Interactive effects based on head movement (accelerometer and gyroscope)
ENABLE_MOTION = True  # Enable motion features (requires preset p20 or higher)

# Motion effects
MOTION_GESTURE_CONTROL = True    # Gestures: nod (change mode), shake (clear)
MOTION_TILT_EFFECTS = True       # Head tilt changes visual effects
MOTION_INTENSITY_SCALING = False  # Motion intensity affects particle count

# Sensitivity thresholds (default values in motion_processor.py)
# You can change them here if you want more/less sensitive detection
