# Quick Start Guide - Milestone 1

## Setup (5 minutes)

### 1. Open Terminal in VS Code
- Press `` Ctrl+` `` or go to Terminal > New Terminal

### 2. Navigate to project
```bash
cd c:/project/local/MyRA
```

### 3. Create virtual environment
```bash
python -m venv venv
```

### 4. Activate virtual environment
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 5. Install dependencies
```bash
pip install -r requirements.txt
```

### 6. Set up API key
Create a file named `.env` in the project root with:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

## Run the Tool

```bash
python -m ra_orchestrator.main
```

## What to Expect

The tool will:
1. Ask for your research question
2. Generate a research plan (takes ~10-20 seconds)
3. Display the plan with:
   - Research title
   - Sub-questions (Q1, Q2, Q3...)
   - Dynamic schema columns
   - Search strategy
4. Ask for your approval: `1` for Approve, `2` for Edit (not implemented), `3` for Reject
5. Generate a dry-run Excel file in `outputs/`

## Example Research Questions

- "What are the key success factors for SaaS companies entering the European market?"
- "How do leading tech companies approach remote work policies?"
- "What strategies have been most effective for reducing customer churn in B2B SaaS?"
- "What are the emerging trends in AI-powered customer service?"

## Output

Check the `outputs/` folder for your Excel file:
- `research_output_dryrun_[timestamp].xlsx`

Open it to see:
- Title block
- Executive Memo placeholder (will be auto-generated in M3)
- Question Decomposition (color-coded)
- Empty ledger with proper schema

## Next Steps

After reviewing the dry-run output:
- Milestone 2: Add actual web research and evidence collection
- Milestone 3: Add synthesis, auto-generated memo, and full formatting

## Troubleshooting

**Can't activate venv?**
- Try: `.\venv\Scripts\activate` or `.\venv\Scripts\Activate.ps1`

**Module not found?**
- Ensure venv is activated (you see `(venv)` in prompt)
- Run `pip install -r requirements.txt` again

**API key error?**
- Double-check `.env` file exists in project root
- No quotes around API key value
- No spaces around `=`

**Need help?**
- Check [README.md](README.md) for full documentation
