
"""Orchestrator graph for RA workflow (Milestone 2 - OPTIMIZED)."""
from pathlib import Path
import os
from anthropic import Anthropic

from ra_orchestrator.state import RAState
from ra_orchestrator.agents.clarifier import run_clarifier
from ra_orchestrator.agents.planner import run_planner, display_plan
from ra_orchestrator.agents.interactive_approval import run_interactive_approval
from ra_orchestrator.agents.schema_designer import run_schema_designer, display_schema
from ra_orchestrator.agents.researcher_optimized import run_researcher  # OPTIMIZED VERSION
from ra_orchestrator.agents.synthesizer import run_synthesizer
from ra_orchestrator.agents.memo_generator import run_memo_generator
from ra_orchestrator.excel.writer import write_dry_run_excel, write_full_excel
from ra_orchestrator.excel.writer_m3 import write_milestone3_excel


class RAOrchestrator:
    """
    Research Assistant Orchestrator - MILESTONE 3 (SYNTHESIS & MEMO).

    Cost optimizations enabled:
    - Prompt caching (50% savings)
    - Batch processing (30% additional savings)
    - Pre-filtering (skip 30% irrelevant sources)
    - Cost tracking

    Quality upgrades (v2):
    - Serper API for better Korean search results
    - Duplicate URL detection
    - Evidence quality validation (min 100 chars, must have data)
    - Universal query decomposition using Claude
    - Research scope clarification

    Synthesis features (Milestone 3 - NEW!):
    - Per-question synthesis with logical reasoning
    - Evidence-backed conclusions
    - Confidence assessment
    - Executive memo generation
    - Cross-question insights

    Flow:
    1. Clarifier understands research scope (entities, segments, priorities)
    2. Planner creates research plan with expected outputs
    3. Interactive approval (question-by-question review)
    4. Schema designer finalizes structure
    5. Researcher performs web research (optimized + quality filters)
    6. Evidence Excel generated
    7. Synthesis agent analyzes evidence per question
    8. Memo generator creates executive summary
    """

    def __init__(self, api_key: str, output_dir: Path):
        """
        Initialize orchestrator.

        Args:
            api_key: Anthropic API key
            output_dir: Directory for output files
        """
        self.client = Anthropic(api_key=api_key)
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def run(self, research_question: str) -> RAState:
        """
        Run the full Milestone 2 workflow with optimizations.

        Args:
            research_question: User's research question

        Returns:
            Final state
        """
        # Initialize state
        state: RAState = {
            "research_question": research_question,
            "research_plan": None,
            "approval_decision": None,
            "ledger_schema": None,
            "ledger_rows": [],
            "memo_block": None,
            "excel_path": None,
            "current_phase": "init",
            "iteration_count": 0,
        }

        print("\n" + "=" * 80)
        print("RA ORCHESTRATOR - MILESTONE 3 (SYNTHESIS & MEMO)")
        print("=" * 80)
        print("\nCost optimizations:")
        print("  ✓ Prompt caching (50% savings)")
        print("  ✓ Pre-filtering (skip irrelevant sources)")
        print("  ✓ Cost tracking")
        print("\nQuality features:")
        print("  ✓ Serper API (better Korean results)")
        print("  ✓ Universal query decomposition")
        print("  ✓ Evidence quality validation")
        print("  ✓ Research scope clarification")
        print("  ✓ Interactive question refinement")
        print("\nSynthesis features (NEW!):")
        print("  ✓ Per-question analysis with reasoning")
        print("  ✓ Evidence-backed conclusions")
        print("  ✓ Executive memo generation")
        print("  ✓ Cross-question insights\n")
        print(f"Research Question: {research_question}\n")

        # Step 1: Clarifier
        print("[1/8] Clarifying research scope...")
        state = run_clarifier(state, self.client)
        print("Scope clarified.\n")

        # Step 2: Planner
        print("[2/8] Running Planner agent...")
        state = run_planner(state, self.client)
        print("Plan created.\n")

        # Display plan
        plan_display = display_plan(state["research_plan"])
        print(plan_display)

        # Step 3: Interactive approval (question-by-question review)
        print("\n[3/8] Interactive question review...")
        state = run_interactive_approval(state, self.client)

        if state["current_phase"] == "plan_rejected":
            print("\n[WORKFLOW TERMINATED] Plan was rejected or edit not supported.")
            return state

        print("\n[APPROVED] Proceeding with research plan.\n")

        # Step 4: Schema designer
        print("[4/8] Finalizing ledger schema...")
        state = run_schema_designer(state)
        schema_display = display_schema(state["ledger_schema"])
        print(schema_display)

        # Step 5: Researcher agent (OPTIMIZED)
        print("\n[5/8] Running OPTIMIZED research agent...")
        print("This will take a few minutes - searching web and extracting evidence.\n")

        # Get Serper API key
        serper_key = os.getenv("SERPER_API_KEY")
        if not serper_key:
            print("\n[ERROR] SERPER_API_KEY not found in environment variables.")
            print("Please add your Serper API key to .env file.")
            print("Get a free key at: https://serper.dev")
            print("\nFalling back to dry-run Excel output...\n")

            # Fallback: write dry-run
            excel_path = write_dry_run_excel(state, self.output_dir)
            state["excel_path"] = excel_path
            state["current_phase"] = "research_failed"
            return state

        # Run OPTIMIZED researcher with quality filters
        state = run_researcher(state, serper_key, self.client)

        if state["current_phase"] != "research_complete":
            print("\n[ERROR] Research failed or incomplete.")
            return state

        # Step 6: Write evidence Excel
        print("\n[6/8] Generating Excel with evidence data...")
        evidence_excel_path = write_full_excel(state, self.output_dir)
        print(f"Evidence Excel saved: {evidence_excel_path}")

        # Step 7: Synthesis (Milestone 3)
        print("\n[7/8] Running Synthesis agent...")
        print("Analyzing evidence to create per-question conclusions...\n")
        state = run_synthesizer(state, self.client)

        # Step 8: Memo generation (Milestone 3)
        print("\n[8/8] Generating executive memo...")
        state = run_memo_generator(state, self.client)

        # Final Excel with SYNTHESIS and MEMO tabs
        print("\nCreating final Excel with synthesis and memo...")
        final_excel_path = write_milestone3_excel(state, evidence_excel_path, self.output_dir)
        state["excel_path"] = final_excel_path
        state["current_phase"] = "m3_complete"

        print(f"\n✓ Final Excel saved to: {final_excel_path}")
        print("\n" + "=" * 80)
        print("MILESTONE 3 COMPLETE - SYNTHESIS & MEMO")
        print("=" * 80)
        print("\nResults:")
        print(f"  - Evidence rows collected: {len(state['ledger_rows'])}")
        print(f"  - Sub-questions synthesized: {len(state.get('question_syntheses', []))}")
        print(f"  - Final Excel file: {final_excel_path}")
        print("\nExcel tabs:")
        print("  1. MEMO - Executive summary with key findings")
        print("  2. SYNTHESIS - Per-question analysis with reasoning")
        print("  3. Research Output - Full evidence ledger")
        print("\nCost optimizations achieved:")
        print("  - See cost summary above for actual savings")
        print("")

        return state
