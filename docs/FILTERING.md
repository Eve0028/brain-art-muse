# 🔬 Filtrowanie Sygnału EEG - Brain Art

## 📊 Przegląd Filtracji

Brain Art stosuje **wieloetapową filtrację** sygnału EEG z Muse S Athena:

```
Surowy sygnał → Detrending → Notch 50Hz → Hanning → FFT → Maski częstotliwościowe → Metryki
```

---

## 🎛️ Etapy Filtracji

### 1️⃣ **Detrending** (Usuwanie Trendu DC)
**Gdzie:** `src/eeg_processor.py` - funkcja `compute_band_powers()` i `compute_band_powers_per_channel()`

```python
window = signal.detrend(window)
```

**Co robi:**
- Usuwa powolny dryftt (DC drift) - trend liniowy w sygnale
- Centruje sygnał wokół zera

**Dlaczego:**
- DC drift zaburza analizę FFT
- Może pochodzić z elektrody referencyjnej

---

### 2️⃣ **Filtr Notch 50Hz/60Hz**
**Gdzie:** `src/eeg_processor.py`
- **Tworzenie filtra:** funkcja `_create_notch_filter()` (wywoływana w `__init__`)
- **Zastosowanie:** funkcje `compute_band_powers()` i `compute_band_powers_per_channel()`

```python
# Filtr notch - usuń zakłócenia 50Hz/60Hz
b, a = self.notch_filter
window = signal.filtfilt(b, a, window)
```

**Co robi:**
- Usuwa zakłócenia od sieci elektrycznej
- **50Hz** w Europie/Azji/Afryce/Australii
- **60Hz** w USA/Kanadzie/Japonii/Korei Południowej

**Parametry:**
- **Quality Factor (Q):** 30
- **Szerokość wycięcia:** ±1.67 Hz wokół częstotliwości centralnej
- **Typ:** IIR notch filter (`scipy.signal.iirnotch`)

**Dlaczego:**
- Muse S Athena **NIE MA** wbudowanego filtra notch
- Sieci elektryczne emitują stałe pole 50/60 Hz
- Zakłóca analizę pasm EEG (szczególnie Alpha 8-13 Hz i Beta 13-30 Hz)

**Konfiguracja:**
W `config.py`:
```python
POWER_LINE_FREQ = 50  # Hz - zmień na 60 dla USA/Kanady
```

---

### 3️⃣ **Okno Hanninga** (Windowing)
**Gdzie:** `src/eeg_processor.py` - funkcje `compute_band_powers()` i `compute_band_powers_per_channel()`

```python
window = window * np.hanning(len(window))
```

**Co robi:**
- Redukuje "spectral leakage" w FFT
- Wygładza brzegi okna czasowego

**Dlaczego:**
- FFT zakłada periodyczność sygnału
- Okno Hanninga minimalizuje artefakty na brzegach

---

### 4️⃣ **Ekstrakcja Pasma** (Frequency Band Extraction)
**Gdzie:** `src/eeg_processor.py` - funkcje `compute_band_powers()` i `compute_band_powers_per_channel()`

```python
# Maski częstotliwościowe na wynikach FFT
for band_name, (low, high) in config.BANDS.items():
    band_mask = (freqs >= low) & (freqs <= high)
    if np.any(band_mask):
        band_powers[band_name] += np.mean(power_spectrum[band_mask])
```

**Uwaga:** Filtry band-pass Butterwortha są tworzone w funkcji `_create_filters()`, ale **nie są stosowane** w aktualnej implementacji. Zamiast tego używa się masek częstotliwościowych na wynikach FFT, co jest szybsze i wystarczające po zastosowaniu filtra notch.

**Pasma EEG:**
| Pasmo | Zakres (Hz) | Znaczenie |
|-------|-------------|-----------|
| Delta | 1-4 Hz | Sen głęboki |
| Theta | 4-8 Hz | Medytacja, senność |
| **Alpha** | **8-13 Hz** | **Relaksacja, zamknięte oczy** |
| **Beta** | **13-30 Hz** | **Aktywna uwaga, koncentracja** |
| Gamma | 30-44 Hz | Przetwarzanie kognitywne |

**Parametry:**
- **Metoda:** Maski częstotliwościowe na wynikach FFT (nie filtry czasowe)
- **Zakresy pasm:** Zgodnie z `config.BANDS`
- **Rozdzielczość:** Zależna od rozmiaru okna FFT (~4 Hz przy 64 samples)

---

### 5️⃣ **FFT** (Fast Fourier Transform)
**Gdzie:** `src/eeg_processor.py` - funkcje `compute_band_powers()` i `compute_band_powers_per_channel()`

