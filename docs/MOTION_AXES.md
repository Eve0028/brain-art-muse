# 🧭 Mapowanie Osi - Muse S Athena

**Wyniki z `test_motion_axes.py`**  
**Testowane na:** Muse S Athena (4-kanałowy EEG + ACC/GYRO)  
**Preset:** OpenMuse `p20` (EEG4 + ACC/GYRO)

Dokument opisujący mapowanie osi akcelerometru i żyroskopu w Muse S Athena.

---

## 📊 Baseline (głowa nieruchoma, patrząc przed siebie)

```
ACC:  [-0.30, 0.04, 0.97] g
GYRO: [-1.7, -0.5, -0.6] °/s
```

**Interpretacja:**
- ACC Z ≈ 1g → Grawitacja działa w dół (głowa jest poziomo)
- ACC X ≈ -0.3g → Lekkie nachylenie (normalne)
- ACC Y ≈ 0g → Głowa nie jest pochylona na bok

---

## 🎯 Mapowanie Gestów

### 1. SKINIĘCIE (ukłon głową do przodu - patrzysz w dół)

**Ruch:** Normalną pozycja → Głowa w dół → Normalna pozycja

**Dominująca oś:**
- **ACC X: 1.400 g** ← Główna oś wykrywania!
- GYRO Y: 143.1 °/s (prędkość kątowa)

**Wykrywanie w kodzie:**
```python
acc_x = window[:, 0]  # Oś X!
x_range = max(acc_x) - min(acc_x)
if x_range > 0.8:  # Próg: 0.8g (test pokazał 1.4g)
    # Skinięcie wykryte!
```

**Implementacja:** `detect_nod()` w `motion_processor.py`

---

### 2. POCHYLENIE GŁOWY (ucho do ramienia)

**Ruch:** Głowa prosto → Ucho do lewego ramienia → Głowa prosto

**Dominująca oś:**
- **ACC Y: 1.377 g** ← Główna oś wykrywania!
- GYRO X: 124.3 °/s (prędkość kątowa)

**Wykrywanie w kodzie:**
```python
tilt_lr = acc[1]  # Oś Y!
# -1 = lewo, +1 = prawo
```

**Implementacja:** `get_head_tilt()` w `motion_processor.py`

---

### 3. POTRZĄSANIE (NIE - lewo-prawo)

**Ruch:** Szybkie: Lewo → Prawo → Lewo

**Dominująca oś:**
- **GYRO Z: 245.0 °/s** ← Główna oś wykrywania!
- ACC Y: 1.538 g (akceleracja podczas ruchu)

**Wykrywanie w kodzie:**
```python
gyro_z = window[:, 2]  # Oś Z!
max_speed = max(abs(gyro_z))
if max_speed > 150:  # Próg: 150°/s (test: 245°/s)
    # Sprawdź oscylacje (zmiany kierunku)
    if zero_crossings >= 2:
        # Potrząsanie wykryte!
```

**Implementacja:** `detect_shake()` w `motion_processor.py`

---

## 📐 Podsumowanie Mapowania

**Uwaga:** Wartość testowa to wynik rzeczywistego testu, a próg w kodzie to wartość progowa użyta w detekcji gestów.

| Ruch                    | Główna oś   | Wartość testowa | Próg w kodzie | Funkcja          |
|-------------------------|-------------|-----------------|---------------|------------------|
| Skinięcie (przód-dół)   | **ACC X**   | 1.400 g         | 0.8 g         | `detect_nod()`   |
| Pochylenie (lewo-prawo) | **ACC Y**   | 1.377 g         | 0.3 g         | `get_head_tilt()`|
| Nachylenie (przód-tył)  | **ACC X**   | 1.400 g         | 0.3 g         | `get_head_tilt()`|
| Potrząsanie (lewo-prawo)| **GYRO Z**  | 245.0 °/s       | 150 °/s       | `detect_shake()` |

---

## 🔧 Orientacja Muse S

```
           PRZÓD (patrzysz tu)
               ↑
               |
   LEWO ←─────●─────→ PRAWO
               |
               ↓
             TYŁ

ACC X: Przód-tył (pitch) - skinięcie
ACC Y: Lewo-prawo (roll) - pochylenie
ACC Z: Góra-dół - grawitacja (~1g)

GYRO X: Obrót wokół osi X (pochylenie)
GYRO Y: Obrót wokół osi Y (skinięcie)
GYRO Z: Obrót wokół osi Z (potrząsanie) ← Najważniejszy!
```

---

## 🧪 Jak przetestować

**1. Test mapowania osi:**
```bash
python test_motion_axes.py
```
Wykonaj każdy ruch i sprawdź które osie się zmieniają.

**2. Test wykrywania gestów:**
```bash
python test_motion.py
```
Sprawdź czy gesty są wykrywane poprawnie.

**3. Debug w aplikacji głównej:**
W `config.py`:
```python
DEBUG_MOTION = True  # Pokaż wartości ACC/GYRO w konsoli
```
