# GitHub + Render Deployment Summary

## Current Deployment Shape

- Flask remains the only backend service entrypoint.
- `/` redirects to `/screensaver/index.html` so the cinematic bundle keeps its relative asset paths intact.
- `/screensaver/<path:path>` serves the static screensaver bundle directly from the repository.
- Legacy public UI paths now redirect to the cinematic entrypoint instead of rendering Jinja templates.

## Key Runtime Files

```text
pulse-of-humanity/
├── app.py
├── population.py
├── config.py
├── requirements.txt
├── render.yaml
├── gunicorn.conf.py
├── start.sh
├── validate_env.py
├── security_audit.py
└── screensaver/
    ├── index.html
    ├── src/
    ├── styles/
    ├── assets/
    └── vendor/
```

## Render Configuration Notes

- Keep `PORT=10000` unless Render overrides it.
- Set `RUN_UPDATER=1` in production if the annual anchor refresher should run.
- Set `FLASK_SECRET_KEY` in production.
- `ADMIN_REANCHOR_TOKEN` remains optional and only affects `POST /admin/reanchor`.

## Verification Commands

Run these before deployment or after a cleanup pass:

```bash
python validate_env.py
python security_audit.py
gunicorn --config gunicorn.conf.py app:app
curl -I http://localhost:10000/
curl -I http://localhost:10000/screensaver/index.html
curl http://localhost:10000/health
```

## Expected Results

- `GET /` returns `302` with `Location: /screensaver/index.html`.
- `GET /screensaver/index.html` returns `200`.
- `GET /pulse`, `/home`, `/about`, `/contact`, `/privacy`, and `/screensaver` all redirect to `/screensaver/index.html`.
- `GET /health` returns `200` and the API endpoints continue to serve JSON.