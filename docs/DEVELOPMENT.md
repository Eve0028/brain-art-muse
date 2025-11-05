# Brain Art - Dokumentacja Rozwojowa

**Dla deweloperów i kontrybutorów**

---

## 📐 Architektura Systemu

### Przepływ Danych

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

### Moduły

#### 1. `muse_connector.py` - Akwizycja Danych

**Odpowiedzialność:**
- Połączenie z Muse S przez LSL
- Strumieniowanie EEG (256 Hz, 4 kanały)
- Monitoring jakości sygnału

**API:**
```python
connector = MuseConnector(mode='lsl', enable_motion=True)
connector.connect()

# Pobierz dane
data = connector.get_eeg_data(duration=1.0)  # ndarray [samples, channels]
quality = connector.get_signal_quality()     # list [n_channels] (0-100%)

connector.disconnect()
```

**Implementacja:**
- Używa `mne_lsl.lsl` (StreamInlet)
- Fallback na `pylsl` jeśli brak mne_lsl
- Dynamiczne pobieranie danych (duration parametr w `get_eeg_data()`)
- Timeout: 5s na connect
- Monitoring jakości sygnału przez `SignalQualityChecker`
- Obsługa motion data (ACC/GYRO) przez `get_motion_data()`

#### 2. `eeg_processor.py` - Przetwarzanie Sygnału

**Odpowiedzialność:**
- FFT i analiza mocy częstotliwościowej
- Notch filtering (50Hz/60Hz - zakłócenia sieciowe)
- Kalibracja (baseline)
- Obliczanie metryk (attention, relaxation)

**API:**
```python
processor = EEGProcessor()  # Parametry z config.py (SAMPLE_RATE, WINDOW_SIZE)

# Dodaj dane
processor.add_data(eeg_array)  # [samples, 4] - używa tylko pierwszych 4 kanałów

# Kalibracja
# UWAGA: W main.py kalibracja jest wykonywana ręcznie, nie używa processor.calibrate()
# W main.py: zbiera dane przez config.CALIBRATION_TIME sekund, potem ustawia baseline
processor.baseline = powers.copy()  # Ręczne ustawienie baseline
processor.is_calibrated = True

# Przetwarzanie
powers = processor.compute_band_powers()  # dict {band: power} - uśrednione po kanałach
powers_per_ch = processor.compute_band_powers_per_channel()  # dict {band: [ch0, ch1, ch2, ch3]}
attention = processor.compute_attention()      # float 0-1
relaxation = processor.compute_relaxation()    # float 0-1
```

**Implementacja:**
- **Pasma częstotliwości (obliczane):**
  - Delta: 1-4 Hz (sen głęboki) - **obliczane, ale nie używane do wizualizacji**
  - Theta: 4-8 Hz (medytacja, senność) - **używane w relaxation (20%)**
  - Alpha: 8-13 Hz (relaksacja) - **główny wskaźnik relaxation (80%)**
  - Beta: 13-30 Hz (uwaga) - **główny wskaźnik attention (70%)**
  - Gamma: 30-44 Hz (przetwarzanie) - **używane w attention (30%)**

- **Uwaga:** Program oblicza wszystkie 5 pasm, ale do wizualizacji używa **tylko 4 pasm** (alpha, beta, gamma, theta). Delta jest obliczane i dostępne w `band_powers`, ale nie jest używane w metrykach attention/relaxation.
  
- **Metryki (używane do wizualizacji):**
  - `attention = 0.7 * (beta / beta_baseline) + 0.3 * (gamma / gamma_baseline)`
    - Używa: **beta (70%) + gamma (30%)**
    - Normalizacja względem baseline, clip do [0, 2], skalowanie do [0, 1]
  - `relaxation = 0.8 * (alpha / alpha_baseline) + 0.2 * (theta / theta_baseline)`
    - Używa: **alpha (80%) + theta (20%)**
    - Normalizacja względem baseline, clip do [0, 2], skalowanie do [0, 1]
  - Smoothing: rolling average (5 próbek w `metric_history`)

