---
name: data-pipeline-patterns
version: "1.0"
description: Patterns for building, debugging, and validating data pipelines in Python. Covers stage design, data validation, error handling, JSON/YAML schemas, API boundary checks, and pipeline debugging workflows.
---

# Data Pipeline Patterns

Best practices for building robust Python data pipelines that fetch, transform, and analyze data from APIs and files.

## When to Activate

- Building or modifying data pipeline stages
- Debugging pipeline failures (empty data, schema mismatches, API errors)
- Adding new data sources or API integrations
- Validating intermediate data files (JSON, YAML, CSV)
- Reviewing pipeline code

## Pipeline Stage Design

### Standard Stage Structure

Every pipeline stage should follow this pattern:

```python
def main(argv=None):
    """Stage entry point — parseable from CLI and callable from pipeline."""
    args = parse_args(argv)

    # 1. Load input
    input_data = load_json_file(Path(args.file))
    if input_data is None:
        sys.exit(1)

    # 2. Validate input
    if not validate_json_structure(input_data, ["required_key"], "Input file"):
        sys.exit(1)

    # 3. Process
    result = process(input_data)

    # 4. Save output with metadata
    output = {
        "metadata": {
            "source_file": str(args.file),
            "generated_at": datetime.now().isoformat(),
            "items_processed": len(result),
        },
        "data": result
    }
    save_json_file(output, output_path)
```

### Key Principles

- **Each stage is independently runnable** — both from CLI and as imported function
- **Input validation first** — check required keys, types, and non-empty data before processing
- **Metadata in every output** — source file, timestamp, counts for debugging
- **Fail fast** — exit immediately on invalid input, don't process partial data
- **Checkpoint on long operations** — save progress every N items for resumability

## Data Validation Patterns

### At Pipeline Boundaries

Always validate data when it crosses a boundary (API response, file load, stage input):

```python
# Validate JSON structure has required keys
def validate_input(data: dict, required_keys: list, context: str) -> bool:
    missing = [k for k in required_keys if k not in data]
    if missing:
        logging.error(f"{context} missing required keys: {missing}")
        return False
    return True

# Validate list is not empty
def validate_non_empty(items: list, context: str) -> bool:
    if not items:
        logging.warning(f"{context}: empty list — nothing to process")
        return False
    return True
```

### Data Shape Checks

```python
# Check expected types
assert isinstance(data.get("items"), list), "items must be a list"
assert all("key" in item for item in data["items"]), "all items must have 'key'"

# Check for unexpected nulls
null_count = sum(1 for item in items if item.get("critical_field") is None)
if null_count > 0:
    logging.warning(f"{null_count}/{len(items)} items missing critical_field")
```

## API Boundary Patterns

### Request Handling

```python
import requests
from time import sleep

def fetch_with_retry(url, headers, max_retries=3, backoff=2):
    """Fetch URL with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Rate limited
                wait = backoff ** attempt
                logging.warning(f"Rate limited, waiting {wait}s...")
                sleep(wait)
                continue
            raise
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                sleep(backoff ** attempt)
                continue
            raise
    return None
```

### Response Validation

```python
# Always check response structure before using
data = response.json()

# Check for API error responses
if "error" in data:
    logging.error(f"API error: {data['error']}")
    return None

# Check pagination completeness
total = data.get("total", 0)
received = len(data.get("items", []))
if received < total:
    logging.warning(f"Received {received}/{total} items — pagination may be needed")
```

## Debugging Pipeline Failures

### Systematic Debug Workflow

When a pipeline stage fails:

1. **Check the input file** — does it exist? Is it valid JSON? Does it have the expected keys?
2. **Check the metadata** — when was the input generated? By which stage?
3. **Check data shape** — how many items? Any empty lists? Unexpected nulls?
4. **Check API responses** — are credentials valid? Is the service up? Rate limited?
5. **Check intermediate state** — if checkpoints exist, where did it stop?

### Common Pipeline Failures

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Empty output file | Input had no matching items | Check filters, validate input data |
| Missing keys in output | Schema changed upstream | Update validation, check input stage |
| API timeout | Service overloaded or VPN down | Add retry logic, check connectivity |
| Rate limit errors (429) | Too many API calls | Add backoff, reduce batch size |
| Partial output | Stage crashed mid-processing | Add checkpointing, circuit breaker |
| Wrong data types | API returned unexpected format | Add type validation at boundaries |
| Duplicate items | Pagination overlap | Deduplicate by key field |

## Circuit Breaker Pattern

For stages that call external APIs (LLM, Jira, etc.):

```python
consecutive_failures = 0
max_failures = 5

for item in items:
    try:
        result = process_item(item)
        consecutive_failures = 0  # Reset on success
    except Exception as e:
        consecutive_failures += 1
        logging.warning(f"Failure {consecutive_failures}/{max_failures}: {e}")
        if consecutive_failures >= max_failures:
            logging.error("Circuit breaker triggered — saving progress")
            break
```

## JSON Data File Conventions

- All output files include `metadata` dict + `data` (list or dict)
- Metadata always has: `source_file`, `generated_at`, count fields
- Use `_` prefix for derived/computed fields
- Dates as ISO 8601 strings (`2026-03-15T10:00:00`)
- Save with `indent=2` and `ensure_ascii=False`

## Anti-Patterns to Avoid

- **Processing without validation** — always check input before transforming
- **Swallowing errors** — never `except: pass` in pipeline stages
- **Hardcoded file paths** — use arguments or config, never absolute paths
- **No logging** — every stage should log what it's doing and how many items
- **Monolithic stages** — if a stage does 3 things, split it into 3 stages
- **Missing metadata** — every output file should be self-describing
