# EEG Monitor - Wizualizacja Sygnałów w Czasie Rzeczywistym

**Drugie okno z podglądem raw EEG i topomap**

---

## 🎯 Przegląd

Monitor EEG to **opcjonalne drugie okno**, które pokazuje:
1. **Topomapy** (skalpy) - wizualizacja aktywności **4 elektrod** dla różnych pasm (Alpha, Beta)
2. **Raw EEG traces** (opcjonalnie) - surowe sygnały z **4 kanałów** (TP9, AF7, AF8, TP10)
3. **Aktualizacja w czasie rzeczywistym** - co 100ms

**Dwa tryby:**
- **Tylko skalpy** (domyślny): pokazuje tylko topomapy, surowe sygnały przez `OpenMuse view`
- **Pełny**: raw traces + topomapy w jednym oknie

**Brain Art używa 4 głównych kanałów EEG z Muse S Athena:**
- TP9, AF7, AF8, TP10
- ⚠️ **Uwaga**: OpenMuse może wysyłać 8 kanałów (4 główne + 4 AUX), ale Brain Art przetwarza tylko pierwsze 4 kanały dla spójności z eeg_processor.py

---

## 🚀 Jak Używać

### Podczas Uruchamiania

```bash
python main.py

# Zobaczysz:
# Otworzyć okno monitora EEG? (y/n): 
```

Wpisz **`y`** aby otworzyć monitor.

### Automatyczne Uruchomienie

W `config.py`:
```python
SHOW_EEG_MONITOR = True  # Auto-start monitora (bez pytania)
```

### Tryb Uruchomienia

Monitor może działać w dwóch trybach:

1. **Osobny proces** (domyślny, zalecany):
   ```python
   EEG_VISUALIZER_SEPARATE_PROCESS = True  # Domyślnie True
   ```
   - Uruchomiony w osobnym procesie (większy boost FPS!)
   - Mniejszy wpływ na główną aplikację
   - Zalecane dla lepszej wydajności

2. **Ten sam proces**:
   ```python
   EEG_VISUALIZER_SEPARATE_PROCESS = False
   ```
   - Działa w głównym procesie
   - Może obniżyć FPS głównej aplikacji

### Test Standalone

```bash
python tests/test_eeg_visualizer.py
```

---

## 📊 Co Pokazuje Monitor

### 1. Raw EEG Traces (górny wykres) - tylko gdy `EEG_MONITOR_SHOW_RAW_TRACES = True`

```
[TP9    ] ───────────∿∿∿─────∿∿∿────────  (główny)
[AF7    ] ──────∿∿∿────────∿∿─────────  (główny)
[AF8    ] ─────∿∿───────∿∿∿∿───────────  (główny)
[TP10   ] ────────∿∿∿──────∿───────────  (główny)
     0s       2s       4s       5s
```

- **4 kanały**: Brain Art używa tylko głównych 4 kanałów (TP9, AF7, AF8, TP10)
  - OpenMuse może wysyłać 8 kanałów (4 główne + 4 AUX), ale Brain Art przetwarza tylko pierwsze 4
  - Kanały AUX są ignorowane dla spójności z `eeg_processor.py`
- **Okno czasowe**: Ostatnie 5 sekund
- **Normalizacja**: Każdy kanał na swojej "ścieżce"
- **Kolory**: Różne dla każdego kanału

**Interpretacja:**
- Fale widoczne gdy zamkniesz oczy (alpha)
- Bardziej "płaskie" gdy otwarte (beta)
- Gwałtowne skoki = artefakty (ruch, mrugnięcie)

### 2. Topomap Alpha (lewy dolny)

```
         ●
    AF7 \ | / AF8     ← PRZÓD GŁOWY (czoło)
         \|/
   TP9 ───●─── TP10
    ●           ●
         (skronie)
```

**Pokazuje:**
- Moc alpha (8-13 Hz) w regionie czołowo-skroniowym
- **4 elektrody** Muse S Athena (TP9, AF7, AF8, TP10)
- Kolor: czerwony = wysoka aktywność, niebieski = niska
- Interpolacja między elektrodami dla wizualizacji

**Interpretacja:**
- **Wysoka alpha** (czerwony AF7/AF8) = relaksacja, oczy zamknięte
- **Niska alpha** (niebieski) = koncentracja, oczy otwarte

### 3. Topomap Beta (prawy dolny)

Podobnie jak alpha, ale dla pasma beta (13-30 Hz).

**Pokazuje:**
- Moc beta w regionie czołowo-skroniowym

**Interpretacja:**
- **Wysoka beta** (czerwony AF7/AF8) = uwaga, koncentracja
- **Niska beta** (niebieski) = relaksacja

---

## ⚙️ Konfiguracja

### W `config.py`

