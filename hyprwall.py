#!/usr/bin/env python3
"""hyprwall: Wallhaven browser + awww painter.

  hyprwall [online|local] [query]   GTK gallery (standalone)
  hyprwall search|list|apply|random headless JSON commands (used by Quickshell)
"""
import os
import sys

SCRIPT_REAL_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_REAL_DIR, "modules"))

from config_loader import load_lua_config

if __name__ == "__main__":
    argv = sys.argv[1:]

    import cli
    if argv and argv[0] in cli.COMMANDS:
        cli.run(load_lua_config(), argv)
        sys.exit(0)

    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    from core_engine import HyprwallEngine

    run_mode = argv[0] if argv and argv[0] in ("online", "local") else "online"
    query_arg = argv[1] if len(argv) > 1 else None
    Gtk.init(sys.argv)
    app = HyprwallEngine(load_lua_config(), run_mode, query_arg)
    Gtk.main()