```python
fft_vals = fft(window)
fft_freq = fftfreq(len(window), 1.0/self.sample_rate)
```

**Co robi:**
- Przekształca sygnał z domeny czasu → domeny częstotliwości
- Wydobywa komponenty częstotliwościowe

**Parametry:**
- **Rozmiar okna:** 64 samples (0.25 sekundy przy 256 Hz)
- **Rozdzielczość częstotliwości:** ~4 Hz

---


## 🔍 Detekcja Zakłóceń (Signal Quality)

**Gdzie:** `src/signal_quality.py` - funkcja `_check_line_noise()` w klasie `SignalQualityChecker`

```python
def _check_line_noise(self, data: np.ndarray) -> dict:
    # FFT
    freqs, psd = signal.welch(data, fs=self.sample_rate, nperseg=min(256, len(data)))

    # Moc przy 50 Hz (±1 Hz)
    noise_50hz = np.mean(psd[(freqs >= 49) & (freqs <= 51)])

    # Moc całkowita
    total_power = np.mean(psd[(freqs >= 1) & (freqs <= 40)])

    # Względny szum
    noise_relative = noise_50hz / total_power
```

**Progi:**
- **noise_relative > 0.3**: Score = 30 (duże zakłócenia) ⚠️
- **noise_relative > 0.15**: Score = 60 (umiarkowane) ⚡
- **noise_relative < 0.15**: Score = 100 (niskie) ✅

**Ostrzeżenie:**
```
⚠️  TP10: Zakłócenia elektryczne (50Hz)
```
Oznacza, że kanał TP10 ma wysoką moc przy 50 Hz.

---

## 🛠️ Rozwiązywanie Problemów

### Problem: "Zakłócenia elektryczne (50Hz)"

**Możliwe przyczyny:**
1. **Słaby kontakt elektrody** z głową
2. **Bliskość źródeł elektrycznych** (zasilacze, lampy, komputer)
3. **Nieuwilgocone elektrody**
4. **Brak uziemienia** (DRL/REF electrode)

**Rozwiązania:**
1. ✅ **Teraz: Filtr notch jest aktywny** - zakłócenia są usuwane w software
2. 💧 **Zwiłż elektrody** - lepszy kontakt = mniej zakłóceń
3. 🔌 **Odsuń się od źródeł elektrycznych** - szczególnie zasilaczy
4. 📍 **Dopasuj opaskę** - mocniejszy kontakt z głową
5. 🔄 **Sprawdź wszystkie elektrody** - upewnij się że wszystkie 4 mają dobry kontakt

### Problem: Wciąż widzę ostrzeżenia po dodaniu filtra

**Wyjaśnienie:**
- **Detekcja** w `signal_quality.py` działa na **surowym sygnale** (przed filtracją)
- **Filtracja** w `eeg_processor.py` działa podczas **analizy FFT**
- Ostrzeżenie pokazuje **jakość wejściową**, ale filtr **usuwa** zakłócenia przed obliczeniem metryk

**To normalne!** Ostrzeżenie informuje o problemie, ale filtr go rozwiązuje.

---

## 📈 Weryfikacja Filtracji

### Test 1: Uruchom aplikację
```bash
python main.py
```

### Test 2: Sprawdź jakość sygnału
**Klawisz:** `Q` (podczas działania aplikacji)

**Przed filtracją (ostrzeżenie):**
```
⚠️  TP10: Zakłócenia elektryczne (50Hz)
Line Noise: 0.35 (score: 30)
```

**Po filtracji (w metryach):**
- Alpha i Beta power **nie będą zawyżone** przez 50Hz
- Wartości będą stabilniejsze

### Test 3: Wizualizacja w EEG Monitor
**W `config.py`:**
```python
SHOW_EEG_MONITOR = True
```

**Obserwuj:**
- Raw traces powinny być **mniej zaszumione**
- Topomapy Alpha/Beta powinny pokazywać **czyste rozkłady**

---

## 🎯 Podsumowanie

| Etap | Narzędzie | Cel |
|------|-----------|-----|
| 1 | `signal.detrend()` | Usunięcie DC drift |
| 2 | `signal.iirnotch()` + `signal.filtfilt()` | Usunięcie 50Hz/60Hz ⚡ |
| 3 | `np.hanning()` | Redukcja spectral leakage |
| 4 | `fft()` + maski częstotliwościowe | Analiza częstotliwościowa i ekstrakcja pasm |

---

## 🔬 Literatura

1. **Muse S SDK Documentation** - Hardware filtering specs
2. **OpenMuse Library** - Signal processing pipeline
3. **SciPy Signal Processing** - `scipy.signal.iirnotch`, `scipy.signal.butter`
4. **"EEG Signal Processing and Feature Extraction"** - Springer (2019)

