import os
import subprocess
import urllib.request

def confirm_and_apply_wallpaper(window, wp):
    source_url = wp['full_url']
    
    # Ensure high-res download is complete
    if window.run_mode == "online":
        if not wp.get('has_full_res') or not os.path.exists(wp['full_cache_path']):
            subprocess.run(["notify-send", "Hyprwall", "Downloading high-res master..."])
            try:
                req = urllib.request.Request(source_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as r:
                    with open(wp['full_cache_path'], 'wb') as f: 
                        f.write(r.read())
            except Exception as e:
                print(f"Download failure: {e}")

    # Runtime extension inspection from file magic bytes
    cache_file = wp['full_cache_path'] if window.run_mode == "online" else wp['local_path']
    ext = ".jpg"
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                header = f.read(4)
                if header.startswith(b'\x89PNG'): 
                    ext = ".png"
                elif header.startswith(b'\xff\xd8\xff'): 
                    ext = ".jpg"
                elif b'WEBP' in header or header.startswith(b'RIFF'): 
                    ext = ".webp"
        except:
            pass

    if window.run_mode == "local":
        filename = os.path.basename(wp['local_path'])
    else:
        base_id = wp.get('id', 'wallpaper')
        filename = f"wallhaven-{base_id}{ext}"
    target_dest = os.path.abspath(f"{window.config['wall_dir']}/{filename}")
    
    if os.path.exists(cache_file):
        os.makedirs(window.config['wall_dir'], exist_ok=True)
        subprocess.run(["cp", cache_file, target_dest])

    from cli import paint
    paint(target_dest)

    # Desktop notification dispatch
    subprocess.Popen(["notify-send", "Wallpaper Applied", filename])
