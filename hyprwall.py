
#!/usr/bin/env python3
import sys
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# FIXED: Hardcode the absolute path so it never gets lost across symlinks
MODULES_PATH = os.path.expanduser("~/.config/hyprwall/modules")
sys.path.append(MODULES_PATH)

from config_loader import load_lua_config
from core_engine import HyprwallEngine

if __name__ == "__main__":
    run_mode = "online"
    query_arg = None
    
    if len(sys.argv) > 1: 
        run_mode = sys.argv[1]
    if len(sys.argv) > 2: 
        query_arg = sys.argv[2]
        
    if run_mode not in ["online", "local"]: 
        run_mode = "online"

    Gtk.init(sys.argv)
    app = HyprwallEngine(load_lua_config(), run_mode, query_arg)
    Gtk.main()
