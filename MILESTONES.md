# Milestone Roadmap

## Overview

The RA Orchestrator is being built in three milestones, each adding critical functionality while maintaining a working system at each stage.

---

## Milestone 1: Planning & Structure ✅ COMPLETE

**Goal:** Establish the foundation with planning, approval loop, and dry-run output.

### Implemented

#### Core System
- ✅ CLI entrypoint with user interaction
- ✅ State management with Pydantic models
- ✅ Orchestrator workflow (graph.py)
- ✅ Environment setup (.env, requirements.txt)

#### Agents
- ✅ **Planner Agent**: Creates research plan from question
  - Question decomposition (Q1, Q2, Q3...)
  - Dynamic schema proposal (adaptive to question)
  - Search strategy
  - Stop rules (~200 rows target)
- ✅ **Approval Loop**: User review and approval
  - Approve/Edit/Reject options
  - Mandatory checkpoint before research
- ✅ **Schema Designer**: Finalizes ledger schema
  - Meta columns (always present)
  - Dynamic columns (question-specific)

#### Excel Output
- ✅ **Dry-Run Excel Writer**:
  - Title block with research question
  - Executive Memo placeholder (structure ready)
  - Question Decomposition (color-coded by Q-ID)
  - Empty ledger with proper schema headers
  - Frozen panes for scrolling
  - Professional formatting and styling

#### Documentation
- ✅ README.md (full documentation)
- ✅ QUICKSTART.md (5-minute guide)
- ✅ INSTALLATION.md (detailed setup)
- ✅ PROJECT_STRUCTURE.md (file organization)
- ✅ validate_setup.py (installation validator)
- ✅ setup.bat (automated installer)

### Demo Flow (M1)

```
User: What are the key success factors for SaaS entering Europe?
  ↓
Planner: Creates plan with Q1, Q2, Q3, dynamic schema
  ↓
System: Displays plan
  ↓
User: Approves (1)
  ↓
Schema Designer: Finalizes schema
  ↓
Excel Writer: Generates dry-run file
  ↓
Output: research_output_dryrun_[timestamp].xlsx
```

### What You Can Do Now

1. Enter any research question
2. Review auto-generated plan
3. Approve to generate structured Excel
4. See proper formatting, decomposition, schema
5. Understand the full output structure

---

## Milestone 2: Research & Evidence Collection

**Goal:** Add web research capabilities to populate the ledger with actual evidence.

### To Implement

#### Agents
- 🔲 **Researcher Agent**:
  - **Wide Scan Phase**:
    - Search web for candidate sources
    - Extract metadata only (title, publisher, date, URL, snippet)
    - Score/rank sources
    - Cost-aware: shallow scan, many sources
  - **Deep Dive Phase**:
    - Select top N sources for deep analysis
    - Extract full content
    - Create EVIDENCE rows
    - Link to sub-questions (Q-ID)
  - **Stop Rules**:
    - Target ~200 total ledger rows
    - Diminishing returns detection
    - Token budget management

#### Ledger Population
- 🔲 **Evidence Rows**:
  - Row_Type: EVIDENCE
  - Must include: Source_URL, Source_Name, Date
  - Statement: Paraphrased evidence (not copy-paste)
  - Question_ID: Link to sub-question
  - Dynamic fields populated
  - Confidence scores

#### Excel Output Update
- 🔲 **Full Ledger Writer**:
  - Write actual EVIDENCE rows
  - Color-code by Question_ID
  - Apply row-level formatting
  - Populate dynamic columns

#### Prompts
- 🔲 research.md: System prompt for researcher agent

### Demo Flow (M2)

```
User: [Same as M1]
  ↓
[M1 flow: Plan → Approve → Schema]
  ↓
Researcher (Wide Scan):
  - Search web for 50-100 sources
  - Extract metadata
  - Score relevance
  ↓
Researcher (Deep Dive):
  - Select top 20 sources
  - Extract evidence
  - Create ~150-200 ledger rows (type: EVIDENCE)
  ↓
Excel Writer: Generates file with actual data
  ↓
Output: research_output_[timestamp].xlsx
```

### What You'll Be Able to Do

1. Get real web research results
2. See actual evidence in ledger
3. Have source attribution for everything
4. Review ~200 rows of structured evidence

---

## Milestone 3: Synthesis & Auto-Memo

**Goal:** Add synthesis, auto-generated memo, QA, and optional PPT.

### To Implement

#### Agents
- 🔲 **Synthesizer Agent**:
  - **SYNTHESIS Rows**:
    - Connect multiple EVIDENCE rows
    - Pattern recognition across sources
    - Must reference Supports_Row_IDs
  - **CONCLUSION Rows** (per sub-question):
    - Answer each Q1, Q2, Q3...
    - Reference supporting SYNTHESIS/EVIDENCE
    - Narrative prose, not just bullets
  - **Top-Level CONCLUSION**:
    - Final answer to main question
    - Feeds into Memo

