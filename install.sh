#!/usr/bin/env bash

# Define updated repository and destination paths
SOURCE_DIR="$HOME/.config/hyprwallhaven-engine"
BIN_DIR="$HOME/.local/bin"
TARGET_BIN="$BIN_DIR/hyprwall"

echo "=================================================="
echo "Installing Hyprwallhaven-Engine Modules..."
echo "=================================================="

# 1. Validate System Core Components
echo "🔍 Interrogating system runtime dependencies..."
# FIXED: Swapped notification-daemon out for your active swaync application
DEPENDENCIES=(awww hyprland lua feh swaync socat)
MISSING_DEPS=0

for pkg in "${DEPENDENCIES[@]}"; do
  if ! command -v "$pkg" &>/dev/null; then
    echo "  ❌ Missing package: '$pkg' is not installed or missing from your PATH."
    MISSING_DEPS=$((MISSING_DEPS + 1))
  else
    echo "  ✔ Found package: '$pkg'"
  fi
done

if [ "$MISSING_DEPS" -gt 0 ]; then
  echo "⚠️  Warning: $MISSING_DEPS core packages are missing. Install them via pacman."
fi

# 2. Build Cache Paths and Verify config.lua Directory Configurations
echo "📁 Syncing runtime configuration environments..."
mkdir -p "$BIN_DIR"
mkdir -p "$HOME/.cache/hyprwall/online_thumbs"

if command -v lua &>/dev/null && [ -f "$SOURCE_DIR/config.lua" ]; then
  # Dynamically extract target wallpaper dir from config.lua to guarantee folder allocation
  WALL_DIR=$(lua -e "local c = dofile('$SOURCE_DIR/config.lua'); print(c.wall_dir)")
  if [ -n "$WALL_DIR" ]; then
    mkdir -p "$WALL_DIR"
    echo "  ✔ Wallpaper storage destination established: $WALL_DIR"
  fi
fi

# 3. Clean stale file handles to prevent zsh alias collision
rm -f "$BIN_DIR/hyprwall"
rm -f "$BIN_DIR/hyprwall.py"

# 4. Source Executable Permission Handling
if [ -f "$SOURCE_DIR/hyprwall.py" ]; then
  chmod +x "$SOURCE_DIR/hyprwall.py"
  echo "  ✔ Marked master source script workspace as executable."
else
  echo "❌ Error: Primary engine wrapper missing at $SOURCE_DIR/hyprwall.py"
  exit 1
fi

# 5. Output Native Executable Subprocess Wrapper
echo "🚀 Emitting binary execution layer wrapper..."
cat <<EOF >"$TARGET_BIN"
#!/usr/bin/env bash
python3 "$SOURCE_DIR/hyprwall.py" "\$@"
EOF
chmod +x "$TARGET_BIN"

# Force environment table hash re-index updates
if [ -n "$ZSH_VERSION" ] || [ -f "/bin/zsh" ]; then
  zsh -c "rehash" 2>/dev/null
elif [ -n "$BASH_VERSION" ]; then
  hash -r 2>/dev/null
fi

echo "=================================================="
echo "✔ Setup complete! Launch globally using: hyprwall"
echo "=================================================="
echo ""
echo "👉 To integrate Hyprwall into your Lua-based desktop,"
echo "   add these lines to your ~/.config/hypr/hyprland.lua:"
echo ""
echo "   hl.exec_once(\"awww-daemon\")"
echo "   hl.bind(\"SUPER\", \"W\", \"exec\", \"hyprwall online\")"
echo "   hl.bind(\"SUPER_ALT\", \"W\", \"exec\", \"hyprwall local\")"
echo ""
echo "=================================================="
