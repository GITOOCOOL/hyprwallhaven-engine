
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

def handle_keypress_events(window, event):
    if isinstance(window.get_focus(), Gtk.Entry):
        if event.keyval == Gdk.KEY_Escape:
            window.search_bar.set_visible(False)
            window.grab_focus()
            return True
        return False

    is_alt = bool(event.state & Gdk.ModifierType.MOD1_MASK)

    if event.keyval == Gdk.KEY_Escape:
        Gtk.main_quit()
        return True
        
    elif event.keyval == Gdk.KEY_Right:
        if window.is_loading: return True
        if is_alt and window.run_mode == "online":
            if window.current_page < window.last_page:
                window.current_page += 1
                window.trigger_background_fetch()
        else:
            if window.current_index < len(window.wallpapers) - 1:
                window.current_index += 1
                window.render_active_wallpaper()
            elif window.run_mode == "online" and window.current_page < window.last_page:
                window.current_page += 1
                window.trigger_background_fetch()
        return True
        
    elif event.keyval == Gdk.KEY_Left:
        if window.is_loading: return True
        if is_alt and window.run_mode == "online":
            if window.current_page > 1:
                window.current_page -= 1
                window.trigger_background_fetch()
        else:
            if window.current_index > 0:
                window.current_index -= 1
                window.render_active_wallpaper()
            elif window.current_page > 1 and window.run_mode == "online":
                window.current_page -= 1
                window.trigger_background_fetch()
        return True

    elif event.keyval == Gdk.KEY_f or event.keyval == Gdk.KEY_F:
        if is_alt and window.run_mode == "online" and not window.is_loading:
            window.search_bar.set_visible(True)
            window.search_bar.grab_focus()
        return True
        
    elif event.keyval == Gdk.KEY_space:
        if window.is_loading: return True
        if window.wallpapers:
            wp = window.wallpapers[window.current_index]
            window.confirm_and_apply_wallpaper(wp)
        return True
        
    return False
