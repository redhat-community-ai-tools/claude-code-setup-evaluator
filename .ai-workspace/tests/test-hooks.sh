#!/bin/bash
# Test suite for workspace hooks
# Run: bash .ai-workspace/tests/test-hooks.sh

set -e
PASS=0
FAIL=0
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass() { PASS=$((PASS + 1)); echo "  PASS  $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL  $1: $2"; }

echo "Running hook tests..."
echo ""

# ============================================================
# SECRET SCAN HOOK TESTS
# ============================================================

# Test 1: Should detect Gemini API key pattern
export CLAUDE_TOOL_INPUT='{"command": "git commit -m test"}'
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/test"
echo 'key = "AIzaSyFakeKeyForTestingPurposes123456"' > "$TMPDIR/test/bad.py"
cd "$TMPDIR/test"
git init -q && git add .
OUTPUT=$(bash -c 'ARGS="$CLAUDE_TOOL_INPUT"; CMD=$(echo "$ARGS" | grep -oP "\"command\"\\s*:\\s*\"\\K[^\"]+" 2>/dev/null); if echo "$CMD" | grep -qiE "git (commit|push)"; then FOUND=$(grep -rn --include="*.py" -E "(AIzaSy|sk-[a-zA-Z0-9]{20,}|sk-ant-|ATATT3x|AKIA[0-9A-Z]{16}|ghp_[0-9a-zA-Z]{36}|hf_[0-9a-zA-Z]{30})" --exclude-dir=.git --exclude=".env*" . 2>/dev/null); if [ -n "$FOUND" ]; then echo "BLOCKED"; exit 2; fi; echo "CLEAN"; fi' 2>&1) || true
if echo "$OUTPUT" | grep -q "BLOCKED"; then
    pass "Secret scan: detects Gemini key pattern"
else
    fail "Secret scan: detects Gemini key pattern" "Expected BLOCKED, got: $OUTPUT"
fi
cd "$PROJECT_DIR"
rm -rf "$TMPDIR"

# Test 2: Should pass clean files
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/test"
echo 'api_key = os.getenv("GOOGLE_API_KEY")' > "$TMPDIR/test/clean.py"
cd "$TMPDIR/test"
git init -q && git add .
OUTPUT=$(bash -c 'ARGS="$CLAUDE_TOOL_INPUT"; CMD=$(echo "$ARGS" | grep -oP "\"command\"\\s*:\\s*\"\\K[^\"]+" 2>/dev/null); if echo "$CMD" | grep -qiE "git (commit|push)"; then FOUND=$(grep -rn --include="*.py" -E "(AIzaSy|sk-[a-zA-Z0-9]{20,}|sk-ant-|ATATT3x|AKIA[0-9A-Z]{16}|ghp_[0-9a-zA-Z]{36}|hf_[0-9a-zA-Z]{30})" --exclude-dir=.git --exclude=".env*" . 2>/dev/null); if [ -n "$FOUND" ]; then echo "BLOCKED"; exit 2; fi; echo "CLEAN"; fi' 2>&1)
if echo "$OUTPUT" | grep -q "CLEAN"; then
    pass "Secret scan: passes clean files"
else
    fail "Secret scan: passes clean files" "Expected CLEAN, got: $OUTPUT"
fi
cd "$PROJECT_DIR"
rm -rf "$TMPDIR"

# Test 3: Should not trigger on non-git commands
export CLAUDE_TOOL_INPUT='{"command": "python main.py"}'
OUTPUT=$(bash -c 'ARGS="$CLAUDE_TOOL_INPUT"; CMD=$(echo "$ARGS" | grep -oP "\"command\"\\s*:\\s*\"\\K[^\"]+" 2>/dev/null); if echo "$CMD" | grep -qiE "git (commit|push)"; then echo "TRIGGERED"; else echo "SKIPPED"; fi' 2>&1)
if echo "$OUTPUT" | grep -q "SKIPPED"; then
    pass "Secret scan: skips non-git commands"
else
    fail "Secret scan: skips non-git commands" "Expected SKIPPED, got: $OUTPUT"
fi

# ============================================================
# SKILL SUGGEST HOOK TESTS
# ============================================================

# Test 4: Python file → python-patterns
export CLAUDE_TOOL_INPUT='{"file_path": "/home/user/main.py"}'
OUTPUT=$(bash "$PROJECT_DIR/.ai-workspace/scripts/skill-suggest.sh" 2>&1)
if echo "$OUTPUT" | grep -q "python-patterns"; then
    pass "Skill suggest: .py → python-patterns"
else
    fail "Skill suggest: .py → python-patterns" "Got: $OUTPUT"
fi

# Test 5: Test file → python-testing (not python-patterns)
export CLAUDE_TOOL_INPUT='{"file_path": "/home/user/tests/test_main.py"}'
OUTPUT=$(bash "$PROJECT_DIR/.ai-workspace/scripts/skill-suggest.sh" 2>&1)
if echo "$OUTPUT" | grep -q "python-testing" && ! echo "$OUTPUT" | grep -q "python-patterns"; then
    pass "Skill suggest: test file → python-testing only"
else
    fail "Skill suggest: test file → python-testing only" "Got: $OUTPUT"
fi

# Test 6: .env file → security-check
export CLAUDE_TOOL_INPUT='{"file_path": "/home/user/.env"}'
OUTPUT=$(bash "$PROJECT_DIR/.ai-workspace/scripts/skill-suggest.sh" 2>&1)
if echo "$OUTPUT" | grep -q "security-check"; then
    pass "Skill suggest: .env → security-check"
else
    fail "Skill suggest: .env → security-check" "Got: $OUTPUT"
fi

# Test 7: Pipeline file → data-pipeline-patterns
export CLAUDE_TOOL_INPUT='{"file_path": "/home/user/scripts/fetch_jira_data.py"}'
OUTPUT=$(bash "$PROJECT_DIR/.ai-workspace/scripts/skill-suggest.sh" 2>&1)
if echo "$OUTPUT" | grep -q "data-pipeline-patterns"; then
    pass "Skill suggest: pipeline file → data-pipeline-patterns"
else
    fail "Skill suggest: pipeline file → data-pipeline-patterns" "Got: $OUTPUT"
fi

# Test 8: Git command → git-workflow
export CLAUDE_TOOL_INPUT='{"command": "git push origin main"}'
OUTPUT=$(bash "$PROJECT_DIR/.ai-workspace/scripts/skill-suggest.sh" 2>&1)
if echo "$OUTPUT" | grep -q "git-workflow"; then
    pass "Skill suggest: git push → git-workflow"
else
    fail "Skill suggest: git push → git-workflow" "Got: $OUTPUT"
fi

# Test 9: No match → no output
export CLAUDE_TOOL_INPUT='{"file_path": "/home/user/photo.jpg"}'
OUTPUT=$(bash "$PROJECT_DIR/.ai-workspace/scripts/skill-suggest.sh" 2>&1)
if [ -z "$OUTPUT" ]; then
    pass "Skill suggest: no match → silent"
else
    fail "Skill suggest: no match → silent" "Got unexpected: $OUTPUT"
fi

# ============================================================
# RESULTS
# ============================================================
echo ""
echo "============================================================"
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
    echo "  ALL $TOTAL TESTS PASSED"
else
    echo "  $PASS passed, $FAIL failed"
fi
echo "============================================================"

exit $FAIL
