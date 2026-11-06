"""Headless hyprwall commands used by the Quickshell wallpaper picker.

  hyprwall search [query] [--page N] [--source S] [filters]
      -> JSON page of results; S = wallhaven (default) | unsplash | pexels | konachan | bing
  hyprwall list [query] [--purity 100]           -> JSON list of local wallpapers
  hyprwall meta                                  -> look up purity/category of local wallhaven-* files
  hyprwall thumbs                                -> build 1600px preview JPEGs for local files (cache)
filters (override config.lua): --purity 110 --categories 111 --sorting toplist
  --range 1M --ratios 16x9,16x10 (or "") --atleast 2560x1440 (or "")
  hyprwall apply <id|path> [full_url] [--source S] [--track URL]
      -> download if needed, save to wall_dir as <source>-<id>.<ext>, paint with awww
  hyprwall random                      -> apply a random local wallpaper
"""
import asyncio
import json
import os
import random
import subprocess
import sys
import urllib.error
import urllib.request

import providers
from api_engine import fetch_wallpapers, fetch_local_wallpapers, download_worker

UA = {"User-Agent": "hyprwall"}
PURITY_BIT = {"sfw": 0, "sketchy": 1, "nsfw": 2}
FLAGS = ("--page", "--purity", "--categories", "--sorting", "--range", "--ratios", "--atleast", "--source", "--track")


def parse_flags(cfg, args):
    """Strip --flag value pairs from args, applying them to a copy of cfg."""
    cfg = dict(cfg)
    rest, page = [], 1
    i = 0
    while i < len(args):
        a = args[i]
        if a in FLAGS and i + 1 < len(args):
            v = args[i + 1]
            if a == "--page":
                page = int(v)
            elif a == "--purity":
                cfg["purity"] = v
            elif a == "--categories":
                cfg["categories"] = v
            elif a == "--sorting":
                cfg["sorting"] = v
            elif a == "--range":
                cfg["top_range"] = v
            elif a == "--ratios":
                cfg["ratio_filter"] = f"ratios={v}" if v else ""
            elif a == "--atleast":
                cfg["resolution_filter"] = f"atleast={v}" if v else ""
            elif a == "--source":
                cfg["source"] = v
            elif a == "--track":
                cfg["track"] = v
            i += 2
        else:
            rest.append(a)
            i += 1
    return cfg, rest, page


def meta_path(cfg):
    return os.path.join(cfg["cache_dir"], "meta.json")


