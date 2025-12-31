"""
Interactive Approval Agent - Question-by-question review and refinement.

This agent allows users to:
1. Review each sub-question individually
2. See expected outputs for each question
3. Modify questions or expected outputs
4. Iteratively refine until satisfied
5. Only proceed when user explicitly approves with "1) Pass"
"""

from typing import Dict, Any
from anthropic import Anthropic

from ra_orchestrator.state import RAState, ResearchPlan, SubQuestion


def run_interactive_approval(state: RAState, client: Anthropic) -> RAState:
    """
    Interactive approval loop - review each sub-question with user.

    User can:
    - Press 1 to pass (move to next question)
    - Press 2 to modify question
    - Press 3 to modify expected output
    - Press 4 to modify both

    Only when ALL questions are approved, workflow proceeds.

    Args:
        state: Current RA state with research_plan
        client: Anthropic client for generating modifications

    Returns:
        Updated state with approved (possibly refined) plan
    """
    plan = state["research_plan"]

    print("\n" + "=" * 80)
    print("INTERACTIVE QUESTION REVIEW")
    print("=" * 80)
    print("\nLet's review each sub-question to ensure it will get you the answers you need.")
    print("For each question, you can refine it until it's exactly what you want.\n")

    # Review each question interactively
    refined_questions = []

    for sq in plan.sub_questions:
        refined_sq = _review_question_interactive(sq, client)
        refined_questions.append(refined_sq)

    # Update plan with refined questions
    plan.sub_questions = refined_questions
    state["research_plan"] = plan
    state["current_phase"] = "plan_approved"

    print("\n" + "=" * 80)
    print("✓ ALL QUESTIONS APPROVED")
    print("=" * 80)
    print("\nProceeding with research...\n")

    return state


def _review_question_interactive(sq: SubQuestion, client: Anthropic) -> SubQuestion:
    """
    Interactively review and refine a single sub-question.

    User loop:
    1. Display question + expected output
    2. User chooses: Pass / Modify Question / Modify Expected / Both
    3. If modify: Ask Claude to generate new version based on user feedback
    4. Repeat until user presses "1) Pass"

    Args:
        sq: SubQuestion to review
        client: Anthropic client

    Returns:
        Refined SubQuestion
    """
    current_sq = sq

    while True:
        # Display current question
        print("\n" + "-" * 80)
        print(f"REVIEWING: {current_sq.q_id}")
        print("-" * 80)
        print(f"\nQuestion:")
        print(f"  {current_sq.question}")
        print(f"\nRationale:")
        print(f"  {current_sq.rationale}")
        print(f"\nExpected Output:")
        print(f"  {current_sq.expected_output if current_sq.expected_output else '(Not specified)'}")
        print("\n" + "-" * 80)

        # Get user input
        print("\nWhat would you like to do?")
        print("  1) Pass (approve this question and move to next)")
        print("  2) Modify question")
        print("  3) Modify expected output")
        print("  4) Modify both question and expected output")
        print("")

        choice = input("> ").strip()

        if choice == "1":
            # Approved - move to next
            print(f"\n✓ {current_sq.q_id} approved!")
            return current_sq

        elif choice == "2":
            # Modify question only
            print("\nWhat changes would you like to make to the question?")
            print("(Describe what you want to change, or provide the new question directly)")
            print("")
            user_feedback = input("> ").strip()

            if user_feedback:
                new_question = _refine_question(current_sq, user_feedback, "question", client)
                current_sq = SubQuestion(
                    q_id=current_sq.q_id,
                    question=new_question,
                    rationale=current_sq.rationale,
                    expected_output=current_sq.expected_output
                )
                print(f"\n✓ Question updated!")

        elif choice == "3":
            # Modify expected output only
            print("\nWhat would you like the expected output to be?")
            print("(Describe what kind of answer/evidence you're looking for)")
            print("")
            user_feedback = input("> ").strip()

            if user_feedback:
                new_expected = _refine_question(current_sq, user_feedback, "expected_output", client)
                current_sq = SubQuestion(
                    q_id=current_sq.q_id,
                    question=current_sq.question,
                    rationale=current_sq.rationale,
                    expected_output=new_expected
                )
                print(f"\n✓ Expected output updated!")

        elif choice == "4":
            # Modify both
            print("\nWhat changes would you like to make?")
            print("(Describe what you want to change about the question and/or expected output)")
            print("")
            user_feedback = input("> ").strip()

            if user_feedback:
                new_question, new_expected = _refine_both(current_sq, user_feedback, client)
                current_sq = SubQuestion(
                    q_id=current_sq.q_id,
                    question=new_question,
                    rationale=current_sq.rationale,
                    expected_output=new_expected
                )
                print(f"\n✓ Question and expected output updated!")

        else:
            print("\nInvalid choice. Please enter 1, 2, 3, or 4.")


def _refine_question(sq: SubQuestion, user_feedback: str, field: str, client: Anthropic) -> str:
    """
    Use Claude to refine a question or expected_output based on user feedback.

    Args:
        sq: Current SubQuestion
        user_feedback: User's requested changes
        field: "question" or "expected_output"
        client: Anthropic client

    Returns:
        Refined text
    """
    if field == "question":
        prompt = f"""The user wants to refine this research sub-question:

Current Question: {sq.question}
Rationale: {sq.rationale}
Expected Output: {sq.expected_output}

User Feedback: {user_feedback}

Please provide a refined version of the QUESTION that incorporates the user's feedback.
Return ONLY the refined question text, nothing else."""

    else:  # expected_output
        prompt = f"""The user wants to refine the expected output for this research question:

Question: {sq.question}
Current Expected Output: {sq.expected_output}

User Feedback: {user_feedback}

Please provide a refined version of the EXPECTED OUTPUT that incorporates the user's feedback.
The expected output should describe:
- What kind of data/evidence we're looking for
- Specific examples of good answers
- Level of detail needed

Return ONLY the refined expected output text, nothing else."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        temperature=0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    return response.content[0].text.strip()


def _refine_both(sq: SubQuestion, user_feedback: str, client: Anthropic) -> tuple[str, str]:
    """
    Use Claude to refine both question and expected_output based on user feedback.

    Args:
        sq: Current SubQuestion
        user_feedback: User's requested changes
        client: Anthropic client

    Returns:
        Tuple of (refined_question, refined_expected_output)
    """
    prompt = f"""The user wants to refine this research sub-question:

Current Question: {sq.question}
Rationale: {sq.rationale}
Current Expected Output: {sq.expected_output}

User Feedback: {user_feedback}

Please provide refined versions of BOTH the question and expected output that incorporate the user's feedback.

Return in this exact format:
QUESTION: [refined question]
EXPECTED_OUTPUT: [refined expected output]"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=800,
        temperature=0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    text = response.content[0].text.strip()

    # Parse response
    question_line = ""
    expected_line = ""

    for line in text.split('\n'):
        if line.startswith("QUESTION:"):
            question_line = line.replace("QUESTION:", "").strip()
        elif line.startswith("EXPECTED_OUTPUT:"):
            expected_line = line.replace("EXPECTED_OUTPUT:", "").strip()

    # Fallback if parsing fails
    if not question_line:
        question_line = sq.question
    if not expected_line:
        expected_line = sq.expected_output

    return question_line, expected_line