- 🔲 **Memo Builder**:
  - **Extract from Ledger** (not generate separately):
    - Key Conclusion: Top-level CONCLUSION row
    - 3 Evidence Bullets: Best EVIDENCE rows
    - Caveat: Add if needed
  - **Enforce Constraints**:
    - Conclusion max 10 lines
    - Exactly 3 evidence bullets
    - Include Row_IDs

- 🔲 **QA Agent**:
  - Validate memo length (≤10 lines)
  - Validate exactly 3 evidence bullets
  - Check all EVIDENCE rows have sources
  - Check all SYNTHESIS/CONCLUSION reference Supports_Row_IDs
  - Verify no unsupported factual claims
  - Report violations for fix

- 🔲 **PPT Generator** (optional):
  - Only runs if user requests "Generate PPT"
  - Slide 1: Memo block (forced)
  - Additional slides from ledger highlights
  - Not default deliverable

#### Excel Output Update
- 🔲 **Full Excel with Memo**:
  - Replace memo placeholder with real content
  - Proper styling (red/bold conclusion)
  - Evidence bullets with Row_ID references
  - Complete ledger with all row types

#### Prompts
- 🔲 synthesis.md: Synthesis agent prompt
- 🔲 memo.md: Memo extraction prompt

### Demo Flow (M3)

```
User: [Same as M1/M2]
  ↓
[M1: Plan → Approve → Schema]
  ↓
[M2: Research → Evidence Collection]
  ↓
Synthesizer:
  - Analyze EVIDENCE rows
  - Create SYNTHESIS rows (reference Supports_Row_IDs)
  - Create CONCLUSION rows per sub-question
  - Create top-level CONCLUSION
  ↓
Memo Builder:
  - Extract top CONCLUSION → Key Conclusion
  - Select 3 best EVIDENCE → Evidence bullets
  - Add caveat if needed
  ↓
QA Agent:
  - Validate all constraints
  - Check traceability
  - Report issues
  ↓
Excel Writer: Complete file with real memo
  ↓
Output: research_output_[timestamp].xlsx (FINAL)

[Optional: User requests "Generate PPT"]
  ↓
PPT Generator: Creates slides with Memo as Slide 1
  ↓
Output: research_output_[timestamp].pptx
```

### What You'll Be Able to Do

1. Get fully automated research deliverables
2. See auto-generated Executive Memo
3. Have synthesis and conclusions, not just evidence
4. Trust traceability (everything references Row_IDs)
5. Optionally generate PPT when needed

---

## Feature Comparison

| Feature | M1 | M2 | M3 |
|---------|----|----|-----|
| Research planning | ✅ | ✅ | ✅ |
| Question decomposition | ✅ | ✅ | ✅ |
| Dynamic schema | ✅ | ✅ | ✅ |
| Approval loop | ✅ | ✅ | ✅ |
| Web research | ❌ | ✅ | ✅ |
| Evidence collection | ❌ | ✅ | ✅ |
| Source attribution | ❌ | ✅ | ✅ |
| Synthesis rows | ❌ | ❌ | ✅ |
| Conclusion rows | ❌ | ❌ | ✅ |
| Auto-generated memo | ❌ | ❌ | ✅ |
| QA validation | ❌ | ❌ | ✅ |
| Excel output | Dry-run | With data | Complete |
| PPT generation | ❌ | ❌ | ✅ (opt) |

---

## Cost & Token Awareness

### M1 (Current)
- Low cost: Only planning LLM call
- ~1,000-2,000 tokens per run

### M2 (Planned)
- Moderate cost: Wide scan (shallow) + deep dive (selective)
- Wide scan: Metadata only, ~100 sources, ~10k tokens
- Deep dive: Full content, ~20 sources, ~50k tokens
- Total: ~60k tokens per research job

### M3 (Planned)
- Higher cost: Synthesis + memo extraction
- Synthesis: Analyze ledger, create connections, ~30k tokens
- Memo: Extract best content, ~5k tokens
- QA: Validate constraints, ~10k tokens
- Total: ~105k tokens per full job

**Optimization strategies:**
- Caching for repeated searches
- Incremental processing
- Smart source selection
- Avoid passing full raw text between agents

---

## Timeline (Suggested)

- **M1**: ✅ Complete (current state)
- **M2**: 1-2 weeks (research agent + web integration)
- **M3**: 1-2 weeks (synthesis + memo + QA)

**Total**: Consulting-grade RA in 2-4 weeks

---

## Current Status: Ready to Use M1

You can now:
1. Test the planning and approval workflow
2. Review output structure and formatting
3. Validate the approach with stakeholders
4. Prepare research questions for M2
5. Provide feedback on schema and decomposition

The foundation is solid. M2 and M3 will build incrementally on this base.
