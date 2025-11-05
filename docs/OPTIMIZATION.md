# ⚡ Optymalizacja Wydajności - Brain Art

**Przewodnik po optymalizacji wydajności aplikacji**

---

## 🚀 Przegląd

Brain Art używa zaawansowanego systemu optymalizacji który **automatycznie wykorzystuje dostępne zasoby** komputera:

### **Co zostało zoptymalizowane:**

1. **EEG Visualizer w osobnym procesie** - nie blokuje głównego renderingu
2. **Obliczenia EEG w osobnym wątku** - FFT i filtry nie spowalniają renderingu
3. **GPU acceleration** - pygame używa karty graficznej do renderingu
4. **Cache cząsteczek** - pre-renderowane cząsteczki
5. **Thread pool** - równoległe przetwarzanie danych
6. **Auto-optymalizacja liczby cząsteczek** - automatyczne dostosowywanie do wydajności

---

## 🎯 Zaimplementowane optymalizacje

### 1. **Cache pre-renderowanych cząsteczek** ✅

**Problem:** Tworzenie nowej `pygame.Surface` dla każdej cząsteczki przy każdej klatce.

**Rozwiązanie:** Cache współdzielony między cząsteczki, ograniczona liczba unikalnych powierzchni w pamięci.

**Implementacja:**
```python
# Klasa Particle - cache statyczny
_cache = {}
_cache_size_limit = 50

@classmethod
def _get_cached_surface(cls, size, color):
    # Check if cache is enabled
    if not config.ENABLE_PARTICLE_CACHE:
        # Cache disabled - create new surface each time
        cache_size = int(size / 2) * 2
        surf = pygame.Surface((cache_size * 2, cache_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, 255), (cache_size, cache_size), cache_size)
        return surf
    
    # Round size to nearest even number for better cache hit rate
    cache_size = int(size / 2) * 2
    cache_key = (cache_size, color)
    if cache_key not in cls._cache:
        # Stwórz tylko gdy brak w cache
        surf = pygame.Surface((cache_size * 2, cache_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, 255), (cache_size, cache_size), cache_size)
        cls._cache[cache_key] = surf
    return cls._cache[cache_key]
```

**Korzyści:**
- Cząsteczki renderowane raz i cache'owane
- Mniej wywołań `pygame.draw.circle()`
- Znacznie szybsze dla dużej liczby cząsteczek
- Kontrolowane przez `ENABLE_PARTICLE_CACHE` w config.py (domyślnie True)

---

### 2. **Auto-optymalizacja liczby cząsteczek** ✅

Automatyczne dostosowywanie `MAX_PARTICLES` i FPS target na podstawie rzeczywistego FPS.

**Tryby wydajności (`PERFORMANCE_MODE`):**

- **"high"**: Cel 60 FPS, MAX_PARTICLES ≥ 200, auto-optymalizacja wyłączona
- **"balanced"**: Cel 30 FPS, MAX_PARTICLES ≤ 150, auto-optymalizacja wyłączona
- **"low"**: Cel 15 FPS, MAX_PARTICLES ≤ 80, auto-optymalizacja wyłączona
- **"auto"**: Automatyczna adaptacja (domyślnie)

**Zachowanie trybu "auto":**
- Niski FPS (< 20) → automatyczne zmniejszenie cząsteczek i FPS target
- Wysoki FPS (> 50) → automatyczne zwiększenie cząsteczek i FPS target
- Adaptacja FPS target: 15→20→25→30→60 (w zależności od wydajności)
- Sprawdzanie co 2 sekundy

**Konfiguracja:**
```python
# config.py
PERFORMANCE_MODE = "auto"  # "high", "balanced", "low", lub "auto"
MAX_PARTICLES = 150  # Start value (dla trybu "auto")
```

**Uwaga:** 
- W trybie "auto" funkcja `_auto_optimize()` automatycznie dostosowuje zarówno `MAX_PARTICLES` jak i FPS target na podstawie rzeczywistego FPS
- W trybach "high", "balanced", "low" ustawienia są stałe i nie zmieniają się automatycznie

---

### 3. **Skip renderowania niewidocznych cząsteczek** ✅

```python
if self.alpha <= 10:  # Skip jeśli prawie niewidoczne
    return
```

---

### 4. **EEG Visualizer w osobnym procesie** ✅

**Architektura:**
```
┌─────────────────┐         ┌──────────────────┐
│  Proces główny  │         │  Proces EEG Viz  │
│                 │         │                  │
│  • Pygame       │◄─────►  │  • Matplotlib    │
│  • Brain Art    │ Queue   │  • Topomapy      │
│  • Rendering    │         │  • Raw traces    │
└─────────────────┘         └──────────────────┘
```

