"""
Synthesis Agent - Analyzes evidence to create mini-conclusions per question.

For each sub-question:
1. Read all evidence collected for that question
2. Generate a mini-conclusion
3. Provide logical reasoning with evidence references
4. Assess confidence level
"""

import json
from typing import List
from anthropic import Anthropic

from ra_orchestrator.state import RAState, QuestionSynthesis, ResearchPlan, LedgerRow


def run_synthesizer(state: RAState, client: Anthropic) -> RAState:
    """
    Run synthesis agent to create mini-conclusions for each sub-question.

    Args:
        state: RA state with research_plan and ledger_rows
        client: Anthropic client

    Returns:
        Updated state with question_syntheses
    """
    plan = state["research_plan"]
    all_evidence = state["ledger_rows"]

    print("\n" + "=" * 80)
    print("SYNTHESIS AGENT - Analyzing Evidence")
    print("=" * 80)
    print(f"\nAnalyzing {len(all_evidence)} evidence rows across {len(plan.sub_questions)} questions...")

    syntheses = []

    for sub_q in plan.sub_questions:
        print(f"\n[{sub_q.q_id}] Synthesizing: {sub_q.question[:60]}...")

        # Get evidence for this question
        q_evidence = [ev for ev in all_evidence if ev.question_id == sub_q.q_id]

        if not q_evidence:
            print(f"  ⚠ No evidence found for {sub_q.q_id}")
            # Create empty synthesis
            synthesis = QuestionSynthesis(
                question_id=sub_q.q_id,
                question=sub_q.question,
                mini_conclusion="No evidence collected for this question.",
                logical_reasoning=["No evidence available"],
                supporting_evidence_ids=[],
                confidence="Low",
                confidence_rationale="No evidence collected"
            )
        else:
            print(f"  → Analyzing {len(q_evidence)} evidence rows...")
            synthesis = _synthesize_question(sub_q, q_evidence, client)

        syntheses.append(synthesis)
        print(f"  ✓ Synthesis complete (Confidence: {synthesis.confidence})")

    state["question_syntheses"] = syntheses
    state["current_phase"] = "synthesis_complete"

    print(f"\n✓ Synthesized {len(syntheses)} sub-questions")
    return state


def _synthesize_question(
    sub_q,
    evidence: List[LedgerRow],
    client: Anthropic
) -> QuestionSynthesis:
    """
    Synthesize evidence for a single sub-question.

    Args:
        sub_q: SubQuestion object
        evidence: List of LedgerRow for this question
        client: Anthropic client

    Returns:
        QuestionSynthesis with conclusion and reasoning
    """
    # Format evidence for Claude
    evidence_text = "\n\n".join([
        f"[Evidence #{ev.row_id}]\n"
        f"Statement: {ev.statement}\n"
        f"Source: {ev.source_name} ({ev.date})\n"
        f"Confidence: {ev.confidence}\n"
        f"URL: {ev.source_url}"
        for ev in evidence[:50]  # Limit to first 50 for token management
    ])

    prompt = f"""You are a strategic analyst synthesizing research findings.

Research Question: {sub_q.question}

Expected Output (what we're looking for):
{sub_q.expected_output}

Evidence Collected:
{evidence_text}

Your task:
1. Write a MINI CONCLUSION (2-4 sentences) that directly answers the research question
2. Provide LOGICAL REASONING - natural prose statements with inline source citations
   - Write in flowing narrative form (NOT numbered bullet points starting with "Evidence #X shows...")
   - Integrate source citations naturally: "알바몬의 핵심 차별화 전략이 AI 기술 기반 양면 서비스임을 보여준다 (Source: [source_name], Evidence #[id])."
   - Each reasoning point should be a complete, self-contained statement with specific data
   - Connect the dots between evidence pieces naturally
   - Format: "[Your insight with specific data] (Source: [source_name], Evidence #[id])."
3. List SUPPORTING EVIDENCE IDs - the most critical evidence row IDs
4. Assess CONFIDENCE level (High/Medium/Low) and explain why

Return a JSON object:
{{
  "mini_conclusion": "2-4 sentence conclusion directly answering the question",
  "logical_reasoning": [
    "Natural statement with specific finding (Source: SourceName, Evidence #15).",
    "Another insight with data points (Source: SourceName, Evidence #23).",
    "Connected insight (Source: SourceName, Evidence #47)."
  ],
  "supporting_evidence_ids": [15, 23, 47],
  "confidence": "High|Medium|Low",
  "confidence_rationale": "Why this confidence level (e.g., multiple independent sources, quantitative data)"
}}

CRITICAL RULES:
- Write NATURAL PROSE, not "Evidence #X shows..." format
- Be SPECIFIC and DATA-DRIVEN (use numbers, percentages, names from evidence)
- Format citations as: "(Source: [source_name], Evidence #[id])" at end of each statement
- Include source_name from the evidence in your citations
- Each reasoning statement should be self-contained and informative
- If evidence conflicts, acknowledge it and explain which is more credible
- Confidence = High if: multiple independent sources, quantitative data, recent dates
- Confidence = Low if: few sources, vague statements, old data, contradictions"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=5000,  # Significantly increased for complex Korean responses
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
            print(f"    ⚠ Synthesis JSON parse error: {e}")
            # Try to repair JSON by removing problematic line breaks
            import re
            repaired_text = re.sub(r'(?<=")\n+(?=")', ' ', text)
            repaired_text = re.sub(r'(?<=[^"])\n+(?=[^"])', ' ', repaired_text)
            try:
                data = json.loads(repaired_text)
                print(f"    ✓ JSON repaired successfully")
            except:
                print(f"    ✗ JSON repair failed")
                raise

        return QuestionSynthesis(
            question_id=sub_q.q_id,
            question=sub_q.question,
            mini_conclusion=data["mini_conclusion"],
            logical_reasoning=data["logical_reasoning"],
            supporting_evidence_ids=data["supporting_evidence_ids"],
            confidence=data["confidence"],
            confidence_rationale=data["confidence_rationale"]
        )

    except Exception as e:
        print(f"    ⚠ Synthesis error: {e}")
        # Fallback synthesis
        return QuestionSynthesis(
            question_id=sub_q.q_id,
            question=sub_q.question,
            mini_conclusion=f"Analysis of {len(evidence)} evidence rows. (Synthesis failed - see raw evidence)",
            logical_reasoning=["Synthesis generation failed - please review evidence directly"],
            supporting_evidence_ids=[ev.row_id for ev in evidence[:5]],
            confidence="Low",
            confidence_rationale="Automated synthesis failed"
        )
