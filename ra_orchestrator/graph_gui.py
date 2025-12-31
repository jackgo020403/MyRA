"""
GUI-compatible orchestrator - skips interactive prompts.
"""
from pathlib import Path
import os
from anthropic import Anthropic

from ra_orchestrator.state import RAState
from ra_orchestrator.agents.planner import run_planner
from ra_orchestrator.agents.schema_designer import run_schema_designer
from ra_orchestrator.agents.researcher_optimized import run_researcher
from ra_orchestrator.agents.synthesizer import run_synthesizer
from ra_orchestrator.agents.memo_generator import run_memo_generator
from ra_orchestrator.excel.writer import write_full_excel
from ra_orchestrator.excel.writer_m3 import write_milestone3_excel


class RAOrchestratorGUI:
    """
    GUI-compatible Research Assistant Orchestrator.

    Skips interactive approval steps - auto-approves everything.
    """

    def __init__(self, api_key: str, output_dir: Path):
        self.client = Anthropic(api_key=api_key)
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def run(self, research_question: str) -> RAState:
        """
        Run research workflow without interactive prompts.

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

        # Skip clarifier - use research question as-is
        state['research_context'] = research_question
        state['scope_clarified'] = True

        # Step 1: Planner (auto-generate plan)
        state = run_planner(state, self.client)

        # Step 2: Auto-approve (skip interactive approval)
        state["approval_decision"] = "approved"
        state["current_phase"] = "plan_approved"

        # Step 3: Schema designer
        state = run_schema_designer(state)

        # Step 4: Researcher
        serper_key = os.getenv("SERPER_API_KEY")
        if not serper_key:
            raise ValueError("SERPER_API_KEY not found in environment")

        state = run_researcher(state, serper_key, self.client)

        if state["current_phase"] != "research_complete":
            raise RuntimeError("Research failed or incomplete")

        # Step 5: Write evidence Excel
        evidence_excel_path = write_full_excel(state, self.output_dir)

        # Step 6: Synthesis
        state = run_synthesizer(state, self.client)

        # Step 7: Memo generation
        state = run_memo_generator(state, self.client)

        # Step 8: Final Excel with SYNTHESIS and MEMO tabs
        final_excel_path = write_milestone3_excel(state, evidence_excel_path, self.output_dir)
        state["excel_path"] = final_excel_path
        state["current_phase"] = "m3_complete"

        return state
