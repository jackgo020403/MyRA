# Installation Guide

## Prerequisites

- Python 3.8 or higher
- VS Code (recommended)
- Anthropic API key ([Get one here](https://console.anthropic.com/))

## Installation Methods

### Method 1: Automated Setup (Windows - Recommended)

1. Open VS Code
2. Open terminal (`` Ctrl+` ``)
3. Navigate to project:
   ```bash
   cd c:/project/local/MyRA
   ```
4. Run setup script:
   ```bash
   setup.bat
   ```
5. Edit `.env` file with your API key
6. Validate installation:
   ```bash
   python validate_setup.py
   ```

### Method 2: Manual Setup (All Platforms)

#### Step 1: Navigate to project
```bash
cd c:/project/local/MyRA
```

#### Step 2: Create virtual environment
```bash
python -m venv venv
```

#### Step 3: Activate virtual environment

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

#### Step 4: Install dependencies
```bash
pip install -r requirements.txt
```

This will install:
- anthropic (Claude API client)
- openpyxl (Excel generation)
- langgraph (orchestration)
- langchain & langchain-anthropic (LLM framework)
- pydantic (data validation)
- python-dotenv (environment variables)

#### Step 5: Create .env file

Create a file named `.env` in the project root:
```
ANTHROPIC_API_KEY=sk-ant-api03-...your_actual_key_here...
```

**Important:**
- No quotes around the API key
- No spaces around `=`
- File must be named exactly `.env` (not `.env.txt`)

#### Step 6: Validate installation
```bash
python validate_setup.py
```

You should see all checks pass.

## Verification

Run the validation script to ensure everything is set up correctly:

```bash
python validate_setup.py
```

Expected output:
```
================================================================================
RA ORCHESTRATOR - Setup Validation
================================================================================

[Python Version]
✓ Python 3.11.x

[Project Structure]
✓ All 12 required files present

[Dependencies]
✓ anthropic
✓ openpyxl
✓ langgraph
✓ langchain
✓ langchain_anthropic
✓ dotenv
✓ pydantic

[Environment File]
✓ .env file exists
✓ ANTHROPIC_API_KEY present in .env

[Output Directory]
✓ outputs/ directory exists

================================================================================
✓ ALL CHECKS PASSED
================================================================================

You're ready to run the RA Orchestrator!

Run: python -m ra_orchestrator.main
```

## First Run

```bash
python -m ra_orchestrator.main
```

You'll be prompted to enter a research question. Try:
> "What are the key success factors for SaaS companies entering the European market?"

The system will:
1. Generate a research plan (~10-20 seconds)
2. Display the plan
3. Ask for approval (enter `1` to approve)
4. Generate a dry-run Excel file in `outputs/`

## Troubleshooting

### Issue: "Python not found"
**Solution:** Install Python 3.8+ from [python.org](https://www.python.org/downloads/)

### Issue: "Cannot activate venv"
**Solution (Windows PowerShell):**
1. Run PowerShell as Administrator
2. Execute: `Set-ExecutionPolicy RemoteSigned`
3. Try activating again

**Alternative:** Use Command Prompt instead of PowerShell

### Issue: "ANTHROPIC_API_KEY not found"
**Solution:**
1. Check `.env` file exists in project root
2. Verify format: `ANTHROPIC_API_KEY=sk-ant-api03-...`
3. No quotes, no spaces around `=`
4. Restart terminal after creating `.env`

### Issue: "Module not found" errors
**Solution:**
1. Ensure virtual environment is activated (see `(venv)` in prompt)
2. Run `pip install -r requirements.txt` again
3. Check Python version: `python --version` (must be 3.8+)

### Issue: Excel file won't open
**Solution:**
1. Check `outputs/` directory exists
2. Try opening with Excel or LibreOffice Calc
3. File should be named `research_output_dryrun_[timestamp].xlsx`

### Issue: API rate limits or errors
**Solution:**
1. Verify API key is valid at [console.anthropic.com](https://console.anthropic.com/)
2. Check you have credits available
3. Wait a moment and retry

## Getting Help

1. Check [README.md](README.md) for full documentation
2. Check [QUICKSTART.md](QUICKSTART.md) for quick reference
3. Review error messages carefully - they usually indicate the issue

## Next Steps

After successful installation:
1. Run the tool with a test question
2. Review the generated Excel output in `outputs/`
3. Experiment with different research questions
4. See [README.md](README.md) for Milestone 2/3 roadmap

## Updating Dependencies

To update to the latest versions:
```bash
pip install --upgrade -r requirements.txt
```

## Uninstallation

To remove the virtual environment:
```bash
deactivate  # Exit venv first
rmdir /s venv  # Windows
rm -rf venv  # Mac/Linux
```

The project files will remain for future use.
