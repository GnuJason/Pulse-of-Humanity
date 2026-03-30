---
description: "Initialize work on this Pulse of Humanity repo by inspecting architecture, commands, env vars, and deployment assumptions"
name: "Project Init"
argument-hint: "Current task or area to focus on"
agent: "agent"
---
Inspect this repository and produce a concise initialization brief.

If the user provided a focus area in the chat request, tailor the brief to that area. Otherwise, provide a general repo initialization summary.

Use the codebase as the source of truth, especially:
- [app.py](../../app.py)
- [config.py](../../config.py)
- [requirements.txt](../../requirements.txt)
- [render.yaml](../../render.yaml)
- [gunicorn.conf.py](../../gunicorn.conf.py)
- [validate_env.py](../../validate_env.py)
- [README.md](../../README.md)
- [DEPLOYMENT.md](../../DEPLOYMENT.md)

Your response should:
1. Summarize the app structure and main entry points.
2. List the most relevant local run, validation, and deployment commands.
3. Call out required environment variables and generated/runtime files.
4. Note any meaningful conflicts between documentation and actual code.
5. End with a short plan tailored to the current task.

Keep the summary practical and brief. Prefer current runtime files over docs when they disagree.