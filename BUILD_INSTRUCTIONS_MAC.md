# Building Research Assistant for macOS

## Prerequisites
- macOS 10.13 or later
- Python 3.12 installed (download from python.org)

## Steps

1. **Open Terminal**

2. **Navigate to project folder**:
   ```bash
   cd /path/to/MyRA
   ```

3. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   pip3 install pyinstaller
   ```

4. **Build the app**:
   ```bash
   pyinstaller build_app_lite.spec --noconfirm
   ```

5. **Find the built app**:
   - Location: `dist/ResearchAssistant.app`
   - Double-click to test it

6. **Create a DMG for distribution** (optional):
   ```bash
   mkdir -p dist/dmg
   cp -r dist/ResearchAssistant.app dist/dmg/
   hdiutil create -volname "Research Assistant" -srcfolder dist/dmg -ov -format UDZO dist/ResearchAssistant.dmg
   ```

7. **Share the file**:
   - Share `dist/ResearchAssistant.app` (right-click → Compress to create .zip)
   - Or share `dist/ResearchAssistant.dmg`

## Troubleshooting

### "App is damaged and can't be opened"
This happens because the app isn't code-signed. Users need to run:
```bash
xattr -cr /path/to/ResearchAssistant.app
```

Or right-click → Open (instead of double-click) the first time.

### Python not found
Install Python from https://www.python.org/downloads/mac-osx/
