# Architecture Overview

## System Architecture (Milestone 1)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (CLI)                               │
│                    [VS Code Terminal]                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Research Question
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      MAIN ENTRYPOINT                             │
│                    [ra_orchestrator/main.py]                     │
│  - Load .env (API key)                                           │
│  - Initialize RAOrchestrator                                     │
│  - Handle user input/output                                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Initialize State
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                     RA ORCHESTRATOR                              │
│                    [ra_orchestrator/graph.py]                    │
│                                                                   │
│  Workflow:                                                        │
│  1. Run Planner Agent                                            │
│  2. Display Plan                                                 │
│  3. Get User Approval                                            │
│  4. Run Schema Designer                                          │
│  5. Write Dry-Run Excel                                          │
│                                                                   │
│  State Management: RAState (TypedDict)                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ↓                   ↓                   ↓
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   PLANNER     │   │   APPROVAL    │   │    SCHEMA     │
│    AGENT      │   │     LOOP      │   │   DESIGNER    │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        │                   │                   │
        ↓                   ↓                   ↓
```

## Agent Details

### 1. Planner Agent
**File:** [ra_orchestrator/agents/planner.py](ra_orchestrator/agents/planner.py)

**Input:**
- Research Question (string)

**Process:**
1. Load prompt template from [prompts/planner.md](ra_orchestrator/prompts/planner.md)
2. Call Claude API with structured output request
3. Parse JSON response
4. Validate with Pydantic (ResearchPlan model)

**Output:**
- Research Title
- Sub-Questions (Q1, Q2, Q3...)
- Preliminary Framework
- Dynamic Schema Proposal
- Search Plan
- Stop Rules

**Model:** Claude Sonnet 4.5
**Temperature:** 0 (deterministic)
**Tokens:** ~2,000-4,000

---

### 2. Approval Loop
**File:** [ra_orchestrator/agents/approval.py](ra_orchestrator/agents/approval.py)

**Input:**
- Displayed Research Plan

**Process:**
1. Display plan to user (CLI)
2. Prompt for decision: Approve / Edit / Reject
3. Validate input
4. Return ApprovalDecision

**Output:**
- Decision: "approve" | "edit" | "reject"
- Optional feedback (for edit/reject)

**User Interaction:** CLI input
**Blocking:** Yes (waits for user)

---

### 3. Schema Designer
**File:** [ra_orchestrator/agents/schema_designer.py](ra_orchestrator/agents/schema_designer.py)

**Input:**
- Approved ResearchPlan

**Process:**
1. Extract dynamic columns from plan
2. Create LedgerSchema object
3. Combine meta + dynamic columns

**Output:**
- LedgerSchema with:
  - Meta columns (fixed 11 columns)
  - Dynamic columns (3-6 columns)

**No LLM call** - deterministic transformation

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        STATE OBJECT                              │
│                    [ra_orchestrator/state.py]                    │
│                                                                   │
│  RAState (TypedDict):                                            │
│    - research_question: str                                      │
│    - research_plan: ResearchPlan | None                          │
│    - approval_decision: ApprovalDecision | None                  │
│    - ledger_schema: LedgerSchema | None                          │
│    - ledger_rows: List[LedgerRow]                                │
│    - memo_block: MemoBlock | None                                │
│    - excel_path: str | None                                      │
│    - current_phase: str                                          │
│    - iteration_count: int                                        │
│                                                                   │
│  State transitions:                                              │
│    init → plan_created → plan_approved → schema_ready →          │
│    dry_run_complete                                              │
│                                                                   │
│  (M1 ends at dry_run_complete)                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Excel Output Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      EXCEL WRITER                                │
│               [ra_orchestrator/excel/writer.py]                  │
│                                                                   │
│  Input: RAState with plan + schema                               │
│                                                                   │
│  Process:                                                         │
│  1. Create Workbook (openpyxl)                                   │
│  2. Write Title Block                                            │
│     ├─ Apply title style (dark blue, white text)                │
│     └─ Merge cells across all columns                           │
│  3. Write Memo Block (placeholder)                               │
│     ├─ Apply memo style (gray background)                       │
│     ├─ Red/bold for conclusion                                  │
│     └─ Structure for 3 evidence bullets                         │
│  4. Write Question Decomposition                                 │
│     ├─ Color-code by Q-ID (yellow, green, etc.)                 │
│     ├─ Apply decomposition style                                │
│     └─ Show rationale for each                                  │
│  5. Write Ledger Header                                          │
│     ├─ Meta columns + dynamic columns                           │
│     ├─ Apply header row style (blue background)                 │
│     └─ Set column widths                                        │
│  6. Add placeholder row                                          │
│  7. Freeze panes (at ledger header)                              │
│  8. Save to outputs/ directory                                   │
│                                                                   │
│  Output: research_output_dryrun_[timestamp].xlsx                 │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Uses
         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      STYLES MODULE                               │
│               [ra_orchestrator/excel/styles.py]                  │
│                                                                   │
│  Functions:                                                       │
│  - apply_title_style()         → Dark blue + white + merge      │
│  - apply_memo_style()          → Gray background + wrap         │
│  - apply_conclusion_style()    → Red + bold                     │
│  - apply_decomposition_style() → Color by Q-ID                  │
│  - apply_header_row_style()    → Blue + white + borders         │
│  - apply_ledger_row_style()    → Color by Q-ID                  │
│  - set_column_widths()         → Optimize widths                │
│                                                                   │
│  Color Palette:                                                   │
│  - Title: 1F4E78 (dark blue)                                     │
│  - Memo: E7E6E6 (light gray)                                     │
│  - Conclusion: C00000 (red)                                      │
│  - Q1: FFF2CC (light yellow)                                     │
│  - Q2: E2EFDA (light green)                                      │
│  - Q3: FCE4D6 (light orange)                                     │
│  - Q4: DDEBF7 (light blue)                                       │
│  - Header: 4472C4 (blue)                                         │
└─────────────────────────────────────────────────────────────────┘
```