- **Przetwarzanie sygnału:**
  - Detrend (usuwanie trendu)
  - Notch filter 50Hz/60Hz (zakłócenia sieciowe) - `scipy.signal.iirnotch`
  - Hanning window (wygładzanie przed FFT)
  - FFT (Fast Fourier Transform) - bezpośrednia analiza częstotliwościowa
  - **UWAGA:** Filtry Butterworth są tworzone w `_create_filters()`, ale nie są używane w `compute_band_powers()` - używa się bezpośrednio FFT

#### 3. `brain_visualizer.py` - Wizualizacja

**Odpowiedzialność:**
- System cząsteczek (particles)
- 3 tryby: Alpha, Beta, Mixed
- Rendering (pygame)
- HUD/info

**API:**
```python
viz = BrainVisualizer()  # Parametry z config.py (WINDOW_WIDTH, WINDOW_HEIGHT, FULLSCREEN)

# Ustaw metryki
viz.set_metrics(attention=0.75, relaxation=0.5, motion_metrics=None)  # motion_metrics opcjonalne

# Zmień tryb
viz.set_mode('mixed')  # 'alpha', 'beta', 'mixed'

# Renderuj klatkę
viz.run_frame()  # Jedna klatka @ TARGET_FPS (domyślnie 30 FPS z config)

# Screenshot
viz.save_screenshot()

# Cleanup
viz.close()
```

**Implementacja:**

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
  - Rate zależny od attention/relaxation
  - Pozycja: losowa (tryb beta) lub centrum (alpha)
  - Kolor: z palety odpowiedniej dla trybu
  - Rozmiar: 8-40 px

- **Rendering:**
  - Fade effect: alpha blend
  - Draw particles: pygame.draw.circle (z cache dla wydajności)
  - Particle cache: pre-rendered surfaces dla lepszego FPS
  - HUD: FPS, metrics, mode, motion status
  - Auto-optimization: dostosowanie MAX_PARTICLES i FPS target na podstawie rzeczywistego FPS

- **Motion Effects (opcjonalne):**
  - Head tilt affects particle direction (95% influence przy silnym tilt)
  - Motion intensity affects particle count (jeśli `MOTION_INTENSITY_SCALING=True` w config, domyślnie: False)
  - Gestures: nod (change mode), shake (clear screen)

#### 4. `main.py` - Główna Aplikacja

**Przepływ:**
```python
1. Setup
   - Połącz z Muse (MuseConnector)
   - Inicjalizuj EEG processor (EEGProcessor)
   - Inicjalizuj motion processor (MotionProcessor, opcjonalnie)
   - Inicjalizuj performance optimizer (PerformanceOptimizer, opcjonalnie)
   - Inicjalizuj brain visualizer (BrainVisualizer)
   - Inicjalizuj EEG monitor (EEGVisualizer, opcjonalnie)

2. Calibration
   - Zbierz dane przez config.CALIBRATION_TIME sekund (domyślnie 5s)
   - Wyświetl instrukcje i progress
   - Ręcznie ustaw baseline: processor.baseline = powers.copy()
   - Ustaw processor.is_calibrated = True
   # UWAGA: NIE używa processor.calibrate() - zbiera dane ręcznie

3. Main Loop
   while running:
       # Motion data (co 100ms - częściej niż EEG)
       if motion_enabled:
           - Pobierz motion data (ACC/GYRO)
           - Dodaj do motion_processor
           - Wykryj gesty (nod → cycle_mode, shake → clear_screen)
       
       # EEG data (co UPDATE_INTERVAL ms, domyślnie 500ms = 2Hz)
       if time_to_update_eeg:
           - Pobierz EEG data
           - Przetwórz (async w thread jeśli optimizer włączony)
           - Oblicz band powers, attention, relaxation
           - Aktualizuj brain visualizer
           - Aktualizuj EEG monitor (jeśli włączony)
       
       # Render
       - Renderuj klatkę wizualizacji
       - Update EEG monitor plots (jeśli w tym samym procesie)
       - Handle events (keyboard, mouse)

4. Cleanup
   - Rozłącz Muse
   - Zamknij visualizers
   - Cleanup optimizer (threads, processes)
```

