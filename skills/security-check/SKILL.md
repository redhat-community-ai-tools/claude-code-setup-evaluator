---
name: security-check
version: "1.0"
description: Scan Python projects for credential leaks, secrets in code, insecure patterns, LLM API key exposure, PII leakage to external AI services, and .env/.gitignore misconfigurations. Focused on data science pipelines handling API keys, tokens, and LLM integrations.
---

# Security Check Skill

Scan for credential leaks, insecure code patterns, and LLM security issues in Python data science projects.

## When to Activate

- Before committing changes
- After modifying `.env`, `.gitignore`, or config files
- When adding new API integrations or credentials
- When reviewing code that handles tokens, keys, or passwords
- When code sends data to external LLM APIs (Gemini, OpenAI, etc.)
- Periodic security hygiene checks

## Check Process

### Step 1: Scan for Hardcoded Secrets

Search for patterns that suggest hardcoded credentials:

```bash
# API keys and tokens (generic)
grep -rn --include="*.py" --include="*.yaml" --include="*.yml" --include="*.json" -E "(api_key|api_token|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}" . --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv

# Common API key patterns
grep -rn --include="*.py" -E "(AIza|sk-|sk-ant-|sk-proj-|ghp_|ghu_|AKIA|xox[bpas]-)" . --exclude-dir=.git --exclude-dir=__pycache__
```

#### Specific Key Patterns to Detect

| Pattern | Service | Regex |
|---------|---------|-------|
| `AIzaSy...` | Google/Gemini API | `AIzaSy[0-9A-Za-z_-]{33}` |
| `sk-...` | OpenAI | `sk-[0-9a-zA-Z]{20,}` |
| `sk-ant-api03-...` | Anthropic | `sk-ant-api03-[0-9a-zA-Z_-]{90,}` |
| `sk-proj-...` | OpenAI project key | `sk-proj-[0-9a-zA-Z_-]{20,}` |
| `ghp_...` | GitHub PAT | `ghp_[0-9a-zA-Z]{36}` |
| `AKIA...` | AWS access key | `AKIA[0-9A-Z]{16}` |
| `xoxb-...` | Slack bot token | `xox[bpas]-[0-9a-zA-Z-]+` |
| `ATATT3x...` | Atlassian/Jira token | `ATATT3x[0-9a-zA-Z_-]{20,}` |
| `hf_...` | Hugging Face | `hf_[0-9a-zA-Z]{30,}` |
| Long random strings (20+ chars) | Generic secrets | Strings with high entropy in assignments |

#### Additional Credential Patterns

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

### Step 2: Verify .gitignore Coverage

Ensure sensitive files are properly ignored:

```bash
# Check .gitignore exists and covers sensitive files
cat .gitignore | grep -E "\.env|config\.yaml|credentials|\.key|\.pem"

# Check if any sensitive files are tracked
git ls-files | grep -E "\.env|credentials|secret|\.key|\.pem"

# Check if any data files with potential PII are tracked
git ls-files | grep -E "\.csv|\.parquet|\.xlsx" | head -10
```

### Step 3: Check .env Files

```bash
# Verify .env.example exists (template without real values)
ls .env.example 2>/dev/null

# Check .env is not committed
git status --porcelain .env 2>/dev/null

# Check git history for accidentally committed secrets
git log --all --full-history -- "*.env" --oneline | head -5
```

### Step 4: Review Config Files

Check configuration files for embedded secrets:

- `config.yaml` / `config.yml` — should reference env vars, not inline secrets
- `*.json` config files — check for tokens or keys
- Jupyter notebooks (`.ipynb`) — check cell outputs for leaked credentials
- `.mcp.json` — check for hardcoded MCP server credentials

### Step 5: Check Python Code Patterns

Look for insecure patterns:

| Pattern | Issue | Severity | Fix |
|---------|-------|----------|-----|
| `os.getenv("KEY", "actual-key")` | Default value is a real key | CRITICAL | Use `os.getenv("KEY")` with no default |
| `requests.get(url, verify=False)` | SSL verification disabled | HIGH | Remove `verify=False` |
| `pickle.load(f)` | Arbitrary code execution | HIGH | Use `json.load()` where possible |
| `yaml.load(f)` without `Loader` | Arbitrary code execution | HIGH | Use `yaml.safe_load(f)` |
| `eval()` / `exec()` | Code injection | CRITICAL | Avoid; use `ast.literal_eval()` if needed |
| `compile()` with user input | Code injection | CRITICAL | Avoid dynamic compilation |
| `subprocess.shell=True` | Command injection | HIGH | Use `subprocess.run(["cmd", "arg"])` |
| `os.system()` | Command injection | HIGH | Use `subprocess.run()` |
| `hashlib.md5()` / `hashlib.sha1()` | Weak cryptography | MEDIUM | Use `hashlib.sha256()` or stronger |
| `random.random()` for security | Predictable randomness | HIGH | Use `secrets` module |
| `tempfile.mktemp()` | Race condition | MEDIUM | Use `tempfile.mkstemp()` |

### Step 6: LLM-Specific Security Checks

For projects that send data to LLM APIs (Gemini, OpenAI, etc.):

| Pattern | Issue | Severity | Fix |
|---------|-------|----------|-----|
| Sending raw user data to LLM without sanitization | PII leakage | HIGH | Sanitize PII before sending (names, emails, IDs) |
| `model.generate_content(user_input)` without validation | Prompt injection | MEDIUM | Validate and sanitize inputs |
| Executing LLM-generated code (`eval(response.text)`) | Code injection | CRITICAL | Never execute LLM output as code |
| Logging full LLM responses with sensitive data | Data leakage | MEDIUM | Redact sensitive fields in logs |
| No rate limiting on LLM API calls | Cost/abuse risk | MEDIUM | Add rate limits or circuit breakers |
| Storing LLM responses with PII to disk | Data retention | MEDIUM | Redact PII before saving |

#### Checks for LLM data pipelines:

```bash
# Check if raw PII fields are sent to LLM prompts
grep -rn --include="*.py" -E "(email|phone|ssn|address|salary)" . --exclude-dir=.git --exclude-dir=__pycache__ | grep -i "prompt\|generate_content\|completion"

# Check for eval/exec on LLM output
grep -rn --include="*.py" -E "(eval|exec)\s*\(\s*(response|result|output|completion)" . --exclude-dir=.git
```

## Output Format

Report findings by severity:

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
