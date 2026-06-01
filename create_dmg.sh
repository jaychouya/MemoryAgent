#!/bin/bash
# Simple script to create MemoryAgent DMG

set -e

APP_NAME="MemoryAgent"
DMG_NAME="${APP_NAME}-Installer.dmg"
VOLUME_NAME="${APP_NAME} Installer"

echo "Creating ${APP_NAME} installer..."

# Clean previous builds
rm -rf "${APP_NAME}.app" "${DMG_NAME}" dmg_staging

# Create app bundle structure
mkdir -p "${APP_NAME}.app/Contents/MacOS"
mkdir -p "${APP_NAME}.app/Contents/Resources"

# Create Info.plist
cat > "${APP_NAME}.app/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleDisplayName</key>
    <string>MemoryAgent</string>
    <key>CFBundleExecutable</key>
    <string>MemoryAgent</string>
    <key>CFBundleIdentifier</key>
    <string>com.memoryagent.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>MemoryAgent</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create launcher script
cat > "${APP_NAME}.app/Contents/MacOS/MemoryAgent" << 'LAUNCHER'
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/../Resources"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 is required. Please install Python 3.9 or later." buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import fastapi" &> /dev/null; then
    osascript -e 'display dialog "Installing dependencies. This may take a few minutes..." buttons {"OK"} default button "OK" giving up after 3'
    pip3 install -r requirements.txt
fi

# Start the application
echo "Starting MemoryAgent..."
python3 src/main.py
LAUNCHER

chmod +x "${APP_NAME}.app/Contents/MacOS/MemoryAgent"

# Copy application files
echo "Copying application files..."
cp -r src "${APP_NAME}.app/Contents/Resources/"
cp requirements.txt "${APP_NAME}.app/Contents/Resources/"

# Create DMG
echo "Creating DMG..."
mkdir -p dmg_staging
mv "${APP_NAME}.app" dmg_staging/
ln -s /Applications dmg_staging/Applications

hdiutil create \
    -volname "${VOLUME_NAME}" \
    -srcfolder dmg_staging \
    -ov \
    -format UDZO \
    "${DMG_NAME}"

# Cleanup
rm -rf dmg_staging

echo ""
echo "Build complete!"
echo "DMG file: ${DMG_NAME}"
echo "Size: $(du -h "${DMG_NAME}" | cut -f1)"
echo ""
echo "To install: Open ${DMG_NAME} and drag ${APP_NAME} to Applications"
