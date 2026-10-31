
import os
import subprocess
import threading
import asyncio
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

from api_engine import fetch_wallpapers, fetch_local_wallpapers, preload_full_res_background
from ui_components import setup_ui_layout, update_pagination_dots_display
from key_handlers import handle_keypress_events
from wallpaper_applier import confirm_and_apply_wallpaper

class HyprwallEngine(Gtk.Window):
    def __init__(self, config_data, run_mode, initial_query):
        super().__init__(title="Hyprwall Gallery Loop")
        self.config = config_data
        self.run_mode = run_mode
        self.current_page = 1
        self.last_page = 1
        self.total_results = 0
        self.search_mode = "query" if initial_query else "toplist"
        self.search_term = initial_query or ""
        self.current_index = 0
        self.wallpapers = []
        self.is_loading = False
        self.dot_labels = []
        self.download_cancel_token = threading.Event()

        self.set_can_focus(True)
        self.set_decorated(False)
        self.fullscreen()

        setup_ui_layout(self)
        
        self.connect("key-press-event", handle_keypress_events)
        self.connect("realize", lambda w: self.render_active_wallpaper() if self.wallpapers else None)
        
        self.trigger_background_fetch()
        self.show_all()
        self.grab_focus()

    def trigger_background_fetch(self):
        if self.is_loading: return
        self.is_loading = True
        self.download_cancel_token.set()
        self.download_cancel_token = threading.Event()

        if self.run_mode == "online":
            subprocess.Popen(["notify-send", "-h", "string:x-canonical-private-synchronous:hyprwall", "Hyprwall", f"Fetching Page {self.current_page}..."])
            threading.Thread(target=self.async_worker_thread, daemon=True).start()
        else:
            self.wallpapers = fetch_local_wallpapers(self.config, self.search_term)
            self.is_loading = False
            if self.wallpapers:
                self.current_index = 0
                self.setup_pagination_dots()
                self.render_active_wallpaper()

    def async_worker_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res, lp, tot = loop.run_until_complete(fetch_wallpapers(self.config, self.current_page, self.search_mode, self.search_term))
        loop.close()
        GLib.idle_add(self.on_fetch_completed, res, lp, tot)

    def on_fetch_completed(self, results, last_page, total):
        self.is_loading = False
        if results:
            self.wallpapers, self.last_page, self.total_results = results, last_page, total
            self.current_index = 0
            self.setup_pagination_dots()
            self.render_active_wallpaper()
            subprocess.Popen(["notify-send", "-h", "string:x-canonical-private-synchronous:hyprwall", "Hyprwall", f"Page {self.current_page}/{self.last_page} loaded."])
            threading.Thread(target=self.lazy_load_full_res_queue, args=(self.download_cancel_token,), daemon=True).start()
        else:
            subprocess.Popen(["notify-send", "-h", "string:x-canonical-private-synchronous:hyprwall", "Hyprwall", "No assets found."])

    def lazy_load_full_res_queue(self, cancel_token):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for idx, wp in enumerate(self.wallpapers):
            if cancel_token.is_set(): break
            if self.run_mode == "online":
                success = loop.run_until_complete(preload_full_res_background(wp, cancel_token))
                if success and not cancel_token.is_set():
                    GLib.idle_add(self.on_single_wallpaper_preloaded, idx)
        loop.close()

    def on_single_wallpaper_preloaded(self, preloaded_index):
        if preloaded_index == self.current_index and not self.is_loading:
            self.render_active_wallpaper()

    def setup_pagination_dots(self):
        for child in self.dots_container.get_children(): 
            self.dots_container.remove(child)
        self.dot_labels = []
        for i in range(len(self.wallpapers)):
            dot = Gtk.Label()
            self.dots_container.pack_start(dot, False, False, 0)
            self.dot_labels.append(dot)
        self.dots_container.show_all()

    def render_active_wallpaper(self):
        if not self.wallpapers or not self.get_window(): return
        wp = self.wallpapers[self.current_index]
        
        display = Gdk.Display.get_default()
        monitor = display.get_monitor_at_window(self.get_window())
        geometry = monitor.get_geometry()
        scr_w, scr_h = geometry.width, geometry.height

        if self.run_mode == "online" and not wp.get('has_full_res'):
            self.status_label.set_text("Fetching High-Res master...")
            self.ui_spinner.start()
            self.status_badge.set_visible(True)
        else:
            self.ui_spinner.stop()
            self.status_badge.set_visible(False)

        path_to_render = wp['full_cache_path'] if wp.get('has_full_res') and os.path.exists(wp['full_cache_path']) else wp['local_path']

        pix_tiny = GdkPixbuf.Pixbuf.new_from_file_at_scale(path_to_render, 32, 32, False)
        self.bg_image.set_from_pixbuf(pix_tiny.scale_simple(scr_w, scr_h, GdkPixbuf.InterpType.BILINEAR))
        self.bg_image.set_opacity(0.8)

        self.fg_image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(path_to_render, int(scr_w * 0.82), int(scr_h * 0.82), True))
        update_pagination_dots_display(self)

    def on_search_submit(self, entry):
        text = entry.get_text().strip()
        if text and not self.is_loading:
            self.search_term, self.search_mode, self.current_page = text, "query", 1
            self.trigger_background_fetch()
            self.search_bar.set_visible(False)
            self.grab_focus()

    def confirm_and_apply_wallpaper(self, wp):
        confirm_and_apply_wallpaper(self, wp)
        Gtk.main_quit()
