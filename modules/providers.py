"""Extra wallpaper sources for the Quickshell picker (Wallhaven lives in api_engine).

Every provider returns (items, last_page, total) where each item is
  {"id", "thumb" (preview URL), "url" (full image URL), "purity", "category",
   "title", "track" (optional URL to ping on download, Unsplash requires it)}

API keys come from the environment or ~/.config/hyprwall/keys.env (KEY=value lines):
  UNSPLASH_ACCESS_KEY   https://unsplash.com/developers  (free, 50 requests/hour)
  PEXELS_API_KEY        https://www.pexels.com/api/      (free, 200 requests/hour)
"""
import json
import os
import urllib.parse
import urllib.request

UA = "hyprwall/1.0 (+https://github.com/hyprwm/Hyprland)"
PER_PAGE = 24
KEYS_FILE = os.path.expanduser("~/.config/hyprwall/keys.env")


class NeedsKey(Exception):
    """Raised when a source needs an API key that isn't set."""

    def __init__(self, var, signup):
        super().__init__(var)
        self.var = var
        self.signup = signup


class NoResults(Exception):
    """Nothing found, with a hint worth showing to the user."""


def key(name):
    if os.environ.get(name):
        return os.environ[name].strip()
    try:
        with open(KEYS_FILE) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    line = line[7:]
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    if k.strip() == name:
                        return v.strip().strip("'\"")
    except OSError:
        pass
    return ""


def get_json(url, headers=None, timeout=15):
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return json.load(r), r.headers


def ping(url, headers=None):
    """Fire-and-forget GET (Unsplash download tracking)."""
    try:
        h = {"User-Agent": UA}
        h.update(headers or {})
        urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=10).read()
    except Exception:
        pass


def min_width(atleast):
    try:
        return int(atleast.split("x")[0]) if atleast else 0
    except ValueError:
        return 0


# ---------------------------------------------------------------- Bing (no key)
def bing(cfg, query, page):
    # The archive serves the last ~16 days: idx 0..7 with n=8, plus idx 8 for older ones.
    items, seen = [], set()
    for idx in (0, 8):
        try:
            d, _ = get_json(f"https://www.bing.com/HPImageArchive.aspx?format=js&idx={idx}&n=8&mkt=en-US")
        except Exception:
            continue
        for im in d.get("images", []):
            hid = im.get("hsh") or im.get("startdate")
            if hid in seen:
                continue
            seen.add(hid)
            base = "https://www.bing.com" + im["urlbase"]
            title = im.get("title") or im.get("copyright", "")
            items.append({"id": f"{im.get('startdate', '')}-{hid[:8]}", "thumb": base + "_1920x1080.jpg",
                          "url": base + "_UHD.jpg", "purity": "sfw", "category": "general",
                          "title": f"{title} · {im.get('copyright', '').split('(')[-1].rstrip(')')}"
                          if title else im.get("copyright", "")})
    q = query.lower()
    if q:
        items = [i for i in items if q in i["title"].lower()]
    return items, 1, len(items)


# ---------------------------------------------------------- Unsplash (key)
def unsplash(cfg, query, page):
    k = key("UNSPLASH_ACCESS_KEY")
    if not k:
        raise NeedsKey("UNSPLASH_ACCESS_KEY", "unsplash.com/developers")
    auth = {"Authorization": f"Client-ID {k}", "Accept-Version": "v1"}
    if query:
        qs = urllib.parse.urlencode({"query": query, "page": page, "per_page": PER_PAGE,
                                     "orientation": "landscape", "order_by": "relevant"})
        d, _ = get_json(f"https://api.unsplash.com/search/photos?{qs}", auth)
        photos, last, total = d.get("results", []), d.get("total_pages", 1), d.get("total")
    else:
        qs = urllib.parse.urlencode({"page": page, "per_page": PER_PAGE, "orientation": "landscape"})
        photos, h = get_json(f"https://api.unsplash.com/topics/wallpapers/photos?{qs}", auth)
        total = int(h.get("X-Total") or 0) or None
        last = max(1, -(-total // PER_PAGE)) if total else page + 1
    w = max(1920, min_width(cfg.get("resolution_filter", "").replace("atleast=", "")) or 3840)
    items = []
    for p in photos:
        raw = p["urls"]["raw"]
        sep = "&" if "?" in raw else "?"
        items.append({"id": p["id"], "thumb": p["urls"].get("regular"),
                      "url": f"{raw}{sep}w={max(w, 3840)}&q=85&fm=jpg&fit=max",
                      "purity": "sfw", "category": "general",
                      "title": f"{(p.get('alt_description') or p.get('description') or '').strip()[:60]}"
                               f" · {p.get('user', {}).get('name', '')}",
                      "track": p.get("links", {}).get("download_location", "")})
    return items, last, total


# ---------------------------------------------------------- Pexels (key)
def pexels(cfg, query, page):
    k = key("PEXELS_API_KEY")
    if not k:
        raise NeedsKey("PEXELS_API_KEY", "pexels.com/api")
    auth = {"Authorization": k}
    params = {"page": page, "per_page": PER_PAGE}
    if query:
        params.update({"query": query, "orientation": "landscape", "size": "large"})
        url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(params)
    else:
        url = "https://api.pexels.com/v1/curated?" + urllib.parse.urlencode(params)
    d, _ = get_json(url, auth)
    total = d.get("total_results")
    last = max(1, -(-total // PER_PAGE)) if total else (page + 1 if d.get("next_page") else page)
    items = []
    for p in d.get("photos", []):
        if not query and p.get("width", 1) < p.get("height", 0):
            continue  # curated feed mixes in portrait shots
        items.append({"id": str(p["id"]), "thumb": p["src"].get("large2x") or p["src"].get("large"),
                      "url": p["src"]["original"], "purity": "sfw", "category": "general",
                      "title": f"{(p.get('alt') or '').strip()[:60]} · {p.get('photographer', '')}"})
    return items, last, total


SOURCES = {"bing": bing, "unsplash": unsplash, "pexels": pexels}


def track(source, url):
    """Download tracking some APIs ask for when an image is actually used."""
    if source == "unsplash" and url:
        k = key("UNSPLASH_ACCESS_KEY")
        if k:
            ping(url, {"Authorization": f"Client-ID {k}"})
