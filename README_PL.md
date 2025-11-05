# 🧠 Brain Art - Muse S Athena

**Interaktywna aplikacja do tworzenia sztuki za pomocą fal mózgowych**

Uczestnik "maluje" kolorowe obrazy używając stanu uwagi (beta/gamma) lub relaksacji (alpha).

---

## ⚡ Szybki Start (3 minuty)

### 1. (Opcjonalnie) Utwórz Virtual Environment

**Zalecane:** Użyj venv do izolacji zależności projektu:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

**Deaktywacja:**
```bash
deactivate
```

### 2. Instalacja

**Opcja A: Instalacja editable:**
```bash
pip install -e .
```

**Opcja B: Instalacja produkcyjna:**
```bash
pip install .
```

### 3. Znajdź Muse S
Włącz Muse S (niebieska dioda) i uruchom:
```bash
OpenMuse find
```
Zapisz adres MAC (np. `00:55:DA:B9:FB:2C`)

### 4. Uruchom
**Terminal 1:**
```bash
# ⚡ ZALECANE: Tylko EEG (oszczędza baterię)
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20

# Lub domyślny (wszystkie czujniki):
# OpenMuse stream --address 00:55:DA:B9:FB:2C
```

**Terminal 2:**
```bash
python main.py
```

Opcjonalnie **Terminal 3:**
```bash
# Wizualizacja sygnałów EEG
OpenMuse view
```

### 5. Gotowe! 🎨
- **Kalibracja**: 10 sekund z zamkniętymi oczami
- **Maluj**: Eksperymentuj z zamykaniem oczu i koncentracją!

**Pełna instalacja:** Zobacz [INSTALLATION.md](docs/INSTALLATION.md)

---

## 🎮 Sterowanie

| Klawisz | Akcja |
|---------|-------|
| `SPACJA` | Wyczyść ekran |
| `1` | Tryb Relaksacja (Alpha) - ciepłe kolory |
| `2` | Tryb Uwaga (Beta) - dynamiczne efekty |
| `3` | Tryb Mieszany |
| `S` | Screenshot |
| `Q` | Sprawdź jakość sygnału |
| `M` | Przełącz motion features (włącz/wyłącz) 🆕 |
| `ESC` | Wyjście |

**Gesty głową (jeśli motion features włączone):**
- 👍 **Skinięcie** (pochylenie głową i wyprost) → Zmienia tryb
- 👎 **Potrząsanie** (lewo-prawo-lewo) → Czyści ekran
- 🔄 **Nachylenie** → Kierunek cząsteczek

---

## 💡 Jak To Działa?

### Tryby Wizualizacji:

**🔵 Tryb Alpha (Relaksacja)**
- Jak osiągnąć: Zamknij oczy, głębokie oddychanie
- Efekt: Ciepłe kolory (fiolet → niebieski), powolne ruchy

**🔴 Tryb Beta (Uwaga)**  
- Jak osiągnąć: Skoncentruj się (liczenie, myślenie)
- Efekt: Jasne kolory (czerwony → żółty), szybkie cząsteczki

**⭐ Tryb Mieszany**
- Kombinacja obu - najbardziej spektakularne!

### Techniczne:
- **EEG**: 4 kanały (TP9, AF7, AF8, TP10) @ 256 Hz
- **FFT**: Analiza pasm częstotliwości (Alpha: 8-13 Hz, Beta: 13-30 Hz)
- **LSL**: Streaming przez OpenMuse (dedykowane dla Muse S Athena)

---

## 🔋 Bateria Szybko Się Rozładowuje?

**Użyj preset `p20` - Tylko EEG4, bez czujników optycznych:**
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
```

**Co wyłącza p20:**
- ❌ **Optics** (PPG/fNIRS) - 16 kanałów optycznych ← **największe oszczędności!**
- ❌ **Red LED** - jasne czerwone LED

**Co zachowuje p20:**
- ✅ **EEG4** - 4 główne kanały EEG @ 256 Hz (wystarczające dla Brain Art!)
- ✅ **ACC/GYRO** - akcelerometr i żyroskop
- ✅ **Pełna funkcjonalność** Brain Art

**Efekt:** Czas pracy zwiększony o **100-150%** (z ~2-3h do ~5-6h)! 🎉

📚 **Szczegóły:** [Oficjalna tabela presetów OpenMuse](https://github.com/DominiqueMakowski/OpenMuse#presets) | [docs/BATTERY_SAVING.md](docs/BATTERY_SAVING.md)

---

## 🔧 Szybkie Rozwiązywanie Problemów

### Muse się nie łączy
```bash
# Sprawdź czy Muse jest włączony (niebieska dioda)
# Zamknij aplikację Muse na telefonie
# Spróbuj ponownie:
OpenMuse find
```

### Słaba jakość sygnału
1. Zwilż czujniki wodą
2. Dopasuj opaskę (dobrze przylegaj do skóry)
3. Odsuń włosy spod czujników

### Za wolne / Za mało na ekranie
Edytuj `config.py`:
```python
# Więcej cząsteczek:
MAX_PARTICLES = 1000
PARTICLE_LIFETIME = 3.0

