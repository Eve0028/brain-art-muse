# Metryki Jakości Sygnału EEG

**Dokumentacja techniczna sprawdzania jakości sygnału w Brain Art**

---

## 🎯 Przegląd

System sprawdzania jakości analizuje sygnał EEG z każdego kanału Muse S (TP9, AF7, AF8, TP10) i ocenia go na podstawie 6 metryk. Wynik końcowy to liczba 0-100, gdzie:

- **🟢 80-100**: Excellent (Doskonała jakość)
- **🟡 60-79**: Good (Dobra jakość)
- **🟠 40-59**: Acceptable (Akceptowalna jakość)
- **🔴 <40**: Poor (Słaba jakość)

---

## 📊 Metryki (6)

### 1. Wariancja Sygnału (30% wagi)

**Co mierzy:** Zmienność amplitudy sygnału EEG

**Interpretacja:**
- **Za niska** (<10 µV²): Słaby kontakt czujnika ze skórą
- **Optymalna** (50-500 µV²): Dobry kontakt, czysty sygnał
- **Za wysoka** (>10000 µV²): Artefakty ruchu, zakłócenia

**Dlaczego ważna:**  
Wariancja pokazuje czy czujnik w ogóle odbiera sygnał biologiczny. Jeśli jest za niska, czujnik może nie dotykać skóry lub być suchy.

---

### 2. Amplituda (20% wagi)

**Co mierzy:** Zakres amplitudy peak-to-peak sygnału

**Interpretacja:**
- **Za niska** (<10 µV): Słaby kontakt
- **Optymalna** (50-200 µV): Typowy dla EEG
- **Za wysoka** (>500 µV): Artefakty (mrugnięcia, ruch mięśni)

**Dlaczego ważna:**  
Normalna amplituda EEG to 10-100 µV. Jeśli jest znacznie wyższa, to prawdopodobnie artefakty elektromiograficzne (EMG) z mięśni.

---

### 3. Moc Alpha (15% wagi)

**Co mierzy:** Obecność fal alpha (8-13 Hz) w spektrum

**Interpretacja:**
- **Wysoka** (>20% mocy całkowitej): Wyraźny alpha peak - dobry znak!
- **Średnia** (10-20%): Umiarkowany alpha
- **Niska** (<5%): Brak alpha (może być OK gdy oczy otwarte)

**Dlaczego ważna:**  
Fale alpha są najbardziej charakterystyczne dla spokojnego EEG przy zamkniętych oczach. Ich obecność potwierdza że sygnał jest biologiczny, a nie szum.

---

### 4. Zakłócenia Sieciowe (15% wagi)

**Co mierzy:** Moc przy 50Hz (zakłócenia elektryczne z sieci)

**Interpretacja:**
- **Niska** (<15% mocy całkowitej): Dobre ekranowanie
- **Średnia** (15-30%): Zauważalne zakłócenia
- **Wysoka** (>30%): Silne zakłócenia z sieci

**Dlaczego ważna:**  
50Hz (w EU) lub 60Hz (w US) to częstotliwość prądu zmiennego. Jeśli jest wysoka, oznacza słabe ekranowanie lub zakłócenia z urządzeń elektrycznych w pobliżu.

---

### 5. Artefakty (15% wagi)

**Co mierzy:** Obecność nagłych skoków, "szpilek" w sygnale

**Metody:**
- **Kurtosis**: Wysoka wartość (>10) = dużo outlierów
- **Max gradient**: Wysoka wartość (>100 µV/próbkę) = nagłe skoki

**Interpretacja:**
- **Czysto** (kurtosis <5, gradient <50): Brak artefaktów
- **Umiarkowane** (kurtosis 5-10, gradient 50-100): Małe artefakty
- **Duże** (kurtosis >10, gradient >100): Częste artefakty (ruch, mrugnięcia)

**Dlaczego ważne:**  
Artefakty zaburzają analizę i mogą być mylone z prawdziwym sygnałem EEG.

---

### 6. Stacjonarność (5% wagi)

**Co mierzy:** Stabilność sygnału w czasie

**Metoda:**
- Dzieli sygnał na 4 części
- Oblicza wariancję każdej części
- Współczynnik zmienności (CV) wariancji

**Interpretacja:**
- **Stabilny** (CV <0.3): Sygnał jednolity w czasie
- **Umiarkowanie stabilny** (CV 0.3-0.8): Małe wahania
- **Niestabilny** (CV >0.8): Duże zmiany (ruch, zmienne warunki)

**Dlaczego ważna:**  
Stabilny sygnał oznacza stabilne warunki pomiaru (dobry kontakt, brak ruchu).

---

## 🧮 Wzory

### Ogólna Jakość Kanału

```
Quality = 0.30 × Variance_score
        + 0.20 × Amplitude_score  
        + 0.15 × Alpha_power_score
        + 0.15 × Line_noise_score
        + 0.15 × Artifacts_score
        + 0.05 × Stationarity_score
```

### Ogólna Jakość Systemu

```
Overall_Quality = średnia(Quality_TP9, Quality_AF7, Quality_AF8, Quality_TP10)
```

