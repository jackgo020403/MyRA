# Project Structure

```
MyRA/
│
├── README.md                           # Full documentation
├── QUICKSTART.md                       # 5-minute setup guide
├── PROJECT_STRUCTURE.md               # This file
├── requirements.txt                    # Python dependencies
├── .env.example                        # API key template
├── .env                               # Your API key (create this, not in git)
├── .gitignore                         # Git ignore rules
│
├── ra_orchestrator/                   # Main package
│   ├── __init__.py
│   ├── main.py                        # CLI entrypoint
│   ├── state.py                       # State models (Pydantic)
│   ├── graph.py                       # Orchestrator workflow
│   │
│   ├── agents/                        # Agent implementations
│   │   ├── __init__.py
│   │   ├── planner.py                 # [M1] Research planning
│   │   ├── approval.py                # [M1] User approval loop
│   │   ├── schema_designer.py         # [M1] Schema finalization
│   │   ├── researcher.py              # [M2] Web research
│   │   ├── synthesizer.py             # [M3] Synthesis & conclusions
│   │   ├── memo_builder.py            # [M3] Memo extraction
│   │   └── qa.py                      # [M3] Quality assurance
│   │
│   ├── excel/                         # Excel output
│   │   ├── __init__.py
│   │   ├── writer.py                  # [M1] Excel generation
│   │   └── styles.py                  # [M1] Formatting utilities
│   │
│   └── prompts/                       # LLM prompts
│       ├── planner.md                 # [M1] Planner system prompt
│       ├── schema.md                  # [M2] Schema design prompt
│       ├── research.md                # [M2] Research prompt
│       ├── synthesis.md               # [M3] Synthesis prompt
│       └── memo.md                    # [M3] Memo extraction prompt
│
├── outputs/                           # Generated files (not in git)
│   └── research_output_dryrun_*.xlsx
│
└── venv/                              # Virtual environment (not in git)
```

## Key Files - Milestone 1

### Core System
- **[main.py](ra_orchestrator/main.py)**: CLI entrypoint, user interaction
- **[state.py](ra_orchestrator/state.py)**: Type definitions and state management
- **[graph.py](ra_orchestrator/graph.py)**: Orchestrator workflow logic

### Agents (M1)
- **[planner.py](ra_orchestrator/agents/planner.py)**: Creates research plan from question
- **[approval.py](ra_orchestrator/agents/approval.py)**: Handles user approval/rejection
- **[schema_designer.py](ra_orchestrator/agents/schema_designer.py)**: Finalizes ledger schema

### Excel Output
- **[writer.py](ra_orchestrator/excel/writer.py)**: Excel file generation
- **[styles.py](ra_orchestrator/excel/styles.py)**: Formatting and color schemes

### Prompts
- **[planner.md](ra_orchestrator/prompts/planner.md)**: System prompt for planning agent

## File Counts

- **Total Python files**: 10 (7 implemented for M1, 3 placeholders for M2/M3)
- **Total prompt files**: 1 (4 more planned for M2/M3)
- **Documentation files**: 4 (README, QUICKSTART, this file, .env.example)

## Code Statistics (M1)

- **State management**: ~130 lines (Pydantic models)
- **Planner agent**: ~120 lines (prompt + logic + display)
- **Schema designer**: ~50 lines
- **Approval loop**: ~50 lines
- **Excel writer**: ~150 lines (dry-run)
- **Excel styles**: ~100 lines (formatting utilities)
- **Orchestrator**: ~90 lines (workflow)
- **Main CLI**: ~50 lines
- **Total**: ~740 lines of production code

## Dependencies

See [requirements.txt](requirements.txt):
- `anthropic` - Claude API client
- `openpyxl` - Excel file generation
- `langgraph` - Graph orchestration (prepared for M2/M3)
- `langchain-anthropic` - LangChain integration (prepared for M2/M3)
- `pydantic` - Data validation
- `python-dotenv` - Environment variable management
