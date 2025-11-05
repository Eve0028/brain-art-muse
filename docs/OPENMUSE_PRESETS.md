# OpenMuse Presets - Przewodnik

**Jak wybrać odpowiedni preset dla Muse S Athena**

---

## 🎯 Szybki Wybór

### ✅ **Zalecane Presety dla Brain Art:**

```bash
# ⭐ NAJLEPSZY: 4 aktywne kanały EEG + Motion (bez Optics - oszczędza baterię!)
OpenMuse stream --address <ADRES> --preset p20

# MINIMALISTYCZNY: 4 kanały EEG + Motion (bez Optics - najdłuższa bateria)
OpenMuse stream --address <ADRES> --preset p10

# ALTERNATYWNY: 8 kanałów EEG + Motion + Optics16 (wszystkie czujniki - wyższe zużycie baterii)
OpenMuse stream --address <ADRES> --preset p1041
```


## 📊 Szczegóły Presetów

### **Preset p10** - Podstawowy (4 kanały)
```
Kanały EEG: TP9, AF7, AF8, TP10
Częstotliwość: 256 Hz
Akcelerometr: TAK (3 osie) ✅
Żyroskop: TAK (3 osie) ✅
Optics: NIE ❌
Bateria: ⭐⭐⭐⭐⭐ (najdłuższa)
```

**📊 Strumienie LSL (potwierdzone testami):**
- **Muse_EEG**: 4 kanały @ 256 Hz
- **Muse_ACCGYRO**: 6 kanałów Motion @ 52 Hz ✅
- **Muse_BATTERY**: 1 kanał @ 1 Hz
- **Muse_OPTICS**: ❌ NIE (0 aktywnych kanałów)

**Idealny dla:**
- Standardowa wizualizacja Brain Art z motion features
- Długie sesje (oszczędza baterię - brak Optics)
- Gesty głową (skinięcie, potrząsanie)
- Proste BCI aplikacje

**💡 Różnica między p10 a p20:**
- Oba mają EEG4 + ACC/GYRO + brak Optics
- Różnica w konfiguracji EEG (p10 może mieć inne ustawienia firmware)

### **Preset p20** - Pełny z Motion ⭐ ZALECANY
```
Kanały EEG: 4 aktywne (TP9, AF7, AF8, TP10) ✅ POTWIERDZONE
Częstotliwość: 256 Hz
Akcelerometr: TAK (3 osie)
Żyroskop: TAK (3 osie)
Bateria: ⭐⭐⭐⭐ (dobra)
```

