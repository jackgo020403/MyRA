# Research Assistant - Quick Start Guide

## For End Users (Using the .exe)

### First Time Setup

1. **Get the Application**
   - Download `ResearchAssistant.exe`
   - Place it in a folder of your choice

2. **Get API Keys** (Required)
   - **Anthropic API**: Go to https://console.anthropic.com/
     - Sign up for an account
     - Navigate to API Keys
     - Create a new key

   - **Serper API**: Go to https://serper.dev/
     - Sign up (free tier available)
     - Get your API key from dashboard

3. **Configure the App**
   - Double-click `ResearchAssistant.exe`
   - Click the "⚙ Settings" button in top-right
   - Paste your API keys
   - Click OK

### Using the Application

1. **Start Research**
   - Type your research question in the input box at bottom
   - Example: "What are the major trends in AI safety research in 2024?"
   - Press Enter or click "Send"

2. **Wait for Results**
   - The app will show progress messages
   - Research typically takes 3-5 minutes
   - You'll see status updates in the chat

3. **Review Results**
   - When complete, you'll get a notification
   - Excel file is saved to `outputs/` folder
   - File contains 3 tabs:
     - **MEMO**: Executive summary
     - **SYNTHESIS**: Detailed analysis
     - **RAW DATA**: All evidence with sources

### Tips

- ✅ **Be specific** in your research questions
- ✅ **Include timeframes** if relevant (e.g., "2022-2024")
- ✅ **Mention key entities** you want researched
- ✅ **Check the outputs folder** for all generated reports
- ⚠️ **Don't close** the app while research is running

---

## For Developers (Building from Source)

### Quick Build

1. **Install Dependencies**
   ```bash
   pip install -r requirements-gui.txt
   ```

2. **Run Build Script**
   ```bash
   build.bat
   ```

3. **Find Executable**
   - Look in `dist/ResearchAssistant.exe`

### Development Mode

To run without building:

```bash
python gui_app.py
```

This runs the GUI directly from Python (useful for development/testing).

---

## Features

### Chat-Like Interface
- Clean, modern design similar to ChatGPT
- User messages on left, assistant on right
- Scrollable chat history

### API Configuration
- Easy settings dialog
- Secure password fields
- Saves to `.env` file

### Background Processing
- Research runs in background thread
- UI stays responsive
- Progress updates in real-time

### Comprehensive Output
- **Evidence Collection**: Web research with quality filters
- **Synthesis**: AI-generated analysis per sub-question
- **Executive Memo**: High-level summary with insights
- **Citations**: All sources with clickable hyperlinks

---

## System Requirements

- **OS**: Windows 10 or later
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 500MB free space
- **Internet**: Required for API calls and web research

---

## Troubleshooting

### "API Keys Required" Error
- Click Settings (⚙) button
- Enter both API keys
- Make sure they're valid

### "Research Failed" Error
- Check internet connection
- Verify API keys are correct
- Ensure you have API credits remaining

### Can't Find Excel File
- Look in `outputs/` folder (same location as .exe)
- Check chat messages for full file path

### App Won't Start
- Make sure you downloaded the full file
- Try running as Administrator
- Check Windows Defender hasn't blocked it

---

## Support

For issues or questions:
1. Check `BUILD_INSTRUCTIONS.md` for technical details
2. Review error messages in the chat window
3. Contact your system administrator

---

## Privacy & Security

- ✅ All research runs locally on your machine
- ✅ API keys stored locally in `.env` file
- ✅ Only connects to Anthropic and Serper APIs
- ✅ No telemetry or data collection
- ✅ Source code compiled and not easily visible