#### 5. `motion_processor.py` - Przetwarzanie Ruchu

**Odpowiedzialność:**
- Przetwarzanie danych ACC/GYRO z Muse S
- Wykrywanie gestów (nod, shake)
- Wykrywanie nachylenia głowy (tilt)
- Obliczanie motion metrics

**API:**
```python
processor = MotionProcessor(sample_rate=52)  # 52 Hz dla ACC/GYRO

# Dodaj dane
processor.add_data(acc_data, gyro_data)  # acc: [X, Y, Z] g, gyro: [X, Y, Z] deg/s

# Wykrywanie gestów
if processor.detect_nod():      # Skinięcie głową (przód-dół)
    # Zmień tryb wizualizacji
if processor.detect_shake():    # Potrząsanie głową (lewo-prawo)
    # Wyczyść ekran

# Nachylenie głowy
tilt_lr, tilt_fb = processor.get_head_tilt()  # -1 do 1

# Metryki
metrics = processor.get_metrics()  # dict z tilt, motion_intensity, etc.
```

**Implementacja:**
- **Gest detection:**
  - Nod: duża zmiana w ACC X (threshold: 0.8g, test: 1.4g)
  - Shake: szybka rotacja GYRO Z (threshold: 150°/s, test: 245°/s)
  - Cooldown: 1.5s między gestami

- **Head tilt:**
  - Tilt left-right: ACC Y (roll)
  - Tilt forward-backward: ACC X (pitch)
  - Używane do modyfikacji kierunku cząsteczek

- **Motion metrics:**
  - `motion_intensity`: 0-1 (na podstawie std dev ACC/GYRO)
  - `tilt_left_right`: -1 (lewo) do +1 (prawo)
  - `tilt_forward_backward`: -1 (przód) do +1 (tył)

#### 6. `eeg_visualizer.py` - Monitor EEG

**Odpowiedzialność:**
- Wizualizacja sygnałów EEG w osobnym oknie
- Topomapy (mapy topograficzne aktywności)
- Raw EEG traces (opcjonalnie)
- Power spectrogram

**API:**
```python
# Factory function
viz = create_eeg_visualizer(use_advanced=True, buffer_duration=5.0)

# Setup
viz.setup_window()

# Update data
viz.update_data(eeg_data, band_powers, band_powers_per_channel)

# Render (w głównej pętli)
viz.update_plots()

# Cleanup
viz.close()
```

**Implementacja:**
- Używa matplotlib (TkAgg backend)
- Wymaga MNE dla topomapów (fallback: SimpleEEGVisualizer)
- Może działać w osobnym procesie (`EEGVisualizerProcess`) dla lepszego FPS
- Per-channel band powers dla dokładniejszych topomapów

#### 7. `performance_optimizer.py` - Optymalizacja Wydajności

**Odpowiedzialność:**
- Multithreading dla obliczeń EEG
- Multiprocessing dla monitora EEG
- GPU acceleration
- Cache management

**API:**
```python
optimizer = PerformanceOptimizer(processor=eeg_processor)

# Async processing
optimizer.process_eeg_async(eeg_data)

# Get results (non-blocking)
results = optimizer.get_eeg_results()  # dict lub None
if results:
    band_powers = results['band_powers']
    attention = results['attention']
    relaxation = results['relaxation']

# Cleanup
optimizer.cleanup()
```

**Implementacja:**
- `EEGComputeThread`: osobny wątek dla obliczeń FFT (nie blokuje głównej pętli)
- `EEGVisualizerProcess`: osobny proces dla monitora EEG (znaczny wzrost FPS)
- Thread pools i process pools dla równoległych obliczeń

#### 8. `signal_quality.py` - Ocena Jakości Sygnału

**Odpowiedzialność:**
- Ocena jakości sygnału EEG
- Metryki per-kanał i ogólna
- Wykrywanie artefaktów i zakłóceń

