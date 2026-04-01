---
name: deep-research
version: "1.0"
description: Multi-source deep research with citations. Use when the user wants thorough research on any topic — technology evaluation, library comparison, algorithm analysis, literature review, or competitive analysis. Searches the web, synthesizes findings, and delivers cited reports.
---

# Deep Research

Produce thorough, cited research reports from multiple web sources.

## When to Activate

- User asks to research any topic in depth
- Technology or library evaluation (e.g., "should we use Polars or Pandas?")
- Algorithm or method comparison
- Literature review on ML/DS topics
- Competitive analysis or market sizing
- Due diligence on tools, frameworks, or vendors
- User says "research", "deep dive", "investigate", "compare", or "what's the current state of"

## MCP / Tool Requirements

Use whatever search/web tools are available in the session:
- **WebSearch** — built-in web search
- **WebFetch** — fetch full page content
- **firecrawl MCP** — `firecrawl_search`, `firecrawl_scrape`
- **exa MCP** — `web_search_exa`, `crawling_exa`

If no web tools are available, inform the user and suggest they enable web search or an MCP.

## Workflow

### Step 1: Understand the Goal

Ask 1-2 quick clarifying questions:
- "What's your goal — learning, making a decision, or writing something?"
- "Any specific angle or depth you want?"

If the user says "just research it" — skip ahead with reasonable defaults.

### Step 2: Plan the Research

Break the topic into 3-5 research sub-questions. Example:

**Topic:** "Best feature store for our ML pipeline"
1. What are the main feature store options available today?
2. How do they compare on latency, scalability, and cost?
3. Which ones have good Python SDK support?
4. What are real-world production experiences?
5. What's the learning curve and community size?

### Step 3: Execute Multi-Source Search

For EACH sub-question, search using available tools:

- Use 2-3 different keyword variations per sub-question
- Mix general and technical queries
- Aim for 15-30 unique sources total
- Prioritize: documentation, papers, benchmarks, reputable tech blogs > forums > random blogs

### Step 4: Deep-Read Key Sources

For the most promising URLs, fetch full content. Read 3-5 key sources in full for depth. Do not rely only on search snippets.

### Step 5: Synthesize and Write Report

```markdown
# [Topic]: Research Report
*Generated: [date] | Sources: [N] | Confidence: [High/Medium/Low]*

## Executive Summary
[3-5 sentence overview of key findings]

## 1. [First Major Theme]
[Findings with inline citations]
- Key point ([Source Name](url))
- Supporting data ([Source Name](url))

## 2. [Second Major Theme]
...

## 3. [Third Major Theme]
...

## Comparison Table (if applicable)
| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| ...       | ...      | ...      | ...      |

## Recommendation
[Clear recommendation with reasoning]

## Key Takeaways
- [Actionable insight 1]
- [Actionable insight 2]
- [Actionable insight 3]

## Sources
1. [Title](url) — [one-line summary]
2. ...

## Methodology
Searched [N] queries across web and technical sources.
Sub-questions investigated: [list]
```

### Step 6: Deliver

- **Short topics**: Post the full report in chat
- **Long reports**: Post the executive summary + key takeaways, save full report to a file in `.tmp/`

## Parallel Research with Subagents

For broad topics, use the Agent tool to parallelize:

```
Launch 3 research agents in parallel:
1. Agent 1: Research sub-questions 1-2
2. Agent 2: Research sub-questions 3-4
3. Agent 3: Research sub-question 5 + cross-cutting themes
```

Each agent searches, reads sources, and returns findings. The main session synthesizes into the final report.

## Quality Rules

1. **Every claim needs a source.** No unsourced assertions.
2. **Cross-reference.** If only one source says it, flag it as unverified.
3. **Recency matters.** Prefer sources from the last 12 months.
4. **Acknowledge gaps.** If you couldn't find good info on a sub-question, say so.
5. **No hallucination.** If you don't know, say "insufficient data found."
6. **Separate fact from inference.** Label estimates, projections, and opinions clearly.

## Examples

```
"Research the best feature store for our ML pipeline"
"Deep dive into Polars vs Pandas vs DuckDB for our data processing"
"What's the current state of MLOps best practices in 2026?"
"Compare experiment tracking tools: MLflow vs W&B vs Neptune"
"Research best practices for deploying scikit-learn models to production"
```
