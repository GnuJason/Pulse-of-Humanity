# Project Guidelines

## Architecture
- The application is a small Flask service centered in `app.py`; routes, background update logic, and large inline templates live there today, so prefer focused edits over framework-level rewrites.
- Runtime state is persisted in `state.json`. Treat it as generated application data, not as source to edit unless the task explicitly requires it.
- Environment parsing and validation helpers live in `config.py`. Keep environment variable names aligned with `render.yaml`, `start.sh`, and `validate_env.py`.

## Build And Validation
- Create a local environment with `python3 -m venv venv` and `source venv/bin/activate`.
- Install dependencies with `pip install -r requirements.txt`.
- Run locally with `python app.py`.
- Use `gunicorn --config gunicorn.conf.py app:app` when checking deployment parity.
- Use `python validate_env.py` for environment validation and `python security_audit.py` for security-related checks.

## Conventions
- Preserve the existing Render deployment assumptions: `PORT` defaults to `10000`, and `RUN_UPDATER=1` enables the background updater loop.
- When modifying contact form or request handling code, keep CSRF protection, rate limiting, and HTTPS redirect behavior intact unless the task explicitly changes those requirements.
- Prefer small, low-risk changes in `app.py`; only extract helpers when it clearly reduces complexity.
- Do not edit `.env`, secrets, or generated runtime files unless the user asks for that specifically.
- If documentation conflicts with code, trust `app.py`, `config.py`, `render.yaml`, and `gunicorn.conf.py` first. The current `README.md` contains duplicated and stale sections.