**API:**
```python
checker = SignalQualityChecker(sample_rate=256)

# Ocena
result = checker.assess_quality(eeg_data)  # dict z metrics, warnings, etc.
# result['overall_quality']: 0-100
# result['channel_quality']: [0-100] per channel
# result['warnings']: list of warnings

# Szybka ocena (dla głównej pętli)
quality = quick_quality_check(eeg_data)  # 0-100
```

**Implementacja:**
- **Metryki:**
  - Variance (wariancja sygnału)
  - Amplitude (amplituda peak-to-peak)
  - Alpha power (obecność fal alpha)
  - Line noise (zakłócenia 50Hz/60Hz)
  - Artifacts (kurtosis, gradient analysis)
  - Stationarity (stabilność sygnału)

- **Wagi:**
  - Variance: 30%
  - Amplitude: 20%
  - Alpha power: 15%
  - Line noise: 15%
  - Artifacts: 15%
  - Stationarity: 5%

#### 9. `config.py` - Konfiguracja

**Sekcje:**
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

## 🔬 Algorytmy

### FFT (Fast Fourier Transform)

**Cel:** Przekształć sygnał czasowy → częstotliwościowy

```python
from scipy.fft import fft, fftfreq

# Input: signal [256 samples]
n = len(signal)
fft_vals = fft(signal)
fft_freqs = fftfreq(n, 1/sample_rate)

# Tylko dodatnie częstotliwości
pos_mask = fft_freqs > 0
freqs = fft_freqs[pos_mask]

# Power spectrum (znormalizowane przez N)
power_spectrum = (np.abs(fft_vals[pos_mask]) / n) ** 2

# Power w paśmie [f1, f2]
band_mask = (freqs >= f1) & (freqs <= f2)
power = np.mean(power_spectrum[band_mask])
```

### Normalizacja

**Cel:** Względne zmiany vs baseline

```python
# Podczas kalibracji (w main.py)
powers = processor.compute_band_powers()
processor.baseline = powers.copy()  # Ustawienie baseline

# Podczas używania
normalized_power = current_power / baseline_power  # Normalizacja względna

# Dla metryk attention/relaxation:
# 1. Normalizacja względem baseline
beta_norm = beta / beta_baseline
gamma_norm = gamma / gamma_baseline

# 2. Kombinacja ważona
attention_value = 0.7 * beta_norm + 0.3 * gamma_norm

# 3. Clip do [0, 2] i skalowanie do [0, 1]
attention_value = np.clip(attention_value, 0, 2) / 2.0

# 4. Smoothing (rolling average)
metric_history['attention'].append(attention_value)
attention_smooth = np.mean(metric_history['attention'])
```

### Smoothing

**Cel:** Redukcja szumu, płynne zmiany

```python
from collections import deque

history = deque(maxlen=5)  # Rolling window
history.append(new_value)
smoothed = np.mean(history)
```

---

## ⚙️ Parametry i Tuning

### Performance

**Jeśli FPS < 30:**
```python
WINDOW_SIZE = 64           # ↓ FFT szybsze
UPDATE_INTERVAL = 500      # ↑ Rzadziej EEG
MAX_PARTICLES = 300        # ↓ Mniej cząsteczek
PARTICLE_LIFETIME = 1.0    # ↓ Krótsze życie
```

**Jeśli CPU > 80%:**
- Zwiększ `UPDATE_INTERVAL`
- Zmniejsz `MAX_PARTICLES`
- Wyłącz `DEBUG`

### Responsiveness

**Jeśli za wolna reakcja:**
```python
# eeg_processor.py
self.metric_history = {
    'attention': deque(maxlen=2),    # było 5
    'relaxation': deque(maxlen=2),
}
```

**Jeśli za szybka (niestabilna):**
```python
maxlen=10  # Więcej wygładzania
```

### Visual Density

**Za mało cząsteczek:**
```python
MAX_PARTICLES = 1000
PARTICLE_LIFETIME = 3.0
PARTICLE_SIZE_MAX = 50
```

