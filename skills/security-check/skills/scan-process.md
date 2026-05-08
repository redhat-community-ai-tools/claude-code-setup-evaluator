# Security Scan Process

## Step 1: Scan for Hardcoded Secrets

Search for patterns that suggest hardcoded credentials:

```bash
# API keys and tokens (generic)
grep -rn --include="*.py" --include="*.yaml" --include="*.yml" --include="*.json" -E "(api_key|api_token|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}" . --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv

# Common API key patterns
grep -rn --include="*.py" -E "(AIza|sk-|sk-ant-|sk-proj-|ghp_|ghu_|AKIA|xox[bpas]-)" . --exclude-dir=.git --exclude-dir=__pycache__
```

### Additional Credential Patterns

```bash
# Database connection strings with embedded passwords
grep -rn --include="*.py" -E "(mysql|postgres|mongodb|redis)://[^:]+:[^@]+@" . --exclude-dir=.git

# JWT tokens
grep -rn --include="*.py" -E "eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}" . --exclude-dir=.git

# Private keys
grep -rn --include="*.py" --include="*.pem" --include="*.key" -E "BEGIN (RSA |EC |DSA )?PRIVATE KEY" . --exclude-dir=.git

# Python dict/config with passwords
grep -rn --include="*.py" -E "['\"]password['\"]\s*:\s*['\"][^'\"]{4,}" . --exclude-dir=.git
```

## Step 2: Verify .gitignore Coverage

```bash
cat .gitignore | grep -E "\.env|config\.yaml|credentials|\.key|\.pem"
git ls-files | grep -E "\.env|credentials|secret|\.key|\.pem"
git ls-files | grep -E "\.csv|\.parquet|\.xlsx" | head -10
```

## Step 3: Check .env Files

```bash
ls .env.example 2>/dev/null
git status --porcelain .env 2>/dev/null
git log --all --full-history -- "*.env" --oneline | head -5
```

## Step 4: Review Config Files

Check configuration files for embedded secrets:
- `config.yaml` / `config.yml` — should reference env vars, not inline secrets
- `*.json` config files — check for tokens or keys
- Jupyter notebooks (`.ipynb`) — check cell outputs for leaked credentials
- `.mcp.json` — check for hardcoded MCP server credentials

## Step 5: Check Python Code Patterns

See `pattern-tables.md` for the full list of insecure patterns and their severities.

## Step 6: LLM-Specific Security Checks

For projects that send data to LLM APIs (Gemini, OpenAI, etc.), see the LLM-specific patterns in `pattern-tables.md`.

```bash
# Check if raw PII fields are sent to LLM prompts
grep -rn --include="*.py" -E "(email|phone|ssn|address|salary)" . --exclude-dir=.git --exclude-dir=__pycache__ | grep -i "prompt\|generate_content\|completion"

# Check for eval/exec on LLM output
grep -rn --include="*.py" -E "(eval|exec)\s*\(\s*(response|result|output|completion)" . --exclude-dir=.git
```

## Output Format

```
SECURITY CHECK REPORT
=====================

CRITICAL (blocks push):
  [file:line] Hardcoded Gemini API key detected (AIzaSy...)
  [file:line] eval() called on LLM response

HIGH (should fix before push):
  [file:line] SSL verification disabled (verify=False)
  [file:line] PII fields sent to external LLM without sanitization

MEDIUM (fix soon):
  [file:line] Using MD5 for hashing

OK: .gitignore covers .env and config.yaml
OK: No credentials in git-tracked files
OK: .env.example exists with placeholders

Verdict: [SAFE TO PUSH / NEEDS FIXES]
```

## Quick Remediation

- Move all secrets to `.env` and load with `python-dotenv`
- Add `.env` to `.gitignore`
- Create `.env.example` with placeholder values
- Use `os.getenv()` without default values for secrets
- Replace `yaml.load()` with `yaml.safe_load()`
- Replace `pickle.load()` with `json.load()` where possible
- Sanitize PII before sending to external LLM APIs
- Never execute LLM-generated code with `eval()` or `exec()`
- Run `git log --all --full-history -- "*.env"` to check if secrets were ever committed
- If secrets were committed historically, rotate them immediately
