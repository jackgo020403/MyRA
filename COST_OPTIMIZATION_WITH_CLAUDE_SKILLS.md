# Cost Optimization with Claude AI Skills

This document outlines opportunities to reduce costs in the RA Orchestrator by implementing Claude AI Skills.

## What Are Claude AI Skills?

Claude AI Skills are reusable, specialized functions that can:
- Handle routine tasks without full LLM calls
- Use lightweight processing (regex, heuristics, embeddings)
- Only escalate to Claude when needed
- Cache results for repeated use

## Cost Savings Opportunities in RA Orchestrator

### 1. Web Content Extraction (HIGH IMPACT)

**Current Implementation:** [researcher.py:180-220]
```python
def fetch_source_content(self, url: str) -> Optional[str]:
    # Uses requests + BeautifulSoup
    # No LLM cost, but could be improved
```

**Skill Opportunity:**
Create a `web_extractor` skill that:
- Handles paywall detection
- Identifies main content vs ads/navigation
- Extracts structured data (tables, lists)
- Handles JavaScript-heavy sites

**Implementation:**
```python
# skill: web_extractor.py
def extract_clean_content(url: str) -> dict:
    """Extract clean content using heuristics + selective LLM."""
    # 1. Try trafilatura or newspaper3k (no LLM)
    # 2. If fails, use lightweight Claude call
    # 3. Cache results by URL hash
    pass
```

**Savings:**
- Current: ~0 tokens (already efficient)
- With skill: Can handle complex sites that currently fail
- **ROI:** Better data quality, not cost reduction

---

### 2. Source Ranking & Scoring (MEDIUM-HIGH IMPACT)

**Current Implementation:** [researcher.py:130-160]
```python
def score_and_rank_sources(self, sources, top_n=20):
    # Currently uses Tavily scores + simple heuristics
    # No LLM calls
```

**Skill Opportunity:**
Create a `source_ranker` skill that:
- Uses domain authority databases
- Checks publication date recency
- Matches keywords against research question
- Only uses Claude for ambiguous cases

**Implementation:**
```python
# skill: source_ranker.py
def rank_sources(sources: List[dict], question: str) -> List[dict]:
    """Rank sources using heuristics + selective LLM."""
    scores = []
    for source in sources:
        # Heuristic scoring (free)
        score = calculate_heuristic_score(source)

        # Only use LLM if score is borderline (0.4-0.6)
        if 0.4 <= score <= 0.6:
            score = llm_score_source(source, question)  # Costs tokens

        scores.append((source, score))

    return sorted(scores, key=lambda x: x[1], reverse=True)
```

**Savings:**
- Current: ~0 tokens (no LLM used)
- **Potential future optimization** if we add LLM scoring
- **Prevents:** Adding expensive LLM scoring without this optimization

---

### 3. Evidence Extraction (HIGHEST IMPACT $$$$)

**Current Implementation:** [researcher.py:240-320]
```python
def extract_evidence_from_source(self, source, plan, schema):
    # Calls Claude for EVERY source
    # Cost: ~5000 tokens per source
    # With 20 sources: ~100k tokens = $0.30-0.50
```

**Skill Opportunity:**
Create an `evidence_extractor` skill that:
- Pre-filters content using keyword matching
- Identifies likely evidence sections
- Batches multiple short sources together
- Uses prompt caching for research plan/schema

**Implementation:**
```python
# skill: evidence_extractor.py
from anthropic import Anthropic

def extract_evidence_smart(source: dict, plan: dict, schema: dict) -> list:
    """Extract evidence with cost optimization."""

    # 1. Pre-filter: Only extract sections with keywords
    relevant_sections = filter_by_keywords(
        source['content'],
        extract_keywords_from_plan(plan)
    )

    if not relevant_sections:
        return []  # Skip LLM call entirely

    # 2. Use prompt caching for plan/schema (reused across sources)
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,  # Reduced from 2000
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Research Plan:\n{json.dumps(plan)}",
                    "cache_control": {"type": "ephemeral"}  # CACHE THIS
                },
                {
                    "type": "text",
                    "text": f"Schema:\n{json.dumps(schema)}",
                    "cache_control": {"type": "ephemeral"}  # CACHE THIS
                },
                {
                    "type": "text",
                    "text": f"Extract evidence from:\n{relevant_sections}"
                }
            ]
        }]
    )

    return parse_evidence(response)
```

**Savings:**
- **Without caching:** 20 sources × 5000 tokens = 100k tokens
- **With caching:**
  - First call: 5000 tokens (write to cache)
  - Next 19 calls: ~2500 tokens each (plan/schema cached)
  - Total: 5000 + (19 × 2500) = 52,500 tokens
- **Savings: ~47% reduction = $0.15-0.25 per research job**

---

### 4. Duplicate Detection (MEDIUM IMPACT)

**Current Implementation:** Not yet implemented (planned for M3)

**Skill Opportunity:**
Create a `dedup_checker` skill that:
- Uses sentence embeddings for similarity
- Only calls Claude for near-duplicates
- Maintains dedup cache across sources

**Implementation:**
```python
# skill: dedup_checker.py
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight, local

def is_duplicate(new_evidence: str, existing_evidence: List[str]) -> bool:
    """Check if evidence is duplicate using embeddings."""

    # 1. Get embedding for new evidence (free, local)
    new_emb = model.encode(new_evidence)

    # 2. Compare to existing embeddings
    for existing in existing_evidence:
        existing_emb = model.encode(existing)
        similarity = cosine_similarity(new_emb, existing_emb)

        # 3. Only use LLM if very similar (0.8-0.95)
        if 0.8 <= similarity <= 0.95:
            # Uncertain - use Claude to decide
            return llm_check_duplicate(new_evidence, existing)
        elif similarity > 0.95:
            return True  # Definitely duplicate

    return False
```

