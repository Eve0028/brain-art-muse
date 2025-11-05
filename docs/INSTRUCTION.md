# Brain Art - Instrukcja Użytkowania

**Podstawowe użytkowanie aplikacji**

---

## 🎮 Sterowanie

| Klawisz | Akcja |
|---------|-------|
| `SPACJA` | Wyczyść ekran |
| `1` | Tryb Alpha (relaksacja) |
| `2` | Tryb Beta (uwaga) |
| `3` | Tryb Mieszany |
| `S` | Screenshot |
| `Q` | Sprawdź jakość sygnału |
| `M` | Przełącz motion features (włącz/wyłącz) |
| `ESC` | Wyjście |

---

## 🎨 Tryby Wizualizacji

### Tryb 1: Alpha (Relaksacja)

**Jak osiągnąć:**
- Zamknij oczy
- Głębokie, powolne oddychanie
- Nie myśl o niczym konkretnym
- Wyobraź sobie spokojne miejsce

**Efekt wizualny:**
- Ciepłe kolory: fiolet → indygo → niebieski
- Duże, powolne cząsteczki
- Centrum ekranu
- Spokojny, medytacyjny efekt

### Tryb 2: Beta (Uwaga)

**Jak osiągnąć:**
- Otwarte oczy
- Skoncentruj się (liczenie, czytanie)
- Aktywne myślenie
- Reaguj na bodźce

**Efekt wizualny:**
- Jasne kolory: czerwony → pomarańczowy → żółty
- Małe, szybkie cząsteczki
- Cały ekran
- Dynamiczny, energiczny efekt

### Tryb 3: Mieszany

**Efekt wizualny:**
- Pastelowe: magenta, cyan, biały
- Średnie cząsteczki
- Najbardziej spektakularne!
- Kombinacja obu trybów

---

## 🎮 Motion Features (Opcjonalnie)

**Nowa funkcja - interaktywne efekty oparte na ruchu głowy!**

### Co to jest?

Motion features wykorzystują **akcelerometr i żyroskop** z Muse S Athena do wykrywania ruchu i gestów głową, które wpływają na wizualizację w czasie rzeczywistym.

### Wymagania

- `ENABLE_MOTION = True` w `config.py` (domyślnie włączone)
- OpenMuse stream z presetem zawierającym ACC/GYRO:
  - ✅ `p20` (zalecane - EEG4 + ACC/GYRO, oszczędza baterię)
  - ✅ `p21` (EEG8 + ACC/GYRO)
  - ✅ `p1041` (wszystkie sensory, wysoka konsumpcja)

### Jak działa?

#### 1. **Gesty głową**
- **Skinięcie** (przód-dół-przód) → **Zmienia tryb wizualizacji** (Alpha/Beta/Mixed)
- **Potrząsanie** (lewo-prawo-lewo) → **Czyści ekran**

#### 2. **Nachylenie głowy wpływa na kierunek cząsteczek**
- Nachyl głowę **w lewo** → cząsteczki płyną w lewo
- Nachyl **w prawo** → cząsteczki w prawo
- Nachyl **do przodu/tyłu** → cząsteczki do przodu/tyłu

#### 3. **Intensywność ruchu wpływa na liczbę cząsteczek**
- Im więcej ruchu, tym więcej cząsteczek (0.5x - 2.0x)
- Nieruchomość → mniejsza liczba cząsteczek (flow state)

### Sterowanie

| Akcja | Efekt |
|-------|-------|
| Klawisz `M` | Przełącz motion features (włącz/wyłącz) |
| Skinięcie | Zmień tryb (Alpha → Beta → Mixed → Alpha...) |
| Potrząsanie | Wyczyść ekran |
| Nachyl głowę | Kierunek cząsteczek |
| Ruch głową | Więcej cząsteczek |

### Konfiguracja

W `config.py`:

```python
# === MOTION FEATURES ===
ENABLE_MOTION = True              # Włącz/wyłącz motion features
MOTION_GESTURE_CONTROL = True     # Gesty (skinięcie, potrząsanie)
MOTION_TILT_EFFECTS = True        # Nachylenie wpływa na wizualizację
MOTION_INTENSITY_SCALING = False  # Intensywność ruchu → liczba cząsteczek (domyślnie wyłączone)
```

### Wskazówki

- **Najlepsze efekty:** Lekkie ruchy głową podczas wizualizacji
- **Flow state:** Siedź nieruchomo → wizualizacja oparta tylko na EEG
- **Wyłącz motion:** Jeśli chcesz tylko EEG, naciśnij `M` lub ustaw `ENABLE_MOTION = False`
- **Oszczędność baterii:** Użyj `p20` zamiast `p1041` (dłuższy czas pracy!)

