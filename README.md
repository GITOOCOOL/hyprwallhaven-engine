
# Hyprwall

A lightweight, modern, and highly modular asynchronous wallpaper manager crafted specifically for **Hyprland** and Wayland environments. Built with Python 3 and GTK 3, it allows you to dynamically browse, search, and apply wallpapers from Wallhaven or your local machine across multi-monitor environments natively.

## 🚀 Features

- **Dual-Mode Engine:** Browse high-res assets online via Wallhaven's API, or manage offline files locally from your wallpaper directory.
- **Modern Transitions:** Utilises the native `awww` (or `swww`) animation backend to push smooth wave transitions across workspaces.
- **Robust Multi-Monitor Sync:** Built to explicitly handle complex display environments, including transformed displays sitting on negative coordinate spaces.
- **Smart Image Decoder:** Reads runtime file binary magic bytes to eliminate extension masking issues, preventing image load failure panics.
- **Bypasses Shell Parsing Issues:** Uses an automated execution loader wrapper to avoid ImageMagick `import` command path collisions.

## ⌨ Keyboard Controls

When the gallery loop window is open, use these interactive hotkeys:

| Keybind | Action |
| :--- | :--- |
| `Right Arrow` / `l` | Navigate to the **Next** wallpaper |
| `Left Arrow` / `h` | Navigate to the **Previous** wallpaper |
| `Up Arrow` / `k` | Request **Previous Page** from Wallhaven API (Online Mode Only) |
| `Down Arrow` / `j` | Request **Next Page** from Wallhaven API (Online Mode Only) |
| `Alt + f` / `/` / `s` | **Toggle Search Bar** and focus cursor inside the text input box |
| `Return` / `Space` | **Apply Selected Wallpaper** cleanly across all active displays |
| `Escape` | Dismiss active search entry focus / Exit Application |
| `q` | Immediately **Quit** the application loop safely |

## 🛠 Installation & Setup

1. **Clone or copy the workspace directory** to your local config folder:
   ```bash
   cd ~/.config/hyprwall
   ```

2. **Make the installer script executable and run it**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   *The script automatically purges stale paths and links an executable `hyprwall` binary script loader straight to your `~/.local/bin/` execution path.*

3. **Verify the global installation profile**:
   ```bash
   hyprwall online  # Run online mode (Toplist/Query mapping)
   hyprwall local   # Run local mode (Offline storage directory)
   ```

## ⚙ Dependencies

Ensure these packages are installed on your Arch Linux system:
```bash
sudo pacman -S python-gobject gtk3 awww feh notification-daemon
```
## 🔗 Hyprland Lua Keybind Integration

To launch the wallpaper manager instantly using your Lua-based configuration syntax, open your main configuration script (usually `~/.config/hypr/hyprland.lua`) and append these instructions:

```lua

hl.bind(
	"SUPER + W",
	hl.dsp.exec_cmd("~/.local/bin/hyprwall online"),
	{ description = "Open Wallhaven Interactive Menu Browser" }
)
hl.bind(
	"SUPER + SHIFT + W",
	hl.dsp.exec_cmd("~/.local/bin/hyprwall local"),
	{ description = "Rotate and Apply a Random Hot Wallpaper" }
)