**Za dużo:**
```python
MAX_PARTICLES = 200
PARTICLE_LIFETIME = 0.5
```

---

## 🚀 Rozszerzenia

### 1. Zapis Danych EEG

```python
# W main.py
import csv

csv_file = open('eeg_recording.csv', 'w', newline='')
writer = csv.writer(csv_file)
writer.writerow(['time', 'TP9', 'AF7', 'AF8', 'TP10', 'attention', 'relaxation'])

# W głównej pętli
writer.writerow([time.time(), *eeg_data[-1], attention, relaxation])

# Cleanup
csv_file.close()
```

### 2. Analiza Nagranych Danych

```python
import pandas as pd
import matplotlib.pyplot as plt

# Wczytaj
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

### 3. Muzyka z EEG

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

# W głównej pętli
freq = 200 + attention * 400  # 200-600 Hz
volume = relaxation * 0.5
tone = generate_tone(freq, 0.1, volume)
tone.play()
```

### 4. OSC do Tabletu

```python
from pythonosc import udp_client

# Setup
osc_client = udp_client.SimpleUDPClient("192.168.1.100", 5005)

# W pętli
osc_client.send_message("/brain/attention", attention)
osc_client.send_message("/brain/relaxation", relaxation)
osc_client.send_message("/brain/alpha", alpha_power)
osc_client.send_message("/brain/beta", beta_power)
```

**Na tablecie (TouchOSC/Processing):**
```processing
import oscP5.*;

OscP5 osc;

void setup() {
  osc = new OscP5(this, 5005);
}

void oscEvent(OscMessage msg) {
  if (msg.checkAddrPattern("/brain/attention")) {
    float attention = msg.get(0).floatValue();
    // Rysuj coś...
  }
}
```

### 5. Własne Wizualizacje

**Linie zamiast cząsteczek:**
```python
# W brain_visualizer.py
def _draw_lines(self):
    if random.random() < 0.1:
        start = (random.randint(0, self.width), 0)
        end = (random.randint(0, self.width), self.height)
        color = self._get_color_for_mode()
        thickness = int(5 + self.attention * 10)
        pygame.draw.line(self.canvas, color, start, end, thickness)
```

**Fraktale:**
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
# Dwa connectory
muse1 = MuseConnector(address='00:55:DA:B9:FB:2C')
muse2 = MuseConnector(address='00:55:DA:B9:XX:XX')

# Dwa procesory
proc1 = EEGProcessor()
proc2 = EEGProcessor()

# W pętli
att1 = proc1.compute_attention()
att2 = proc2.compute_attention()

# Tryby:
# 1. Współpraca: avg_attention = (att1 + att2) / 2
# 2. Rywalizacja: winner = "P1" if att1 > att2 else "P2"
# 3. Duel: każdy kontroluje połowę ekranu
```

---

## 🧪 Testing

### Uruchamianie Testów

Wszystkie testy znajdują się w katalogu `tests/`. Uruchamiaj je indywidualnie:

```bash
# Kompleksowy test systemu (zalecane jako pierwszy)
python tests/test_system.py

# Test funkcjonalności monitora EEG
python tests/test_eeg_visualizer.py

# Testy optymalizacji wydajności
python tests/test_performance.py

