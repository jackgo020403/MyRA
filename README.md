# RA Orchestrator - Multi-Agent Research Assistant

A consulting-grade research assistant that produces structured Excel deliverables with mandatory user approval checkpoints.

## Overview

The RA Orchestrator is a multi-agent system that:
- Creates research plans with question decomposition
- Requires user approval before proceeding
- Generates structured Excel outputs with Executive Memo, Question Decomposition, and Research Ledger
- Supports dynamic schema generation adapted to each research question
- Cost-aware: wide scans are shallow, deep dives selective

## Current Status: Milestone 1

**Implemented:**
- Planner agent with structured output
- Mandatory approval loop (Approve/Edit/Reject)
- Schema designer for dynamic ledger columns
- Dry-run Excel writer with formatting
  - Title block
  - Executive Memo placeholder
  - Question Decomposition with color coding
  - Empty ledger with proper schema

**Coming in Milestone 2:**
- Researcher agent (wide scan + deep dive)
- Actual evidence collection
- Source tracking and metadata

**Coming in Milestone 3:**
- Synthesizer agent
- Memo builder (auto-extraction from ledger)
- QA agent for constraint enforcement
- Full Excel formatting and styling
- Optional PPT generator

## Installation

### 1. Create virtual environment

```bash
cd c:/project/local/MyRA
python -m venv venv
```

### 2. Activate virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up API key

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

### Run Milestone 1

```bash
python -m ra_orchestrator.main
```

The CLI will:
1. Prompt you for a research question
2. Generate a research plan
3. Display the plan and ask for approval
4. Generate a dry-run Excel file in `outputs/`

### Example Session

```
Enter your research question: What are the key success factors for SaaS companies entering the European market?

[The system will create a plan with:]
- Refined research title
- 3-5 sub-questions
- Dynamic schema columns (e.g., Factor, Evidence_Type, Geography, Company_Example)
- Search strategy

[You review and approve]

[System generates dry-run Excel with structure]
```

## Project Structure

```
MyRA/
├── ra_orchestrator/
│   ├── main.py                 # CLI entrypoint
│   ├── state.py                # State management & Pydantic models
│   ├── graph.py                # Orchestrator workflow
│   ├── agents/
│   │   ├── planner.py          # Research planning
│   │   ├── schema_designer.py  # Schema finalization
│   │   ├── approval.py         # User approval loop
│   │   ├── researcher.py       # [Milestone 2]
│   │   ├── synthesizer.py      # [Milestone 3]
│   │   ├── memo_builder.py     # [Milestone 3]
│   │   └── qa.py               # [Milestone 3]
│   ├── excel/
│   │   ├── writer.py           # Excel generation
│   │   └── styles.py           # Formatting utilities
│   └── prompts/
│       └── planner.md          # Planner system prompt
├── outputs/                    # Generated Excel files
├── requirements.txt
├── .env                        # API keys (create this)
└── README.md
```

## Output Specification

The Excel file includes:

### A) Title Block
- Merged cell with research question
- Dark blue background, white text

### B) Executive Memo (Placeholder in M1)
- Key Conclusion (max 10 lines, red/bold)
- Key Supporting Evidence (exactly 3 bullets with source + Row ID)
- Optional Caveat/Confidence

### C) Question Decomposition
- Sub-questions (Q1, Q2, Q3...)
- Color-coded by question
- Rationale for each

### D) Research Ledger
- Meta columns: Row_ID, Row_Type, Question_ID, Section, Statement, Supports_Row_IDs, Source_URL, Source_Name, Date, Confidence, Notes
- Dynamic columns: Adapted to research question
- Row types: HEADER, EVIDENCE, SYNTHESIS, CONCLUSION
- Color-coded by question
- Frozen panes for scrolling

## Design Principles

1. **User Alignment First**: Mandatory approval before research
2. **Dynamic Frameworks**: Schema adapts to question, not hard-coded
3. **Cost Awareness**: Shallow scans, selective deep dives
4. **Traceability**: All synthesis/conclusions reference evidence Row_IDs
5. **Consulting Quality**: Professional formatting, clear narrative

## Next Steps

After running Milestone 1:
1. Review the dry-run Excel structure
2. Provide feedback on schema and decomposition
3. Milestone 2 will add actual web research
4. Milestone 3 will add synthesis and auto-generated memo

## Troubleshooting

**Error: ANTHROPIC_API_KEY not found**
- Ensure `.env` file exists in project root
- Check that the API key is valid

**Import errors**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

**Excel file not opening**
- Check `outputs/` directory
- Ensure openpyxl is installed
