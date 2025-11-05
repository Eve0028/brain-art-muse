# 📚 Dokumentacja Brain Art

Oto folder dokumentacji projektu **Brain Art**!

## 📖 Dostępna Dokumentacja

> **Note:** Documentation is available in two languages:
> - **Polish** (PL) - files in `docs/` directory
> - **English** (EN) - files in `docs/eng/` directory

### Dla Użytkowników

1. **[INSTALLATION.md](INSTALLATION.md)** 🔧
   - Szczegółowa instrukcja instalacji krok po kroku
   - Konfiguracja sprzętu (Muse S Athena, dongle Bluetooth)
   - Pierwsze uruchomienie i troubleshooting
   - Rozwiązywanie problemów z połączeniem

2. **[INSTRUCTION.md](INSTRUCTION.md)** 🎮
   - Jak używać aplikacji
   - Sterowanie i skróty klawiszowe
   - Tryby wizualizacji (Alpha, Beta, Mixed)
   - Wskazówki dla użytkowników

3. **[FESTIVAL.md](FESTIVAL.md)** 🎪
   - Przygotowanie stoiska na festiwal naukowy
   - Checklista sprzętu
   - Timeline sesji z uczestnikami
   - Wskazówki dla prezenterów
   - Troubleshooting na żywo

4. **[BATTERY_SAVING.md](BATTERY_SAVING.md)** 🔋
   - Jak oszczędzać baterię Muse S Athena
   - Presety OpenMuse (p20 vs p1041)
   - Wydłużenie czasu pracy o 100%!
   - Porównanie czujników i zużycia energii

### Dla Deweloperów

5. **[DEVELOPMENT.md](DEVELOPMENT.md)** 💻
   - Architektura systemu
   - API modułów
   - Algorytmy przetwarzania sygnału
   - Rozszerzenia i modyfikacje
   - Uruchamianie testów i debugowanie

6. **[QUALITY_METRICS.md](QUALITY_METRICS.md)** 📊
   - Szczegóły metryk jakości sygnału EEG
   - Wagi i progi
   - Interpretacja wyników

7. **[EEG_MONITOR.md](EEG_MONITOR.md)** 🧠
   - Opcjonalne okno monitora EEG
   - Raw traces i topomapy
   - Wizualizacja w czasie rzeczywistym

8. **[FILTERING.md](FILTERING.md)** ⚡
   - Filtracja sygnału EEG (detrending, notch, band-pass)
   - Filtr notch 50Hz/60Hz dla zakłóceń elektrycznych
   - Dokumentacja techniczna filtrów

## 🚀 Szybki Start

Jeśli dopiero zaczynasz, przejdź do:
1. **[INSTALLATION.md](INSTALLATION.md)** - zainstaluj wszystko
2. **[INSTRUCTION.md](INSTRUCTION.md)** - naucz się używać

Jeśli przygotowujesz stoisko na festiwal:
→ **[FESTIVAL.md](FESTIVAL.md)**

Jeśli chcesz modyfikować kod:
→ **[DEVELOPMENT.md](DEVELOPMENT.md)**

## 📝 Struktura Dokumentacji

```
docs/
├── README.md              # Ten plik (PL)
├── INSTALLATION.md        # Setup i instalacja (PL)
├── INSTRUCTION.md         # Instrukcja użytkownika (PL)
├── FESTIVAL.md            # Poradnik festiwalowy (PL)
├── BATTERY_SAVING.md      # Oszczędzanie baterii (PL)
├── DEVELOPMENT.md         # Dokumentacja techniczna (PL)
├── EEG_MONITOR.md         # Monitor EEG (PL)
├── QUALITY_METRICS.md     # Metryki jakości (PL)
├── FILTERING.md           # Filtrowanie sygnału (PL)
│
└── eng/                   # English documentation
    ├── INSTALLATION.md    # Installation guide (EN)
    ├── USER_GUIDE.md      # User manual (EN)
    ├── BATTERY_SAVING.md  # Battery optimization (EN)
    └── DEVELOPMENT.md     # Developer docs (EN)
```

## 🔗 Zobacz Też

- [README główny](../README.md) - Przegląd projektu
- [README_PL.md](../README_PL.md) - Dokumentacja w języku polskim
- [config.py](../config.py) - Wszystkie ustawienia
- [docs/eng/](eng/) - Dokumentacja w języku angielskim

---

**Brain Art** - Interactive EEG Visualization | v1.0.0

