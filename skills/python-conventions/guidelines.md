# Guidelines

## Credential Management — Hard Limits

- **NEVER** use real values as defaults: `os.getenv("KEY", "AIza...")` exposes the key
- **ALWAYS** create `.env.example` with placeholders
- **ALWAYS** add `.env` to `.gitignore`
- **Load early** — `load_dotenv()` at entry points, not deep in utility code
- **Fail fast** — exit immediately if required secrets are missing

## API Client — Hard Limits

- **ALWAYS** set `timeout=30` on all requests — no request should hang indefinitely
- **Retry only transient failures** — 429, 500, 502, 503, 504, connection errors
- **NEVER retry permanent failures** — 400, 401, 403, 404, 422
- **NEVER log full response bodies** — log method, URL, status code, duration only
- **Validate response structure** before accessing fields

## Testing — Requirements

- Target **80%+ coverage**
- **ALWAYS** set `random_state=42` for reproducibility
- **NEVER** hit real external APIs in unit tests — mock them
- Test behavior, not internals
- Each test sets up its own data (independent tests)
