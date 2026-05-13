---
description: "Test LLM prompts against sample inputs. Shows outputs, checks for regressions when prompts change, and compares different prompt versions side-by-side."
---

# Prompt Test

Test your LLM prompts before deploying them. Run a prompt against sample inputs, inspect the outputs, and catch regressions when you modify prompts.

## When to Use

- After editing a prompt template (e.g., `prompts/person_prompts.py`)
- Before committing prompt changes to make sure outputs didn't degrade
- When comparing two prompt versions side-by-side
- When building a new prompt from scratch and iterating on quality

## Instructions

### 1. Identify the Prompt

- If $ARGUMENTS specifies a file, read it and find the prompt function(s)
- If $ARGUMENTS is empty, search the current repo for prompt files (look in `prompts/`, or files with "prompt" in the name)
- List the available prompt functions and ask the user which to test

### 2. Prepare Test Inputs

- Look for existing test data in the repo (e.g., sample JSON files in `data/`, test fixtures in `tests/`)
- If no test data exists, generate 2-3 realistic sample inputs based on the prompt's expected input format
- Show the user the test inputs and ask if they want to modify them

### 3. Build and Run the Prompt

- Call the prompt function with each test input to generate the actual prompt text
- Display the rendered prompt for each input so the user can review what's being sent to the LLM
- If the user wants to actually call the LLM (requires API key):
  - Run the prompt against the configured LLM (check .env for GOOGLE_API_KEY, OPENAI_API_KEY, etc.)
  - Show the raw LLM response for each input
  - If the pipeline has a parsing function (e.g., `parse_person_summary`), run it on the response and show the parsed result

### 4. Evaluate Output Quality

For each test output, check:

- **Completeness**: Did the LLM fill all expected fields? Any empty or "Unknown" values that shouldn't be?
- **Format compliance**: Does the output match the expected format (e.g., SUMMARY/PRODUCTS/TECHNOLOGIES/WORK_FOCUS)?
- **Grounding**: Does the output reference specific details from the input, or is it generic/hallucinated?
- **Length**: Is the output within expected bounds (not too short, not too long)?
- **Parseability**: If there's a parsing function, does it successfully parse the output without falling back to defaults?

### 5. Compare Versions (if applicable)

If the user is comparing a modified prompt against the original:

- Run both prompt versions against the same inputs
- Show outputs side-by-side
- Highlight differences in quality, completeness, and format compliance
- Give a clear verdict: BETTER / SAME / WORSE for each test case

### 6. Report

```
Prompt Test Results
===================
Prompt: get_person_summary_prompt (prompts/person_prompts.py)
Inputs tested: 3
LLM called: Yes (gemini-2.5-flash-preview)

Test 1: Person with 50 issues
  Completeness:  PASS — all fields populated
  Format:        PASS — SUMMARY/PRODUCTS/TECHNOLOGIES/WORK_FOCUS present
  Grounding:     PASS — references specific projects and technologies
  Parseability:  PASS — parse_person_summary extracted all fields

Test 2: Person with 2 issues
  Completeness:  WARN — TECHNOLOGIES is "Unknown" (may be expected for low-activity)
  Format:        PASS
  Grounding:     PASS
  Parseability:  PASS

Test 3: Person with no description in issues
  Completeness:  WARN — SUMMARY is generic
  Format:        PASS
  Grounding:     FAIL — mentions "Python" but no evidence in input data
  Parseability:  PASS

Overall: 2 PASS, 1 WARN — prompt is working but may hallucinate on sparse inputs
```

## Regression Mode

If the user says "check for regressions" or provides a baseline file:

1. Load the baseline outputs (from a previous run saved as JSON)
2. Run the current prompt against the same inputs
3. Compare field by field
4. Report any regressions (fields that were populated before but are now empty, format changes, quality drops)

To save a baseline for future comparison:
```
Save these results as a baseline? The file will be saved to .tmp/prompt-test/baseline_<prompt_name>.json
```

## Important

- Never modify the prompt files — this command only tests them
- If no API key is available, still render and display the prompt text (skip the LLM call)
- Show the full rendered prompt at least once so the user can eyeball it
- Be honest about output quality — don't say PASS if the output looks generic or hallucinated
- Token count: estimate and display the token count of each rendered prompt

## Arguments

$ARGUMENTS can be:
- A prompt file (e.g., `prompts/person_prompts.py`)
- A specific function (e.g., `prompts/person_prompts.py:get_person_summary_prompt`)
- `--compare` — compare current prompt against git HEAD version
- `--baseline <file>` — compare against a saved baseline
- Empty — search for prompt files and ask
