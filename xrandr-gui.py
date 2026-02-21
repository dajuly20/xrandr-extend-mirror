#!/usr/bin/env python3
"""
xrandr-extend-mirror GUI
A graphical interface for managing display mirroring and extending.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import subprocess
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Display:
    """Represents a connected display."""
    name: str
    width: int
    height: int
    x: int
    y: int
    is_primary: bool
    is_connected: bool
    modes: list  # Available resolutions
    current_mode: str
    current_rate: str


class DisplayWidget(Gtk.DrawingArea):
    """A widget that draws a visual representation of a display."""

    def __init__(self, display: Display, scale: float = 0.08, gui=None):
        super().__init__()
        self.display = display
        self.scale = scale
        self.selected = False
        self.is_source = False
        self.is_target = False
        self.gui = gui  # Reference to XrandrGUI for drag operations

        # Drag state
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.has_pending_changes = False
        self.is_mirrored = False  # Part of a mirrored group
        self.mirrored_with = []  # Names of displays this is mirrored with

        # Set size based on display resolution
        self.set_size_request(
            max(int(display.width * scale), 100),
            max(int(display.height * scale), 60)
        )

        self.connect('draw', self.on_draw)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )

        # Connect drag event handlers
        self.connect('button-press-event', self.on_button_press)
        self.connect('button-release-event', self.on_button_release)
        self.connect('motion-notify-event', self.on_motion_notify)

    def on_draw(self, widget, cr):
        """Draw the display representation."""
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height

        # Background color based on state
        if self.is_mirrored:
            cr.set_source_rgb(0.6, 0.3, 0.6)  # Purple for mirrored
        elif self.is_source:
            cr.set_source_rgb(0.2, 0.6, 0.9)  # Blue for source
        elif self.is_target:
            cr.set_source_rgb(0.9, 0.5, 0.2)  # Orange for target
        elif self.selected:
            cr.set_source_rgb(0.3, 0.7, 0.4)  # Green for selected
        else:
            cr.set_source_rgb(0.3, 0.3, 0.35)  # Dark gray

        # Draw rounded rectangle for monitor
        radius = 8
        cr.arc(radius, radius, radius, 3.14, 1.5 * 3.14)
        cr.arc(width - radius, radius, radius, 1.5 * 3.14, 2 * 3.14)
        cr.arc(width - radius, height - radius - 15, radius, 0, 0.5 * 3.14)
        cr.arc(radius, height - radius - 15, radius, 0.5 * 3.14, 3.14)
        cr.close_path()
        cr.fill()

        # Draw monitor stand
        stand_width = width * 0.3
        stand_height = 12
        cr.set_source_rgb(0.25, 0.25, 0.3)
        cr.rectangle((width - stand_width) / 2, height - stand_height - 3, stand_width, stand_height)
        cr.fill()

        # Draw monitor base
        base_width = width * 0.5
        base_height = 5
        cr.rectangle((width - base_width) / 2, height - base_height, base_width, base_height)
        cr.fill()

        # Draw screen bezel
        bezel = 4
        cr.set_source_rgb(0.15, 0.15, 0.18)
        cr.rectangle(bezel, bezel, width - 2 * bezel, height - 20 - 2 * bezel)
        cr.fill()

        # Draw screen content area (gradient to simulate display)
        screen_x = bezel + 3
        screen_y = bezel + 3
        screen_w = width - 2 * bezel - 6
        screen_h = height - 20 - 2 * bezel - 6

        if self.is_source or self.is_target:
            cr.set_source_rgb(0.2, 0.25, 0.35)
        else:
            cr.set_source_rgb(0.1, 0.12, 0.18)
        cr.rectangle(screen_x, screen_y, screen_w, screen_h)
        cr.fill()

        # Draw display name
        cr.set_source_rgb(1, 1, 1)
        cr.select_font_face("Sans", 0, 1)
        cr.set_font_size(11)

        text = self.display.name
        extents = cr.text_extents(text)
        cr.move_to((width - extents.width) / 2, screen_y + 18)
        cr.show_text(text)

        # Draw resolution
        cr.set_font_size(9)
        cr.set_source_rgb(0.7, 0.7, 0.7)
        res_text = f"{self.display.width}x{self.display.height}"
        extents = cr.text_extents(res_text)
        cr.move_to((width - extents.width) / 2, screen_y + 32)
        cr.show_text(res_text)

        # Draw mode indicator
        if self.is_mirrored:
            cr.set_source_rgb(0.9, 0.6, 0.9)
            mode_text = "MIRRORED"
        elif self.is_source:
            cr.set_source_rgb(0.4, 0.8, 1)
            mode_text = "SOURCE"
        elif self.is_target:
            cr.set_source_rgb(1, 0.7, 0.3)
            mode_text = "TARGET"
        else:
            mode_text = ""

        if mode_text:
            cr.set_font_size(10)
            extents = cr.text_extents(mode_text)
            cr.move_to((width - extents.width) / 2, screen_y + screen_h - 8)
            cr.show_text(mode_text)

        # Draw mirrored-with indicator
        if self.is_mirrored and self.mirrored_with:
            cr.set_font_size(8)
            cr.set_source_rgb(0.8, 0.8, 0.8)
            mirror_text = f"= {', '.join(self.mirrored_with)}"
            extents = cr.text_extents(mirror_text)
            cr.move_to((width - extents.width) / 2, screen_y + screen_h - 20)
            cr.show_text(mirror_text)

        # Draw "pending changes" indicator
        if self.has_pending_changes:
            cr.set_source_rgb(1, 0.8, 0.2)  # Yellow indicator
            cr.arc(width - 10, 10, 5, 0, 2 * 3.14159)
            cr.fill()

        return False

    def on_button_press(self, widget, event):
        """Handle button press for drag initiation."""
        if event.button == 1:  # Left mouse button
            self.dragging = True
            # Calculate offset from widget origin to click position
            self.drag_offset_x = event.x
            self.drag_offset_y = event.y
            # Change cursor to indicate dragging
            cursor = Gdk.Cursor.new_from_name(self.get_display(), "grabbing")
            self.get_window().set_cursor(cursor)
        return False  # Allow event to propagate for selection handling

    def on_button_release(self, widget, event):
        """Handle button release to end drag and snap to position."""
        if self.dragging and event.button == 1:
            self.dragging = False
            # Reset cursor
            self.get_window().set_cursor(None)

            if self.gui:
                # Get current widget position in container
                container = self.get_parent()
                if isinstance(container, Gtk.Fixed):
                    # Snap to nearest display edge
                    self.gui.snap_widget_position(self)

        return False

    def on_motion_notify(self, widget, event):
        """Handle mouse motion for dragging."""
        if self.dragging and self.gui:
            container = self.get_parent()
            if isinstance(container, Gtk.Fixed):
                # Calculate new position
                # Get widget's current position in the container
                alloc = self.get_allocation()
                parent_alloc = container.get_allocation()

                # Convert event coords to container coords
                new_x = alloc.x + event.x - self.drag_offset_x
                new_y = alloc.y + event.y - self.drag_offset_y

                # Clamp to container bounds
                new_x = max(0, min(new_x, parent_alloc.width - alloc.width))
                new_y = max(0, min(new_y, parent_alloc.height - alloc.height))

                # Move widget
                container.move(self, int(new_x), int(new_y))

        return True


class XrandrGUI(Gtk.Window):
    """Main application window."""

    def __init__(self):
        super().__init__(title="Display Mirror & Extend")
        self.set_default_size(900, 600)
        self.set_border_width(10)

        self.displays = []
        self.display_widgets = {}
        self.source_display = None
        self.target_display = None
        self.pending_layout_changes = {}  # {display_name: (relative_to, direction)}

        self.setup_ui()
        self.refresh_displays()

    def setup_ui(self):
        """Set up the user interface."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(header_box, False, False, 0)

        title_label = Gtk.Label()
        title_label.set_markup("<span size='large' weight='bold'>Display Configuration</span>")
        header_box.pack_start(title_label, False, False, 0)

        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_btn.set_tooltip_text("Refresh displays")
        refresh_btn.connect("clicked", self.on_refresh_clicked)
        header_box.pack_end(refresh_btn, False, False, 0)

        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<span size='small'>Click a display to select it as <b>Source</b>, "
            "then click another to select it as <b>Target</b></span>"
        )
        instructions.set_xalign(0)
        main_box.pack_start(instructions, False, False, 0)

        # Display area with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        main_box.pack_start(scrolled, True, True, 0)

        # Container for displays (will arrange them based on position)
        self.display_container = Gtk.Fixed()
        self.display_container.set_size_request(800, 300)
        scrolled.add(self.display_container)

        # Selection info box
        selection_frame = Gtk.Frame(label="Selection")
        main_box.pack_start(selection_frame, False, False, 0)

        selection_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        selection_box.set_border_width(10)
        selection_frame.add(selection_box)

        # Source info
        source_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        selection_box.pack_start(source_box, True, True, 0)

        source_title = Gtk.Label()
        source_title.set_markup("<b>Source Display</b>")
        source_box.pack_start(source_title, False, False, 0)

        self.source_label = Gtk.Label(label="(none selected)")
        self.source_label.set_name("source-label")
        source_box.pack_start(self.source_label, False, False, 0)

        # Arrow
        arrow_label = Gtk.Label()
        arrow_label.set_markup("<span size='xx-large'>→</span>")
        selection_box.pack_start(arrow_label, False, False, 0)

        # Target info
        target_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        selection_box.pack_start(target_box, True, True, 0)

        target_title = Gtk.Label()
        target_title.set_markup("<b>Target Display</b>")
        target_box.pack_start(target_title, False, False, 0)

        self.target_label = Gtk.Label(label="(none selected)")
        self.target_label.set_name("target-label")
        target_box.pack_start(self.target_label, False, False, 0)

        # Action buttons
        action_frame = Gtk.Frame(label="Actions")
        main_box.pack_start(action_frame, False, False, 0)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_border_width(10)
        action_box.set_homogeneous(True)
        action_frame.add(action_box)

        # Mirror button
        self.mirror_btn = Gtk.Button(label="Mirror Displays")
        self.mirror_btn.get_style_context().add_class("suggested-action")
        self.mirror_btn.connect("clicked", self.on_mirror_clicked)
        self.mirror_btn.set_sensitive(False)
        self.mirror_btn.set_tooltip_text("Mirror source display content to target display")
        action_box.pack_start(self.mirror_btn, True, True, 0)

        # Extend right button
        self.extend_right_btn = Gtk.Button(label="Extend → (Target right of Source)")
        self.extend_right_btn.connect("clicked", self.on_extend_right_clicked)
        self.extend_right_btn.set_sensitive(False)
        self.extend_right_btn.set_tooltip_text("Place target display to the right of source")
        action_box.pack_start(self.extend_right_btn, True, True, 0)

        # Extend left button
        self.extend_left_btn = Gtk.Button(label="Extend ← (Target left of Source)")
        self.extend_left_btn.connect("clicked", self.on_extend_left_clicked)
        self.extend_left_btn.set_sensitive(False)
        self.extend_left_btn.set_tooltip_text("Place target display to the left of source")
        action_box.pack_start(self.extend_left_btn, True, True, 0)

        # Clear selection button
        clear_btn = Gtk.Button(label="Clear Selection")
        clear_btn.connect("clicked", self.on_clear_clicked)
        action_box.pack_start(clear_btn, True, True, 0)

        # Layout action row
        layout_frame = Gtk.Frame(label="Layout")
        main_box.pack_start(layout_frame, False, False, 0)

        layout_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        layout_box.set_border_width(10)
        layout_frame.add(layout_box)

        layout_info = Gtk.Label()
        layout_info.set_markup("<span size='small'>Drag displays to arrange them. Changes are applied when you click 'Apply Layout'.</span>")
        layout_info.set_xalign(0)
        layout_box.pack_start(layout_info, True, True, 0)

        # Apply Layout button
        self.apply_layout_btn = Gtk.Button(label="Apply Layout")
        self.apply_layout_btn.get_style_context().add_class("suggested-action")
        self.apply_layout_btn.connect("clicked", self.on_apply_layout_clicked)
        self.apply_layout_btn.set_sensitive(False)
        self.apply_layout_btn.set_tooltip_text("Apply the new display arrangement")
        layout_box.pack_end(self.apply_layout_btn, False, False, 0)

        # Unlink mirrored button (for un-mirroring displays)
        self.unlink_mirror_btn = Gtk.Button(label="Unlink Mirrored")
        self.unlink_mirror_btn.connect("clicked", self.on_unlink_mirror_clicked)
        self.unlink_mirror_btn.set_sensitive(False)
        self.unlink_mirror_btn.set_tooltip_text("Separate mirrored displays")
        layout_box.pack_end(self.unlink_mirror_btn, False, False, 0)

        # Resolution options
        options_frame = Gtk.Frame(label="Options")
        main_box.pack_start(options_frame, False, False, 0)

        options_grid = Gtk.Grid()
        options_grid.set_column_spacing(10)
        options_grid.set_row_spacing(5)
        options_grid.set_border_width(10)
        options_frame.add(options_grid)

        # Mode selection
        mode_label = Gtk.Label(label="Resolution:")
        mode_label.set_xalign(0)
        options_grid.attach(mode_label, 0, 0, 1, 1)

        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.set_tooltip_text("Target resolution for mirror/extend operation")
        options_grid.attach(self.mode_combo, 1, 0, 1, 1)

        # Rate selection
        rate_label = Gtk.Label(label="Refresh Rate:")
        rate_label.set_xalign(0)
        options_grid.attach(rate_label, 2, 0, 1, 1)

        self.rate_combo = Gtk.ComboBoxText()
        self.rate_combo.append_text("30.00")
        self.rate_combo.append_text("50.00")
        self.rate_combo.append_text("59.94")
        self.rate_combo.append_text("60.00")
        self.rate_combo.set_active(3)
        options_grid.attach(self.rate_combo, 3, 0, 1, 1)

        # Status bar
        self.statusbar = Gtk.Statusbar()
        main_box.pack_end(self.statusbar, False, False, 0)
        self.status_context = self.statusbar.get_context_id("main")

        # Apply CSS styling
        self.apply_css()

    def apply_css(self):
        """Apply custom CSS styling."""
        css = b"""
        #source-label {
            color: #3498db;
            font-weight: bold;
        }
        #target-label {
            color: #e67e22;
            font-weight: bold;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def parse_xrandr_output(self) -> list:
        """Parse xrandr output to get display information."""
        displays = []

        try:
            result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True)
            output = result.stdout
        except Exception as e:
            self.show_status(f"Error running xrandr: {e}")
            return displays

        current_display = None

        for line in output.split('\n'):
            # Match display line: "HDMI-1 connected primary 1920x1080+0+0 ..."
            match = re.match(
                r'^(\S+)\s+(connected|disconnected)\s*(primary)?\s*'
                r'(?:(\d+)x(\d+)\+(\d+)\+(\d+))?',
                line
            )

            if match:
                name = match.group(1)
                is_connected = match.group(2) == 'connected'
                is_primary = match.group(3) == 'primary'

                if is_connected:
                    width = int(match.group(4)) if match.group(4) else 1920
                    height = int(match.group(5)) if match.group(5) else 1080
                    x = int(match.group(6)) if match.group(6) else 0
                    y = int(match.group(7)) if match.group(7) else 0

                    current_display = Display(
                        name=name,
                        width=width,
                        height=height,
                        x=x,
                        y=y,
                        is_primary=is_primary,
                        is_connected=True,
                        modes=[],
                        current_mode=f"{width}x{height}",
                        current_rate="60.00"
                    )
                    displays.append(current_display)

            # Match mode lines: "   1920x1080     60.00*+  50.00    59.94"
            elif current_display and line.startswith('   '):
                mode_match = re.match(r'\s+(\d+x\d+)\s+([\d.]+)', line)
                if mode_match:
                    mode = mode_match.group(1)
                    if mode not in current_display.modes:
                        current_display.modes.append(mode)
                    if '*' in line:
                        current_display.current_mode = mode
                        rate_match = re.search(r'([\d.]+)\*', line)
                        if rate_match:
                            current_display.current_rate = rate_match.group(1)

        return displays

    def refresh_displays(self):
        """Refresh the display list from xrandr."""
        # Clear existing widgets
        for child in self.display_container.get_children():
            self.display_container.remove(child)
        self.display_widgets.clear()

        # Get display info
        self.displays = self.parse_xrandr_output()

        if not self.displays:
            label = Gtk.Label(label="No displays detected")
            self.display_container.put(label, 50, 50)
            self.show_status("No displays found")
            return

        # Calculate scale and positions
        total_width = sum(d.width for d in self.displays) + 100 * (len(self.displays) - 1)
        scale = min(0.15, 700 / total_width) if total_width > 0 else 0.1

        # Find min position to offset
        min_x = min(d.x for d in self.displays)
        min_y = min(d.y for d in self.displays)

        # Create widgets for each display
        for i, display in enumerate(self.displays):
            widget = DisplayWidget(display, scale, gui=self)
            widget.connect("button-press-event", self.on_display_clicked, display)

            # Position based on actual display position
            x_pos = int((display.x - min_x) * scale) + 20 + i * 10
            y_pos = int((display.y - min_y) * scale) + 20

            self.display_container.put(widget, x_pos, y_pos)
            self.display_widgets[display.name] = widget

        # Detect and mark mirrored displays (same position)
        mirrored_groups = self._find_mirrored_display_groups()
        has_mirrored = False
        for group in mirrored_groups:
            if len(group) > 1:
                has_mirrored = True
                for display_name in group:
                    widget = self.display_widgets.get(display_name)
                    if widget:
                        widget.is_mirrored = True
                        widget.mirrored_with = [n for n in group if n != display_name]
                        widget.queue_draw()

        # Enable/disable unlink button
        self.unlink_mirror_btn.set_sensitive(has_mirrored)

        # Clear pending changes on refresh
        self.pending_layout_changes.clear()
        self.apply_layout_btn.set_sensitive(False)

        # Update mode combo with common resolutions
        self.mode_combo.remove_all()
        all_modes = set()
        for d in self.displays:
            all_modes.update(d.modes)

        # Sort modes by resolution (descending)
        sorted_modes = sorted(all_modes,
                             key=lambda m: int(m.split('x')[0]) * int(m.split('x')[1]),
                             reverse=True)
        for mode in sorted_modes:
            self.mode_combo.append_text(mode)

        if sorted_modes:
            # Default to 1920x1080 if available, otherwise first
            try:
                idx = sorted_modes.index("1920x1080")
                self.mode_combo.set_active(idx)
            except ValueError:
                self.mode_combo.set_active(0)

        self.display_container.show_all()
        self.show_status(f"Found {len(self.displays)} connected display(s)")

    def on_display_clicked(self, widget, event, display):
        """Handle display widget click."""
        if self.source_display is None:
            # Select as source
            self.source_display = display
            widget.is_source = True
            widget.queue_draw()
            self.source_label.set_text(f"{display.name} ({display.current_mode})")
            self.show_status(f"Selected {display.name} as source")
        elif self.target_display is None and display.name != self.source_display.name:
            # Select as target
            self.target_display = display
            widget.is_target = True
            widget.queue_draw()
            self.target_label.set_text(f"{display.name} ({display.current_mode})")
            self.update_action_buttons()
            self.show_status(f"Selected {display.name} as target")
        elif display.name == self.source_display.name:
            # Deselect source
            widget.is_source = False
            widget.queue_draw()
            self.source_display = None
            self.source_label.set_text("(none selected)")
            self.update_action_buttons()
        elif display.name == self.target_display.name:
            # Deselect target
            widget.is_target = False
            widget.queue_draw()
            self.target_display = None
            self.target_label.set_text("(none selected)")
            self.update_action_buttons()

    def update_action_buttons(self):
        """Update action button sensitivity."""
        has_both = self.source_display is not None and self.target_display is not None
        self.mirror_btn.set_sensitive(has_both)
        self.extend_right_btn.set_sensitive(has_both)
        self.extend_left_btn.set_sensitive(has_both)

    def on_clear_clicked(self, button):
        """Clear all selections."""
        for widget in self.display_widgets.values():
            widget.is_source = False
            widget.is_target = False
            widget.queue_draw()

        self.source_display = None
        self.target_display = None
        self.source_label.set_text("(none selected)")
        self.target_label.set_text("(none selected)")
        self.update_action_buttons()
        self.show_status("Selection cleared")

    def on_refresh_clicked(self, button):
        """Refresh display list."""
        self.on_clear_clicked(None)
        self.refresh_displays()

    def get_selected_mode(self):
        """Get the selected resolution mode."""
        return self.mode_combo.get_active_text() or "1920x1080"

    def get_selected_rate(self):
        """Get the selected refresh rate."""
        return self.rate_combo.get_active_text() or "60.00"

    def on_mirror_clicked(self, button):
        """Mirror source to target."""
        if not self.source_display or not self.target_display:
            return

        source = self.source_display.name
        target = self.target_display.name
        mode = self.get_selected_mode()
        rate = self.get_selected_rate()

        cmd = ['xrandr', '--output', target, '--same-as', source,
               '--mode', mode, '--rate', rate]

        self.run_xrandr_command(cmd, f"Mirroring {source} to {target}")

    def on_extend_right_clicked(self, button):
        """Extend target to the right of source."""
        if not self.source_display or not self.target_display:
            return

        source = self.source_display.name
        target = self.target_display.name
        mode = self.get_selected_mode()
        rate = self.get_selected_rate()

        cmd = ['xrandr', '--auto', '--output', target,
               '--mode', mode, '--rate', rate, '--right-of', source]

        self.run_xrandr_command(cmd, f"Extending {target} to the right of {source}")

    def on_extend_left_clicked(self, button):
        """Extend target to the left of source."""
        if not self.source_display or not self.target_display:
            return

        source = self.source_display.name
        target = self.target_display.name
        mode = self.get_selected_mode()
        rate = self.get_selected_rate()

        cmd = ['xrandr', '--auto', '--output', target,
               '--mode', mode, '--rate', rate, '--left-of', source]

        self.run_xrandr_command(cmd, f"Extending {target} to the left of {source}")

    def snap_widget_position(self, dragged_widget):
        """Snap a dragged widget to the nearest display edge."""
        container = self.display_container
        dragged_alloc = dragged_widget.get_allocation()
        dragged_display = dragged_widget.display

        # Get positions of all other widgets
        best_snap = None
        min_distance = float('inf')
        snap_threshold = 50  # Pixels

        for name, widget in self.display_widgets.items():
            if name == dragged_display.name:
                continue

            other_alloc = widget.get_allocation()
            other_display = widget.display

            # Check all four snap positions (right-of, left-of, above, below)
            snap_positions = [
                # Right of other display
                ('right-of', other_alloc.x + other_alloc.width, other_alloc.y),
                # Left of other display
                ('left-of', other_alloc.x - dragged_alloc.width, other_alloc.y),
                # Above other display
                ('above', other_alloc.x, other_alloc.y - dragged_alloc.height),
                # Below other display
                ('below', other_alloc.x, other_alloc.y + other_alloc.height),
            ]

            for direction, snap_x, snap_y in snap_positions:
                # Calculate distance from current position to snap position
                dx = dragged_alloc.x - snap_x
                dy = dragged_alloc.y - snap_y
                distance = (dx * dx + dy * dy) ** 0.5

                if distance < min_distance and distance < snap_threshold * 3:
                    min_distance = distance
                    best_snap = (snap_x, snap_y, other_display.name, direction)

        if best_snap:
            snap_x, snap_y, relative_to, direction = best_snap

            # Check for overlap with any display at snap position
            if not self._would_overlap(dragged_widget, snap_x, snap_y):
                # Move widget to snap position
                container.move(dragged_widget, int(snap_x), int(snap_y))

                # Record pending change
                self.pending_layout_changes[dragged_display.name] = (relative_to, direction)
                dragged_widget.has_pending_changes = True
                dragged_widget.queue_draw()

                # Enable apply button
                self.apply_layout_btn.set_sensitive(True)
                self.show_status(f"Snapped {dragged_display.name} {direction} {relative_to}")
        else:
            # No valid snap - revert to original position or find safe position
            self._find_non_overlapping_position(dragged_widget)

    def _would_overlap(self, dragged_widget, new_x, new_y):
        """Check if placing widget at position would overlap other displays."""
        dragged_alloc = dragged_widget.get_allocation()
        dragged_name = dragged_widget.display.name

        for name, widget in self.display_widgets.items():
            if name == dragged_name:
                continue

            other_alloc = widget.get_allocation()

            # Check rectangle intersection
            if (new_x < other_alloc.x + other_alloc.width and
                new_x + dragged_alloc.width > other_alloc.x and
                new_y < other_alloc.y + other_alloc.height and
                new_y + dragged_alloc.height > other_alloc.y):
                return True

        return False

    def _find_non_overlapping_position(self, widget):
        """Find a non-overlapping position for the widget."""
        container = self.display_container
        alloc = widget.get_allocation()

        # Try positions around the container
        test_positions = [(20, 20), (200, 20), (400, 20), (20, 150), (200, 150)]

        for x, y in test_positions:
            if not self._would_overlap(widget, x, y):
                container.move(widget, x, y)
                return

    def on_apply_layout_clicked(self, button):
        """Apply all pending layout changes."""
        if not self.pending_layout_changes:
            return

        success_count = 0
        for display_name, (relative_to, direction) in self.pending_layout_changes.items():
            cmd = ['xrandr', '--output', display_name, f'--{direction}', relative_to]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    success_count += 1
                else:
                    error = result.stderr.strip() or "Unknown error"
                    self.show_status(f"Failed to position {display_name}: {error}")
            except Exception as e:
                self.show_status(f"Error positioning {display_name}: {e}")

        if success_count > 0:
            self.show_status(f"Applied {success_count} layout change(s)")

        # Clear pending changes
        self.pending_layout_changes.clear()
        for widget in self.display_widgets.values():
            widget.has_pending_changes = False
            widget.queue_draw()
        self.apply_layout_btn.set_sensitive(False)

        # Refresh display
        GLib.timeout_add(500, self.refresh_displays)

    def on_unlink_mirror_clicked(self, button):
        """Unlink mirrored displays."""
        mirrored_groups = self._find_mirrored_displays()
        if not mirrored_groups:
            self.show_status("No mirrored displays found")
            return

        # Unlink all mirrored displays by placing them side by side
        commands = []
        x_offset = 0
        for i, display in enumerate(self.displays):
            # Position each display in sequence
            if i == 0:
                cmd = ['xrandr', '--output', display.name, '--pos', '0x0']
            else:
                prev_display = self.displays[i - 1]
                cmd = ['xrandr', '--output', display.name, '--right-of', prev_display.name]
            commands.append((cmd, display.name))

        for cmd, name in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.show_status(f"Failed to unlink {name}")
            except Exception as e:
                self.show_status(f"Error unlinking {name}: {e}")

        self.show_status("Unlinked mirrored displays")
        self.unlink_mirror_btn.set_sensitive(False)
        GLib.timeout_add(500, self.refresh_displays)

    def _find_mirrored_displays(self):
        """Find displays that are mirrored (same position)."""
        mirrored = []
        for group in self._find_mirrored_display_groups():
            if len(group) > 1:
                mirrored.extend(group)
        return mirrored

    def _find_mirrored_display_groups(self):
        """Find groups of displays that are mirrored (same position)."""
        position_groups = {}

        for display in self.displays:
            pos = (display.x, display.y)
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(display.name)

        return list(position_groups.values())

    def run_xrandr_command(self, cmd, description):
        """Run an xrandr command and show result."""
        self.show_status(f"{description}...")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.show_status(f"{description} - Success!")
                # Refresh after a short delay
                GLib.timeout_add(1000, self.refresh_displays)
            else:
                error = result.stderr.strip() or "Unknown error"
                self.show_error(f"xrandr failed: {error}")
        except Exception as e:
            self.show_error(f"Error: {e}")

    def show_status(self, message):
        """Show a status message."""
        self.statusbar.pop(self.status_context)
        self.statusbar.push(self.status_context, message)

    def show_error(self, message):
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        self.show_status(f"Error: {message}")


def main():
    win = XrandrGUI()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