# Testy gestów ruchowych (wymaga aktywnego strumienia OpenMuse)
python tests/gestures/test_motion.py
python tests/gestures/test_motion_axes.py
python tests/gestures/test_tilt.py
```

### Zestawy Testów

- **test_system.py**: Kompleksowy test komponentów z danymi syntetycznymi
  - Testuje wszystkie główne moduły (MuseConnector, EEGProcessor, BrainVisualizer)
  - Weryfikuje importy i zależności
  - Opcjonalny test połączenia OpenMuse
  - Nie wymaga urządzenia (używa danych syntetycznych)

- **test_eeg_visualizer.py**: Test funkcjonalności okna monitora EEG
  - Testuje wizualizator EEG standalone
  - Weryfikuje komponenty wizualizacji

- **test_performance.py**: Testy optymalizacji wydajności
  - Informacje o CPU
  - Threading i multiprocessing
  - Testy FPS pygame
  - Rekomendacje konfiguracji

- **gestures/** - Testy funkcji ruchowych:
  - `test_motion.py`: Testy wykrywania gestów (skinięcie, potrząsanie)
  - `test_motion_axes.py`: Identyfikacja osi akcelerometru/żyroskopu
  - `test_tilt.py`: Testy wykrywania nachylenia głowy
  - **Uwaga**: Wymagają aktywnego strumienia OpenMuse z danymi ruchowymi (preset p20, p21, p1041)

- **debug_channels.py**: Analiza strumieni LSL i inspekcja kanałów
  - Wyświetla dostępne strumienie LSL
  - Pokazuje nazwy kanałów i ich kolejność
  - Przydatne do rozwiązywania problemów z połączeniem

### Unit Tests

Przykład struktury testów jednostkowych:

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
# test_system.py (już istnieje)
python tests/test_system.py
```

### Manual Testing Checklist

- [ ] Połączenie z Muse
- [ ] Jakość sygnału > 70%
- [ ] Kalibracja (5s domyślnie)
- [ ] Zamknij oczy → więcej alpha → ciepłe kolory
- [ ] Otwórz oczy + liczenie → więcej beta → jasne kolory
- [ ] Motion gestures działają (nod → zmiana trybu, shake → wyczyszczenie)
- [ ] Head tilt wpływa na kierunek cząsteczek
- [ ] EEG monitor działa (jeśli włączony)
- [ ] Screenshoty zapisują się
- [ ] FPS > 30 (lub dostosowany do PERFORMANCE_MODE)
- [ ] Brak memory leaks (długa sesja)

---

## 📊 Metryki i Monitoring

### Performance Metrics

```python
# W main.py
import time

frame_times = []

while running:
    start = time.time()

    # ... główna pętla ...

    frame_time = time.time() - start
    frame_times.append(frame_time)

    if len(frame_times) > 100:
        avg_fps = 1.0 / np.mean(frame_times)
        print(f"Avg FPS: {avg_fps:.1f}")
        frame_times = []
```

### Signal Quality Monitoring

```python
# W muse_connector.py
from src.signal_quality import SignalQualityChecker

# Inicjalizacja
self.quality_checker = SignalQualityChecker(sample_rate=256)

# Aktualizacja jakości (w _update_signal_quality)
quality_result = self.quality_checker.assess_quality(eeg_data)
self.signal_quality = quality_result['channel_quality']  # [0-100] per channel
self.overall_quality = quality_result['overall_quality']  # 0-100
self.quality_warnings = quality_result['warnings']  # List of warnings

# Pobranie jakości
quality_list = connector.get_signal_quality()  # [0-100] per channel
overall = connector.get_overall_quality()  # 0-100
warnings = connector.get_quality_warnings()  # List of strings
```

**Metryki jakości:**
- Variance: 30% (wariancja sygnału)
- Amplitude: 20% (peak-to-peak)
- Alpha power: 15% (obecność fal alpha)
- Line noise: 15% (zakłócenia 50Hz/60Hz)
- Artifacts: 15% (ruchy, mruganie)
- Stationarity: 5% (stabilność)

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
# Sprawdź rozmiar okna
assert len(signal) == WINDOW_SIZE
# Sprawdź czy są NaN
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

## 📚 Zasoby

### Dokumentacja
- **OpenMuse:** https://github.com/DominiqueMakowski/OpenMuse
- **MNE-LSL:** https://mne.tools/mne-lsl/
- **Pygame:** https://www.pygame.org/docs/
- **SciPy Signal:** https://docs.scipy.org/doc/scipy/reference/signal.html

### Naukowe
- **EEG Bands:** https://en.wikipedia.org/wiki/Electroencephalography
- **BCI:** https://www.frontiersin.org/journals/human-neuroscience
- **FFT:** https://en.wikipedia.org/wiki/Fast_Fourier_transform

### Inspiracje
- NeuroSky MindWave
- InteraXon Muse Apps
- BCI Art Projects
