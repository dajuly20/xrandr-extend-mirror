#!/bin/bash
#
# xrandr-extend-mirror - Multi-monitor screen mirroring and extending utility
# https://github.com/dajuly20/xrandr-extend-mirror
#
# Easily mirror one screen to another while keeping others extended,
# using simple screen numbers instead of cryptic port names.
#

set -e

# ============================================================================
# CONFIGURATION - Customize this for your setup
# ============================================================================

# Map screen numbers (left to right) to xrandr output names
# Run 'xrandr' to find your output names, then adjust this mapping
declare -A SCREEN_MAP=(
    [1]="DVI-I-3-2"
    [2]="DVI-I-2-1"
    [3]="eDP-1"
    [4]="HDMI-1"
)

# Default values
DEFAULT_MIRROR_SOURCE="eDP-1"
DEFAULT_MIRROR_TARGET="HDMI-1"
DEFAULT_EXTEND_MODE="3840x2160"
DEFAULT_EXTEND_RATE="30.00"
DEFAULT_MIRROR_MODE="1920x1080"
DEFAULT_MIRROR_RATE="50.00"

# ============================================================================
# FUNCTIONS
# ============================================================================

show_help() {
    cat << 'EOF'
xrandr-extend-mirror - Multi-monitor mirroring and extending utility

USAGE:
    xrandr-extend-mirror <command> [options]

COMMANDS:
    mirror <source> <target>     Mirror source screen to target
    mirror-num <src#> <tgt#>     Mirror using screen numbers (1-4)
    extend <display> <right-of>  Extend display to the right of another
    extend-num <disp#> <right#>  Extend using screen numbers
    layout                       Show ASCII diagram of screen layout
    list                         List connected displays (xrandr output)
    help                         Show this help message

EXAMPLES:
    # Mirror laptop screen to TV
    xrandr-extend-mirror mirror eDP-1 HDMI-1

    # Mirror screen #3 to screen #4 (using numbers)
    xrandr-extend-mirror mirror-num 3 4

    # Extend HDMI-1 to the right of eDP-1
    xrandr-extend-mirror extend HDMI-1 eDP-1

    # Show your screen layout
    xrandr-extend-mirror layout

CONFIGURATION:
    Edit the SCREEN_MAP array at the top of this script to match your setup.
    Run 'xrandr' to find your display output names.

EOF
}

show_layout() {
    cat << 'EOF'
Screen number layout (customize SCREEN_MAP in script for your setup):

                                                         ┌─────────────────────────────────────────┐
                                                         │                                         │
                                                         │             Philips LED TV              │
                                                         │                65' @4k                  │
                                                         │                                         │
                                                         │                                         │
┌──────────────┐   ┌──────────────┐                      │                                         │
│              │   │              │                      │                                         │
│ Monitor Left │   │Monitor Right │    ┌──────────┐      │                                         │
│   DVI-I-2-1  |   │   DVI-I-3-2  │    │  Laptop  │      │                 HDMI-1                  │
│              │   │              │    │   eDP-1  │      │                                         │
│      #1      │   │      #2      │    │    #3    │      │                   #4                    │
└──────────────┘   └──────────────┘    └──────────┘      └─────────────────────────────────────────┘

EOF
}

screen_num_to_name() {
    local num="$1"
    if [[ -z "${SCREEN_MAP[$num]}" ]]; then
        echo "Error: Unknown screen number '$num'. Valid: ${!SCREEN_MAP[*]}" >&2
        return 1
    fi
    echo "${SCREEN_MAP[$num]}"
}

list_displays() {
    echo "Connected displays:"
    echo "==================="
    xrandr | grep " connected"
    echo ""
    echo "All outputs:"
    xrandr
}

do_mirror() {
    local source="${1:-$DEFAULT_MIRROR_SOURCE}"
    local target="${2:-$DEFAULT_MIRROR_TARGET}"
    local mode="${3:-$DEFAULT_MIRROR_MODE}"
    local rate="${4:-$DEFAULT_MIRROR_RATE}"

    echo "Mirroring: $source -> $target"
    echo "Mode: ${mode} @ ${rate}Hz"
    echo ""
    echo "To switch back to extended mode:"
    echo "  $0 extend $target $source"
    echo ""

    xrandr --output "$target" --same-as "$source" --rate "$rate" --mode "$mode"
    echo "Done!"
}

do_mirror_num() {
    local src_num="$1"
    local tgt_num="$2"

    if [[ -z "$src_num" || -z "$tgt_num" ]]; then
        show_layout
        echo "Usage: $0 mirror-num <source-screen-#> <target-screen-#>"
        echo "Example: $0 mirror-num 3 4"
        return 1
    fi

    local source target
    source=$(screen_num_to_name "$src_num") || return 1
    target=$(screen_num_to_name "$tgt_num") || return 1

    echo "Screen #$src_num ($source) -> Screen #$tgt_num ($target)"
    do_mirror "$source" "$target"
}

do_extend() {
    local display="${1:-HDMI-1}"
    local right_of="${2:-eDP-1}"
    local mode="${3:-$DEFAULT_EXTEND_MODE}"
    local rate="${4:-$DEFAULT_EXTEND_RATE}"

    echo "Extending: $display to the right of $right_of"
    echo "Mode: ${mode} @ ${rate}Hz"
    echo ""

    xrandr --auto --output "$display" --mode "$mode" --rate "$rate" --right-of "$right_of"
    echo "Done!"
}

do_extend_num() {
    local disp_num="$1"
    local right_of_num="$2"

    if [[ -z "$disp_num" || -z "$right_of_num" ]]; then
        show_layout
        echo "Usage: $0 extend-num <display-#> <right-of-#>"
        echo "Example: $0 extend-num 4 3  (place screen #4 to the right of #3)"
        return 1
    fi

    local display right_of
    display=$(screen_num_to_name "$disp_num") || return 1
    right_of=$(screen_num_to_name "$right_of_num") || return 1

    echo "Screen #$disp_num ($display) -> right of Screen #$right_of_num ($right_of)"
    do_extend "$display" "$right_of"
}

# ============================================================================
# MAIN
# ============================================================================

case "${1:-help}" in
    mirror)
        shift
        do_mirror "$@"
        ;;
    mirror-num)
        shift
        do_mirror_num "$@"
        ;;
    extend)
        shift
        do_extend "$@"
        ;;
    extend-num)
        shift
        do_extend_num "$@"
        ;;
    layout)
        show_layout
        ;;
    list)
        list_displays
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run '$0 help' for usage information."
        exit 1
        ;;
esac