## Pydantic Models (Type System)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PYDANTIC MODELS                              │
│                  [ra_orchestrator/state.py]                      │
│                                                                   │
│  SubQuestion:                                                     │
│    - q_id: str (Q1, Q2, etc.)                                    │
│    - question: str                                               │
│    - rationale: str                                              │
│                                                                   │
│  DynamicColumn:                                                   │
│    - name: str                                                   │
│    - description: str                                            │
│    - example_values: List[str]                                   │
│                                                                   │
│  LedgerSchema:                                                    │
│    - dynamic_columns: List[DynamicColumn]                        │
│    - meta_columns: List[str] (property)                          │
│                                                                   │
│  ResearchPlan:                                                    │
│    - research_title: str                                         │
│    - sub_questions: List[SubQuestion]                            │
│    - preliminary_framework: str                                  │
│    - dynamic_schema_proposal: List[DynamicColumn]                │
│    - search_plan: str                                            │
│    - stop_rules: str                                             │
│                                                                   │
│  ApprovalDecision:                                                │
│    - decision: Literal["approve", "edit", "reject"]              │
│    - feedback: Optional[str]                                     │
│                                                                   │
│  LedgerRow: (For M2/M3)                                          │
│    - row_id: int                                                 │
│    - row_type: Literal["HEADER", "EVIDENCE", ...]                │
│    - question_id: str                                            │
│    - statement: str                                              │
│    - supports_row_ids: Optional[str]                             │
│    - source_url, source_name, date: Optional[str]                │
│    - dynamic_fields: Dict[str, Any]                              │
│                                                                   │
│  MemoBlock: (For M3)                                             │
│    - key_conclusion: str                                         │
│    - evidence_bullets: List[Dict[str, str]]                      │
│    - caveat: Optional[str]                                       │
│                                                                   │
│  RAState: (TypedDict)                                            │
│    - All of the above as Optional fields                         │
│    - current_phase: str                                          │
│    - iteration_count: int                                        │
└─────────────────────────────────────────────────────────────────┘
```

## File Organization

```
ra_orchestrator/
│
├── main.py              ← Entry point, user I/O
├── state.py             ← Pydantic models, type definitions
├── graph.py             ← Orchestrator workflow logic
│
├── agents/              ← Agent implementations
│   ├── planner.py       ← Research planning (LLM call)
│   ├── approval.py      ← User approval (CLI interaction)
│   ├── schema_designer.py ← Schema finalization (deterministic)
│   ├── researcher.py    ← [M2] Web research
│   ├── synthesizer.py   ← [M3] Synthesis
│   ├── memo_builder.py  ← [M3] Memo extraction
│   └── qa.py            ← [M3] Quality assurance
│
├── excel/               ← Excel output
│   ├── writer.py        ← Excel file generation
│   └── styles.py        ← Formatting utilities
│
└── prompts/             ← LLM system prompts
    ├── planner.md       ← Planner prompt
    ├── research.md      ← [M2] Research prompt
    ├── synthesis.md     ← [M3] Synthesis prompt
    └── memo.md          ← [M3] Memo extraction prompt
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                         STACK LAYERS                             │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    USER INTERFACE                          │ │
│  │               VS Code Integrated Terminal                  │ │
│  │                      (CLI / REPL)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  APPLICATION LAYER                         │ │
│  │        Python 3.8+  │  Python-dotenv  │  Pathlib          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                 ORCHESTRATION LAYER                        │ │
│  │          Custom Workflow (graph.py)                        │ │
│  │      [LangGraph for M2/M3 - prepared but not used]         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   AGENT LAYER                              │ │
│  │      Planner │ Approval │ Schema Designer                  │ │
│  │      [+ Researcher, Synthesizer, etc. in M2/M3]            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  DATA/TYPE LAYER                           │ │
│  │           Pydantic Models  │  TypedDict                    │ │
│  │      (ResearchPlan, LedgerSchema, RAState, etc.)           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   LLM/API LAYER                            │ │
│  │            Anthropic Python SDK                            │ │
│  │        (Claude Sonnet 4.5 via REST API)                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  OUTPUT LAYER                              │ │
│  │     OpenPyXL (Excel generation)                            │ │
│  │     [python-pptx for M3 PPT generation]                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  FILE SYSTEM                               │ │
│  │            outputs/ directory (Excel files)                │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Milestone Evolution

