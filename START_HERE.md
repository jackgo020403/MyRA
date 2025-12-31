# START HERE - RA Orchestrator

Welcome to the **RA Orchestrator** - your multi-agent consulting-grade research assistant!

## What Is This?

A CLI tool that:
- Takes a research question
- Creates a structured research plan
- **Requires your approval** before proceeding
- Outputs a professionally formatted Excel file
- Uses dynamic schemas adapted to each question
- Will eventually provide auto-generated memos and full research

## Current Status: Milestone 1 Complete ✅

You have a fully working system that:
1. Plans research with question decomposition
2. Proposes dynamic ledger schemas
3. Waits for your approval (mandatory checkpoint)
4. Generates a dry-run Excel with structure

## Quick Start (5 minutes)

### 1. Install
```bash
cd c:/project/local/MyRA
setup.bat
```

### 2. Add API Key
Edit `.env` file:
```
ANTHROPIC_API_KEY=your_actual_key_here
```

### 3. Validate
```bash
python validate_setup.py
```

### 4. Run
```bash
python -m ra_orchestrator.main
```

### 5. Test Question
Try: "What are the key success factors for SaaS companies entering the European market?"

## What You'll Get

An Excel file (`outputs/research_output_dryrun_*.xlsx`) with:

### A) Title Block
- Your research question in a formatted header

### B) Executive Memo (Placeholder)
- Structure ready for auto-generation in Milestone 3
- Key Conclusion (max 10 lines)
- 3 Evidence bullets
- Optional caveat

### C) Question Decomposition
- Sub-questions (Q1, Q2, Q3...)
- Color-coded by question
- Rationale for each

### D) Research Ledger
- **Meta columns** (always present):
  - Row_ID, Row_Type, Question_ID, Section, Statement
  - Supports_Row_IDs, Source_URL, Source_Name, Date
  - Confidence, Notes
- **Dynamic columns** (question-specific):
  - Adapted to your research question
  - Examples: Trend, Player, Outcome, Mechanism, etc.

## Key Documents

| Document | Purpose |
|----------|---------|
| **[START_HERE.md](START_HERE.md)** | This file - your entry point |
| **[QUICKSTART.md](QUICKSTART.md)** | 5-minute setup guide |
| **[INSTALLATION.md](INSTALLATION.md)** | Detailed installation steps |
| **[README.md](README.md)** | Full documentation |
| **[MILESTONES.md](MILESTONES.md)** | Roadmap for M1/M2/M3 |
| **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** | File organization |

## What's Coming Next?

### Milestone 2: Research & Evidence
- Actual web research (wide scan + deep dive)
- Evidence collection (~200 rows)
- Source attribution
- Populated ledger

### Milestone 3: Synthesis & Memo
- Auto-generated Executive Memo
- Synthesis across evidence
- Conclusions per sub-question
- QA validation
- Optional PPT generation

## The Approval Loop (Core Feature)

**Before any research happens, you approve the plan:**

```
[System generates plan]
  ↓
[Displays: Title, Sub-questions, Schema, Search plan]
  ↓
[You decide: Approve / Edit / Reject]
  ↓
[Only proceeds if approved]
```

This ensures:
- You control the research direction
- No wasted API costs on wrong approaches
- Alignment before execution
- Transparency in methodology

## Key Design Principles

1. **User Alignment First**: Mandatory approval checkpoint
2. **Dynamic Frameworks**: Schema adapts to question (not hard-coded)
3. **Cost Awareness**: Shallow wide scans, selective deep dives
4. **Traceability**: All claims reference evidence Row_IDs
5. **Excel Default**: One professional deliverable, no separate memos
6. **Consulting Quality**: ~200 row ledgers with narrative conclusions

## Example Research Questions

Try these to see how the schema adapts:

**Market Entry:**
> "What are the key success factors for SaaS companies entering the European market?"

Expected schema: Factor, Evidence_Type, Geography, Company_Example, Outcome

**Decision Analysis:**
> "What strategies have proven most effective for reducing customer churn in B2B SaaS?"

Expected schema: Strategy, Outcome, Company, Metric, Context, Transferability

**Trend Analysis:**
> "What are the emerging trends in AI-powered customer service?"

Expected schema: Trend, Momentum, Player, Use_Case, Evidence_Quality

**Benchmarking:**
> "How do leading tech companies structure their remote work policies?"

Expected schema: Company, Policy_Type, Details, Year, Industry, Scale

## File Locations

```
MyRA/
├── START_HERE.md              ← You are here
├── QUICKSTART.md              ← Next, read this
├── setup.bat                  ← Run this to install
├── validate_setup.py          ← Run this to verify
├── .env                       ← Create this with API key
├── ra_orchestrator/
│   └── main.py                ← Entry point
└── outputs/                   ← Your Excel files appear here
```

## Getting Help

**Installation Issues?**
- See [INSTALLATION.md](INSTALLATION.md)
- Run `python validate_setup.py`

**Want to understand the code?**
- See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- See [README.md](README.md)

**Want to know what's next?**
- See [MILESTONES.md](MILESTONES.md)

## Next Steps

1. **Install** (5 min): Run `setup.bat` and add API key
2. **Validate** (1 min): Run `python validate_setup.py`
3. **Test** (2 min): Run with a sample question
4. **Review** (5 min): Open the Excel output and explore
5. **Experiment**: Try different research questions
6. **Provide Feedback**: What schema columns make sense?

## Questions?

- Check [README.md](README.md) for comprehensive docs
- Review [MILESTONES.md](MILESTONES.md) for roadmap
- All code is documented and readable

---

**Ready to start?**

```bash
setup.bat
```

Then open [QUICKSTART.md](QUICKSTART.md) for the next steps.

---

**Built with:**
- Claude Sonnet 4.5 (Anthropic API)
- Python 3.8+
- OpenPyXL for Excel generation
- LangGraph for orchestration (M2/M3)

**License:** Your project, your rules.

**Version:** Milestone 1 Complete ✅
