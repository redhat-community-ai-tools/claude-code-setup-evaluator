---
name: python-conventions
version: "1.0"
description: Team-specific Python conventions — credential management with dotenv, API client rules, LLM response parsing, TDD workflow, and testing patterns for data pipelines.
---

# Python Conventions — Team Patterns

## When to Activate

- When writing code that uses environment variables or credentials
- When creating or modifying `.env` files
- When writing tests or following TDD
- When building or modifying code that calls external APIs (GitHub, Stripe, LDAP)
- When reviewing code that handles HTTP responses or LLM output

## Credential Management

### Loading Pattern

```python
from pathlib import Path
from dotenv import load_dotenv

# Load from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# No default for secrets (fail if missing)
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not set in .env file")
    sys.exit(1)

# Optional values can have defaults
model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
```

### Rules

- **Never** use real values as defaults: `os.getenv("KEY", "AIza...")` exposes the key
- **Always** create `.env.example` with placeholders, add `.env` to `.gitignore`
- **Load early** — `load_dotenv()` at entry points, not deep in utility code
- **Validate required vars** — fail fast if missing

## API Clients

Claude already knows retry logic, pagination, and auth patterns. These are team-specific rules:

1. **Always set timeouts** — no request should hang indefinitely (`timeout=30`)
2. **Retry transient failures only** — 429, 500, 502, 503, 504, connection errors
3. **Don't retry permanent failures** — 400, 401, 403, 404, 422
4. **Validate responses before accessing fields** — check structure, not just status code
5. **Log method, URL (without secrets), status code, duration** — never log full response bodies

### LLM Response Parsing

LLM outputs often include markdown fences that break JSON parsing. Always clean before parsing:

```python
import json

def clean_llm_response(text):
    for prefix in ("```markdown", "```json", "```"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text

def parse_llm_json(text):
    text = clean_llm_response(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logging.error(f"LLM returned invalid JSON: {text[:200]}")
        return None
```

### API Anti-Patterns

| Anti-Pattern | Do This Instead |
|-------------|-----------------|
| No timeout on requests | Always `timeout=30` |
| Retrying 401/403 | Only retry transient errors |
| `verify=False` | Fix the cert or use proper CA bundle |
| Logging full responses | Log status code + item count only |
| String concatenation for URLs | Use `urllib.parse.urljoin` or params dict |
| Catching all exceptions | Catch specific: `requests.exceptions.*` |

## Testing

### TDD Cycle

**RED** (write failing test) → **GREEN** (minimal code to pass) → **REFACTOR** (improve while green). Target 80%+ coverage.

### Testing Patterns

```python
# DataFrame testing
import pandas.testing as tm

def test_feature_engineering():
    input_df = pd.DataFrame({"price": [100, 200], "quantity": [2, 3]})
    result = add_total_column(input_df)
    expected = pd.DataFrame({"price": [100, 200], "quantity": [2, 3], "total": [200, 600]})
    tm.assert_frame_equal(result, expected)
```

```python
# Model reproducibility
def test_model_reproducibility(sample_df):
    model_1 = train_model(sample_df, random_state=42)
    model_2 = train_model(sample_df, random_state=42)
    X = sample_df[["feature_1"]]
    assert (model_1.predict(X) == model_2.predict(X)).all()
```

### Rules

- **Test behavior, not internals** — assert outputs, not private attributes
- **Independent tests** — each test sets up its own data
- **Always set random seeds** — `random_state=42` for reproducibility
- **Test edge cases** — None, empty DataFrame, NaN, inf
- **Mock external APIs** — never hit real GitHub/Stripe/LDAP in unit tests
