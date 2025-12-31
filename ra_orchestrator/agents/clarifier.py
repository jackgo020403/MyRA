"""
Clarification Agent - Understands research scope before planning.

This agent runs BEFORE the planner to:
1. Auto-detect entities, categories, and scope from research question
2. Present detected scope to user for confirmation
3. Allow user to provide corrections or additional context
4. Store clarified context for planner to use

This prevents the planner from making wrong assumptions about:
- Which specific companies/platforms to include/exclude
- Industry segments or categories
- Geographic scope
- Key metrics to prioritize
"""

from typing import Dict, Any
from anthropic import Anthropic

from ra_orchestrator.state import RAState


def run_clarifier(state: RAState, client: Anthropic) -> RAState:
    """
    Run clarification agent to understand research scope.

    Steps:
    1. Auto-detect likely entities and scope using Claude
    2. Present detection to user
    3. Ask for corrections or confirmation
    4. Store clarified context in state

    Args:
        state: Current RA state with research_question
        client: Anthropic client

    Returns:
        Updated state with research_context added
    """
    print("\n" + "=" * 80)
    print("RESEARCH SCOPE CLARIFICATION")
    print("=" * 80)
    print("\nAnalyzing your research question to understand scope...\n")

    # Step 1: Auto-detect scope using Claude
    detected_scope = _detect_scope(state["research_question"], client)

    # Step 2: Present to user
    print("Detected Research Scope:")
    print("-" * 80)
    print(detected_scope)
    print("-" * 80)

    # Step 3: Ask for confirmation or corrections
    print("\nIs this scope correct?")
    print("  - Press ENTER to confirm")
    print("  - Type 'questions' to answer clarifying questions instead")
    print("  - Type corrections/additions to modify the scope\n")

    user_input = input("> ").strip()

    # Step 4: Handle user response
    if user_input.lower() == 'questions':
        # Interactive question mode
        clarifications = _ask_clarifying_questions(state["research_question"], client)
        final_context = f"{state['research_question']}\n\nClarifications:\n{clarifications}"
    elif user_input == "":
        # User confirmed auto-detected scope
        final_context = f"{state['research_question']}\n\nResearch Scope:\n{detected_scope}"
        print("\n✓ Scope confirmed!")
    else:
        # User provided corrections
        final_context = f"{state['research_question']}\n\nResearch Scope (user-specified):\n{user_input}"
        print("\n✓ Scope updated with your corrections!")

    # Step 5: Store in state
    state['research_context'] = final_context
    state['scope_clarified'] = True

    print("\nProceeding with clarified scope...\n")
    return state


def _detect_scope(research_question: str, client: Anthropic) -> str:
    """
    Auto-detect entities, categories, and scope from research question.

    Uses Claude to analyze the question and identify:
    - Specific companies/platforms mentioned or implied
    - Industry categories or segments
    - Geographic scope
    - Time periods
    - Key aspects to research

    Args:
        research_question: The research question to analyze
        client: Anthropic client

    Returns:
        Formatted string with detected scope
    """

    prompt = f"""Analyze this research question and identify the research scope:

Research Question: {research_question}

Please identify and list:

1. **Specific Entities** (companies, platforms, organizations):
   - Which specific entities should be researched?
   - Are there similar entities that should be EXCLUDED?
   - List both included and excluded entities if relevant

2. **Industry Category/Segment**:
   - What specific industry segment or category?
   - Are there related but different segments to exclude?

3. **Geographic Scope**:
   - What regions or countries?
   - Is it nationwide or specific cities/regions?

4. **Time Period**:
   - What time range should be covered?
   - Are there specific years or periods of focus?

5. **Key Research Aspects** (in priority order):
   - Market share/competition
   - Business models/revenue
   - User behavior/demographics
   - Technology/features
   - Trends/outlook
   - Other aspects

Be SPECIFIC about what should be included vs excluded. For example:
- If the question mentions "아르바이트 플랫폼" (part-time job platforms), clarify whether this includes full-time job platforms like 사람인, 잡코리아 or excludes them.
- If mentioning competitors, list specific names rather than generic terms.

Format as a clear bulleted list under each category."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1500,
        temperature=0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    return response.content[0].text


def _ask_clarifying_questions(research_question: str, client: Anthropic) -> str:
    """
    Generate and ask interactive clarifying questions.

    Uses Claude to generate 3-5 targeted questions about:
    - Specific entities to include/exclude
    - Industry segments
    - Geographic scope
    - Key priorities

    Args:
        research_question: The research question
        client: Anthropic client

    Returns:
        User's answers to clarifying questions
    """

    # Generate questions using Claude
    prompt = f"""Generate 3-5 clarifying questions to understand the scope of this research:

Research Question: {research_question}

Generate questions that help clarify:
1. Which specific companies/platforms to include or exclude
2. Industry segments or categories (if ambiguous)
3. Geographic scope (if not clear)
4. Priority aspects to research

Format each question with:
- Clear question text
- Multiple choice options (a, b, c, d) where applicable
- Allow for "Other" or custom input

Make questions ACTIONABLE and SPECIFIC. For example:
- Instead of "What platforms?", ask "Should we include full-time job platforms (사람인, 잡코리아) or only part-time gig platforms (당근알바, 급구)?"
- Instead of "What aspects?", ask "Which aspect is highest priority: market share, business models, or user behavior?"

Format as numbered questions with options."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        temperature=0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    questions = response.content[0].text

    # Display questions
    print("\n" + "=" * 80)
    print("CLARIFYING QUESTIONS")
    print("=" * 80)
    print(questions)
    print("=" * 80)
    print("\nPlease answer the questions above (you can answer in any format):\n")

    # Get user answers
    answers = input("> ").strip()

    return f"{questions}\n\nUser Answers:\n{answers}"


def display_clarified_scope(state: RAState) -> None:
    """
    Display the clarified research scope.

    Args:
        state: RA state with research_context
    """
    if 'research_context' not in state:
        return

    print("\n" + "=" * 80)
    print("CLARIFIED RESEARCH SCOPE")
    print("=" * 80)
    print(state['research_context'])
    print("=" * 80)
