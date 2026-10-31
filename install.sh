#!/usr/bin/env bash

# Define source and destination paths
SOURCE_DIR="$HOME/.config/hyprwall"
BIN_DIR="$HOME/.local/bin"
TARGET_BIN="$BIN_DIR/hyprwall"

echo "=================================================="
echo "Installing Hyprwall Wallpaper Manager Modules..."
echo "=================================================="

# 1. Guarantee global binary path folder is available
mkdir -p "$BIN_DIR"

# 2. Clear out any old aliased or broken extension files to prevent shell parsing bugs
echo "🧹 Purging old execution file references..."
rm -f "$BIN_DIR/hyprwall"
rm -f "$BIN_DIR/hyprwall.py"

# 3. Ensure the underlying project script files are executable
if [ -f "$SOURCE_DIR/hyprwall.py" ]; then
  chmod +x "$SOURCE_DIR/hyprwall.py"
  echo "✔ Marked master source script workspace as executable."
else
  echo "❌ Error: Could not find primary script at $SOURCE_DIR/hyprwall.py"
  exit 1
fi

# 4. Generate the explicit binary shell wrapper to bypass image validation errors
echo "🚀 Generating native binary execution wrapper link..."
cat <<EOF >"$TARGET_BIN"
#!/usr/bin/env bash
python3 "$SOURCE_DIR/hyprwall.py" "\$@"
EOF

# 5. Make the wrapper executable and clear out the active shell location cache table
chmod +x "$TARGET_BIN"
if [ -n "$ZSH_VERSION" ] || [ -f "/bin/zsh" ]; then
  zsh -c "rehash" 2>/dev/null
elif [ -n "$BASH_VERSION" ]; then
  hash -r 2>/dev/null
fi

echo "=================================================="
echo "✔ Setup complete! You can now type: hyprwall"
echo "=================================================="
