
import os
import subprocess

def load_lua_config():
    path = os.path.expanduser("~/.config/hyprwall/config.lua")
    defaults = {
        "api_uri": "https://wallhaven.cc",
        "wall_dir": os.path.expanduser("~/Pictures/Wallpapers"),
        "cache_dir": os.path.expanduser("~/.cache/hyprwall"),
        "monitors": ["eDP-1", "HDMI-A-1"],
        "api_key": "", "categories": "111", "purity": "100", "sorting": "toplist", "top_range": "1M",
        "resolution_filter": "atleast=1920x1080", "ratio_filter": "ratios=16x9,16x10"
    }
    if not os.path.exists(path):
        return defaults
    try:
        lua_cmd = f"lua -e \"local c = dofile('{path}'); print(c.api_uri..'\\t'..c.wall_dir..'\\t'..c.cache_dir..'\\t'..c.api_key..'\\t'..c.categories..'\\t'..c.purity..'\\t'..c.sorting..'\\t'..c.top_range..'\\t'..c.resolution_filter..'\\t'..c.ratio_filter..'\\t'..table.concat(c.monitors,','))\""
        output = subprocess.check_output(lua_cmd, shell=True).decode().strip().split('\t')
        if len(output) >= 11:
            return {
                "api_uri": output[0], "wall_dir": output[1], "cache_dir": output[2], "api_key": output[3],
                "categories": output[4], "purity": output[5], "sorting": output[6], "top_range": output[7],
                "resolution_filter": output[8], "ratio_filter": output[9], "monitors": output[10].split(',')
            }
    except Exception as e:
        print(f"Lua parsing failed fallback: {e}")
    return defaults
