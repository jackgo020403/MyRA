"""State management for RA Orchestrator."""
from typing import TypedDict, List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class SubQuestion(BaseModel):
    """A decomposed sub-question."""
    q_id: str = Field(description="Question ID (Q1, Q2, etc.)")
    question: str = Field(description="The sub-question text")
    rationale: str = Field(description="Why this sub-question matters")
    expected_output: str = Field(
        description="What kind of answer/evidence we expect for this question",
        default=""
    )


class DynamicColumn(BaseModel):
    """A dynamic column for the ledger schema."""
    name: str = Field(description="Column name")
    description: str = Field(description="What this column captures")
    example_values: List[str] = Field(description="Example values for this column")


class LedgerSchema(BaseModel):
    """Schema for the research ledger."""
    dynamic_columns: List[DynamicColumn] = Field(
        description="Dynamic columns specific to this research question"
    )

    @property
    def meta_columns(self) -> List[str]:
        """Fixed operational columns that always exist."""
        return [
            "Row_ID",
            "Row_Type",
            "Question_ID",
            "Section",
            "Statement",
            "Supports_Row_IDs",
            "Source_URL",
            "Source_Name",
            "Date",
            "Confidence",
            "Notes"
        ]


class ResearchPlan(BaseModel):
    """Output from the Planner agent."""
    research_title: str = Field(description="Refined research question/title")
    sub_questions: List[SubQuestion] = Field(description="Question decomposition")
    preliminary_framework: str = Field(
        description="Analytical approach description"
    )
    dynamic_schema_proposal: List[DynamicColumn] = Field(
        description="Proposed dynamic columns for ledger"
    )
    search_plan: str = Field(description="High-level search strategy")
    stop_rules: str = Field(description="When to stop research (e.g., 200 rows)")


class ApprovalDecision(BaseModel):
    """User approval decision."""
    decision: Literal["approve", "edit", "reject"] = Field(
        description="User decision"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="User feedback for edit/reject"
    )


class LedgerRow(BaseModel):
    """A single row in the research ledger."""
    row_id: int
    row_type: Literal["HEADER", "EVIDENCE", "SYNTHESIS", "CONCLUSION"]
    question_id: str
    section: str
    statement: str
    supports_row_ids: Optional[str] = None  # Comma-separated IDs
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    date: Optional[str] = None
    confidence: Optional[str] = None
    notes: Optional[str] = None
    dynamic_fields: Dict[str, Any] = Field(default_factory=dict)


class QuestionSynthesis(BaseModel):
    """Synthesis for a single sub-question."""
    question_id: str = Field(description="Q1, Q2, etc.")
    question: str = Field(description="The sub-question text")
    mini_conclusion: str = Field(description="2-4 sentence conclusion answering this question")
    logical_reasoning: List[str] = Field(description="List of reasoning points with evidence references")
    supporting_evidence_ids: List[int] = Field(description="Row IDs of key supporting evidence")
    confidence: Literal["High", "Medium", "Low"] = Field(description="Confidence level in this conclusion")
    confidence_rationale: str = Field(description="Why this confidence level")


class MemoBlock(BaseModel):
    """Executive memo - overall synthesis."""
    executive_summary: str = Field(description="3-5 sentence overview of entire research")
    key_findings: List[str] = Field(description="Main findings, organized by sub-question")
    cross_question_insights: List[str] = Field(description="Insights connecting multiple questions")
    implications: List[str] = Field(description="What this means / recommendations")
    methodology_note: str = Field(description="Brief note on research approach and limitations")


class RAState(TypedDict, total=False):
    """Complete state for the RA orchestrator."""
    # Input
    research_question: str

    # Planning phase
    research_plan: Optional[ResearchPlan]
    approval_decision: Optional[ApprovalDecision]

    # Schema phase
    ledger_schema: Optional[LedgerSchema]

    # Research phase
    ledger_rows: List[LedgerRow]

    # Synthesis phase (Milestone 3)
    question_syntheses: List[QuestionSynthesis]  # One per sub-question
    memo_block: Optional[MemoBlock]  # Overall executive summary

    # Output
    excel_path: Optional[str]

    # Flow control
    current_phase: str
    iteration_count: int