**Korzyści:**
- Matplotlib NIE blokuje pygame
- Każdy proces ma własne CPU core
- Komunikacja przez queue (non-blocking)

---

### 5. **Wątek obliczeń EEG** ✅

**Architektura:**
```
Główna pętla:                    Wątek EEG:
┌──────────┐                    ┌──────────────┐
│ Pobierz  │──► Queue ──►       │ Odbierz dane │
│ dane EEG │                    │ FFT + Filtry │
│          │                    │ Band powers  │
│ Renderuj │◄── Queue ◄─────────│ Attention    │
│ cząstki  │     (wyniki)       │ Relaxation   │
└──────────┘                    └──────────────┘
```

**Korzyści:**
- FFT nie blokuje renderingu
- Obliczenia w tle (inny rdzeń CPU)
- Non-blocking - używamy ostatnich dostępnych wyników

---

### 6. **GPU Acceleration** ✅

```python
# Pygame z hardware acceleration
pygame.HWSURFACE | pygame.DOUBLEBUF
```

**Korzyści:**
- Rendering na GPU zamiast CPU
- Szybszy blit i alpha blending
- Mniej obciążenia procesora

---

### 7. **Cache FFT**

**Problem:** FFT jest kosztowne obliczeniowo, a te same okna danych mogą być przetwarzane wielokrotnie (np. podczas kalibracji).

**Rozwiązanie:** Cache wyników FFT dla identycznych okien danych (hash-based).

**Implementacja:**
```python
# EEGProcessor - cache FFT
def _compute_fft_cached(self, window, channel):
    if not config.ENABLE_FFT_CACHE:
        # Cache disabled - compute directly
        return compute_fft(window)
    
    # Create cache key from window hash + channel
    window_hash = hashlib.md5(window.tobytes()).digest()
    cache_key = (channel, window_hash)
    
    if cache_key in self.fft_cache:
        return self.fft_cache[cache_key]  # Cache hit
    
    # Cache miss - compute and store
    result = compute_fft(window)
    self.fft_cache[cache_key] = result
    return result
```

**Korzyści:**
- Przyspiesza przetwarzanie gdy te same okna są analizowane wielokrotnie
- Szczególnie przydatne podczas kalibracji
- Kontrolowane przez `ENABLE_FFT_CACHE` w config.py (domyślnie False)
- Automatyczne zarządzanie pamięcią (max 100 wpisów, FIFO)

**Uwaga:** Cache FFT jest najbardziej przydatny gdy:
- Te same okna danych są przetwarzane wielokrotnie
- Podczas kalibracji (wielokrotne wywołania `compute_band_powers()`)
- W trybie testowym z powtarzającymi się danymi

---

## ⚙️ Konfiguracja

### W `config.py`

```python
# === OPTYMALIZACJA ZAAWANSOWANA ===

# Performance Mode
PERFORMANCE_MODE = "auto"  # "high" (60fps), "balanced" (30fps), "low" (15fps), "auto"
                           # "auto" - automatyczna adaptacja FPS i MAX_PARTICLES

# Threading i wielordzeniowość
USE_THREADING = True  # Osobne wątki dla obliczeń EEG ⭐ ZALECANE
USE_PROCESS_POOL = True  # Process pool dla ciężkich obliczeń
MAX_THREADS = None  # Liczba wątków (None = auto-detect) - domyślnie None

# EEG Visualizer w osobnym procesie
EEG_VISUALIZER_SEPARATE_PROCESS = True  # ⭐ DUŻY WZROST WYDAJNOŚCI!

# GPU Acceleration
USE_GPU_ACCELERATION = True  # Użyj GPU do renderingu ⭐ ZALECANE
PYGAME_USE_OPENGL = False  # OpenGL (eksperymentalne)

# Cache
ENABLE_PARTICLE_CACHE = True  # Cache cząsteczek ⭐ ZALECANE
ENABLE_FFT_CACHE = False  # Cache FFT (więcej RAM, może przyspieszyć przy duplikatach okien)
```

**Uwaga:** 
- `ENABLE_PARTICLE_CACHE` kontroluje czy cząsteczki są cache'owane (zalecane: True)
- `ENABLE_FFT_CACHE` cache'uje wyniki FFT dla identycznych okien danych (może przyspieszyć przy częstych wywołaniach, ale zużywa więcej RAM)

---

## 🎯 Zalecane Ustawienia

### **Dla Maksymalnej Wydajności:**

