# Milestone 2 Implementation Guide

## What I've Created

✅ **Completed Files:**
1. `ra_orchestrator/agents/researcher.py` - Full researcher agent with cost optimization notes
2. `ra_orchestrator/prompts/research.md` - Evidence extraction prompt
3. `requirements.txt` - Updated with tavily-python, beautifulsoup4, requests
4. `.env.example` - Added TAVILY_API_KEY placeholder
5. `COST_OPTIMIZATION_WITH_CLAUDE_SKILLS.md` - Comprehensive cost savings guide

## What Needs Manual Updates

Due to file modification conflicts, you need to manually update these files:

### 1. Update `ra_orchestrator/excel/writer.py`

Replace the `write_full_excel` function (line 153-166) with this version:

[See file: /tmp/write_full_excel_new.py created earlier or the version in this guide below]

The key changes:
- Writes actual ledger rows from `state["ledger_rows"]`
- Populates all meta columns + dynamic columns
- Applies color-coding by Question_ID
- Still shows memo placeholder (M3 will fill this)

### 2. Update `ra_orchestrator/graph.py`

Add researcher agent to the workflow. Insert after schema designer:

```python
from ra_orchestrator.agents.researcher import run_researcher
import os

class RAOrchestrator:
    def run(self, research_question: str) -> RAState:
        # ... existing code ...

        # After schema designer:
        print("[3/5] Finalizing ledger schema...")
        state = run_schema_designer(state)

        # NEW: Add researcher
        print("\n[4/5] Running research agent (this will take a few minutes)...")
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            print("ERROR: TAVILY_API_KEY not found in .env")
            print("Get a free key at: https://tavily.com")
            return state

        state = run_researcher(state, tavily_key, self.client)

        # Update Excel writer call
        print("\n[5/5] Generating Excel output with research data...")
        from ra_orchestrator.excel.writer import write_full_excel  # Import new function
        excel_path = write_full_excel(state, self.output_dir)  # Use new function
        state["excel_path"] = excel_path
        state["current_phase"] = "research_complete"
```

### 3. Install New Dependencies

```bash
pip install tavily-python beautifulsoup4 requests
```

### 4. Get Tavily API Key

1. Go to: https://tavily.com
2. Sign up (free tier: 1000 searches/month)
3. Copy your API key
4. Add to `.env`:
   ```
   TAVILY_API_KEY=tvly-...your_key_here...
   ```

## Quick Implementation Steps

1. **Install dependencies:**
   ```bash
   pip install tavily-python beautifulsoup4 requests
   ```

2. **Get Tavily key:**
   - Visit https://tavily.com
   - Sign up and get API key
   - Add to `.env`

3. **Update writer.py:**
   - Replace `write_full_excel` function with new version
   - (I'll provide complete file if needed)

4. **Update graph.py:**
   - Import researcher
   - Add researcher step after schema designer
   - Change `write_dry_run_excel` to `write_full_excel`

5. **Test:**
   ```bash
   python -m ra_orchestrator.main
   ```

## What Will Happen

When you run M2:
1. Planner creates plan → You approve
2. Schema designer finalizes schema
3. **NEW: Researcher agent:**
   - Wide scan: Searches web for ~50 sources using Tavily
   - Ranking: Selects top 20 sources
   - Deep dive: Extracts evidence from each source using Claude
   - Creates ~150-200 evidence rows
4. Excel writer: Creates file with REAL DATA

## Expected Output

Excel file with:
- Title block
- Memo placeholder (M3 will fill)
- Question decomposition (color-coded)
- **FULL LEDGER with ~150-200 evidence rows:**
  - Row_ID, Row_Type (EVIDENCE), Question_ID
  - Statement (paraphrased evidence)
  - Source_URL, Source_Name, Date
  - Dynamic fields populated
  - Color-coded by Question_ID

## Cost Estimate (M2)

Per research job:
- Tavily API: ~$0.01-0.02 (20 searches)
- Claude API: ~$0.50-0.70 (20 sources × ~5k tokens each)
- **Total: ~$0.51-0.72 per research question**

With prompt caching (see COST_OPTIMIZATION guide):
- **Reduced to: ~$0.25-0.35 per job**

## Troubleshooting

**"TAVILY_API_KEY not found"**
- Check `.env` file exists
- Verify key format: `TAVILY_API_KEY=tvly-...`
- Restart terminal after adding

**"No sources found"**
- Check Tavily API key is valid
- Try simpler research question
- Check internet connection

**"Error fetching URL"**
- Some sites block scrapers (normal)
- System will skip and continue
- Should still get 150+ evidence rows from other sources

**Excel file empty**
- Check if researcher ran successfully
- Look for "Collected N evidence rows" message
- Check state["ledger_rows"] is populated

## Files You Need to Manually Edit

1. **ra_orchestrator/excel/writer.py**
   - Function: `write_full_excel` (lines 153-166)
   - Action: Replace with new implementation

2. **ra_orchestrator/graph.py**
   - Location: After `run_schema_designer` call
   - Action: Add researcher step, change excel writer call

Would you like me to create the complete updated versions of these files for you to copy?
