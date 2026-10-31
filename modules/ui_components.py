
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

def setup_ui_layout(window):
    window.main_overlay = Gtk.Overlay()
    window.add(window.main_overlay)

    window.bg_image = Gtk.Image()
    window.main_overlay.add(window.bg_image)

    window.fg_image = Gtk.Image()
    window.fg_image.set_margin_start(90)
    window.fg_image.set_margin_end(90)
    window.fg_image.set_margin_top(90)
    window.fg_image.set_margin_bottom(120)
    window.main_overlay.add_overlay(window.fg_image)

    window.search_bar = Gtk.Entry()
    window.search_bar.set_placeholder_text("Search Wallhaven... (Type + Hit Enter)")
    window.search_bar.set_width_chars(45)
    window.search_bar.set_halign(Gtk.Align.CENTER)
    window.search_bar.set_valign(Gtk.Align.START)
    window.search_bar.set_margin_top(40)
    window.search_bar.connect("activate", window.on_search_submit)
    
    if window.run_mode == "local":
        window.search_bar.set_visible(False)
    window.main_overlay.add_overlay(window.search_bar)

    # Status pill container
    window.status_badge = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    window.status_badge.set_halign(Gtk.Align.CENTER)
    window.status_badge.set_valign(Gtk.Align.START)
    window.status_badge.set_margin_top(100)
    
    context = window.status_badge.get_style_context()
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(b"""
        .badge-box { background-color: rgba(0, 0, 0, 0.75); padding: 8px 18px; border-radius: 20px; }
        .badge-text { color: #ffffff; font-size: 12px; font-weight: bold; }
        .spinner-light { color: #ffffff; }
    """)
    context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    context.add_class("badge-box")

    # FIXED: Added a size request layout constraint so the spinner renders visibly at 24x24 pixels
    window.ui_spinner = Gtk.Spinner()
    window.ui_spinner.set_size_request(24, 24)
    window.ui_spinner.get_style_context().add_class("spinner-light")
    window.status_badge.pack_start(window.ui_spinner, False, False, 0)

    window.status_label = Gtk.Label()
    window.status_label.get_style_context().add_class("badge-text")
    window.status_badge.pack_start(window.status_label, False, False, 0)
    window.status_badge.set_visible(False)
    window.main_overlay.add_overlay(window.status_badge)

    window.dots_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
    window.dots_container.set_halign(Gtk.Align.CENTER)
    window.dots_container.set_valign(Gtk.Align.END)
    window.dots_container.set_margin_bottom(40)
    window.main_overlay.add_overlay(window.dots_container)

def update_pagination_dots_display(window):
    for idx, dot in enumerate(window.dot_labels):
        if idx == window.current_index:
            dot.set_markup("<span color='#000000' size='22000'>•</span>")
        else:
            dot.set_markup("<span color='#cccccc' size='22000'>•</span>")
