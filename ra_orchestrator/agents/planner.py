"""Planner agent for research strategy."""
import json
from pathlib import Path
from anthropic import Anthropic
from ra_orchestrator.state import RAState, ResearchPlan


PLANNER_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "planner.md"


def load_planner_prompt() -> str:
    """Load the planner prompt template."""
    return PLANNER_PROMPT_PATH.read_text(encoding='utf-8')


def run_planner(state: RAState, client: Anthropic) -> RAState:
    """
    Planner agent: Create research plan from the research question.

    Args:
        state: Current RA state with research_question (and optional research_context)
        client: Anthropic client

    Returns:
        Updated state with research_plan
    """
    # Use clarified context if available, otherwise use original question
    if 'research_context' in state and state['research_context']:
        research_input = state['research_context']
    else:
        research_input = state["research_question"]

    # Load prompt template
    prompt_template = load_planner_prompt()
    # Use replace instead of format to avoid issues with JSON examples in prompt
    prompt = prompt_template.replace("{research_question}", research_input)

    # Call Claude with structured output
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=6000,  # Increased for detailed Korean plans
        temperature=0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    # Parse JSON response
    response_text = response.content[0].text

    # Extract JSON from markdown code blocks if present
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()

    # Try to parse JSON
    try:
        plan_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"\n[ERROR] Failed to parse planner response as JSON: {e}")
        print(f"[ERROR] Response text (first 500 chars):\n{response_text[:500]}")
        print("\n[DEBUG] Full response:\n", response_text)
        raise

    # Validate with Pydantic
    research_plan = ResearchPlan(**plan_data)

    # Update state
    state["research_plan"] = research_plan
    state["current_phase"] = "plan_created"

    return state


def display_plan(plan: ResearchPlan) -> str:
    """
    Format the research plan for user review.

    Args:
        plan: ResearchPlan to display

    Returns:
        Formatted string for CLI display
    """
    output = []
    output.append("=" * 80)
    output.append("RESEARCH PLAN")
    output.append("=" * 80)
    output.append("")

    output.append(f"Research Title: {plan.research_title}")
    output.append("")

    output.append("Question Decomposition:")
    for sq in plan.sub_questions:
        output.append(f"  {sq.q_id}: {sq.question}")
        output.append(f"      Rationale: {sq.rationale}")
        if sq.expected_output:
            output.append(f"      Expected Output: {sq.expected_output}")
    output.append("")

    output.append(f"Preliminary Framework:")
    output.append(f"  {plan.preliminary_framework}")
    output.append("")

    output.append("Dynamic Schema (in addition to meta-columns):")
    for col in plan.dynamic_schema_proposal:
        output.append(f"  - {col.name}: {col.description}")
        output.append(f"    Examples: {', '.join(col.example_values)}")
    output.append("")

    output.append(f"Search Plan:")
    output.append(f"  {plan.search_plan}")
    output.append("")

    output.append(f"Stop Rules:")
    output.append(f"  {plan.stop_rules}")
    output.append("")

    output.append("=" * 80)

    return "\n".join(output)
