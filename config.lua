-- ==========================================
-- HYPRWALL ENGINE CONFIGURATION MODULE (LUA)
-- ==========================================

return {
	api_uri = "https://wallhaven.cc/api/v1/search",
	wall_dir = os.getenv("HOME") .. "/Pictures/Wallpapers",
	cache_dir = os.getenv("HOME") .. "/.cache/hyprwall",
	theme_file = os.getenv("HOME") .. "/.config/rofi/hyprwall.rasi",

	-- Active Screen Outputs (Zsh maps this dynamically)
	monitors = { "eDP-1", "HDMI-A-1" },

	-- Search Filters
	api_key = "",
	categories = "111", -- general/anime/people -> (1 = on, 0 = off)
	purity = "100", -- SFW / Sketchy / NSFW -> (100 = SFW only)
	sorting = "toplist", -- date_added, relevance, random, views, favorites, toplist
	top_range = "1M", -- 1d, 3d, 1w, 1M, 3M, 6M, 1y

	-- Resolution Targets
	resolution_filter = "atleast=1920x1080",
	ratio_filter = "ratios=16x9,16x10",
}