```python
SHOW_EEG_MONITOR = False  # Auto-start monitora (True/False)
                          # Jeśli False, zapyta przy starcie aplikacji

EEG_MONITOR_SHOW_RAW_TRACES = False  # Pokaż surowe sygnały (True/False)
                                      # False = tylko skalpy (topomapy) - domyślne w config.py
                                      # True = raw traces + topomapy
```

**Tryb tylko-skalpy (domyślny):**
- Monitor pokazuje tylko topomapy (Alpha, Beta)
- Surowe sygnały możesz zobaczyć przez: `OpenMuse view`
- Mniejsze okno, mniej obciążenia

**Tryb pełny:**
- Monitor pokazuje raw traces + topomapy
- Wszystko w jednym oknie

### W kodzie (main.py)

**Tryb osobny proces (domyślny):**
```python
from src.performance_optimizer import EEGVisualizerProcess

# W main.py setup()
self.eeg_visualizer = EEGVisualizerProcess(
    use_advanced=True,
    buffer_duration=5.0
)
self.eeg_visualizer.start()  # Uruchom w osobnym procesie

# W pętli głównej
self.eeg_visualizer.send_data(eeg_data, band_powers, band_powers_per_channel)
```

**Tryb ten sam proces:**
```python
from src.eeg_visualizer import create_eeg_visualizer

# W main.py setup()
viz = create_eeg_visualizer(
    use_advanced=True,      # Użyj wersji z MNE (topomapy) jeśli dostępne
    buffer_duration=5.0    # 5 sekund okna czasowego
)
viz.setup_window()  # Tworzy okno matplotlib

# W pętli głównej
viz.update_data(eeg_data, band_powers, band_powers_per_channel)
viz.update_plots()  # Throttled do 10 Hz
```

---

## 💡 Zastosowania

### 1. **Debugowanie**

Sprawdź czy sygnał EEG jest OK:
- Czy widać fale?
- Czy są artefakty?
- Jak wygląda jakość sygnału?

### 2. **Edukacja**

Pokaż uczestnikom:
- Jak wyglądają prawdziwe fale mózgowe
- Różnica między alpha a beta
- Wpływ zamykania oczu na EEG

### 3. **Badania**

Monitoruj:
- Jakość sygnału podczas sesji
- Wzorce aktywności mózgu
- Reakcje na różne stany

---

## 🔬 Techniczne Detale

### Update Rate

- **EEG data**: 256 Hz (próbki z Muse S)
- **Buffer**: 5 sekund = 1280 próbek (5s × 256 Hz)
- **Rendering**: 10 Hz (co 100ms = `update_interval: float = 0.1`)
- **Throttling**: Automatyczny, aby nie obciążać CPU

### Topomapy (MNE)

**Pozycje elektrod** (układ 10-20, znormalizowane 2D):
```python
{
    # 4 główne elektrody (używane w topomapach)
    'TP9':  [-0.6, -0.2],     # Lewy tył (za uchem)
    'AF7':  [-0.4,  0.6],     # Lewy przód (nad okiem)
    'AF8':  [ 0.4,  0.6],     # Prawy przód (nad okiem)
    'TP10': [ 0.6, -0.2],     # Prawy tył (za uchem)
}
```

**Zdefiniowane w:** `src/eeg_visualizer.py`, metoda `_create_electrode_positions()`

**Interpolacja**: 
- Biharmonic spline (MNE default)
- **Ograniczona do przodu głowy**: `sphere=(0, 0.35, 0, 0.45)` - mniejszy obszar interpolacji
- Niższa rozdzielczość (`res=64`) = mniej "zgadywania" między elektrodami
- 3 kontury (zamiast domyślnych 6) dla większej czytelności
- **Jitter pozycji**: Małe losowe przesunięcia (±0.001) aby uniknąć błędów Qhull dla współokręgowych punktów
- **Kolormap**: `RdYlBu_r` (czerwony = wysoka aktywność, niebieski = niska)

**Pokrycie**: 
- **Region czołowo-skroniowy** (przód głowy)
- **4 elektrody** Muse S Athena (TP9, AF7, AF8, TP10)

---

## 🐛 Troubleshooting

### Monitor się nie otwiera

```bash
# Test standalone
python tests/test_eeg_visualizer.py

# Sprawdź matplotlib backend
python -c "import matplotlib; print(matplotlib.get_backend())"
# Powinno być: TkAgg (ustawione w eeg_visualizer.py: matplotlib.use('TkAgg'))
```

### Brak topomap (tylko raw traces)

```bash
# Sprawdź MNE
python -c "import mne; print(mne.__version__)"

# Zainstaluj jeśli brak
pip install mne
```

### Okno zamyka się samo

- Sprawdź czy są błędy w konsoli
- Upewnij się że `is_running = True`
- Zmniejsz `update_interval` w `eeg_visualizer.py`

---

## 🔗 Zobacz Też

- **[QUALITY_METRICS.md](QUALITY_METRICS.md)** - Metryki jakości sygnału
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - API i architektura
- **[INSTALLATION.md](INSTALLATION.md)** - Setup i konfiguracja

