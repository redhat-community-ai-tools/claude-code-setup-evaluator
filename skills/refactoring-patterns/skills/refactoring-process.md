# Refactoring Process

## Step 1: Profile (before touching anything)

Measure the current state. These are your baseline numbers.

**Complexity metrics:**

```bash
# Function length (lines per function)
grep -n "def " <file> | head -20

# File length
wc -l <file>

# Nesting depth (deepest indentation level)
awk '{ match($0, /^[[:space:]]*/); depth=RLENGTH/4; if(depth>max) max=depth } END { print "Max nesting:", max }' <file>
```

**For Python projects with ruff:**

```bash
# Complexity check
ruff check --select C901 <file> 2>&1

# All style issues
ruff check <file> 2>&1 | wc -l
```

**Record these numbers.** You'll compare against them after refactoring.

| Metric | How to measure | Red flag threshold |
|--------|---------------|-------------------|
| Function length | `grep -c` between defs | >50 lines |
| File length | `wc -l` | >500 lines |
| Nesting depth | Count indentation levels | >3 levels |
| Cyclomatic complexity | `ruff check --select C901` | >10 per function |
| Parameter count | Count function args | >5 parameters |
| Duplication | Identical blocks >10 lines | Any |

## Step 2: Identify What to Refactor

Pick ONE refactoring target. Not "clean up the whole file" — one specific transformation.

**Extraction patterns (most common):**

| Pattern | When to use | How |
|---------|------------|-----|
| Extract function | Code block does one identifiable thing | Move block to named function, replace with call |
| Extract module | File has 2+ unrelated concerns | Split into focused modules, update imports |
| Extract constant | Magic number/string used in logic | Name it at module level |
| Extract class | Group of functions share state via parameters | Encapsulate state + methods |

**Simplification patterns:**

| Pattern | When to use | How |
|---------|------------|-----|
| Flatten nesting | >3 levels of if/for/try | Use early returns, guard clauses |
| Replace conditional with polymorphism | Long if/elif chains on type | Use dispatch dict or class hierarchy |
| Inline temp variable | Variable used once, name adds nothing | Replace variable with expression |
| Remove dead code | Unreachable or never-called code | Delete it (git has history) |

**Consolidation patterns:**

| Pattern | When to use | How |
|---------|------------|-----|
| Merge duplicates | Same logic in 2+ places | Extract shared function, replace call sites |
| Parameterize | Similar functions differ by 1-2 values | Merge into one function with parameters |
| Unify error handling | Same try/except in multiple functions | Extract error handler or use decorator |

## Step 3: Refactor

Apply the chosen transformation. Follow these rules:

1. **Make the smallest change that achieves the goal.** Don't refactor things you pass by.
2. **Keep tests green at every step.** Run tests after each atomic change.
3. **Preserve behavior.** Refactoring changes structure, not behavior. If tests fail, you changed behavior — revert.
4. **One type of refactoring at a time.** Don't extract AND rename AND restructure in the same step.

## Step 4: Measure (after refactoring)

Re-run the same measurements from Step 1.

```bash
# Compare before vs after
echo "=== BEFORE ==="
echo "Lines: <before_count>"
echo "Complexity: <before_complexity>"
echo "Nesting: <before_nesting>"

echo "=== AFTER ==="
wc -l <file>
ruff check --select C901 <file> 2>&1
```

## Step 5: Keep or Revert

**Keep** if ANY of these improved without others getting worse:
- Function length decreased
- Nesting depth decreased
- Complexity score decreased
- Duplication eliminated
- File count increased but each file is more focused (single responsibility)

**Revert** if:
- Metrics stayed the same or got worse
- Tests broke and the fix is non-trivial
- The refactoring introduced new abstractions that only have one user
- The code is "different but not better"

```bash
# Revert if needed
git checkout -- <file>
```

## Bulk Refactoring Mode

For mechanical changes across 10+ files (renaming, replacing deprecated patterns, updating API calls):

1. **Find all targets:**

```bash
grep -rn "old_pattern" --include="*.py" . | wc -l
```

2. **Verify the pattern is mechanical** (same transformation everywhere, no context-dependent decisions)

3. **Apply with sed or ruff:**

```bash
# For renames
find . -name "*.py" -exec sed -i 's/old_name/new_name/g' {} +

# For import updates
ruff check --fix --select I .
```

4. **Verify no breakage:**

```bash
# Run tests
pytest -x -q 2>&1 | tail -5

# Check for remaining references
grep -rn "old_pattern" --include="*.py" .
```

5. **Single commit for bulk changes** — don't make 50 commits for a rename.
