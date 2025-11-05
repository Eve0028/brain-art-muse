# Instalacja i Setup - Brain Art

## 📋 Wymagania

**Hardware:**
- Muse S Athena
- Laptop z Windows 11 (wbudowany Bluetooth wystarczy)
- Opcjonalnie: USB dongle BLED112 (backup)

**Software:**
- Python 3.12 (testowane tylko na tej wersji)
- ~200 MB miejsca na dysku

---

## 🔧 Instalacja Krok po Kroku

### 1. Sprawdź Python

```bash
python --version
```

Jeśli nie masz Python 3.12:
- Pobierz z https://www.python.org/downloads/

### 2. (Opcjonalnie) Utwórz Virtual Environment

**Zalecane:** Użyj venv do izolacji zależności projektu:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

Po aktywacji prompt powinien pokazać `(venv)`.

**Deaktywacja:**
```bash
deactivate
```

### 3. Zainstaluj Zależności

**Opcja A: Instalacja editable:**

```bash
cd Brain_Art
pip install -e .
```

To zainstaluje pakiet w trybie editable (zmiany w kodzie są od razu widoczne) oraz wszystkie zależności:
- **OpenMuse** - dedykowane wsparcie dla Muse S Athena
- **MNE-LSL** - Lab Streaming Layer
- **pygame, numpy, scipy** - wizualizacja i przetwarzanie

**Opcja B: Instalacja produkcyjna (bez editable):**

```bash
cd Brain_Art
pip install .
```

To zainstaluje pakiet normalnie (kopiuje do site-packages) - importy działają tak samo z dowolnego katalogu, ale zmiany w kodzie wymagają reinstalacji.

**Opcja C: Tradycyjna instalacja (tylko zależności):**

```bash
cd Brain_Art
pip install -r requirements.txt
```

⚠️ **Uwaga:** Opcja C nie instaluje pakietu `brain-art`, więc importy z `src.*` będą wymagały modyfikacji `sys.path` w testach.

### 4. Test Instalacji

```bash
python -c "import pygame, numpy, scipy, OpenMuse; print('✅ Wszystko OK!')"
```

Jeśli błąd:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

## ✨ OpenMuse - Dlaczego i Jak?

### Dlaczego OpenMuse?

