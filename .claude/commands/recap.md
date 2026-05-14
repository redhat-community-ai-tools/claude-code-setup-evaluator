---
description: "Generate a session summary: what changed, why, key decisions, and a ready-to-share update for standups or stakeholder messages."
---

# Recap Command

Summarize the current work session into a structured, shareable update.

## Instructions

### Step 1: Gather What Happened

```bash
# Recent commits (this session's work)
git log --oneline --since="8 hours ago" 2>/dev/null || git log --oneline -15

# What files changed
git diff --stat HEAD~10..HEAD 2>/dev/null || git diff --stat

# Current status
git status --short
```

Also review the conversation history for:
- What the user asked for
- Key decisions made (and why)
- Problems encountered and how they were solved
- Skills, agents, or commands that were used

### Step 2: Generate the Recap

**Format the output like this:**

```
SESSION RECAP
=============
Date: [today's date]
Repo: [repository name]

WHAT WAS DONE:
  1. [Change #1 — one sentence describing what and why]
  2. [Change #2 — one sentence]
  3. [Change #3 — one sentence]
  ...

KEY DECISIONS:
  - [Decision and reasoning — e.g., "Kept closed issues as lightweight entries
    instead of removing them, to give the AI context about completed work"]
  - [Decision and reasoning]

PROBLEMS SOLVED:
  - [Problem → Solution — e.g., "Merge conflict on executive_report.html
    → skipped local commit, kept remote version"]

FILES CHANGED:
  [X] files modified, [Y] files created, [Z] files deleted

TESTS:
  [All N tests passing / X failures]

READY TO SHARE (copy-paste for standup/Slack/email):
──────────────────────────────────────────────────────
[2-3 sentence summary suitable for a non-technical audience.
Focus on WHAT was accomplished and WHY it matters,
not the technical details of HOW.]
──────────────────────────────────────────────────────
```

### Step 3: Offer Follow-ups

After the recap, ask:
- "Want me to adjust the tone (more technical / more executive)?"
- "Want me to expand any section?"
- "Want me to draft a message for a specific person?"

## Important

- The "READY TO SHARE" section should be copy-pasteable as-is — no markdown, no jargon
- Focus on outcomes ("split the pipeline for easier debugging") not mechanics ("edited 14 files")
- If multiple repos were touched, organize by repo
- Include commit hashes for traceability

## Arguments

$ARGUMENTS can specify:
- A time range: `/recap today`, `/recap "last 3 days"`
- A branch: `/recap feature/split-pipeline`
- A style: `/recap --executive` (short, high-level) or `/recap --technical` (detailed)
