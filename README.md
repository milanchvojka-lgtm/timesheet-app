# 📊 Timesheet Analyzer

Webová aplikace pro analýzu pracovních výkazů Design týmu. Vytvořeno pomocí Streamlit.

## ✨ Funkce

- 📤 **Nahrání Excel souboru** - Drag & drop rozhraní pro nahrání exportu z Costlocker
- 📊 **Analýza projektů** - Přehled hodin a FTE podle projektů
- 👥 **Analýza podle osob** - FTE jednotlivých členů týmu
- 🎯 **Plánované vs. skutečné FTE** - Porovnání s možností úpravy plánovaných hodnot
- 🔧 **OPS aktivity** - Detailní analýza operačních aktivit (Jobs, Reviews, Hiring)
- 📈 **Interaktivní grafy** - Plotly vizualizace s možností přiblížení a exportu
- 📥 **Export do Excel** - Stažení zpracovaných dat včetně všech analýz

## 🚀 Rychlý start

### Lokální spuštění

1. **Nainstalujte závislosti:**
   ```bash
   cd timesheet-app
   pip install -r requirements.txt
   ```

2. **Spusťte aplikaci:**
   ```bash
   streamlit run app.py
   ```

3. **Otevřete v prohlížeči:**
   - Aplikace se automaticky otevře na `http://localhost:8501`
   - Nebo klikněte na odkaz v terminálu

### První použití

1. Klikněte na tlačítko "Browse files" v postranním panelu
2. Nahrajte Excel soubor s timesheety (export z Costlocker)
3. Aplikace automaticky zpracuje data a zobrazí všechny analýzy
4. V postranním panelu můžete upravit plánované FTE hodnoty
5. Stáhněte si Excel report pomocí tlačítka na konci stránky

## 📋 Formát vstupních dat

Excel soubor musí obsahovat následující sloupce:

| Sloupec | Popis |
|---------|-------|
| **Datum** | Datum záznamu (formát data) |
| **Projekt** | Název projektu (např. "Design tým OPS_2025") |
| **Osoba** | Jméno člena týmu |
| **Natrackováno** | Počet odpracovaných hodin (číslo) |
| **Popis** | Popis aktivity (text) |

## 🌐 Nasazení na Streamlit Cloud (ZDARMA)

### Postup nasazení:

1. **Vytvořte GitHub repository:**
   ```bash
   cd timesheet-app
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/timesheet-app.git
   git push -u origin main
   ```

2. **Nasaďte na Streamlit Cloud:**
   - Přejděte na [share.streamlit.io](https://share.streamlit.io)
   - Klikněte na "New app"
   - Vyberte své GitHub repository
   - Hlavní soubor: `app.py`
   - Klikněte na "Deploy"

3. **Připraveno!**
   - Aplikace bude dostupná na URL: `your-app-name.streamlit.app`
   - Automatické aktualizace při každém git push

## 🎨 Přizpůsobení

### Změna barev grafů:

V souboru `app.py` najděte funkce `create_bar_chart` a `create_comparison_chart` a upravte parametry:
- `main_color='#FF7CAC'` - hlavní barva
- `light_color='#FFD9E5'` - světlá barva pro porovnání

### Úprava kategorií OPS aktivit:

V třídě `TimesheetAnalyzer` upravte slovník `self.categories`:
```python
self.categories = {
    'Jobs': ['jobs', 'job'],
    'Reviews': ['review'],
    'Hiring': ['hiring'],
    'Meetings': ['meeting', 'schůzka']  # Přidat novou kategorii
}
```

### Změna výchozích plánovaných FTE:

V souboru `app.py` v sekci "Sidebar - Planned FTE inputs" upravte hodnoty:
```python
default_value = 1.0
if 'Chvojka' in person:
    default_value = 0.9  # Upravte podle potřeby
```

## 📊 Přehled analýz

### 1. Analýza podle projektů
- Celkové hodiny na projekt
- FTE (Full-Time Equivalent) pro každý projekt
- Procentuální podíl jednotlivých projektů

### 2. Analýza podle osob
- FTE pro každého člena týmu
- Porovnání s plánovanými hodnotami
- Celkové kapacity týmu

### 3. OPS aktivity
- Rozdělení do kategorií (Jobs, Reviews, Hiring, Ostatní)
- Celkový přehled i detaily podle jednotlivých osob
- Individuální grafy pro každého člena týmu

## 🛠️ Technologie

- **Streamlit** - Framework pro webové aplikace
- **Pandas** - Zpracování dat
- **Plotly** - Interaktivní grafy
- **openpyxl** - Práce s Excel soubory
- **holidays** - Výpočet českých svátků pro FTE

## 📝 Licence

Tento projekt je open-source a k dispozici pro použití podle potřeby.

## 🐛 Hlášení chyb

Pokud narazíte na problém:
1. Zkontrolujte formát vstupního Excel souboru
2. Ujistěte se, že máte nainstalované všechny závislosti
3. Zkuste restartovat aplikaci

## 🎯 Plánované vylepšení

- [ ] Možnost analyzovat více měsíců najednou
- [ ] Porovnání měsíc ku měsíci
- [ ] Export grafů jako PDF
- [ ] Nastavitelné rozsahy dat
- [ ] Cachování pro rychlejší opakované načítání
