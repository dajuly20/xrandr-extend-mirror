# xrandr-extend-mirror

A simple bash utility to mirror some screens while extending others on Linux. Uses `xrandr` under the hood but provides an intuitive interface with screen numbers instead of cryptic port names.

## The Problem

You have multiple monitors and want to:
- Mirror your laptop screen to a TV (for presentations/movies)
- Keep your other monitors extended as usual

The Display Settings GUI often can't handle this mixed setup well. Raw `xrandr` commands are powerful but hard to remember.

## The Solution

```bash
# Mirror screen #3 (laptop) to screen #4 (TV)
./xrandr-extend-mirror.sh mirror-num 3 4

# Later, extend them again
./xrandr-extend-mirror.sh extend-num 4 3
```

## Installation

```bash
git clone https://github.com/dajuly20/xrandr-extend-mirror.git
cd xrandr-extend-mirror
chmod +x xrandr-extend-mirror.sh

# Optional: add to PATH
sudo ln -s "$(pwd)/xrandr-extend-mirror.sh" /usr/local/bin/xrandr-extend-mirror
```

## Usage

```
COMMANDS:
    mirror <source> <target>     Mirror source screen to target
    mirror-num <src#> <tgt#>     Mirror using screen numbers (1-4)
    extend <display> <right-of>  Extend display to the right of another
    extend-num <disp#> <right#>  Extend using screen numbers
    layout                       Show ASCII diagram of screen layout
    list                         List connected displays
    help                         Show help message
```

### Examples

```bash
# Show your screen layout with numbers
./xrandr-extend-mirror.sh layout

# Mirror using port names
./xrandr-extend-mirror.sh mirror eDP-1 HDMI-1

# Mirror using screen numbers (easier!)
./xrandr-extend-mirror.sh mirror-num 3 4

# Extend HDMI-1 to the right of laptop display
./xrandr-extend-mirror.sh extend HDMI-1 eDP-1

# List all connected displays
./xrandr-extend-mirror.sh list
```

## Configuration

Edit the `SCREEN_MAP` array at the top of the script to match your setup:

```bash
declare -A SCREEN_MAP=(
    [1]="DVI-I-3-2"    # Left external monitor
    [2]="DVI-I-2-1"    # Right external monitor
    [3]="eDP-1"        # Laptop built-in display
    [4]="HDMI-1"       # TV
)
```

Find your display names by running:
```bash
xrandr | grep " connected"
```

## Shell Integration (Optional)

Add these aliases to your `.bashrc` or `.zshrc` for quick access:

```bash
alias screen-mirror='/path/to/xrandr-extend-mirror.sh mirror-num'
alias screen-extend='/path/to/xrandr-extend-mirror.sh extend-num'
alias screen-layout='/path/to/xrandr-extend-mirror.sh layout'
```

## Requirements

- Linux with X11
- `xrandr` (usually pre-installed)
- Bash 4+ (for associative arrays)

---

## GUI-Version (xrandr-gui.py)

Zusätzlich zum Bash-Skript gibt es eine grafische Oberfläche, die das Verwalten von Bildschirmen noch einfacher macht.

### Installation der GUI

```bash
# Python 3 und GTK3 werden benötigt
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# GUI starten
./xrandr-gui.py

# Oder mit Desktop-Integration
cp xrandr-gui.desktop ~/.local/share/applications/
```

### Grundkonzept: Source und Target

Die GUI arbeitet mit zwei Bildschirmen, die du auswählen musst:

| Begriff | Bedeutung | Farbe in der GUI |
|---------|-----------|------------------|
| **Source** (Quelle) | Der "Referenz-Bildschirm" - an diesem orientiert sich die Positionierung | Blau |
| **Target** (Ziel) | Der Bildschirm, der gespiegelt oder verschoben wird | Orange |

**Wichtig**: Die Reihenfolge, in der du die Bildschirme auswählst, bestimmt Source und Target!
- **Erster Klick** = Source
- **Zweiter Klick** = Target

### Bedienung der GUI

