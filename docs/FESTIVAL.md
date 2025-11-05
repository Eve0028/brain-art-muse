# Brain Art - Guide Festiwalowy

**Kompletna instrukcja przygotowania i prowadzenia stanowiska**

---

## 📋 Spis Treści

1. [Checklist Przed Festiwalem](#checklist-przed-festiwalem)
2. [Setup Stanowiska](#setup-stanowiska)
3. [Przebieg Sesji](#przebieg-sesji)
4. [Wskazówki dla Prowadzących](#wskazówki-dla-prowadzących)
5. [Materiały Edukacyjne](#materiały-edukacyjne)
6. [Troubleshooting na Miejscu](#troubleshooting-na-miejscu)

---

## ✅ Checklist Przed Festiwalem

### Tydzień Przed

- [ ] **Test całego systemu** z prawdziwym Muse S
- [ ] **Przygotuj backup laptop** (kopia aplikacji + dane)
- [ ] **Kup materiały:**
  - [ ] Żel przewodzący (lub chusteczki nawilżające)
  - [ ] Chusteczki/płyn do czyszczenia czujników
  - [ ] Powerbank (backup zasilania)
- [ ] **Wydrukuj materiały:**
  - [ ] Plakat wyjaśniający (wzór poniżej)
  - [ ] Instrukcja szybkiego resetu (laminowana)
  - [ ] QR code do screenshotów (jeśli używasz)

### Dzień Przed

- [ ] **Naładuj Muse S** do 100%
- [ ] **Test na laptopie festiwalowym:**
  - [ ] Instalacja aplikacji
  - [ ] Test z Muse
  - [ ] Test z monitorem/TV przez HDMI
- [ ] **Przećwicz pitch** (30 sekund):
  - Co to jest?
  - Jak działa?
  - Co zobaczysz?
- [ ] **Pakowanie:**
  - [ ] Laptop + ładowarka
  - [ ] Muse S + kabel USB-C
  - [ ] Kabel HDMI
  - [ ] Wszystkie materiały

### Rano w Dniu Festiwalu

- [ ] **Przyjdź wcześnie** (30-60 min przed otwarciem)
- [ ] **Setup stanowiska** (patrz sekcja poniżej)
- [ ] **Uruchom OpenMuse stream** w tle
- [ ] **Test end-to-end** z kimś z zespołu
- [ ] **Przygotuj backup:** nagranie demo na wypadek awarii

---

## 🎪 Setup Stanowiska

### Sprzęt Potrzebny

**Must-have:**
- ✅ Laptop z zainstalowaną aplikacją
- ✅ Duży monitor/TV (podłączony HDMI)
- ✅ Muse S naładowany
- ✅ Wygodne krzesło dla uczestnika
- ✅ Chusteczki/woda
- ✅ Wydrukowane materiały

**Nice-to-have:**
- Przedłużacz (zasilanie)
- Tablet (większy ekran dla uczestnika)
- Powerbank
- Kartki do notatek

### Układ Stanowiska

```
┌─────────────┐
│   Monitor   │  ← Dla publiczności/uczestnika
│   (duży TV) │
└─────────────┘
      │ HDMI
┌─────────────┐
│   Laptop    │  ← Na stoliku z boku
└─────────────┘
      │ Bluetooth
┌─────────────┐
│   Krzesło   │  ← Wygodne, naprzeciwko monitora
└─────────────┘
```

### Konfiguracja Software

**Terminal 1 (uruchom rano i zostaw):**
```bash
cd Brain_Art
# ⚡ ZALECANE: Tylko EEG (oszczędza baterię!)
OpenMuse stream --address 00:55:DA:B9:FB:2C --preset p20
# Zostaw działające w tle
```

**config.py - ustawienia festiwalowe:**
```python
FULLSCREEN = True          # Pełny ekran
DEBUG = False              # Wyłącz debug info
SHOW_FPS = False           # Nie pokazuj FPS
CALIBRATION_TIME = 5       # Szybka kalibracja
MAX_PARTICLES = 500        # Efektowne
PARTICLE_LIFETIME = 2.0    # Pełne kolory
```

**Uruchamianie aplikacji:**
```bash
# Terminal 2 (dla każdej nowej sesji możesz restartować)
python main.py
```

---

## ⏱️ Przebieg Sesji (1-2 minuty)

### Timeline

| Czas | Etap | Opis |
|------|------|------|
| 0:00 | **Wprowadzenie** (15s) | Witaj, wyjaśnij krótko |
| 0:15 | **Założenie Muse** (15s) | Dopasuj, zwilż, sprawdź |
| 0:30 | **Kalibracja** (5s) | Zamknij oczy, spokój |
| 0:35 | **Eksperymentowanie** (60s) | Zabawa, próby |
| 1:35 | **Zakończenie** (15s) | Screenshot, zdjęcie opaski |

### 0:00 - Wprowadzenie (15s)

**Co powiedzieć:**
```
"Cześć! 👋 Chcesz stworzyć sztukę swoim mózgiem?

Ta opaska czyta twoje fale mózgowe i zamienia je na kolory!
Za chwilę zobaczysz jak twój mózg tworzy sztukę."
```

**Krótko:**
- Kim jesteś, co robisz
- Co zobaczy uczestnik
- Ile to potrwa (~1 minuta)

### 0:15 - Założenie Muse (15s)

**Kroki:**
1. Weź Muse S
2. "Włóż tak, żeby czujniki były na czole i za uszami"
3. Dopasuj (wygodnie ale przylegająco) 
4. **Zwilż czujniki** - chusteczka nawilżająca
5. Sprawdź czy czujniki dotykają skóry (nie włosów!)

**Uwaga:** To najważniejszy krok! Jeśli czujniki są suche lub nie dotykają skóry = słaba jakość sygnału.

### 0:30 - Kalibracja (5s)

**Co powiedzieć:**
```
"Teraz przez 5 sekund zamknij oczy i oddychaj spokojnie.
Aplikacja poznaje twoją bazową aktywność mózgu."
```

**Ekran wizualizacji:** Pokaże duży komunikat "🎯 Kalibracja... Xs pozostało" z instrukcją "Zamknij oczy i oddychaj spokojnie"

**Terminal:** W tle będzie pokazywać postęp i jakość sygnału (np. "Remaining: 3.2s | Quality: [██████░░░░] 65%")

**Nie mów więcej** - daj uczestnikowi spokój podczas kalibracji. Komunikaty są wyświetlane na ekranie.

### 0:35 - Eksperymentowanie (60s)

**Co powiedzieć:**
```
"Teraz TY masz kontrolę! 🎨

Zobacz co się dzieje gdy:
- Zamkniesz oczy i się zrelaksujesz → spokojne, ciepłe kolory
- Otworzysz oczy i skoncentrujesz się → dynamiczne, jasne efekty

Spróbuj!  poćwiczyć liczenie do 100 w myślach..."
```

**Wskazówki:**
- Zachęcaj do eksperymentowania
- Pytaj: "Co czujesz gdy widzisz te kolory?"
- "Spróbuj teraz zamknąć oczy..."
- "A teraz otwórz i skoncentruj się na czymś..."

**Tryby (możesz pokazać):**
- Klawisz `1`: Tryb relaksacji (ciepłe kolory)
- Klawisz `2`: Tryb uwagi (dynamiczne)
- Klawisz `3`: Mieszany (najbardziej efektowny)

### 1:35 - Zakończenie (15s)

1. **Screenshot** - naciśnij `S`
   - "Chcesz zapisać swoją sztukę?"
   - Zapisze w `screenshots/`
   - Możesz pokazać QR code do przesłania

2. **Zdejmij Muse**
   - Ostrożnie, żeby nie plątać czujników

3. **Wyczyść czujniki**
   - Chusteczka do następnej osoby

4. **Restart aplikacji** (co ~10 osób)
   - Ctrl+C w terminalu 2
   - `python main.py` ponownie

---

## 💡 Wskazówki dla Prowadzących

### Techniczne

**Rutynowe:**
- **Co ~10 osób:** Restart aplikacji (reset kalibracji)
- **Co ~5 osób:** Wyczyść czujniki Muse dokładnie
- **Co ~30 min:** Sprawdź temperaturę laptopa
- **Co ~2h:** Sprawdź baterię Muse (powinna pokazywać w OpenMuse)

**Jeśli coś nie działa:**
- Restart aplikacji (Ctrl+C, python main.py)
- Sprawdź czy OpenMuse stream nadal działa
- Backup: pokaż nagranie demo

### Demonstracja

**Przed otwarciem:**
- Pokaż na sobie jak działa
- Przećwicz timing (1-2 minuty to dużo!)
- Sprawdź co mówisz vs co widać

**Wyjaśniaj co oznaczają kolory:**
- **Ciepłe/powolne** (fiolet, niebieski) = relaksacja (alpha)
- **Jasne/szybkie** (czerwony, żółty) = uwaga (beta)

**Nie mów za dużo:**
- Ludzie chcą próbować sami
- Krótkie instrukcje > długie wykłady

### Interakcja

**Pytania które działają:**
- "Co czujesz gdy widzisz te kolory?"
- "Spróbuj teraz zamknąć oczy... Zobacz różnicę!"
- "A teraz policz w myślach do 20..."
- "Widzisz jak się zmieniło?"

**Unikaj:**
- Za długich wyjaśnień technicznych (chyba że pytają)
- Zmuszania do konkretnych stanów ("musisz się bardziej zrelaksować")
- Oceniania ("źle, nie relaksujesz się")

---

## 🎓 Materiały Edukacyjne

### Plakat - Wzór

```
┌─────────────────────────────────────────┐
│                                         │
│     🧠 ZRÓB SZTUKĘ SWOIM MÓZGIEM! 🎨   │
│                                         │
│  [Zdjęcie Muse S na głowie]            │
│                                         │
│  JAK TO DZIAŁA?                         │
│  • Opaska czyta fale mózgowe (EEG)     │
│  • Alpha (relaks) → 💙 Spokojne kolory│
│  • Beta (uwaga) → 🔴 Dynamiczne efekty │
│                                         │
│  ⏱️  1-2 minuty                         │
│  🎨 Unikalna sztuka                    │
│  🧠 Twój mózg = artysta!               │
│                                         │
│  [QR code → więcej info/screenshots]   │
│                                         │
│  Genesys - Festiwal Nauki 2025         │
└─────────────────────────────────────────┘
```

### Co Wyjaśnić Uczestnikom

**Poziom 1 - Proste (dla wszystkich):**
```
"Twój mózg to 86 miliardów neuronów.
Komunikują się elektrycznie i tworzą fale.
My je mierzymy i zamieniamy na sztukę!"
```

**Poziom 2 - Średni (dla ciekawskich):**
```
Alpha (8-13 Hz) - Relaksacja
  → Pojawia się gdy zamkniesz oczy
  → Ciepłe, spokojne kolory

Beta (13-30 Hz) - Koncentracja
  → Aktywne myślenie, liczenie
  → Jasne, dynamiczne efekty
```

**Poziom 3 - Zaawansowany (dla pasjonatów):**
```
- EEG mierzy napięcie (~mikroVolty)
- FFT rozkłada na częstotliwości
- Filtrowanie pasmowe
- Brain-Computer Interfaces (BCI)
- Zastosowania: medytacja, ADHD, gaming, Neuralink
```

### Odpowiedzi na Częste Pytania

**"Czy to czyta moje myśli?"**
```
Nie! 😊 Czyta tylko ogólną aktywność elektryczną mózgu.
Nie możemy wiedzieć CO myślisz, tylko JAK aktywny jest twój mózg.
```

**"Czy to działa na każdym?"**
```
Tak! Każdy ma fale mózgowe.
Ale każdy ma trochę inne - jak odcisk palca.
Dlatego twoja sztuka będzie unikalna!
```

**"Czy mogę się tego nauczyć?"**
```
Tak! To się nazywa biofeedback.
Im częściej widzisz swoje fale mózgowe,
tym lepiej uczysz się je kontrolować.
Używane w treningach medytacji i koncentracji!
```

**"Czy to bezpieczne?"**
```
Tak! To tylko czytanie sygnału (jak słuchanie).
Nic nie wysyłamy do twojego mózgu.
Używane w medycynie i badaniach od dziesiątek lat.
```

---

## 🔧 Troubleshooting na Miejscu

### Problem: Aplikacja nie widzi streamu

**Szybka diagnoza:**
```bash
# Terminal 3
python -c "from mne_lsl.lsl import resolve_streams; print(len(resolve_streams()))"
# Powinno pokazać liczbę > 0
```

**Rozwiązanie:**
1. Sprawdź czy OpenMuse stream działa (Terminal 1)
2. Jeśli nie - restart: Ctrl+C, potem `OpenMuse stream --address ...`
3. Restart aplikacji (Terminal 2)

### Problem: Słaba jakość sygnału (niestabilne kolory)

**Szybka diagnoza:**
```
Naciśnij klawisz 'Q' w aplikacji
→ Zobaczysz raport jakości dla każdego czujnika
→ Konkretne ostrzeżenia co poprawić
```

**Checklist:**
- [ ] Zwilż czujniki (najważniejsze!)
- [ ] Czujniki dotykają skóry (nie włosów)
- [ ] Opaska dobrze przylega
- [ ] Usuń włosy spod czujników za uszami
- [ ] Uczestnik nie rusza głową

**Szybka naprawa:**
```
"Poczekaj, dostosujemy opaskę..."
[Zdejmij, zwilż czujniki mocniej, załóż ponownie]
"Spróbuj nie ruszać głową przez kalibrację"
```

**Interpretacja raportu jakości (klawisz Q):**
- 🟢 80-100%: Doskonała - kontynuuj
- 🟡 60-79%: Dobra - może zadziałać
- 🟠 40-59%: Akceptowalna - lepiej popraw
- 🔴 <40%: Słaba - KONIECZNIE zwilż czujniki!

### Problem: Brak reakcji na zmiany

**Przyczyna:** Źle zrobiona kalibracja

**Rozwiązanie:**
```
"Spróbujmy jeszcze raz kalibrację."
[Restart aplikacji: Ctrl+C, python main.py]
"Tym razem NAPRAWDĘ siedź spokojnie przez te 5 sekund"
```

### Problem: Muse się nie łączy (rano)

**Checklist:**
1. Muse włączony? (niebieska dioda)
2. Bluetooth w laptopie aktywny?
3. Muse nie połączony z telefonem? (wyłącz BT w telefonie)
4. `OpenMuse find` go widzi?

**Rozwiązanie:**
```bash
# Restart Muse
[Przytrzymaj przycisk 5s, poczekaj, włącz]

# Restart Bluetooth
Get-Service bthserv | Restart-Service

# Sprawdź
OpenMuse find
OpenMuse stream --address ...
```

### Problem: Aplikacja wolno działa (< 30 FPS)

**Szybka naprawa w config.py:**
```python
MAX_PARTICLES = 300        # Było 500
PARTICLE_LIFETIME = 1.0    # Było 2.0
UPDATE_INTERVAL = 500      # Rzadziej EEG
```

Restart aplikacji.

---

## 📊 Po Festiwalu

### Zbierz Feedback

- Ile osób przeszło?
- Średni czas sesji?
- Najczęstsze pytania?
- Co działało, co nie?

### Screenshoty

- Zebrane w `screenshots/`
- Można zrobić galerię/kolaż
- Post na social media
- Prezentacja dla koła naukowego

### Spostrzeżenia

- Co poprawić na następny raz?
- Jakie problemy techniczne?
- Pomysły na rozszerzenia?

---

## 🎯 Pro Tips

1. **Humor i luz** - ludzie przychodzą się bawić, nie na wykład
2. **Pokaż najpierw na sobie** - buduje zaufanie
3. **Zachęcaj do eksperymentowania** - nie ma "złych" wyników
4. **Krótkie kolejki** - 1-2 minuty na osobę = więcej ludzi
5. **Miej backup plan** - demo video, prezentacja slajdów
6. **Rób zdjęcia** - ludzie uwielbiają pamiątki
7. **Baw się** - jeśli ty się bawisz, oni też będą!

