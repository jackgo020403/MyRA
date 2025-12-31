# Building the Research Assistant Windows Application

This guide shows how to package the Research Assistant into a standalone Windows executable.

## Prerequisites

1. Python 3.12 installed
2. All project dependencies installed

## Step 1: Install GUI Dependencies

```bash
pip install -r requirements-gui.txt
```

This installs:
- PyQt6 (GUI framework)
- PyInstaller (packaging tool)
- All other required dependencies

## Step 2: Build the Executable

Run PyInstaller with the spec file:

```bash
pyinstaller build_app.spec
```

This will:
- Analyze all dependencies
- Bundle Python interpreter and libraries
- Package everything into a single .exe file
- Output to `dist/ResearchAssistant.exe`

**Build time:** 2-5 minutes depending on your system.

## Step 3: Test the Application

After building, you'll find the executable at:

```
dist/ResearchAssistant.exe
```

Double-click to run. The application will:
1. Show a chat-like interface
2. Prompt for API keys on first run (Settings button)
3. Allow you to enter research questions
4. Generate Excel reports with research results

## Step 4: Distribute

To share the application:

1. **Option A - Single File:**
   - Just send `dist/ResearchAssistant.exe`
   - Users need to configure API keys on first run
   - No Python installation required!

2. **Option B - With .env:**
   - Create a `.env` file with API keys:
     ```
     ANTHROPIC_API_KEY=your_key_here
     SERPER_API_KEY=your_key_here
     ```
   - Place it in the same folder as `ResearchAssistant.exe`
   - Zip the folder and share

## Features

✅ **Clean Chat Interface** - Similar to ChatGPT/Claude
✅ **No Console Window** - Professional windowed app
✅ **Self-Contained** - All code bundled, not visible to users
✅ **Easy Configuration** - Settings dialog for API keys
✅ **Progress Indication** - Shows research status
✅ **Excel Output** - Generates comprehensive research reports

## File Size

- Executable size: ~150-200 MB
- This includes Python interpreter and all libraries
- No installation required for end users

## Troubleshooting

### Build fails with "module not found"
- Ensure all dependencies are installed: `pip install -r requirements-gui.txt`
- Try: `pip install --upgrade pyinstaller`

### Executable doesn't start
- Run from command prompt to see error messages:
  ```bash
  cd dist
  ResearchAssistant.exe
  ```

### Missing .md files error
- The spec file includes the prompts folder
- Ensure `ra_orchestrator/prompts/*.md` files exist

## Advanced: Custom Icon

To add a custom icon:

1. Create or download a `.ico` file
2. Edit `build_app.spec`, change `icon=None` to:
   ```python
   icon='path/to/your/icon.ico'
   ```
3. Rebuild: `pyinstaller build_app.spec`

## Performance Notes

- First run may be slower (PyQt6 initialization)
- Research takes 2-5 minutes depending on complexity
- Excel generation is fast (<1 second)
- Application uses ~200-300 MB RAM when running

## Security

- Code is compiled to bytecode (.pyc)
- Not easily reverse-engineered
- API keys stored in local .env file (user-controlled)
- No telemetry or external connections except API calls