**Savings:**
- **Without skill:** ~200 evidence × ~500 tokens = 100k tokens for dedup
- **With skill:** Only ~10% need LLM → 10k tokens
- **Savings: ~90% reduction = $0.25-0.35 per job**

---

### 5. Batch Processing (HIGH IMPACT)

**Current Implementation:** [researcher.py:300-320]
```python
for source in sources:
    evidence = extract_evidence_from_source(source, plan, schema)
    # Separate API call for each source
```

**Skill Opportunity:**
Batch multiple sources in a single Claude call:

**Implementation:**
```python
# skill: batch_extractor.py
def extract_evidence_batch(sources: List[dict], plan: dict, schema: dict) -> dict:
    """Extract evidence from multiple sources in one call."""

    # Combine sources up to token limit
    batches = create_batches(sources, max_tokens=15000)

    all_evidence = {}
    for batch in batches:
        combined_content = "\n\n---SOURCE SEPARATOR---\n\n".join([
            f"Source {i+1} ({s['url']}):\n{s['content'][:2000]}"
            for i, s in enumerate(batch)
        ])

        # One call for multiple sources
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=3000,
            messages=[{
                "role": "user",
                "content": f"Extract evidence from each source:\n{combined_content}"
            }]
        )

        # Parse and attribute evidence to sources
        all_evidence.update(parse_batch_evidence(response, batch))

    return all_evidence
```

**Savings:**
- **Without batching:** 20 calls × ~5k tokens = 100k tokens
- **With batching (5 sources per call):** 4 calls × ~12k tokens = 48k tokens
- **Savings: ~52% reduction = $0.15-0.25 per job**

---

## Combined Savings Summary

| Optimization | Current Cost | With Skill | Savings | Priority |
|--------------|--------------|------------|---------|----------|
| Prompt Caching | $0.50 | $0.25 | 50% | ⭐⭐⭐ HIGH |
| Batch Processing | $0.50 | $0.25 | 50% | ⭐⭐⭐ HIGH |
| Duplicate Detection | $0.35 | $0.04 | 90% | ⭐⭐ MEDIUM |
| Source Ranking | $0.00 | $0.00 | 0% | ⭐ LOW (prevent future costs) |
| Web Extraction | $0.00 | $0.00 | 0% | ⭐ LOW (quality improvement) |

**Total Savings Per Research Job:**
- **Current:** ~$0.50-0.70 per job (20 sources, M2)
- **With All Optimizations:** ~$0.15-0.25 per job
- **Savings: ~60-70% reduction**

**Annual Savings (if running 100 jobs/month):**
- Without optimization: $600-840/year
- With optimization: $180-300/year
- **Savings: $420-540/year**

---

## Implementation Priority

### Phase 1 (Immediate - Highest ROI)
1. **Prompt Caching** in evidence extraction
   - Modify [researcher.py:240-320]
   - Add cache_control to plan/schema
   - **Effort:** 30 minutes
   - **Savings:** 50%

2. **Batch Processing** for small sources
   - Group sources under 2k words
   - **Effort:** 2 hours
   - **Savings:** Additional 30-40%

### Phase 2 (Next Sprint - Good ROI)
3. **Duplicate Detection Skill**
   - Use sentence-transformers
   - **Effort:** 4 hours
   - **Savings:** 90% of dedup costs (M3)

### Phase 3 (Future - Marginal Gains)
4. **Smart Source Ranking**
5. **Advanced Web Extraction**

---

## How to Implement Skills in This Project

### Option 1: Simple Python Functions (Recommended for M2)
```python
# ra_orchestrator/skills/caching.py
def create_cached_prompt(plan, schema, content):
    """Create prompt with caching enabled."""
    return [{
        "type": "text",
        "text": f"Plan:\n{json.dumps(plan)}",
        "cache_control": {"type": "ephemeral"}
    }, {
        "type": "text",
        "text": f"Schema:\n{json.dumps(schema)}",
        "cache_control": {"type": "ephemeral"}
    }, {
        "type": "text",
        "text": f"Content:\n{content}"
    }]
```

### Option 2: Claude Agent SDK Skills (Advanced)
If you want to build reusable skills across projects, use the Claude Agent SDK:

```python
# Install: pip install claude-agent-sdk

from claude_agent_sdk import Skill, SkillContext

class EvidenceExtractorSkill(Skill):
    name = "evidence_extractor"

    def execute(self, ctx: SkillContext) -> dict:
        # Implement with caching, batching, etc.
        pass
```

---

## Monitoring Costs

Add cost tracking to [researcher.py]:

```python
class ResearchAgent:
    def __init__(self):
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.total_cost_usd = 0

    def track_usage(self, response):
        usage = response.usage
        self.total_tokens_input += usage.input_tokens
        self.total_tokens_output += usage.output_tokens

        # Sonnet 4.5 pricing (as of Dec 2024)
        cost_input = usage.input_tokens * 0.003 / 1000  # $3 per MTok
        cost_output = usage.output_tokens * 0.015 / 1000  # $15 per MTok
        self.total_cost_usd += (cost_input + cost_output)

    def print_cost_summary(self):
        print(f"\n[COST SUMMARY]")
        print(f"  Input tokens: {self.total_tokens_input:,}")
        print(f"  Output tokens: {self.total_tokens_output:,}")
        print(f"  Total cost: ${self.total_cost_usd:.2f}")
```

---

## Next Steps

1. **Implement prompt caching** (30 min, 50% savings)
2. **Add cost tracking** (15 min, visibility)
3. **Test with batch processing** (2 hrs, additional 30% savings)
4. **Document in M3 roadmap** (include dedup skill)

**Ready to implement?** Start with prompt caching in [researcher.py:280] - see example above.