```python
PERFORMANCE_MODE = "high"  # 60 FPS target, MAX_PARTICLES ≥ 200
USE_THREADING = True
USE_PROCESS_POOL = True
MAX_THREADS = None  # Auto-detect (użyje wszystkie rdzenie)
EEG_VISUALIZER_SEPARATE_PROCESS = True
USE_GPU_ACCELERATION = True
PYGAME_USE_OPENGL = False  # Zostaw False (bezpieczniejsze)
ENABLE_PARTICLE_CACHE = True
```

### **Dla Stabilności (Starszy PC):**

```python
PERFORMANCE_MODE = "low"  # 15 FPS target, MAX_PARTICLES ≤ 80
USE_THREADING = True
USE_PROCESS_POOL = False  # Wyłącz process pool
MAX_THREADS = 2  # Ogranicz liczbę wątków
EEG_VISUALIZER_SEPARATE_PROCESS = True  # Nadal zalecane!
USE_GPU_ACCELERATION = True
PYGAME_USE_OPENGL = False
ENABLE_PARTICLE_CACHE = True
```

### **Dla Minimalnego Obciążenia:**

```python
PERFORMANCE_MODE = "low"  # 15 FPS target, MAX_PARTICLES ≤ 80
USE_THREADING = False  # Wszystko w głównym wątku
USE_PROCESS_POOL = False
EEG_VISUALIZER_SEPARATE_PROCESS = False
USE_GPU_ACCELERATION = False
ENABLE_PARTICLE_CACHE = True
```

---

## 🔧 Dodatkowe optymalizacje (opcjonalne)

### A. Wyłącz EEG Monitor jeśli nie potrzebny

EEG Monitor (MNE-Python plotting) może znacząco wpływać na wydajność.

```python
# config.py
SHOW_EEG_MONITOR = False  # Wyłącz dla lepszej wydajności
```

---

### B. Zmniejsz częstotliwość update'ów

```python
# config.py
UPDATE_INTERVAL = 1000  # ms (było 500)
```

EEG nie musi być aktualizowany co 0.5s. 1 sekunda wystarczy.

---

### C. Wyłącz Motion Debug

```python
# config.py
DEBUG_MOTION = False
```

Print do konsoli spowalnia.

---

### D. Manualna redukcja cząsteczek

Jeśli auto-optymalizacja nie wystarczy:

```python
# config.py
MAX_PARTICLES = 100  # Bardzo płynne
# lub
MAX_PARTICLES = 75   # Ultra płynne (minimalistyczne)
```

---

### E. Zmniejsz rozmiar okna

```python
# config.py
WINDOW_WIDTH = 1024  # było 1280
WINDOW_HEIGHT = 576  # było 720
```

Mniej pikseli = szybszy rendering.

---

### F. Zmniejsz czas życia cząsteczek

```python
# config.py
PARTICLE_LIFETIME = 1.5  # było 2.0
```

Mniej cząsteczek na ekranie = lepsza wydajność.

---

## 🧪 Testowanie wydajności

### Test 1: Baseline

```bash
python main.py
```

Obserwuj FPS w prawym górnym rogu.

### Test 2: Z optymalizacjami

1. Wyłącz EEG Monitor
2. Ustaw `UPDATE_INTERVAL = 1000`
3. Ustaw `DEBUG_MOTION = False`
4. Uruchom i porównaj wydajność

### Test 3: Profiling (zaawansowany)

```bash
python -m cProfile -o profile.stats main.py
# Ctrl+C po 30 sekundach

python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

---

## 🔍 Monitorowanie wydajności

### W HUD (lewy górny róg):

```
Uwaga: 0.65
Relaksacja: 0.42
Cząsteczek: 145
```

Liczba cząsteczek powinna być blisko `MAX_PARTICLES`.

### FPS (prawy górny róg):

```
FPS: 58
```

Monitoruj FPS i dostosuj ustawienia w razie potrzeby.

---

## 🔬 Techniczne Szczegóły

### Threading Model

- **Główny wątek:** Pygame rendering, input handling
- **EEG compute wątek:** FFT, band powers, metryki
- **EEG visualizer proces:** Matplotlib (całkowicie oddzielny)

### Komunikacja

```python
# Thread-safe queues
data_queue = queue.Queue(maxsize=5)
result_queue = queue.Queue(maxsize=5)

# Non-blocking operations
try:
    results = result_queue.get_nowait()
except queue.Empty:
    # Użyj poprzednich wartości