[OpenMuse](https://github.com/DominiqueMakowski/OpenMuse) to **jedyne rozwiązanie z pełnym wsparciem dla Muse S Athena**:


**Znajdź Muse:**
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

**Presets (opcjonalnie):**
```bash
# ⚡ ZALECANE: Tylko EEG (oszczędza baterię!)
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
# lub
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p21

# Wszystkie czujniki (domyślny - zużywa więcej baterii)
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p1041
```

**🔋 Oszczędzanie Baterii:**

Według [oficjalnej dokumentacji OpenMuse](https://github.com/DominiqueMakowski/OpenMuse#presets):

| Preset | EEG | Optics (PPG/fNIRS) | ACC/GYRO | Red LED | Zużycie Baterii |
|--------|-----|-------------------|----------|---------|-----------------|
| **`p20`/`p21`** | **EEG4** | **—** (brak) | ✅ | off | 🟢 **Najniższe** |
| `p1041` (domyślny) | EEG8 | Optics16 | ✅ | bright | 🔴 **Najwyższe** |

💡 **Rekomendacja dla Brain Art:** Używaj `p20`!
- ✅ **EEG4** (4 główne kanały) - w zupełności wystarczające
- ❌ Bez czujników optycznych (PPG/fNIRS) - **największe oszczędności!**
- ❌ Bez jasnego LED
- **Efekt:** Czas pracy **2-3x dłuższy** (z ~2-3h do ~5-6h)! 🎉

**Nagrywanie:**
```bash
OpenMuse record --address 00:55:DA:B9:FB:2C --duration 60 --outfile session.txt
```

**Wizualizacja live:**
```bash
OpenMuse view
```

---

## 🚀 Pierwsze Uruchomienie

### Krok 1: Przygotuj Muse S

**Ładowanie:**
- Pełne naładowanie: ~2 godziny
- Bateria: ~10 godzin pracy
- Czerwona dioda = ładowanie, zgasła = naładowane

**Zakładanie:**
- Czujniki z przodu (AF7, AF8) na czole nad brwiami
- Czujniki z tyłu (TP9, TP10) za uszami
- Opaska wygodna ale przylegająca

**Jakość sygnału:**
- **Zwilż czujniki!** (najważniejsze)
- Woda, żel przewodzący
- Czujniki muszą dotykać skóry
- Odsuń włosy

### Krok 2: Znajdź MAC Address

```bash
# Włącz Muse (naciśnij przycisk - niebieska dioda)
OpenMuse find
# Zapisz wyświetlony adres MAC
```

### Krok 3: Uruchom Stream

**Terminal 1:**
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
# Czekaj na "Streaming data..."
```

### Krok 4: Uruchom Aplikację

**Terminal 2:**
```bash
python main.py
```

### Krok 5: Kalibracja

- Automatyczna (10 sekund)
- **Siedź spokojnie z zamkniętymi oczami**
- Oddychaj normalnie
- Nie myśl o niczym

### Krok 6: Eksperymentuj! 🎨

- Zamykaj/otwieraj oczy
- Koncentruj się na liczeniu
- Relaksuj się
- Zobacz jak zmieniają się kolory!

---

## 🔧 Rozwiązywanie Problemów

### OpenMuse find nie znajduje urządzenia

**Sprawdź:**
1. Muse włączony (niebieska dioda)
2. Bluetooth aktywny w Windows
3. Muse NIE połączony z telefonem (zamknij Muse app!)
4. W zasięgu (~2-3m)

**Rozwiązanie:**
```bash
# Restart Muse (przytrzymaj 5s, poczekaj, włącz)
# Restart Bluetooth
Get-Service bthserv | Restart-Service
# Spróbuj ponownie
OpenMuse find
```

### Stream się łączy ale aplikacja nie widzi

```bash
# Sprawdź czy stream działa
OpenMuse view

# Sprawdź strumienie LSL
python -c "from mne_lsl.lsl import resolve_streams; print(resolve_streams())"
```

### Import errors

```bash
# Sprawdź instalację
pip list | findstr "OpenMuse pygame numpy brain-art"

# Jeśli używasz editable install:
pip install -e .  # Reinstalacja pakietu (zależności nie są reinstalowane jeśli już są)

# Jeśli używasz requirements.txt:
pip uninstall OpenMuse mne-lsl -y
pip install -r requirements.txt

# Sprawdź Python
python -c "import sys; print(sys.executable)"

# Sprawdź czy pakiet jest zainstalowany
python -c "from src.muse_connector import MuseConnector; print('✅ Import OK')"
```

### Słaba jakość sygnału

**Objawy:**
- Niestabilne kolory
- Brak reakcji na zamykanie oczu
- Podczas kalibracji: jakość poniżej 60%

**Sprawdzenie jakości:**
```bash
# Podczas działania aplikacji naciśnij klawisz 'Q'
# Zobaczysz szczegółowy raport:
# - Jakość każdego kanału (TP9, AF7, AF8, TP10)
# - Metryki: wariancja, amplituda, alpha power, zakłócenia
# - Konkretne ostrzeżenia i zalecenia
```

**Rozwiązanie:**
1. **Zwilż czujniki** (najważniejsze!)
2. Dopasuj opaskę
3. Odsuń włosy spod czujników
4. Minimalizuj zakłócenia (telefon, WiFi)
5. Minimalizuj ruch głową
6. Sprawdź czy czujniki dotykają skóry (nie włosów)

---

## ⚙️ Konfiguracja

### Plik `config.py`

**Podstawowe ustawienia:**
```python
# EEG
SAMPLE_RATE = 256          # Nie zmieniaj (spec Muse S)
WINDOW_SIZE = 64           # FFT window (64/128/256)
CALIBRATION_TIME = 10      # Sekundy kalibracji

# Wizualizacja
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FULLSCREEN = False         # True na produkcję
TARGET_FPS = 30

# Cząsteczki
PARTICLE_LIFETIME = 2.0
MAX_PARTICLES = 150
PARTICLE_SIZE_MAX = 40

# Debug
DEBUG = True               # False na produkcję
SHOW_FPS = True
```

**Kolory:**
```python
COLOR_PALETTES = {
    'alpha': [
        (138, 43, 226),   # Fiolet
        (75, 0, 130),     # Indygo
        (0, 0, 255),      # Niebieski
    ],
    'beta': [
        (255, 0, 0),      # Czerwony
        (255, 165, 0),    # Pomarańczowy
        (255, 255, 0),    # Żółty
    ],
}
```

---

## 🎮 Sterowanie

| Klawisz | Akcja |
|---------|-------|
| `SPACJA` | Wyczyść ekran |
| `1` | Tryb Alpha (relaksacja) |
| `2` | Tryb Beta (uwaga) |
| `3` | Tryb Mieszany |
| `S` | Screenshot |
| `Q` | Sprawdź jakość sygnału (szczegółowy raport) |
| `ESC` | Wyjście |

## 📊 Monitor EEG (Opcjonalny)

Podczas uruchamiania możesz otworzyć **drugie okno z podglądem EEG**:
- **Raw EEG** - wszystkie kanały Muse S Athena (4-8 w czasie rzeczywistym)
- **Topomapy** - wizualizacja aktywności **wszystkich elektrod**
- **Zaawansowane** - używa biblioteki MNE-Python

Automatyczne uruchomienie w `config.py`:
```python
SHOW_EEG_MONITOR = True
```

---

## 📚 Dalsze Kroki

- **Użytkowanie:** Zobacz README.md
- **Festiwal:** Zobacz FESTIVAL.md
- **Rozwój:** Zobacz DEVELOPMENT.md