```
┌─────────────────────────────────────────────────────────────┐
│ Display Configuration                              [⟳]      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  eDP-1   │    │ HDMI-1   │    │ DP-1     │             │
│   │1920x1080 │    │1920x1080 │    │2560x1440 │             │
│   │  SOURCE  │    │  TARGET  │    │          │             │
│   └──────────┘    └──────────┘    └──────────┘             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Selection:  eDP-1 (1920x1080)  →  HDMI-1 (1920x1080)       │
├─────────────────────────────────────────────────────────────┤
│ [Mirror Displays] [Extend →] [Extend ←] [Clear Selection]  │
├─────────────────────────────────────────────────────────────┤
│ Resolution: [1920x1080 ▼]    Refresh Rate: [60.00 ▼]       │
└─────────────────────────────────────────────────────────────┘
```

1. **Bildschirme werden automatisch erkannt** und als Monitor-Icons angezeigt
2. **Klicke auf den ersten Bildschirm** → wird zum Source (blau)
3. **Klicke auf den zweiten Bildschirm** → wird zum Target (orange)
4. **Wähle eine Aktion** (siehe unten)

### Die vier Aktionen erklärt

#### 1. Mirror Displays (Spiegeln)
```
Vorher:                          Nachher:
┌───────┐ ┌───────┐              ┌───────────────┐
│   A   │ │   B   │      →       │   A = B       │
└───────┘ └───────┘              │ (gleiches Bild)
                                 └───────────────┘
```
- Der Target-Bildschirm zeigt exakt das gleiche Bild wie der Source
- Beide Bildschirme bekommen dieselben Koordinaten (x=0, y=0)
- **Hinweis**: Das ist der Grund für "Überlappung" - technisch korrekt, da beide dasselbe anzeigen sollen

#### 2. Extend → (Target rechts von Source)
```
Vorher (überlappend):            Nachher:
┌───────────────┐                ┌───────┐┌───────┐
│   A + B       │        →       │   A   ││   B   │
│ (überlappt!)  │                │Source ││Target │
└───────────────┘                └───────┘└───────┘
```
- Platziert den Target-Bildschirm **rechts** neben den Source
- Behebt Überlappungen!

#### 3. Extend ← (Target links von Source)
```
Vorher (überlappend):            Nachher:
┌───────────────┐                ┌───────┐┌───────┐
│   A + B       │        →       │   B   ││   A   │
│ (überlappt!)  │                │Target ││Source │
└───────────────┘                └───────┘└───────┘
```
- Platziert den Target-Bildschirm **links** neben den Source
- Auch hier werden Überlappungen behoben!

#### 4. Clear Selection (Auswahl löschen)
- Setzt Source und Target zurück
- Erlaubt eine neue Auswahl

### Häufige Probleme und Lösungen

#### Problem: Bildschirme überlappen sich!

**Ursache**: Beide Bildschirme haben dieselben Koordinaten (z.B. beide bei x=0, y=0). Das passiert nach dem Spiegeln oder bei falscher Konfiguration.

**Lösung**:
1. Öffne die GUI
2. Wähle den **Hauptbildschirm als Source** (erster Klick)
3. Wähle den **überlappenden Bildschirm als Target** (zweiter Klick)
4. Klicke auf **"Extend →"** oder **"Extend ←"** je nachdem, wo der Bildschirm hin soll

#### Problem: Falsche Reihenfolge der Bildschirme

**Du willst**: Laptop links, externer Monitor rechts

| Schritt | Aktion |
|---------|--------|
| 1 | Klicke auf den **Laptop-Bildschirm** (wird Source) |
| 2 | Klicke auf den **externen Monitor** (wird Target) |
| 3 | Klicke auf **"Extend →"** (Target = extern → rechts von Source = Laptop) |

**Du willst**: Externer Monitor links, Laptop rechts

| Schritt | Aktion |
|---------|--------|
| 1 | Klicke auf den **Laptop-Bildschirm** (wird Source) |
| 2 | Klicke auf den **externen Monitor** (wird Target) |
| 3 | Klicke auf **"Extend ←"** (Target = extern → links von Source = Laptop) |

**Alternative**: Tausche einfach Source und Target!
| Schritt | Aktion |
|---------|--------|
| 1 | Klicke auf den **externen Monitor** (wird Source) |
| 2 | Klicke auf den **Laptop-Bildschirm** (wird Target) |
| 3 | Klicke auf **"Extend →"** (Target = Laptop → rechts von Source = extern) |

