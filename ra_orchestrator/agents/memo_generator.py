"""
Memo Generator - Creates executive summary from all syntheses.

Takes all question syntheses and creates:
1. Executive summary
2. Key findings (organized by question)
3. Cross-question insights
4. Implications/recommendations
"""

import json
from anthropic import Anthropic

from ra_orchestrator.state import RAState, MemoBlock, QuestionSynthesis


def run_memo_generator(state: RAState, client: Anthropic) -> RAState:
    """
    Generate executive memo from question syntheses.

    Args:
        state: RA state with question_syntheses
        client: Anthropic client

    Returns:
        Updated state with memo_block
    """
    syntheses = state["question_syntheses"]
    plan = state["research_plan"]

    print("\n" + "=" * 80)
    print("MEMO GENERATOR - Creating Executive Summary")
    print("=" * 80)
    print(f"\nIntegrating insights from {len(syntheses)} sub-questions...")

    memo = _generate_memo(plan.research_title, syntheses, client)

    state["memo_block"] = memo
    state["current_phase"] = "memo_complete"

    print("✓ Executive memo generated")
    return state


def _generate_memo(
    research_title: str,
    syntheses: list,
    client: Anthropic
) -> MemoBlock:
    """
    Generate executive memo from syntheses.

    Args:
        research_title: Overall research question
        syntheses: List of QuestionSynthesis
        client: Anthropic client

    Returns:
        MemoBlock with executive summary
    """
    # Format syntheses for Claude
    syntheses_text = "\n\n".join([
        f"{s.question_id}: {s.question}\n"
        f"Conclusion: {s.mini_conclusion}\n"
        f"Key Reasoning:\n" + "\n".join([f"  - {r}" for r in s.logical_reasoning]) + "\n"
        f"Confidence: {s.confidence} ({s.confidence_rationale})"
        for s in syntheses
    ])

    prompt = f"""You are a strategy consultant writing an executive memo.

Research Title: {research_title}

Sub-Question Syntheses:
{syntheses_text}

Your task: Create an executive memo that integrates ALL findings into a cohesive narrative.

Components:

1. EXECUTIVE SUMMARY (3-5 sentences)
   - DIRECTLY ANSWER the research question: "{research_title}"
   - What did we discover? What's the answer?
   - Focus on FINDINGS and INSIGHTS, NOT on what the research program did
   - Be specific with data points, numbers, names from the syntheses
   - What's the "so what?" - why does this matter?

2. KEY FINDINGS (organized by sub-question)
   - For each sub-question, include FULL QUESTION TEXT + key insight
   - Format: "Q1: [Full question text here?] [Key insight/answer]"
   - Each finding should be 2-3 sentences with specific data
   - Use actual numbers, names, and concrete findings from syntheses

3. CROSS-QUESTION INSIGHTS (2-4 insights)
   - Connections BETWEEN different sub-questions
   - Format: "Q1 + Q3 connection: [insight]"
   - Patterns that emerge when looking across questions
   - These are the "aha!" moments

4. IMPLICATIONS (3-5 bullet points)
   - What should be DONE with these findings?
   - Recommendations, action items, strategic implications
   - "So what?" translated into "Now what?"

5. METHODOLOGY NOTE (2-3 sentences)
   - Brief note on research approach
   - Any limitations or caveats
   - Confidence in overall findings

Return a JSON object:
{{
  "executive_summary": "3-5 sentence overview",
  "key_findings": [
    "Q1: Finding from first question",
    "Q2: Finding from second question",
    ...
  ],
  "cross_question_insights": [
    "Q1 + Q3: Insight connecting these questions",
    "Q2 + Q4: Another cross-question insight",
    ...
  ],
  "implications": [
    "Implication 1: Action or recommendation",
    "Implication 2: Strategic insight",
    ...
  ],
  "methodology_note": "Brief note on approach and limitations"
}}

CRITICAL RULES:
- Be SPECIFIC and CONCRETE - use actual findings from syntheses
- Executive summary should be ACTIONABLE, not just descriptive
- Cross-question insights should reveal NON-OBVIOUS connections
- Implications should be ACTIONABLE - what should stakeholders DO?
- Acknowledge limitations honestly in methodology note"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=6000,  # Significantly increased for complex Korean memo with full questions
            temperature=0,  # Ensure consistent, deterministic output
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        text = response.content[0].text.strip()

        # Extract JSON
        if "```json" in text:
            json_start = text.find("```json") + 7
            json_end = text.find("```", json_start)
            text = text[json_start:json_end].strip()
        elif "```" in text:
            json_start = text.find("```") + 3
            json_end = text.find("```", json_start)
            text = text[json_start:json_end].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"\n[ERROR] Memo JSON parse error: {e}")
            print(f"[DEBUG] Response text:\n{text[:500]}...")
            # Try to repair JSON by removing problematic characters
            # Replace newlines within strings, fix common issues
            import re
            # Remove line breaks within JSON string values
            repaired_text = re.sub(r'(?<=")\n+(?=")', ' ', text)
            repaired_text = re.sub(r'(?<=[^"])\n+(?=[^"])', ' ', repaired_text)
            try:
                data = json.loads(repaired_text)
                print("[INFO] JSON repaired successfully")
            except:
                print("[ERROR] JSON repair failed, using fallback")
                raise

        return MemoBlock(
            executive_summary=data["executive_summary"],
            key_findings=data["key_findings"],
            cross_question_insights=data["cross_question_insights"],
            implications=data["implications"],
            methodology_note=data["methodology_note"]
        )

    except Exception as e:
        print(f"  ⚠ Memo generation error: {e}")
        # Fallback memo
        return MemoBlock(
            executive_summary=f"Research on '{research_title}' complete. {len(syntheses)} sub-questions analyzed. (Automated summary generation failed - see individual syntheses)",
            key_findings=[f"{s.question_id}: {s.mini_conclusion}" for s in syntheses],
            cross_question_insights=["Automated cross-question analysis failed - please review individual syntheses"],
            implications=["Please review individual question syntheses for detailed insights"],
            methodology_note="Automated memo generation failed. Please review individual question syntheses and evidence."
        )
