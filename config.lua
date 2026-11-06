-- ==========================================
-- HYPRWALL ENGINE CONFIGURATION MODULE (LUA)
-- ==========================================

return {
	api_uri = "https://wallhaven.cc/api/v1/search",
	wall_dir = os.getenv("HOME") .. "/Pictures/Wallpapers",
	cache_dir = os.getenv("HOME") .. "/.cache/hyprwall",

	-- unused by the painter (awww paints every output); kept for the config loader
	monitors = { "eDP-1", "HDMI-A-1" },

	-- Search Filters
	api_key = os.getenv("WALLHAVEN_API_KEY") or "",
	categories = "111", -- general/anime/people -> (1 = on, 0 = off)
	purity = "111", -- SFW / Sketchy / NSFW -> (100 = SFW only)
	sorting = "favorites", -- date_added, relevance, random, views, favorites, toplist
	top_range = "3d", -- 1d, 3d, 1w, 1M, 3M, 6M, 1y

	-- Resolution Targets
	resolution_filter = "atleast=1920x1080",
	ratio_filter = "ratios=16x9,16x10",
}