### Drag & Drop Layout

Die GUI unterstützt Drag & Drop für eine intuitive Bildschirm-Anordnung:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  eDP-1   │    │ HDMI-1   │    │ DP-1     │             │
│   │1920x1080 │    │1920x1080 │    │2560x1440 │  ← Drag me! │
│   └──────────┘    └──────────┘    └──────────┘             │
│                                                             │
│  Layout: [Drag displays to arrange]         [Apply Layout] │
└─────────────────────────────────────────────────────────────┘
```

1. **Ziehe einen Bildschirm** mit der Maus an die gewünschte Position
2. **Automatisches Einrasten**: Der Bildschirm rastet an Kanten anderer Bildschirme ein (rechts, links, oben, unten)
3. **Gelber Punkt**: Zeigt an, dass ungespeicherte Änderungen vorhanden sind
4. **"Apply Layout"**: Wendet alle Änderungen per xrandr an

**Wichtig**: Bildschirme können sich nicht überlappen - sie rasten immer an Kanten ein!

### Gespiegelte Bildschirme erkennen

Gespiegelte Bildschirme werden automatisch erkannt und besonders dargestellt:

```
┌──────────────────┐
│   eDP-1          │
│   1920x1080      │    ← Lila = gespiegelt
│   MIRRORED       │
│   = HDMI-1       │    ← zeigt welche Displays gespiegelt sind
└──────────────────┘
```

- **Lila Farbe**: Kennzeichnet gespiegelte Displays
- **"MIRRORED"**: Label für gespiegelte Bildschirme
- **"= HDMI-1"**: Zeigt an, mit welchem Display gespiegelt wird
- **"Unlink Mirrored"**: Button zum Aufheben der Spiegelung

### Optionen

- **Resolution**: Wähle die Auflösung für die Mirror/Extend-Operation
- **Refresh Rate**: Bildwiederholrate (60Hz für normale Monitore, 30Hz für einige TVs)

### Technische Details

Die GUI führt folgende xrandr-Befehle aus:

```bash
# Mirror
xrandr --output TARGET --same-as SOURCE --mode 1920x1080 --rate 60.00

# Extend rechts
xrandr --auto --output TARGET --mode 1920x1080 --rate 60.00 --right-of SOURCE

# Extend links
xrandr --auto --output TARGET --mode 1920x1080 --rate 60.00 --left-of SOURCE
```

### Tipps

1. **Nach dem Spiegeln wieder erweitern**: Wenn du gespiegelt hast und wieder separate Bildschirme willst, benutze "Extend →" oder "Extend ←"

2. **Falsch geklickt?** Klicke nochmal auf einen ausgewählten Bildschirm, um ihn abzuwählen, oder benutze "Clear Selection"

3. **Refresh-Button**: Wenn ein Bildschirm nicht angezeigt wird (z.B. nach dem Anstecken), klicke auf ⟳

## Ähnliche Tools

Es gibt bereits ähnliche Tools für Display-Management unter Linux:

| Tool | Verfügbarkeit | Beschreibung |
|------|---------------|--------------|
| **[ARandR](https://christian.amsuess.com/tools/arandr/)** | `apt install arandr` | Die bekannteste xrandr-GUI mit Drag&Drop |
| **wdisplays** | Wayland | Für wlroots-Compositors |
| **nwg-displays** | Wayland | Für Sway/Hyprland |
| **dippi** | `snap install dippi` | Berechnet DPI und Seitenverhältnis |

### Unterschiede zu ARandR

Dieses Tool bietet einige Vorteile gegenüber ARandR:

- **Source/Target-Workflow**: Einfaches Spiegeln/Erweitern durch Auswahl von zwei Displays
- **Erkennung gespiegelter Displays**: Visuelle Darstellung (lila) wenn Displays gespiegelt sind
- **Integrierter Unlink-Button**: Schnelles Aufheben der Spiegelung
- **Kombiniert CLI + GUI**: Bash-Skript für schnelle Terminal-Nutzung, GUI für visuelle Konfiguration

## License

MIT