---

## ⚙️ Konfiguracja

### Plik `config.py` - Główne Ustawienia

**EEG:**
```python
SAMPLE_RATE = 256          # Hz (nie zmieniaj - Muse S spec)
WINDOW_SIZE = 64           # Próbek do FFT (64/128/256)
CALIBRATION_TIME = 10      # Sekundy kalibracji
```

**Wizualizacja:**
```python
WINDOW_WIDTH = 1280        # Rozdzielczość
WINDOW_HEIGHT = 720
FULLSCREEN = False         # True na produkcje
TARGET_FPS = 30            # Cel FPS
UPDATE_INTERVAL = 500      # ms między aktualizacjami EEG
```

**Cząsteczki:**
```python
PARTICLE_LIFETIME = 2.0    # Jak długo żyją (sekundy)
PARTICLE_SIZE_MIN = 8      # Minimalna wielkość
PARTICLE_SIZE_MAX = 40     # Maksymalna wielkość
MAX_PARTICLES = 150        # Limit na ekranie
```

**Debug:**
```python
DEBUG = True               # False na produkcje
SHOW_FPS = True            # Pokaż FPS
SHOW_SIGNAL_QUALITY = True # Pokaż jakość sygnału
```

### Własne Kolory

W `config.py` zmień palety:
```python
COLOR_PALETTES = {
    'alpha': [
        (138, 43, 226),   # Fiolet
        (75, 0, 130),     # Indygo
        (0, 0, 255),      # Niebieski
        (0, 128, 128),    # Turkusowy
    ],
    'beta': [
        (255, 0, 0),      # Czerwony
        (255, 165, 0),    # Pomarańczowy
        (255, 255, 0),    # Żółty
        (0, 255, 0),      # Zielony
    ],
    'mixed': [
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Cyan
        (255, 255, 255),  # Biały
        (255, 192, 203),  # Różowy
    ],
}
```

---

## 🔧 Dostosowywanie Wydajności

### Aplikacja Wolno Działa (< 30 FPS)

**Edytuj `config.py`:**
```python
# Zmniejsz obciążenie:
WINDOW_SIZE = 64          # Szybsze FFT
UPDATE_INTERVAL = 500     # Rzadziej przetwarzanie EEG
MAX_PARTICLES = 300       # Mniej cząsteczek
PARTICLE_LIFETIME = 1.0   # Krótsze życie
TARGET_FPS = 60           # Cel FPS
```

Lub zamknij inne aplikacje.

### Za Mało Cząsteczek na Ekranie

**Edytuj `config.py`:**
```python
MAX_PARTICLES = 1000        # Więcej
PARTICLE_LIFETIME = 3.0     # Dłuższe życie
PARTICLE_SIZE_MAX = 50      # Większe
```

### Za Dużo Cząsteczek

```python
MAX_PARTICLES = 200         # Mniej
PARTICLE_LIFETIME = 0.5     # Krótsze życie
```

### Brak Reakcji na Zmiany Stanu

**Przyczyny:**
1. Nieodpowiednia kalibracja
2. Słaba jakość sygnału
3. Za duże wygładzanie

**Rozwiązanie:**
```bash
# 1. Zrestartuj aplikację
# 2. Podczas kalibracji NAPRAWDĘ bądź spokojny
# 3. Sprawdź jakość sygnału (zwilż czujniki!)
```

W `eeg_processor.py` możesz zmienić wygładzanie:
```python
self.metric_history = {
    'attention': deque(maxlen=2),     # było 5
    'relaxation': deque(maxlen=2),    # było 5
}
```

---

## 📊 Interpretacja Wyników

### Pasma Częstotliwości

| Pasmo | Hz | Stan | Brain Art |
|-------|-----|------|-----------|
| **Delta** | 1-4 | Sen głęboki | Nie używane |
| **Theta** | 4-8 | Medytacja, senność | Mały wpływ |
| **Alpha** | 8-13 | **Relaksacja** | **Główny wskaźnik** |
| **Beta** | 13-30 | **Uwaga** | **Główny wskaźnik** |
| **Gamma** | 30-44 | Przetwarzanie | Dodatkowy |


## 🔗 Więcej Informacji

- **Instalacja:** Zobacz [INSTALLATION.md](INSTALLATION.md)
- **Festiwal:** Zobacz [FESTIVAL.md](FESTIVAL.md)
- **Rozwój:** Zobacz [DEVELOPMENT.md](DEVELOPMENT.md)

