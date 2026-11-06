#!/usr/bin/env python3
import os
import sys
import json
import re
import urllib.request
import ssl

sys.path.append(os.path.expanduser("~/.config/hyprwall/modules"))
from config_loader import load_lua_config
from api_engine import inject_image_metadata

def backfill_existing_metadata():
    config = load_lua_config()
    wall_dir = config['wall_dir']
    
    if not os.path.exists(wall_dir):
        print(f"ERROR: Wallpaper directory {wall_dir} not found.")
        return

    valid_exts = (".jpg", ".jpeg", ".png")
    print(f"=== STARTING HYPRWALL METADATA BACKFILL IN: {wall_dir} ===")

    for file in os.listdir(wall_dir):
        if not file.lower().endswith(valid_exts):
            continue
            
        full_path = os.path.join(wall_dir, file)
        meta_path = os.path.join(wall_dir,f".{file}.meta")
        
        # Skip if companion layout file is already cached locally
        if os.path.exists(meta_path):
            print(f" Skipping: [{file}] (Metadata companion file already exists)")
            continue

        name_without_ext = os.path.splitext(file)[0]
        match = re.search(r'([a-z0-9]{6})$', name_without_ext.lower())
        
        if not match:
            print(f" Skipping: [{file}] (Could not parse a valid Wallhaven ID from filename)")
            continue
            
        wp_id = match.group(1)
        
        base_api_url = config['api_uri'].rsplit('/search', 1)[0]
        url = f"{base_api_url}/w/{wp_id}"
        if config['api_key']:
            url += f"?apikey={config['api_key']}"

        print(f"-> Querying details for wallpaper ID: {wp_id} ... ", end="", flush=True)
        try:
            bypass_context = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'})
            
            with urllib.request.urlopen(req, timeout=5, context=bypass_context) as response:
                res_data = json.loads(response.read().decode())
                
            item = res_data.get('data', {})
            if item:
                api_tags = [t['name'].lower() for t in item.get('tags', [])]
                
                meta_payload = {
                    "id": wp_id,
                    "category": item.get("category", "general"),
                    "purity": item.get("purity", "sfw"),
                    "tags": [wp_id, item.get("category", "general"), item.get("purity", "sfw")] + api_tags
                }
                
                inject_image_metadata(meta_path, meta_payload)
                print("SUCCESS")
            else:
                print("FAILED (Empty return)")
        except Exception as e:
            print(f"FAILED (Network error: {e})")

    print("=== METADATA BACKFILL COMPLETION SUCCESSFUL ===")

if __name__ == "__main__":
    backfill_existing_metadata()