def load_meta(cfg):
    try:
        with open(meta_path(cfg)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_meta(cfg, meta):
    os.makedirs(cfg["cache_dir"], exist_ok=True)
    tmp = meta_path(cfg) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(meta, f)
    os.replace(tmp, meta_path(cfg))


def wall_id(filename):
    """Key into meta.json: wallhaven-abc123.png -> abc123, konachan-42.jpg -> konachan-42,
    None for files that came from nowhere we know."""
    base = os.path.splitext(filename)[0]
    if base.startswith("wallhaven-"):
        return base[len("wallhaven-"):]
    src = base.split("-", 1)[0]
    return base if src in providers.SOURCES else None


THUMB_W = 1600


def thumb_of(cfg, path):
    """Cached preview for a local file, or None if it isn't built (or is stale)."""
    t = os.path.join(cfg["cache_dir"], "thumbs", os.path.basename(path) + ".jpg")
    try:
        if os.path.getmtime(t) >= os.path.getmtime(path):
            return t
    except OSError:
        pass
    return None


def make_thumb(cfg, path):
    t = os.path.join(cfg["cache_dir"], "thumbs", os.path.basename(path) + ".jpg")
    os.makedirs(os.path.dirname(t), exist_ok=True)
    tmp = t + ".tmp.jpg"
    r = subprocess.run(["magick", path + "[0]", "-auto-orient", "-resize", f"{THUMB_W}x{THUMB_W}>",
                        "-strip", "-quality", "82", tmp], capture_output=True)
    if r.returncode == 0:
        os.replace(tmp, t)


def allowed(purity_mask, purity):
    """purity_mask like "110"; unknown purity is shown only when SFW is allowed."""
    bit = PURITY_BIT.get(purity, 0)
    return len(purity_mask) > bit and purity_mask[bit] == "1"


def _ext_of(path):
    try:
        with open(path, "rb") as f:
            head = f.read(12)
    except OSError:
        return ".jpg"
    if head.startswith(b"\x89PNG"):
        return ".png"
    if head[8:12] == b"WEBP":
        return ".webp"
    return ".jpg"


def paint(path):
    """Paint on every output with awww, starting the daemon if needed."""
    if subprocess.run(["awww", "query"], capture_output=True).returncode != 0:
        subprocess.Popen(["awww-daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        for _ in range(20):
            if subprocess.run(["awww", "query"], capture_output=True).returncode == 0:
                break
            subprocess.run(["sleep", "0.1"])
    subprocess.run(["awww", "img", path, "--transition-type", "grow", "--transition-pos", "top-right",
                    "--transition-duration", "1.2", "--transition-fps", "120"])
    # remember it so login restores it (awww also caches per output)
    link = os.path.expanduser("~/.cache/hyprwall/current")
    os.makedirs(os.path.dirname(link), exist_ok=True)
    try:
        if os.path.lexists(link):
            os.remove(link)
        os.symlink(path, link)
    except OSError:
        pass


def cmd_search(cfg, args):
    cfg, args, page = parse_flags(cfg, args)
    query = " ".join(args).strip()
    source = cfg.get("source", "wallhaven")
    if source != "wallhaven":
        return search_provider(cfg, source, query, page)
    mode = "query" if query else "toplist"
    items, last, total = asyncio.run(fetch_wallpapers(cfg, page, mode, query, limit=24, download_thumbs=False))
    # remember ratings so downloaded wallpapers can be filtered in the Library
    meta = load_meta(cfg)
    for w in items:
        m = w.get("meta", {})
        meta[w["id"]] = {"purity": m.get("purity", "sfw"), "category": m.get("category", "general")}
    if items:
        save_meta(cfg, meta)
    print(json.dumps({"page": page, "lastPage": last, "total": total, "items": [
        {"id": w["id"], "thumb": w.get("thumb_url") or w["local_path"], "url": w["full_url"],
         "purity": w.get("meta", {}).get("purity", "sfw"),
         "category": w.get("meta", {}).get("category", "general")} for w in items]}))


def search_provider(cfg, source, query, page):
    try:
        items, last, total = providers.SOURCES[source](cfg, query, page)
    except providers.NeedsKey as e:
        print(json.dumps({"page": page, "lastPage": 1, "items": [], "error": "needs_key",
                          "var": e.var, "signup": e.signup}))
        return
    except providers.NoResults as e:
        print(json.dumps({"page": page, "lastPage": 1, "items": [], "error": "hint", "hint": str(e)}))
        return
    except Exception as e:
        print(json.dumps({"page": page, "lastPage": 1, "items": [], "error": str(e)[:200]}))
        return
    meta = load_meta(cfg)
    for w in items:
        meta[f"{source}-{w['id']}"] = {"purity": w["purity"], "category": w["category"]}
    if items:
        save_meta(cfg, meta)
    print(json.dumps({"page": page, "lastPage": last, "total": total, "items": items}))


def cmd_list(cfg, args):
    cfg, args, _ = parse_flags(cfg, args)
    query = " ".join(args)
    meta = load_meta(cfg)
    out, unknown, missing = [], 0, 0
    for w in fetch_local_wallpapers(cfg, query):
        wid = wall_id(w["id"])
        m = meta.get(wid, {}) if wid else {}
        if wid and not m and w["id"].startswith("wallhaven-"):
            unknown += 1  # only Wallhaven ratings can be looked up afterwards
        purity = m.get("purity", "unknown")
        if not allowed(cfg["purity"], purity):
            continue
        cats = cfg.get("categories", "111")
        ci = {"general": 0, "anime": 1, "people": 2}.get(m.get("category"), -1)
        if ci >= 0 and len(cats) > ci and cats[ci] != "1":
            continue
        thumb = thumb_of(cfg, w["local_path"])
        if not thumb:
            missing += 1
        out.append({"id": w["id"], "thumb": thumb or w["local_path"], "url": w["local_path"],
                    "purity": purity, "category": m.get("category", "")})
    print(json.dumps({"page": 1, "lastPage": 1, "total": len(out), "unknown": unknown,
                      "missingThumbs": missing, "items": out}))


def cmd_thumbs(cfg, args):
    from concurrent.futures import ThreadPoolExecutor
    todo = [w["local_path"] for w in fetch_local_wallpapers(cfg, "") if not thumb_of(cfg, w["local_path"])]
    with ThreadPoolExecutor(max_workers=max(2, (os.cpu_count() or 4) // 2)) as ex:
        list(ex.map(lambda p: make_thumb(cfg, p), todo))
    print(json.dumps({"built": len(todo)}))


def cmd_meta(cfg, args):
    """Fill meta.json for local wallhaven-* files (Wallhaven allows ~45 requests/min)."""
    import time
    meta = load_meta(cfg)
    todo = []
    for f in sorted(os.listdir(cfg["wall_dir"])):
        wid = wall_id(f)
        if wid and wid not in meta and f.startswith("wallhaven-"):
            todo.append(wid)
    for n, wid in enumerate(todo):
        url = f"https://wallhaven.cc/api/v1/w/{wid}"
        if cfg.get("api_key"):
            url += f"?apikey={cfg['api_key']}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
                d = json.load(r)["data"]
            meta[wid] = {"purity": d.get("purity", "sfw"), "category": d.get("category", "general")}
        except urllib.error.HTTPError as e:
            if e.code == 401:  # NSFW posts need an API key to view
                meta[wid] = {"purity": "nsfw", "category": ""}
            elif e.code == 404:
                meta[wid] = {"purity": "unknown", "category": ""}
            elif e.code == 429:
                time.sleep(30)
                continue
        except Exception:
            pass
        save_meta(cfg, meta)
        if n + 1 < len(todo):
            time.sleep(1.4)
    print(json.dumps({"checked": len(todo)}))


def cmd_apply(cfg, args):
    cfg, args, _ = parse_flags(cfg, args)
    target, url = args[0], (args[1] if len(args) > 1 else "")
    source = cfg.get("source", "wallhaven")
    if os.path.isfile(target):
        paint(os.path.abspath(target))
        return
    # online id: download the full image into the cache, then keep it in wall_dir
    name = target if source == "wallhaven" else f"{source}-{target}"
    cache = os.path.join(cfg["cache_dir"], "online_thumbs", f"{name}_full.jpg")
    if not os.path.exists(cache):
        if not url:
            sys.exit("apply: unknown id and no url given")
        if not asyncio.run(download_worker(url, cache)):
            sys.exit("apply: download failed")
    os.makedirs(cfg["wall_dir"], exist_ok=True)
    prefix = "wallhaven-" if source == "wallhaven" else ""
    dest = os.path.join(cfg["wall_dir"], f"{prefix}{name}{_ext_of(cache)}")
    with open(cache, "rb") as src, open(dest, "wb") as out:
        out.write(src.read())
    providers.track(source, cfg.get("track", ""))
    paint(dest)


def cmd_random(cfg, args):
    cfg, _, _ = parse_flags(cfg, args)
    meta = load_meta(cfg)
    items = [w for w in fetch_local_wallpapers(cfg, "")
             if allowed(cfg["purity"], meta.get(wall_id(w["id"]) or "", {}).get("purity", "unknown"))]
    if items:
        paint(random.choice(items)["local_path"])


COMMANDS = {"search": cmd_search, "list": cmd_list, "apply": cmd_apply, "random": cmd_random, "meta": cmd_meta, "thumbs": cmd_thumbs}


def run(cfg, argv):
    COMMANDS[argv[0]](cfg, argv[1:])
