
import os
import json
import urllib.request
import urllib.parse
import asyncio

async def download_worker(url, dest, cancel_token=None):
    try:
        if cancel_token and cancel_token.is_set():
            return False
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'})
        def self_read_and_write():
            with urllib.request.urlopen(req) as response:
                with open(dest, 'wb') as f:
                    f.write(response.read())
        await asyncio.to_thread(self_read_and_write)
        return True
    except Exception as e:
        print(f"Download worker failure on {url}: {e}")
        return False

async def fetch_wallpapers(config, current_page, search_mode, search_term, limit=6, download_thumbs=True):
    filter_str = f"categories={config['categories']}&purity={config['purity']}&sorting={config['sorting']}&topRange={config['top_range']}&{config['resolution_filter']}&{config['ratio_filter']}&page={current_page}"
    if config['api_key']:
        filter_str += f"&apikey={config['api_key']}"

    if search_mode == "query" and search_term.strip() != "":
        clean_query = urllib.parse.quote(search_term.strip())
        url = f"{config['api_uri']}?q={clean_query}&{filter_str}"
    else:
        url = f"{config['api_uri']}?{filter_str}"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'})
        def perform_request():
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
                
        res_data = await asyncio.to_thread(perform_request)
        if not res_data.get('data') or len(res_data['data']) == 0:
            return [], 1, 0
            
        meta = res_data.get('meta', {})
        last_page = meta.get('last_page', 1)
        total_results = meta.get('total', meta.get('total_results', len(res_data['data'])))

        items = res_data["data"][0:limit]
        wallpapers = []
        thumb_dir = f"{config['cache_dir']}/online_thumbs"
        os.makedirs(thumb_dir, exist_ok=True)

        thumb_tasks = []
        for item in items:
            wp_id = item['id']
            full_path = item['path'].replace(r'\/', '/')
            thumb_path = item['thumbs']['large'].replace(r'\/', '/')
            target_thumb = f"{thumb_dir}/{wp_id}.jpg"
            target_full = f"{thumb_dir}/{wp_id}_full.jpg"
            
            meta_payload = {
                "id": wp_id,
                "category": item.get("category", "general"),
                "purity": item.get("purity", "sfw"),
                "tags": [wp_id, item.get("category", "general"), item.get("purity", "sfw")]
            }

            wallpapers.append({
                "id": wp_id, 
                "local_path": target_thumb, 
                "full_cache_path": target_full, 
                "full_url": full_path,
                "thumb_url": thumb_path,
                "has_full_res": False,
                "meta": meta_payload
            })
            if download_thumbs and not os.path.exists(target_thumb):
                thumb_tasks.append(download_worker(thumb_path, target_thumb))
            
        await asyncio.gather(*thumb_tasks)
        return wallpapers, last_page, total_results
    except Exception as e:
        print(f"API Connection Exception: {e}")
        return [], 1, 0

async def preload_full_res_background(wp, cancel_token):
    if os.path.exists(wp['full_cache_path']):
        wp['has_full_res'] = True
        return True
    if cancel_token.is_set():
        return False
    success = await download_worker(wp['full_url'], wp['full_cache_path'], cancel_token)
    if success and not cancel_token.is_set():
        wp['has_full_res'] = True
        return True
    return False

def inject_image_metadata(file_path, meta_dict):
    try:
        meta_path = '.' + str(file_path) + ".meta"
        with open(meta_path, "w") as f:
            json.dump(meta_dict, f, indent=4)
    except Exception as e:
        print(f"Metadata companion write failed: {e}")

def fetch_local_wallpapers(config, search_term=""):
    wallpapers = []
    if not os.path.exists(config['wall_dir']):
        return wallpapers
        
    valid_exts = (".jpg", ".jpeg", ".png", ".webp")
    raw_files = []
    
    for file in os.listdir(config['wall_dir']):
        if file.lower().endswith(valid_exts):
            full_path = os.path.join(config['wall_dir'], file)
            try:
                raw_files.append((file, full_path, os.path.getmtime(full_path)))
            except:
                pass
                
    raw_files.sort(key=lambda x: x[2], reverse=True)
    clean_search = search_term.strip().lower()
    
    for file, full_path, _ in raw_files:
        matched = False
        meta_path = full_path + ".meta"
        
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                tags = [str(t).lower() for t in meta.get("tags", [])]
                if not clean_search or any(clean_search in t for t in tags):
                    matched = True
            except:
                pass
                
        if not matched and clean_search and clean_search in file.lower():
            matched = True
            
        if clean_search and not matched:
            continue
            
        # FIXED: Added explicit full_cache_path mappings to perfectly mirror the online layout engine expectation
        wallpapers.append({
            "id": file, 
            "local_path": full_path, 
            "full_cache_path": full_path, 
            "full_url": "file://" + full_path,
            "has_full_res": True
        })
    return wallpapers
