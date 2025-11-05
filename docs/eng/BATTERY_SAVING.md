# 🔋 Battery Saving - Muse S Athena

**Guide to maximize battery life**

---

## ⚡ Problem: Fast Discharge

Muse S Athena has **many sensors** that consume power:
- ✅ **EEG** (4 channels) - what we need (TP9, AF7, AF8, TP10)
- ✅ **Accelerometer/Gyroscope** - optional, used by motion features (gestures, tilt)
- ❌ **PPG** (heart rate, SpO2) - HIGH energy consumption!
- ❌ **fNIRS** (if active) - additional consumption

**By default OpenMuse enables ALL sensors** (preset `p1041`) 🔋💨

---

## ✅ Solution: Preset `p20` - EEG + Motion (no Optics)!

### Instead of this:
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C
# Default preset p1041 = all sensors
```

### Use this:
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
# Preset p20 = EEG4 + ACC/GYRO (no Optics - saves battery!)
```

### Alternatively:
```bash
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p21
# Preset p21 = alternative EEG configuration
```

---

## 📊 Official Presets Table (OpenMuse)

**Source:** [GitHub OpenMuse - Presets Table](https://github.com/DominiqueMakowski/OpenMuse)

| Preset | EEG | Optics (PPG/fNIRS) | ACC/GYRO | Battery | Red LED | Consumption | Battery Life* |
|--------|-----|-------------------|----------|---------|---------|-------------|---------------|
| **`p20`** | **EEG4** | **—** (none) | ✅ | ✅ | off | 🟢 **Lowest** | **~5-6h** |
| **`p21`** | **EEG4** | **—** (none) | ✅ | ✅ | off | 🟢 **Lowest** | **~5-6h** |
| `p50` | EEG4 | — | ✅ | ✅ | off | 🟢 Low | ~5-6h |
| `p51` | EEG4 | — | ✅ | ✅ | off | 🟢 Low | ~5-6h |
| `p60` | EEG4 | — | ✅ | ✅ | off | 🟢 Low | ~5-6h |
| `p61` | EEG4 | — | ✅ | ✅ | off | 🟢 Low | ~5-6h |
| `p1035` | EEG4 | Optics4 | ✅ | ✅ | dim | 🟡 Medium | ~4h |
| `p1034` | EEG8 | Optics8 | ✅ | ✅ | bright | 🟡 Medium-high | ~3-4h |
| `p1043` | EEG8 | Optics8 | ✅ | ✅ | bright | 🟡 Medium-high | ~3-4h |
| `p1044` | EEG8 | Optics8 | ✅ | ✅ | dim | 🟡 Medium | ~3-4h |
| `p1045` | EEG8 | Optics4 | ✅ | ✅ | dim | 🟡 Medium | ~3-4h |
| `p1046` | EEG8 | Optics4 | ✅ | ✅ | — | 🟡 Medium | ~3-4h |
| **`p1041`** | **EEG8** | **Optics16** | ✅ | ✅ | **bright** | 🔴 **HIGHEST** | **~2-3h** |
| `p1042` | EEG8 | Optics16 | ✅ | ✅ | bright | 🔴 High | ~2-3h |
| `p4129` | EEG8 | Optics4 | ✅ | ✅ | dim | 🟡 Medium | ~3-4h |

*Approximate values, may vary depending on usage

### 📝 Legend:
- **EEG4**: 4 main channels (TP9, AF7, AF8, TP10)
- **EEG8**: 8 channels (4 main + 4 AUX)
- **Optics**: PPG (heart rate, SpO2) + fNIRS (blood flow)
  - **Optics4**: 4 optical channels
  - **Optics8**: 8 optical channels
  - **Optics16**: 16 optical channels (MOST!)
- **ACC/GYRO**: Accelerometer + Gyroscope (motion measurement)

---

## 🎯 Key Difference for Brain Art

### 🔴 p1041 (default) drains battery by:
1. **Optics16** - 16 optical channels (PPG + fNIRS) 💨💨💨
2. **Red LED bright** - bright red LEDs 💡
3. **EEG8** - 8 EEG channels (OK, but unnecessary for Brain Art)

### 🟢 p20 saves battery by:
1. **No Optics** - optical sensors completely disabled ✅
2. **Red LED off** - LED disabled ✅  
3. **EEG4** - only 4 channels (sufficient for Brain Art) ✅
4. **ACC/GYRO enabled** - needed for motion features (gestures, tilt) ✅

**Effect:** Battery life **2-3x longer**! 🎉

---

## 💡 Additional Battery Saving Tips

### 1. **Disable Optics (PPG/fNIRS) - most important!**
**Optics** (PPG for heart rate/SpO2 + fNIRS for blood flow) is the **biggest battery drain**:
- **Optics16** (p1041): 16 optical channels = HUGE consumption! 💨💨💨
- **Optics8** (p1034): 8 channels = high consumption
- **Optics4** (p1035): 4 channels = medium consumption
- **No Optics** (p20/p21): EEG ONLY = minimal consumption ✅

Preset `p20` **completely disables** optical sensors!

### 2. **Reduce LED brightness** (if device has it)
Muse S Athena may have LED indicators - check in Muse app if they can be dimmed.

### 3. **Charge regularly**
Don't let it fully discharge (<10%) - shortens battery life.

### 4. **Store properly**
- Room temperature (18-25°C)
- Don't leave in direct sunlight
- For longer storage: ~50% charge

### 5. **Turn off after use**
Long press power button → turn off (not just disconnect).

---

## 📚 See Also

- [INSTALLATION.md](INSTALLATION.md) - OpenMuse setup with presets
- [README.md](../../README.md) - Main documentation