# Szybsze przetwarzanie:
UPDATE_INTERVAL = 500
WINDOW_SIZE = 64
```

**Więcej troubleshooting:** [docs/INSTALLATION.md](docs/INSTALLATION.md)

---

## 📊 Monitor EEG

Oprócz okna Brain Art, możesz otworzyć **drugie okno z podglądem sygnałów EEG**:

**Monitor pokazuje:**
- 📈 Raw EEG traces (**4 kanały** - TP9, AF7, AF8, TP10) - jeśli włączone w konfiguracji, ale zalecam korzytać z `OpenMuse view`
- 🧠 Topomapy Alpha/Beta (aktywność **wszystkich elektrod**)
- 📊 Wizualizacja w czasie rzeczywistym

```bash
python main.py
# Wybierz "y" gdy zapyta o monitor EEG
```

Auto-start: `SHOW_EEG_MONITOR = True` w `config.py`

---

## 📚 Dokumentacja

- **[INSTALLATION.md](INSTALLATION.md)** - Instalacja, OpenMuse, konfiguracja, troubleshooting
- **[FESTIVAL.md](FESTIVAL.md)** - Kompletny guide festiwalowy (checklist, przebieg, materiały)
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Dla deweloperów (architektura, API, rozszerzenia)
- **[QUALITY_METRICS.md](QUALITY_METRICS.md)** - Dokumentacja metryk jakości sygnału

---

## 📋 Wymagania

**Hardware:**
- Muse S Athena
- Laptop z Windows 11 (Bluetooth wbudowany wystarczy!)
- Opcjonalnie: Duży monitor/TV (HDMI)

**Software:**
- Python 3.12 (testowane tylko na tej wersji)
- OpenMuse (zainstaluje się z `requirements.txt`)

---

## 📂 Struktura Projektu

```
Brain_Art/
├── main.py                 # Punkt wejścia aplikacji
├── config.py               # Centralna konfiguracja
├── requirements.txt        # Zależności Python
├── pyproject.toml          # Konfiguracja pakietu
│
├── src/                    # Moduły źródłowe
│   ├── muse_connector.py   # Połączenie z Muse S (LSL streaming)
│   ├── eeg_processor.py    # Przetwarzanie sygnału EEG (FFT, analiza pasm)
│   ├── brain_visualizer.py # System wizualizacji cząsteczek
│   ├── eeg_visualizer.py   # Opcjonalne okno monitora EEG
│   ├── motion_processor.py # Wykrywanie gestów głową (ACC/GYRO)
│   ├── signal_quality.py   # Metryki jakości sygnału
│   └── performance_optimizer.py # Optymalizacja wydajności
│
├── utils/                  # Narzędzia pomocnicze
│   └── find_muse.py        # Wyszukiwanie urządzeń
│
├── tests/                  # Zestaw testów
│   ├── test_system.py      # Testy integracyjne systemu
│   ├── test_eeg_visualizer.py
│   └── ... 
│
├── docs/                   # Dokumentacja
│   ├── INSTALLATION.md       # Przewodnik instalacji
│   ├── FESTIVAL.md         # Przewodnik festiwalowy
│   ├── DEVELOPMENT.md           # Dokumentacja deweloperska
│   └── ...                 # Dodatkowe dokumenty
│
└── screenshots/            # Zapisane zrzuty ekranu
```

---

## 🙏 Podziękowania

- **OpenMuse**: https://github.com/DominiqueMakowski/OpenMuse
- **Pygame**: https://www.pygame.org/
- **MNE-LSL**: https://mne.tools/mne-lsl/
- **SciPy**: Signal processing

---

## 📄 Licencja

Open-source - używaj i modyfikuj jak chcesz!
