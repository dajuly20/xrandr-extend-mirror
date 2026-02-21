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

## License

MIT