---

## 🔍 Jak Używać

### Podczas Kalibracji

System automatycznie pokazuje jakość na pasku postępu:
```
⏱️  Pozostało: 3.5s | Jakość: [████████░░] 80%
```

Jeśli jakość <60%, otrzymasz ostrzeżenia:
```
⚠️  UWAGA: Jakość sygnału poniżej 60%
💡 Zalecenia:
   ⚠️  TP9: Bardzo niski sygnał - zwilż czujnik!
   ⚠️  AF7: Artefakty ruchu
```

### Podczas Użytkowania

**W konsoli (jeśli SHOW_SIGNAL_QUALITY = True):**
```
🟢 Jakość: 85% | Uwaga: 0.67 | Relaks: 0.45
```

**Naciśnij 'Q' dla szczegółowego raportu:**
```
📊 RAPORT JAKOŚCI SYGNAŁU EEG
============================================================
🎯 Jakość ogólna: 82/100 - 🟢 Excellent

📡 Jakość kanałów:
  TP9: [████████████████░░░░] 80/100
  AF7: [█████████████████░░░] 85/100
  AF8: [██████████████████░░] 90/100
  TP10: [███████████████░░░░] 75/100

✅ Brak ostrzeżeń - sygnał dobrej jakości!
```

---

## 🛠️ Troubleshooting przez Metryki

| Problem | Metryka | Rozwiązanie |
|---------|---------|-------------|
| Brak reakcji na zamykanie oczu | Alpha power niska | Sprawdź kontakt, zwilż |
| Niestabilne kolory | Stationarity niska | Minimalizuj ruch |
| Dziwne, gwałtowne zmiany | Artifacts wysokie | Rozluźnij szczękę, nie mrugaj |
| Ciągły szum | Line noise wysokie | Odsuń telefon, laptop zasilany |
| Zerowy sygnał | Variance bardzo niska | Zwilż czujniki! |
| Przesterowanie | Amplitude bardzo wysoka | Artefakty EMG - relaks |

---

## 📚 Referencje

### Typowe wartości EEG (Muse S):

| Parametr | Typowy zakres |
|----------|---------------|
| Amplituda | 10-100 µV |
| Wariancja | 50-500 µV² |
| Alpha power (oczy zamknięte) | 5-15 µV² |
| Beta power (oczy otwarte) | 2-8 µV² |
| SNR | >10 dB |

### Pasma częstotliwości:

| Pasmo | Hz | Typowa moc |
|-------|-----|------------|
| Delta | 1-4 | 100-200 µV² |
| Theta | 4-8 | 50-100 µV² |
| **Alpha** | 8-13 | **30-60 µV²** |
| **Beta** | 13-30 | **20-40 µV²** |
| Gamma | 30-44 | 10-20 µV² |

---

## 💻 API

### Szybkie sprawdzenie (w głównej pętli):

```python
from signal_quality import quick_quality_check

quality = quick_quality_check(eeg_data)  # Returns 0-100
```

### Szczegółowe sprawdzenie:

```python
from signal_quality import detailed_quality_check

result = detailed_quality_check(eeg_data, print_report=True)
# result = {
#     'overall_quality': 85,
#     'channel_quality': [80, 85, 90, 75],
#     'channel_metrics': [...],
#     'warnings': [],
#     'status': '🟢 Excellent',
# }
```

### Przez MuseConnector:

```python
connector = MuseConnector(mode='lsl')
connector.connect()

# Automatycznie aktualizowane przy każdym get_eeg_data()
overall = connector.get_overall_quality()  # 0-100
per_channel = connector.get_signal_quality()  # [80, 85, 90, 75]
warnings = connector.get_quality_warnings()  # ['⚠️  TP9: ...', ...]

# Szczegółowy raport
connector.print_quality_status()
```

---

## 🔬 Zaawansowane

### Optymalizacja Performance

- **Szybkie sprawdzenie** (`quick_quality_check`): ~50ms, wszystkie metryki (używa `assess_quality`)
- **Pełne sprawdzenie** (`detailed_quality_check`): ~50ms, wszystkie metryki + szczegółowy raport
- W głównej pętli: używaj pełnego co 500ms (config.UPDATE_INTERVAL)
- Dla debugowania: używaj `print_quality_status()` na żądanie (klawisz 'Q')

### Dostosowanie Progów

W `signal_quality.py`:
```python
self.thresholds = {
    'variance_min': 10,      # µV²
    'variance_max': 10000,   
    'amplitude_max': 500,    # µV
    'alpha_power_min': 0.1,  
    'line_noise_max': 0.3,   
}
```

### Własne Metryki

Rozszerz `SignalQualityChecker`:
```python
def _check_my_metric(self, data):
    # Twoja logika
    return {'value': result, 'score': 0-100}
```

---

**Pytania? Zobacz:** 
- [INSTALLATION.md](INSTALLATION.md) - troubleshooting
- [DEVELOPMENT.md](DEVELOPMENT.md) - API i rozwój
- `signal_quality.py` - kod źródłowy
