# 🔋 Oszczędzanie Baterii - Muse S Athena

**Przewodnik jak maksymalnie wydłużyć czas pracy baterii**

---

## ⚡ Problem: Szybkie Rozładowywanie

Muse S Athena ma **wiele czujników**, które zużywają energię:
- ✅ **EEG** (4 kanały) - to czego potrzebujemy (TP9, AF7, AF8, TP10)
- ✅ **Akcelerometr/Żyroskop** - opcjonalne, używane przez motion features (gesty, tilt)
- ❌ **PPG** (tętno, SpO2) - DUŻE zużycie energii!
- ❌ **fNIRS** (jeśli aktywne) - dodatkowe zużycie

**Domyślnie OpenMuse włącza WSZYSTKIE czujniki** (preset `p1041`) 🔋💨

---

## ✅ Rozwiązanie: Preset `p20` - EEG + Motion (bez Optics)!

### Zamiast tego:
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C
# Domyślny preset p1041 = wszystkie czujniki
```

### Użyj tego:
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
# Preset p20 = EEG4 + ACC/GYRO (bez Optics - oszczędza baterię!)
```

### Alternatywnie:
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p21
# Preset p21 = alternatywna konfiguracja EEG
```

---

## 📊 Oficjalna Tabela Presetów (OpenMuse)

**Źródło:** [GitHub OpenMuse - Presets Table](https://github.com/DominiqueMakowski/OpenMuse)

| Preset | EEG | Optics (PPG/fNIRS) | ACC/GYRO | Battery | Red LED | Zużycie | Czas Pracy* |
|--------|-----|-------------------|----------|---------|---------|---------|-------------|
| **`p20`** | **EEG4** | **—** (brak) | ✅ | ✅ | off | 🟢 **Najniższe** | **~5-6h** |
| **`p21`** | **EEG4** | **—** (brak) | ✅ | ✅ | off | 🟢 **Najniższe** | **~5-6h** |
| `p50` | EEG4 | — | ✅ | ✅ | off | 🟢 Niskie | ~5-6h |
| `p51` | EEG4 | — | ✅ | ✅ | off | 🟢 Niskie | ~5-6h |
| `p60` | EEG4 | — | ✅ | ✅ | off | 🟢 Niskie | ~5-6h |
| `p61` | EEG4 | — | ✅ | ✅ | off | 🟢 Niskie | ~5-6h |
| `p1035` | EEG4 | Optics4 | ✅ | ✅ | dim | 🟡 Średnie | ~4h |
| `p1034` | EEG8 | Optics8 | ✅ | ✅ | bright | 🟡 Średnie-wysokie | ~3-4h |
| `p1043` | EEG8 | Optics8 | ✅ | ✅ | bright | 🟡 Średnie-wysokie | ~3-4h |
| `p1044` | EEG8 | Optics8 | ✅ | ✅ | dim | 🟡 Średnie | ~3-4h |
| `p1045` | EEG8 | Optics4 | ✅ | ✅ | dim | 🟡 Średnie | ~3-4h |
| `p1046` | EEG8 | Optics4 | ✅ | ✅ | — | 🟡 Średnie | ~3-4h |
| **`p1041`** | **EEG8** | **Optics16** | ✅ | ✅ | **bright** | 🔴 **NAJWYŻSZE** | **~2-3h** |
| `p1042` | EEG8 | Optics16 | ✅ | ✅ | bright | 🔴 Wysokie | ~2-3h |
| `p4129` | EEG8 | Optics4 | ✅ | ✅ | dim | 🟡 Średnie | ~3-4h |

*Przybliżone wartości, mogą się różnić w zależności od użytkowania

### 📝 Legenda:
- **EEG4**: 4 główne kanały (TP9, AF7, AF8, TP10)
- **EEG8**: 8 kanałów (4 główne + 4 AUX)
- **Optics**: PPG (tętno, SpO2) + fNIRS (przepływ krwi)
  - **Optics4**: 4 kanały optyczne
  - **Optics8**: 8 kanałów optycznych
  - **Optics16**: 16 kanałów optycznych (NAJWIĘCEJ!)
- **ACC/GYRO**: Akcelerometr + Żyroskop (pomiar ruchu)

---

## 🎯 Kluczowa Różnica dla Brain Art

### 🔴 p1041 (domyślny) zużywa baterię przez:
1. **Optics16** - 16 kanałów optycznych (PPG + fNIRS) 💨💨💨
2. **Red LED bright** - jasne czerwone LED 💡
3. **EEG8** - 8 kanałów EEG (OK, ale niepotrzebne dla Brain Art)

### 🟢 p20 oszczędza baterię przez:
1. **Brak Optics** - czujniki optyczne całkowicie wyłączone ✅
2. **Red LED off** - LED wyłączone ✅  
3. **EEG4** - tylko 4 kanały (wystarczające dla Brain Art) ✅
4. **ACC/GYRO włączone** - potrzebne dla motion features (gesty, tilt) ✅

**Efekt:** Czas pracy **2-3x dłuższy**! 🎉

---

## 💡 Dodatkowe Wskazówki Oszczędzania

### 1. **Wyłącz Optics (PPG/fNIRS) - najważniejsze!**
**Optics** (PPG dla tętna/SpO2 + fNIRS dla przepływu krwi) to **największy pożeracz baterii**:
- **Optics16** (p1041): 16 kanałów optycznych = OGROMNE zużycie! 💨💨💨
- **Optics8** (p1034): 8 kanałów = duże zużycie
- **Optics4** (p1035): 4 kanały = średnie zużycie
- **Brak Optics** (p20/p21): TYLKO EEG = minimalne zużycie ✅

Preset `p20` **całkowicie wyłącza** czujniki optyczne!

### 2. **Zmniejsz jasność LEDów** (jeśli urządzenie ma)
Muse S Athena może mieć wskaźniki LED - sprawdź w aplikacji Muse czy można je przyciemnić.

### 3. **Ładuj regularnie**
Nie dopuszczaj do pełnego rozładowania (<10%) - skraca żywotność baterii.

### 4. **Przechowuj właściwie**
- Temperatura pokojowa (18-25°C)
- Nie zostawiaj w pełnym słońcu
- Przy dłuższym przechowaniu: ~50% naładowania

### 5. **Wyłącz po użyciu**
Długie przytrzymanie przycisku zasilania → wyłączenie (nie tylko disconnect).

---

## 📚 Zobacz Też

- [INSTALLATION.md](INSTALLATION.md) - Setup OpenMuse z presetami
- [FESTIVAL.md](FESTIVAL.md) - Optymalizacja dla długich sesji
- [README.md](../README.md) - Główna dokumentacja