### Milestone 1 (Current)
```
User Question → Planner → Approval → Schema → Dry-Run Excel
```

### Milestone 2 (Planned)
```
User Question → Planner → Approval → Schema →
  Researcher (Wide Scan + Deep Dive) → Evidence Rows → Excel
```

### Milestone 3 (Planned)
```
User Question → Planner → Approval → Schema →
  Researcher → Evidence Rows →
  Synthesizer → Synthesis/Conclusion Rows →
  Memo Builder → Auto-Generated Memo →
  QA Validation → Full Excel → [Optional: PPT]
```

## Key Design Decisions

### 1. No LangGraph in M1
- Custom workflow is simpler for linear flow
- LangGraph prepared for M2/M3 when complexity increases
- Easier to debug and understand

### 2. Pydantic for Type Safety
- Runtime validation
- Clear schemas
- JSON serialization
- Better IDE support

### 3. Separate Styling Module
- Reusable formatting functions
- Consistent color palette
- Easy to maintain
- Extensible for M2/M3

### 4. CLI over Web UI
- Faster to build
- Better for VS Code integration
- Suitable for power users
- Can add web UI later

### 5. Dry-Run Excel in M1
- Validates output structure early
- User can review format before research
- Easier to iterate on design
- Clear milestone boundary

## Error Handling Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      ERROR HANDLING                              │
│                                                                   │
│  Layer 1: Input Validation                                       │
│    - Empty research question → Error + exit                      │
│    - Missing .env file → Error + instructions                    │
│    - Invalid API key → Error + instructions                      │
│                                                                   │
│  Layer 2: API Errors                                             │
│    - Rate limits → Caught + displayed                            │
│    - JSON parse errors → Caught + displayed                      │
│    - Network errors → Caught + displayed                         │
│                                                                   │
│  Layer 3: User Interaction                                       │
│    - Invalid approval choice → Re-prompt                         │
│    - Rejection → Graceful exit with message                      │
│                                                                   │
│  Layer 4: File I/O                                               │
│    - Missing outputs/ dir → Create automatically                 │
│    - Excel write errors → Caught + displayed                     │
│                                                                   │
│  Layer 5: Validation                                             │
│    - Pydantic validation → Caught + displayed                    │
│    - Setup validation → validate_setup.py script                 │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Considerations

### Token Usage (M1)
- Planner call: ~2,000-4,000 tokens
- Total per run: ~2,000-4,000 tokens
- Cost: ~$0.01-0.02 per research question

### Runtime (M1)
- Planner agent: 10-20 seconds
- Schema designer: < 1 second
- Excel writer: < 1 second
- Total: ~10-25 seconds per run

### Scalability (M2/M3)
- M2: ~60k tokens (~$0.20 per job)
- M3: ~105k tokens (~$0.35 per job)
- Caching can reduce repeat costs

## Security Considerations

- API key in .env (not committed)
- .gitignore properly configured
- No hardcoded credentials
- Input validation on user input
- Safe file path handling

---

**For more details:**
- See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for file organization
- See [MILESTONES.md](MILESTONES.md) for roadmap
- See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for what was built