**✅ POTWIERDZONE TESTAMI:**
- **Dokumentacja GitHub PRAWIDŁOWA**: [p20 = EEG4](https://github.com/DominiqueMakowski/OpenMuse#presets)
- **Struktura LSL**: 8 kanałów (4 aktywne + 4 padding zerowy)
- **Test `debug_channels_detailed.py`** pokazał że kanały 5-8 mają **wszystkie wartości 0.00**

**📊 Strumienie LSL (potwierdzone testami):**
- **Muse_EEG**: 4 aktywne kanały @ 256 Hz (struktura LSL: 8 kanałów, kanały 5-8 są padding=0)
- **Muse_ACCGYRO**: 6 kanałów Motion @ 52 Hz
- **Muse_BATTERY**: 1 kanał @ 1 Hz
- **Muse_OPTICS**: ❌ NIE (preset p20 wyłącza Optics dla oszczędności baterii)

**Idealny dla:**
- Brain Art z motion features
- Gesty głową (skinięcie, potrząsanie)
- Efekty wizualne zależne od nachylenia głowy
- Długie sesje (oszczędza baterię - brak Optics)

**💡 Dlaczego p20 zamiast p1041?**
- Preset p1041 ma Optics16 (16 kanałów optycznych) = **wysokie zużycie baterii** (~2-3h)
- Preset p20 **bez Optics** = **niskie zużycie** (~5-6h) - **2-3x dłuższy czas pracy!**

---

## 🔍 Fakty o Preset p20

### **Weryfikacja przez Debug:**

Uruchomienie `python tests/debug_channels.py` pokazuje:

```
Muse_EEG:     8 kanałów @ 256 Hz  ← Główny strumień (4 aktywne + 4 padding)
Muse_ACCGYRO: 6 kanałów @ 52 Hz   ← Motion (ACC_X/Y/Z + GYRO_X/Y/Z)
Muse_BATTERY: 1 kanał @ 1 Hz      ← Stan baterii
Muse_OPTICS:  ❌ NIE (wyłączone dla oszczędności baterii)
```

### **Kanały EEG - POTWIERDZONE ✅**

**Struktura LSL: 8 kanałów (4 aktywne + 4 padding)**

- **Kanały 1-4: AKTYWNE** (TP9, AF7, AF8, TP10) - rzeczywiste sygnały EEG
- **Kanały 5-8: PADDING** - wszystkie wartości 0.00 (nieużywane)

**Weryfikacja:** `python tests/debug_channels.py`
```
Kanał 1: ✅ AKTYWNY - Std Dev: 11.71, Zakres: 71.96
Kanał 2: ✅ AKTYWNY - Std Dev: 31.47, Zakres: 122.94
Kanał 3: ✅ AKTYWNY - Std Dev: 97.05, Zakres: 349.07
Kanał 4: ✅ AKTYWNY - Std Dev: 52.87, Zakres: 187.37
Kanały 5-8: ❌ PADDING - wszystkie 0.00
```

### **Kanały Motion (6 total):**

```
Ch1-3: Akcelerometr (ACC_X, ACC_Y, ACC_Z) w [g]
Ch4-6: Żyroskop (GYRO_X, GYRO_Y, GYRO_Z) w [°/s]
```

### **Brain Art:**

**Automatycznie wykrywa i używa:**
- Strumień **Muse_EEG** (może być 8 kanałów) → **Brain Art używa tylko pierwszych 4** (TP9, AF7, AF8, TP10)
- Strumień **Muse_ACCGYRO** (6 kanałów) → dla motion features

**Topomapy** używają zawsze 4 kanałów (TP9, AF7, AF8, TP10) niezależnie od tego, ile kanałów wysyła OpenMuse.

---

## 🛠️ Jak Sprawdzić Co Wysyła Twój Preset?

### **Sprawdź które kanały mają DANE:**
```bash
python tests/debug_channels.py
```

Pokaże:
- Które kanały mają rzeczywiste sygnały (niezerowe)
- Które mogą być padding/unused w strukturze LSL
- Faktyczną liczbę aktywnych kanałów EEG

---

## 📋 Pełna Lista Presetów Muse

| Preset | Kanały EEG | Optics | Motion | Strumienie LSL | Źródło |
|--------|------------|--------|--------|----------------|--------|
| **p10** | 4 ✅ | — | ✅ | 4 | [GitHub](https://github.com/DominiqueMakowski/OpenMuse#presets) |
| **p20** | 4 ✅ | — | ✅ | 8 (4 aktywne) | [GitHub](https://github.com/DominiqueMakowski/OpenMuse#presets) |
| **p1041** | 8 | 16 | ✅ | 4 | [GitHub](https://github.com/DominiqueMakowski/OpenMuse#presets) |
| **p1042** | 8 | 16 | ✅ | 4 | [GitHub](https://github.com/DominiqueMakowski/OpenMuse#presets) |
| **p1044** | 8 | 8 | ✅ | 4 | [GitHub](https://github.com/DominiqueMakowski/OpenMuse#presets) |

**Źródło dokumentacji:** [OpenMuse GitHub](https://github.com/DominiqueMakowski/OpenMuse#presets)

---

## 🔬 Szczegóły Kanałów OPTICS (Preset p1041)

### **Co to jest OPTICS?**

**OPTICS** to strumień danych z czujników optycznych (PPG - Photoplethysmography) na Muse S Athena. Te czujniki mierzą:
- **Tętno** (heart rate) - przez wykrywanie zmian przepływu krwi
- **SpO2** (nasycenie tlenem) - przez analizę absorpcji światła
- **Przepływ krwi** (fNIRS - functional Near-Infrared Spectroscopy) - przez analizę odbicia światła

### **Struktura nazewnictwa kanałów:**

Format: `OPTICS_[POZYCJA]_[DŁUGOŚĆ_FALI]`

#### **POZYCJA** (położenie czujnika na opasce):
- **RI** = Right Inner (prawy wewnętrzny)
- **LI** = Left Inner (lewy wewnętrzny)
- **RO** = Right Outer (prawy zewnętrzny)
- **LO** = Left Outer (lewy zewnętrzny)

#### **DŁUGOŚĆ_FALI** (typ światła):
- **AMB** = Ambient (światło otoczenia) - kompensacja światła zewnętrznego
- **RED** = Red (światło czerwone ~660nm) - używane do pomiaru SpO2
- **IR** = Infrared (podczerwień ~880nm) - używane do pomiaru tętna
- **NIR** = Near-Infrared (bliska podczerwień ~850nm) - używane do fNIRS (przepływ krwi)

### **16 Kanałów OPTICS w preset p1041:**

| Kanał | Nazwa | Opis |
|-------|-------|------|
| 1 | `OPTICS_RI_AMB` | Prawy wewnętrzny - światło otoczenia |
| 2 | `OPTICS_LI_AMB` | Lewy wewnętrzny - światło otoczenia |
| 3 | `OPTICS_RI_RED` | Prawy wewnętrzny - światło czerwone (SpO2) |
| 4 | `OPTICS_LI_RED` | Lewy wewnętrzny - światło czerwone (SpO2) |
| 5 | `OPTICS_RO_AMB` | Prawy zewnętrzny - światło otoczenia |
| 6 | `OPTICS_LO_AMB` | Lewy zewnętrzny - światło otoczenia |
| 7 | `OPTICS_RO_RED` | Prawy zewnętrzny - światło czerwone (SpO2) |
| 8 | `OPTICS_LO_RED` | Lewy zewnętrzny - światło czerwone (SpO2) |
| 9 | `OPTICS_RI_IR` | Prawy wewnętrzny - podczerwień (tętno) |
| 10 | `OPTICS_LI_IR` | Lewy wewnętrzny - podczerwień (tętno) |
| 11 | `OPTICS_RI_NIR` | Prawy wewnętrzny - bliska podczerwień (fNIRS) |
| 12 | `OPTICS_LI_NIR` | Lewy wewnętrzny - bliska podczerwień (fNIRS) |
| 13 | `OPTICS_RO_IR` | Prawy zewnętrzny - podczerwień (tętno) |
| 14 | `OPTICS_LO_IR` | Lewy zewnętrzny - podczerwień (tętno) |
| 15 | `OPTICS_RO_NIR` | Prawy zewnętrzny - bliska podczerwień (fNIRS) |
| 16 | `OPTICS_LO_NIR` | Lewy zewnętrzny - bliska podczerwień (fNIRS) |

### **Zastosowania:**

- **AMB** - Kompensacja światła zewnętrznego (redukcja szumu)
- **RED** - Pomiar SpO2 (nasycenie tlenem krwi)
- **IR** - Pomiar tętna (heart rate)
- **NIR** - Analiza przepływu krwi (fNIRS) - aktywacja kory mózgowej

### **⚠️ Uwaga:**

- **Brain Art NIE używa** kanałów OPTICS - to tylko informacja dla użytkowników zainteresowanych danymi biometrycznymi
- **Optics16 zużywa dużo baterii** (~2-3h pracy vs ~5-6h bez Optics)
- Dla Brain Art **nie potrzebujesz** preset p1041 - użyj **p20** (bez Optics) dla lepszej wydajności baterii

---

## 💡 Rekomendacje

### **Dla Większości Użytkowników:**
```bash
OpenMuse stream --address <ADRES> --preset p20
```
**Dlaczego?**
- 4 kanały EEG (wystarczające)
- ACC/GYRO dla motion features (gesty, nachylenie)
- Dobra równowaga między funkcjami a baterią
- Brain Art automatycznie używa tylko pierwszych 4 kanałów (TP9, AF7, AF8, TP10)


## 🔧 Zmiana Presetu

### **Zatrzymaj obecny stream:**
```bash
# Ctrl+C w terminalu z OpenMuse stream
```

### **Uruchom z nowym presetem:**
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p10
```

### **Zrestartuj Brain Art:**
```bash
python main.py
```

---

## 🐛 Troubleshooting

### **Problem: Brak ACC/GYRO**

**Użyj preset p20 lub p21:**
```bash
OpenMuse stream --address <ADRES> --preset p20
```

---

## 📚 Więcej Informacji

- **[INSTALLATION.md](INSTALLATION.md)** - Setup OpenMuse
- **[QUICK_START.md](../QUICK_START.md)** - Szybki start
- **[MOTION_AXES.md](MOTION_AXES.md)** - Motion features

---

**Podsumowanie:** Używaj preset **p20** dla pełnej funkcjonalności Brain Art. Brain Art automatycznie obsługuje motion (6 kanałów ACC/GYRO) i używa tylko 4 kanałów EEG! 🎯

