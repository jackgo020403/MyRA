"""Schema designer agent for finalizing ledger schema."""
from ra_orchestrator.state import RAState, LedgerSchema


def run_schema_designer(state: RAState) -> RAState:
    """
    Schema designer: Finalize ledger schema from approved plan.

    Args:
        state: Current RA state with approved research_plan

    Returns:
        Updated state with ledger_schema
    """
    plan = state["research_plan"]

    # Create ledger schema from plan's dynamic columns
    ledger_schema = LedgerSchema(
        dynamic_columns=plan.dynamic_schema_proposal
    )

    # Update state
    state["ledger_schema"] = ledger_schema
    state["current_phase"] = "schema_ready"

    return state


def display_schema(schema: LedgerSchema) -> str:
    """
    Format the ledger schema for display.

    Args:
        schema: LedgerSchema to display

    Returns:
        Formatted string for CLI display
    """
    output = []
    output.append("=" * 80)
    output.append("LEDGER SCHEMA")
    output.append("=" * 80)
    output.append("")

    output.append("Meta Columns (fixed):")
    for col in schema.meta_columns:
        output.append(f"  - {col}")
    output.append("")

    output.append("Dynamic Columns (question-specific):")
    for col in schema.dynamic_columns:
        output.append(f"  - {col.name}: {col.description}")
    output.append("")

    output.append("=" * 80)

    return "\n".join(output)