```

### Memory Management

- **Particle cache:** ~10-20 MB (ograniczony do 50 rozmiarów, tylko jeśli `ENABLE_PARTICLE_CACHE=True`)
- **FFT cache:** ~5-10 MB (max 100 wpisów, tylko jeśli `ENABLE_FFT_CACHE=True`)
- **EEG buffers:** ~5 MB (5 sekund @ 256 Hz)
- **Process overhead:** ~50 MB (osobny proces Python)

**Total:** ~65-75 MB (bez cache FFT) lub ~75-85 MB (z cache FFT)

---

## 💡 Wskazówki

### 1. **Dostosuj MAX_PARTICLES**

Więcej rdzeni CPU = możliwość użycia więcej cząsteczek:

```python
# 4 rdzenie
MAX_PARTICLES = 80

# 8+ rdzeni
MAX_PARTICLES = 150

# 12+ rdzeni  
MAX_PARTICLES = 200
```

### 2. **Monitoruj FPS**

```python
SHOW_FPS = True  # Pokaż FPS w prawym górnym rogu
```

Dostosuj ustawienia jeśli wydajność jest niska.

### 3. **Wyłącz co nie używasz**

Jeśli nie używasz EEG monitora:
```python
SHOW_EEG_MONITOR = False  # Nie pytaj o monitor
```

Jeśli nie używasz motion:
```python
ENABLE_MOTION = False
```

### 4. **Zarządzanie cache**

**Particle cache** (zalecane: włączony):
```python
ENABLE_PARTICLE_CACHE = True  # Szybszy rendering, +10-20 MB RAM
# lub
ENABLE_PARTICLE_CACHE = False  # Oszczędność RAM, wolniejszy rendering
```

**FFT cache** (opcjonalne, włącz jeśli potrzebujesz):
```python
ENABLE_FFT_CACHE = True  # Szybsze powtarzające się obliczenia, +5-10 MB RAM
# Przydatne podczas kalibracji lub testów z powtarzającymi się danymi
```

**Ręczne czyszczenie cache:**
```python
# W kodzie (jeśli potrzebujesz)
from src.brain_visualizer import Particle
Particle.clear_cache()  # Wyczyść cache cząsteczek

from src.eeg_processor import EEGProcessor
processor = EEGProcessor()
processor.clear_fft_cache()  # Wyczyść cache FFT
```

### 5. **OpenGL - Eksperymentalne**

OpenGL może dać dodatkową poprawę wydajności, ale jest niestabilny:

```python
PYGAME_USE_OPENGL = True  # Spróbuj na własne ryzyko!
```

Jeśli działa - świetnie! Jeśli crashuje - zostaw False.

---

## 🐛 Troubleshooting

### Problem: "Nie widzę poprawy wydajności"

**Sprawdź:**
```python
# W config.py - czy wszystko włączone?
USE_THREADING = True
EEG_VISUALIZER_SEPARATE_PROCESS = True
USE_GPU_ACCELERATION = True
```

### Problem: "App się crashuje przy starcie"

**Rozwiązanie:**
```python
# Wyłącz process pool
USE_PROCESS_POOL = False

# Lub ogranicz wątki
MAX_THREADS = 2
```

### Problem: "EEG Monitor nie działa w osobnym procesie"

**Sprawdź:**
- Czy `matplotlib` jest dostępne (`pip install matplotlib`)
- Czy `multiprocessing` działa (wbudowany moduł Pythona, powinien działać zawsze)

**Fallback:**
```python
# Użyj starego trybu (w tym samym procesie)
EEG_VISUALIZER_SEPARATE_PROCESS = False
```

### Problem: "GPU acceleration nie działa"

**Windows:**
```python
# Sprawdź czy używasz DirectX
import os
print(os.environ.get('SDL_VIDEODRIVER'))  # Powinno być 'directx'
```

**Fallback:**
```python
USE_GPU_ACCELERATION = False  # Użyj software rendering
```

---

## 📈 Roadmap

**Przyszłe optymalizacje:**

- [ ] Numba JIT dla FFT (@jit decorator)
- [ ] CuPy dla obliczeń na GPU (NVIDIA CUDA)
- [ ] Vulkan backend dla pygame
- [ ] Batch processing dla wielu Muse devices
- [ ] Hardware-accelerated matplotlib (QtAgg)

---

## 🔗 Zobacz Też

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Architektura systemu
- **[INSTALLATION.md](INSTALLATION.md)** - Konfiguracja i setup
- **[config.py](../config.py)** - Pełna konfiguracja

---

**Podsumowanie:** Włącz `USE_THREADING`, `EEG_VISUALIZER_SEPARATE_PROCESS`, `USE_GPU_ACCELERATION` i `ENABLE_PARTICLE_CACHE` dla maksymalnej wydajności! Włącz `ENABLE_FFT_CACHE` jeśli przetwarzasz te same dane wielokrotnie. 🚀
