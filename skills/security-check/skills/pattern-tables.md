# Security Pattern Tables

## API Key Patterns to Detect

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

## Insecure Python Code Patterns

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

## LLM-Specific Security Patterns

| Pattern | Issue | Severity | Fix |
|---------|-------|----------|-----|
| Sending raw user data to LLM without sanitization | PII leakage | HIGH | Sanitize PII before sending (names, emails, IDs) |
| `model.generate_content(user_input)` without validation | Prompt injection | MEDIUM | Validate and sanitize inputs |
| Executing LLM-generated code (`eval(response.text)`) | Code injection | CRITICAL | Never execute LLM output as code |
| Logging full LLM responses with sensitive data | Data leakage | MEDIUM | Redact sensitive fields in logs |
| No rate limiting on LLM API calls | Cost/abuse risk | MEDIUM | Add rate limits or circuit breakers |
| Storing LLM responses with PII to disk | Data retention | MEDIUM | Redact PII before saving |
