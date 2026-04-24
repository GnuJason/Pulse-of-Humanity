# Contributing to Pulse of Humanity

Thanks for your interest in contributing! This guide covers how to set up a local environment, run tests, and submit changes.

## Getting Started

### Prerequisites

- Python 3.11 or later
- Git

### Local Setup

```bash
git clone https://github.com/GnuJason/Pulse-of-Humanity.git
cd Pulse-of-Humanity
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values as needed
```

### Running the App

```bash
python app.py
# Open http://localhost:10000
```

### Running Tests

```bash
python -m pytest tests/ -v
```

All 10 tests should pass before submitting a PR.

### Other Checks

```bash
python validate_env.py     # environment variable validation
python security_audit.py   # security audit
```

## Submitting Changes

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/my-change
   ```
2. Make your changes — keep commits focused and descriptive.
3. Run the test suite and confirm all tests pass.
4. **Push** your branch and open a **Pull Request** against `main`.
5. Describe what you changed and why in the PR description.

## Code Style

- Follow the existing patterns in the codebase.
- Keep `app.py` small — extract helpers into modules (`population.py`, `forms.py`, `config.py`) when it clearly reduces complexity.
- Use CSS variables from the design system in `base.html` rather than hardcoded colors.
- Tailwind CSS is compiled at build time — run `./tailwindcss-linux-x64 -i input.css -o static/css/main.css --minify` after changing templates.
- Preserve security controls (CSRF, rate limiting, HTTPS redirect, CSP) unless your change explicitly modifies them.

## Reporting Issues

Open a [GitHub Issue](https://github.com/GnuJason/Pulse-of-Humanity/issues) with:
- A clear title and description
- Steps to reproduce (if it's a bug)
- Expected vs. actual behavior

## License

By contributing you agree that your contributions will be licensed under the [GNU General Public License v3.0](LICENSE).
