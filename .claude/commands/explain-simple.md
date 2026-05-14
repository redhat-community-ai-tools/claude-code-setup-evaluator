---
description: "Explain a file or folder in very simple words, like to a 15-year-old. No jargon, no technical depth — just what it does and why."
---

# Explain Simple

Explain code like you're talking to a smart 15-year-old who has never programmed. No jargon. No implementation details. Just what it does, why it exists, and how it fits into the bigger picture.

## Instructions

### 1. Read the Target

- Read the file or folder specified in $ARGUMENTS
- If it's a folder, read the key files to understand the overall purpose
- If it's a single file, understand what it does in context

### 2. Explain Simply

Write an explanation that follows these rules:

- **No jargon.** Don't say "API endpoint", say "a way for other programs to ask for data." Don't say "parses JSON", say "reads a data file."
- **Use analogies.** Compare to real-world things. A pipeline is like an assembly line. A config file is like a settings menu. A function is like a recipe.
- **Start with WHY.** Before explaining what it does, explain why someone built it. What problem does it solve?
- **Short sentences.** If a sentence has a comma, consider splitting it.
- **No code.** Don't show code snippets. If you must reference something technical, explain it immediately.
- **Structure it:** What is this? → Why does it exist? → How does it work (simply)? → How does it connect to the rest of the project?

### 3. Format

```
What is this?
[1-2 sentences]

Why does it exist?
[1-2 sentences about the problem it solves]

How does it work?
[3-5 bullet points, simple language, analogies welcome]

How does it fit in?
[1-2 sentences about where it sits in the bigger project]
```

## Example

For a file like `scripts/fetch_data.py`:

```
What is this?
This is a script that downloads records from an external API.

Why does it exist?
We want to know what everyone is working on, but that information is scattered across
thousands of tickets. This script collects all of them automatically.

How does it work?
- It goes through a list of people and looks up their tickets, one person at a time
- It's polite about it — if the server says "slow down", it waits before asking again
- For each ticket, it also grabs the parent project it belongs to, so we get the full picture
- It saves everything into one big file that other scripts can use later

How does it fit in?
This is step 2 of 4. First we get the list of people (step 1), then this script gets their
work data, then another script summarizes what each person does (step 3), and finally
everything gets organized into a report (step 4).
```

## Important

- The audience is NOT a developer. It's someone who wants to understand what this project does.
- If you catch yourself writing something a 15-year-old wouldn't understand, rewrite it.
- Shorter is better. Aim for under 200 words.

## Arguments

$ARGUMENTS can be:
- A file path (e.g., `scripts/summarize_people.py`)
- A folder (e.g., `repositories/backend-api`)
- A concept (e.g., "the pipeline", "the chat script")
- Empty — explain the current project root
