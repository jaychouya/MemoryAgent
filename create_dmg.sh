#!/bin/bash
set -e

APP_NAME="MemoryAgent"
VERSION="1.0.1"
DMG_NAME="${APP_NAME}-Installer-${VERSION}.dmg"
VOLUME_NAME="${APP_NAME} Installer"

echo "Creating ${APP_NAME} ${VERSION} installer..."

rm -rf "${APP_NAME}.app" "${DMG_NAME}" dmg_staging

mkdir -p "${APP_NAME}.app/Contents/MacOS"
mkdir -p "${APP_NAME}.app/Contents/Resources"

cat > "${APP_NAME}.app/Contents/Info.plist" << EOF
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
    <string>${VERSION}</string>
    <key>CFBundleVersion</key>
    <string>2</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

cat > "${APP_NAME}.app/Contents/MacOS/MemoryAgent" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$DIR/../Resources/scripts/launch-memoryagent.sh"
LAUNCHER

chmod +x "${APP_NAME}.app/Contents/MacOS/MemoryAgent"

echo "Copying application files..."
cp -r src "${APP_NAME}.app/Contents/Resources/"
cp requirements.txt "${APP_NAME}.app/Contents/Resources/"
cp -r frontend "${APP_NAME}.app/Contents/Resources/"
mkdir -p "${APP_NAME}.app/Contents/Resources/scripts"
cp scripts/launch-memoryagent.sh "${APP_NAME}.app/Contents/Resources/scripts/"
chmod +x "${APP_NAME}.app/Contents/Resources/scripts/launch-memoryagent.sh"

rm -rf "${APP_NAME}.app/Contents/Resources/frontend/node_modules" \
       "${APP_NAME}.app/Contents/Resources/frontend/.next" 2>/dev/null || true

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

rm -rf dmg_staging

ln -sf "${DMG_NAME}" "${APP_NAME}-Installer.dmg"

echo ""
echo "Build complete: ${DMG_NAME} ($(du -h "${DMG_NAME}" | cut -f1))"
