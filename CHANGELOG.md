# Changelog

All notable changes to Pulse of Humanity are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Hero screenshot placeholder in `docs/` for README
- `CONTRIBUTING.md` with setup, testing, and PR guidelines
- This `CHANGELOG.md`
- GitHub topic tags in README

### Changed
- README rewritten with clean structure: badges, demo section, tech stack table, API reference, env var table
- License badge corrected from MIT to GPL v3

## [P3] — 2026-04-15

### Added
- Page-load motion choreography: `fadeIn`, `scaleIn`, staggered delay classes with cubic-bezier easing
- Typography scale system: `.heading-xl`, `.heading-lg`, `.heading-md`, `.heading-sm`, `.body-lg`, `.body-md`
- Atmospheric footer with gradient glow border and `backdrop-filter` blur
- `prefers-reduced-motion` support across all animations

### Changed
- Fonts replaced: Orbitron + Outfit → JetBrains Mono (display) + Instrument Sans (body)
- Color system unified: darker palette with `--bg-card`, `--bg-card-alt`, `--border-color`, `--accent-dim` variables
- All templates (`about.html`, `privacy.html`, `contact.html`) updated to use new typography scale and CSS variable colors
- Removed all hardcoded `text-gray-*` / `bg-gray-*` Tailwind classes from templates

## [P2] — 2026-04-15

### Added
- Compiled Tailwind CSS via standalone CLI (`tailwindcss-linux-x64` v3.4.1) — replaces CDN
- `input.css` and `tailwind.config.js` for build-time compilation
- Enter / Space keyboard activation on interactive SVG continent paths

### Changed
- CSP updated to remove `cdn.tailwindcss.com`
- Static CSS output at `static/css/main.css` (13 KB minified)

## [P1] — 2026-04-15

### Added
- `population.py` (485 lines) — extracted population model, state management, API sync
- `forms.py` (93 lines) — extracted WTForms contact form class
- `templates/base.html` — shared layout with design system variables
- `templates/index.html` — main page extracted from inline `app.py` template
- `templates/partials/world-map.svg` — accessible SVG with ARIA labels
- `templates/contact.html` — contact form page
- `.env.example` with correct SMTP defaults

### Changed
- `app.py` reduced from 1 377 → 326 lines
- `about.html` and `privacy.html` refactored to extend `base.html`

## [P0] — 2026-04-15

### Changed
- `.gitignore` updated with Python, environment, and editor patterns
- `README.md` initial cleanup pass

## [1.0.0] — 2025-09-22

### Added
- Real-time population counter with smooth easing animations
- Interactive SVG world map with per-continent tooltips
- VANTA.js animated 3D globe background
- Contact form with CSRF protection, math captcha, rate limiting, SMTP email
- Mobile-responsive design with touch-optimized interactions
- Security headers: HTTPS redirect, CSP, HSTS
- Gunicorn + Render deployment configuration (`render.yaml`, `start.sh`)
- Privacy policy and about pages
- Health check endpoint (`/health`)
- GNU GPL v3 license
