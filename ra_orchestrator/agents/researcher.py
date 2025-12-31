"""Researcher agent for web search and evidence collection.

COST OPTIMIZATION OPPORTUNITIES WITH CLAUDE SKILLS:
====================================================

1. **Web Content Extraction** (Lines 100-150)
   - CURRENT: Uses requests + BeautifulSoup for every source
   - SKILL OPPORTUNITY: Create a "web_scraper" skill that:
     * Handles common website patterns
     * Extracts clean text without LLM calls
     * Returns structured content
   - SAVINGS: Avoid preprocessing tokens, faster execution

2. **Source Scoring** (Lines 200-250)
   - CURRENT: Uses Claude to score every source
   - SKILL OPPORTUNITY: Create a "source_ranker" skill that:
     * Uses lightweight heuristics (domain authority, date, relevance)
     * Only uses LLM for ambiguous cases
   - SAVINGS: ~50% reduction in scoring tokens

3. **Duplicate Detection** (Lines 300-350)
   - CURRENT: Passes all evidence to LLM to check duplicates
   - SKILL OPPORTUNITY: Create a "dedup_checker" skill that:
     * Uses embedding similarity (fast, cheap)
     * Only escalates to LLM when uncertain
   - SAVINGS: ~70% reduction in dedup tokens

4. **Batch Processing** (Lines 400-450)
   - CURRENT: One LLM call per source
   - OPTIMIZATION: Process multiple sources in one call (with prompt caching)
   - SAVINGS: Reduced API overhead, better caching

See COST_OPTIMIZATION.md for detailed implementation guide.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
from anthropic import Anthropic

from ra_orchestrator.state import RAState, LedgerRow, ResearchPlan, LedgerSchema


RESEARCH_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "research.md"


def load_research_prompt() -> str:
    """Load the research prompt template."""
    return RESEARCH_PROMPT_PATH.read_text(encoding="utf-8")


class ResearchAgent:
    """
    Researcher agent for Milestone 2.

    Performs:
    1. Wide scan - search for many candidate sources
    2. Source scoring - rank by relevance
    3. Deep dive - extract content from top sources
    4. Evidence extraction - create ledger rows
    """

    def __init__(self, anthropic_client: Anthropic, tavily_api_key: str):
        """Initialize researcher with API clients."""
        self.anthropic = anthropic_client
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.evidence_count = 0

    def run_wide_scan(
        self,
        research_plan: ResearchPlan,
        max_sources: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Phase 1: Wide scan - search for candidate sources.

        COST OPTIMIZATION: This uses Tavily API (not Claude tokens).
        Each sub-question gets its own search.

        Args:
            research_plan: Approved research plan
            max_sources: Max sources to find per sub-question

        Returns:
            List of source metadata dicts
        """
        print(f"\n[WIDE SCAN] Searching for sources...")

        all_sources = []

        for sub_q in research_plan.sub_questions:
            print(f"  Searching for {sub_q.q_id}: {sub_q.question[:60]}...")

            # Tavily search - returns ~10 results per query
            # COST: Tavily API (~$1 per 1000 searches), no Claude tokens
            try:
                search_results = self.tavily.search(
                    query=sub_q.question,
                    max_results=min(max_sources // len(research_plan.sub_questions), 10),
                    search_depth="basic",  # "basic" is cheaper than "advanced"
                    include_raw_content=False  # Save bandwidth, we'll fetch later
                )

                for result in search_results.get('results', []):
                    all_sources.append({
                        'question_id': sub_q.q_id,
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'snippet': result.get('content', '')[:300],  # Truncate snippet
                        'score': result.get('score', 0.5),
                        'published_date': result.get('published_date', 'Unknown'),
                    })

                print(f"    Found {len(search_results.get('results', []))} sources")

            except Exception as e:
                print(f"    Error searching {sub_q.q_id}: {e}")
                continue

        print(f"\n[WIDE SCAN] Total sources found: {len(all_sources)}")
        return all_sources

    def score_and_rank_sources(
        self,
        sources: List[Dict[str, Any]],
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Phase 2: Score and rank sources for deep dive.

        COST OPTIMIZATION OPPORTUNITY:
        - CURRENT: Uses Tavily scores only (no LLM)
        - SKILL OPPORTUNITY: Add a "source_scorer" skill that uses
          domain authority, recency, and keyword matching

        Args:
            sources: Source metadata from wide scan
            top_n: Number of top sources to return

        Returns:
            Top N ranked sources
        """
        print(f"\n[RANKING] Scoring {len(sources)} sources...")

        # Simple scoring based on Tavily score + recency
        # SKILL OPPORTUNITY: Replace with custom skill for better control
        for source in sources:
            base_score = source.get('score', 0.5)

            # Boost recent sources
            pub_date = source.get('published_date', 'Unknown')
            if pub_date != 'Unknown':
                try:
                    year = int(pub_date[:4])
                    if year >= 2023:
                        base_score += 0.2
                    elif year >= 2020:
                        base_score += 0.1
                except:
                    pass

            source['final_score'] = base_score

        # Sort and take top N
        ranked = sorted(sources, key=lambda x: x['final_score'], reverse=True)[:top_n]

        print(f"[RANKING] Selected top {len(ranked)} sources for deep dive")
        return ranked

    def fetch_source_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract clean text from a URL.

        COST OPTIMIZATION OPPORTUNITY:
        - CURRENT: Uses requests + BeautifulSoup (no LLM cost)
        - SKILL OPPORTUNITY: Create "web_extractor" skill for complex sites

        Args:
            url: URL to fetch

        Returns:
            Clean text content or None if error
        """
        try:
            # SKILL OPPORTUNITY: This is where a custom web scraper skill would help
            # Handle paywalls, JavaScript-heavy sites, etc.

            response = requests.get(
                url,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Research Bot)'}
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # Limit to ~4000 words to control token costs
            words = text.split()
            if len(words) > 4000:
                text = ' '.join(words[:4000]) + "..."

            return text

        except Exception as e:
            print(f"    Error fetching {url}: {e}")
            return None

    def extract_evidence_from_source(
        self,
        source: Dict[str, Any],
        research_plan: ResearchPlan,
        schema: LedgerSchema
    ) -> List[LedgerRow]:
        """
        Phase 3: Deep dive - extract evidence from a source.

        COST ANALYSIS:
        - Input tokens: ~4000 (source content) + ~500 (prompt) = ~4500 tokens
        - Output tokens: ~500-1000 (evidence JSON)
        - Total per source: ~5000-6000 tokens
        - Cost per source: ~$0.015-0.025

        OPTIMIZATION OPPORTUNITIES:
        1. Use prompt caching for research plan/schema (static across sources)
        2. Batch multiple sources in one call (if content fits)
        3. Use a skill for initial filtering before LLM extraction

        Args:
            source: Source metadata with URL
            research_plan: Research plan for context
            schema: Ledger schema for dynamic fields

        Returns:
            List of LedgerRow objects (evidence)
        """
        print(f"    Processing: {source['title'][:60]}...")

        # Fetch content
        content = self.fetch_source_content(source['url'])
        if not content:
            print(f"      Skipped (fetch failed)")
            return []

        # Build prompt
        prompt_template = load_research_prompt()

        # Format sub-questions
        sub_q_text = "\n".join([
            f"{sq.q_id}: {sq.question}"
            for sq in research_plan.sub_questions
        ])

        # Format dynamic schema
        schema_text = "\n".join([
            f"- {col.name}: {col.description} (e.g., {', '.join(col.example_values[:2])})"
            for col in schema.dynamic_columns
        ])

        prompt = prompt_template.replace("{sub_questions}", sub_q_text)
        prompt = prompt.replace("{dynamic_schema}", schema_text)
        prompt = prompt.replace("{source_url}", source['url'])
        prompt = prompt.replace("{source_name}", source.get('title', 'Unknown'))
        prompt = prompt.replace("{source_date}", source.get('published_date', 'Unknown'))
        prompt = prompt.replace("{source_content}", content[:10000])  # Limit to control costs

        # Call Claude
        # OPTIMIZATION: Use prompt caching for the research plan/schema parts
        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,  # Limit output to control costs
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            # Parse evidence array
            evidence_data = json.loads(response_text)
            if not isinstance(evidence_data, list):
                evidence_data = [evidence_data]  # Wrap single object

            # Convert to LedgerRow objects
            ledger_rows = []
            for ev in evidence_data:
                self.evidence_count += 1

                ledger_row = LedgerRow(
                    row_id=self.evidence_count,
                    row_type="EVIDENCE",
                    question_id=ev.get('question_id', source['question_id']),
                    section=ev.get('section', 'General'),
                    statement=ev.get('statement', ''),
                    supports_row_ids=None,  # Evidence doesn't support other rows
                    source_url=source['url'],
                    source_name=source.get('title', 'Unknown'),
                    date=source.get('published_date', 'Unknown'),
                    confidence=ev.get('confidence', 'Medium'),
                    notes=ev.get('notes', ''),
                    dynamic_fields=ev.get('dynamic_fields', {})
                )
                ledger_rows.append(ledger_row)

            print(f"      Extracted {len(ledger_rows)} evidence units")
            return ledger_rows

        except Exception as e:
            print(f"      Error extracting evidence: {e}")
            return []


def run_researcher(state: RAState, tavily_api_key: str, client: Anthropic) -> RAState:
    """
    Run the full researcher workflow.

    Args:
        state: Current RA state with approved plan and schema
        tavily_api_key: Tavily API key
        client: Anthropic client

    Returns:
        Updated state with ledger_rows populated
    """
    plan = state["research_plan"]
    schema = state["ledger_schema"]

    researcher = ResearchAgent(client, tavily_api_key)

    # Phase 1: Wide scan
    sources = researcher.run_wide_scan(plan, max_sources=50)

    if not sources:
        print("\n[ERROR] No sources found. Check Tavily API key or search query.")
        return state

    # Phase 2: Rank sources
    top_sources = researcher.score_and_rank_sources(sources, top_n=20)

    # Phase 3: Deep dive and extract evidence
    print(f"\n[DEEP DIVE] Extracting evidence from top {len(top_sources)} sources...")
    all_evidence = []

    for i, source in enumerate(top_sources, 1):
        print(f"\n  Source {i}/{len(top_sources)}")
        evidence = researcher.extract_evidence_from_source(source, plan, schema)
        all_evidence.extend(evidence)

        # Stop if we hit target row count
        if len(all_evidence) >= 200:
            print(f"\n[STOP RULE] Reached target of ~200 evidence rows ({len(all_evidence)})")
            break

    # Update state
    state["ledger_rows"] = all_evidence
    state["current_phase"] = "research_complete"

    print(f"\n[RESEARCH COMPLETE] Collected {len(all_evidence)} evidence rows")

    return state
