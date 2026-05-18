#!/bin/bash
# Install and start the GHN Dashboard Auto-refresh service

PLIST_NAME="com.ghn.dashboard.refresh.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME"
SOURCE_PATH="/Users/macbook/Downloads/GHN/$PLIST_NAME"

echo "🚀 Setting up GHN Dashboard Auto-refresh..."

# Copy plist to LaunchAgents
cp "$SOURCE_PATH" "$PLIST_PATH"

# Unload if already running
launchctl bootout gui/$(id -u) "$PLIST_PATH" 2>/dev/null

# Load and start
launchctl bootstrap gui/$(id -u) "$PLIST_PATH"

echo "✅ Auto-refresh service installed and started!"
echo "📈 Data will update every hour on the hour (7h, 8h, 9h...)"
echo "📝 Logs can be found at: /Users/macbook/Downloads/GHN/auto_refresh.log"
