---
name: api-client-patterns
version: "1.0"
description: Patterns for building robust API clients in Python — retry logic, error handling, rate limiting, response validation, and LLM API integration. Covers REST APIs, Jira, LDAP, and LLM services (Gemini, OpenAI).
---

# API Client Patterns

Best practices for building reliable Python API clients that handle failures gracefully.

## When to Activate

- Building or modifying code that calls external APIs
- Adding new API integrations (REST, LLM, database)
- Debugging API failures (timeouts, rate limits, auth errors)
- Reviewing code that handles HTTP responses

## Core Principles

1. **Never hardcode credentials** — always `os.getenv()`, never defaults with real values
2. **Always set timeouts** — no request should hang indefinitely
3. **Retry transient failures** — 429, 500, 502, 503, 504, connection errors
4. **Don't retry permanent failures** — 400, 401, 403, 404, 422
5. **Validate responses** — check structure before accessing fields
6. **Log API calls** — method, URL (without secrets), status code, duration

## Retry with Exponential Backoff

```python
import requests
from time import sleep
import logging

TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

def api_request(method, url, max_retries=3, backoff_base=2, timeout=30, **kwargs):
    """Make an API request with retry logic."""
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)

            if response.status_code in TRANSIENT_STATUS_CODES:
                if attempt < max_retries:
                    # Use Retry-After header if available (common for 429)
                    wait = int(response.headers.get("Retry-After", backoff_base ** attempt))
                    logging.warning(f"HTTP {response.status_code}, retrying in {wait}s (attempt {attempt + 1})")
                    sleep(wait)
                    continue

            response.raise_for_status()
            return response

        except requests.exceptions.ConnectionError:
            if attempt < max_retries:
                wait = backoff_base ** attempt
                logging.warning(f"Connection error, retrying in {wait}s")
                sleep(wait)
                continue
            raise
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                logging.warning(f"Timeout, retrying (attempt {attempt + 1})")
                continue
            raise

    return None
```

## Response Validation

```python
def validate_response(response, required_keys=None, context="API"):
    """Validate API response structure."""
    try:
        data = response.json()
    except ValueError:
        logging.error(f"{context}: Response is not valid JSON")
        return None

    if isinstance(data, dict) and "error" in data:
        logging.error(f"{context}: API error — {data['error']}")
        return None

    if required_keys:
        missing = [k for k in required_keys if k not in data]
        if missing:
            logging.error(f"{context}: Missing keys {missing}")
            return None

    return data
```

## Authentication Patterns

```python
# Bearer token (Jira, most REST APIs)
headers = {
    "Authorization": f"Bearer {os.getenv('API_TOKEN')}",
    "Content-Type": "application/json",
}

# Basic auth (Jira Cloud with email + token)
from requests.auth import HTTPBasicAuth
auth = HTTPBasicAuth(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN"))

# API key in header (Gemini, OpenAI)
headers = {"X-API-Key": os.getenv("API_KEY")}

# Validate credentials exist before calling
def require_env(var_name):
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(f"Required environment variable {var_name} is not set")
    return value
```

## Rate Limiting

```python
from time import sleep, time

class RateLimiter:
    """Simple rate limiter for API calls."""
    def __init__(self, calls_per_second=2):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0

    def wait(self):
        elapsed = time() - self.last_call
        if elapsed < self.min_interval:
            sleep(self.min_interval - elapsed)
        self.last_call = time()

# Usage
limiter = RateLimiter(calls_per_second=5)
for item in items:
    limiter.wait()
    response = api_request("GET", url)
```

## LLM API Patterns

For Gemini, OpenAI, and other LLM services:

```python
# Configure with safety defaults
model = configure_gemini(api_key, model_name, max_output_tokens=2048)

# Always handle LLM-specific errors
try:
    response = model.generate_content(prompt)
    text = response.text.strip()
except Exception as e:
    if "quota" in str(e).lower() or "rate" in str(e).lower():
        logging.warning("LLM rate limit — backing off")
        sleep(10)
    else:
        logging.error(f"LLM error: {e}")
        return None
```

### LLM Response Parsing

```python
# Strip markdown fences from LLM output
def clean_llm_response(text):
    if text.startswith("```markdown"):
        text = text[len("```markdown"):].strip()
    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    if text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text

# Parse JSON from LLM (with fallback)
import json

def parse_llm_json(text):
    text = clean_llm_response(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logging.error(f"LLM returned invalid JSON: {text[:200]}")
        return None
```

## Pagination

```python
def fetch_all_pages(url, headers, page_size=100):
    """Fetch all pages from a paginated API."""
    all_items = []
    start = 0

    while True:
        params = {"startAt": start, "maxResults": page_size}
        response = api_request("GET", url, headers=headers, params=params)
        data = validate_response(response)
        if not data:
            break

        items = data.get("values", data.get("items", []))
        all_items.extend(items)

        # Check if we got all items
        total = data.get("total", len(items))
        if start + len(items) >= total or not items:
            break
        start += len(items)

    return all_items
```

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Do This Instead |
|-------------|-------------|-----------------|
| No timeout on requests | Hangs forever if API is down | Always set `timeout=30` |
| Retrying 401/403 | Will never succeed, wastes time | Only retry transient errors |
| `verify=False` | Disables SSL, man-in-the-middle risk | Fix the cert or use proper CA bundle |
| Logging full responses | Leaks sensitive data | Log status code + item count only |
| String concatenation for URLs | Injection risk, encoding bugs | Use `urllib.parse.urljoin` or params dict |
| Catching all exceptions | Hides bugs | Catch specific: `requests.exceptions.*` |
