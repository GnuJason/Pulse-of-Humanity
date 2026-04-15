# 🌍 Pulse of Humanity

A real-time world population visualization web application that displays live global population statistics with an interactive SVG world map, animated backgrounds, and mobile-responsive design.

![Status](https://img.shields.io/badge/Status-Live-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Real-time Population Counter** — Live-updating world population display with smooth easing animations
- **Interactive World Map** — Embedded SVG with per-continent population, births, and deaths data
- **Continental Breakdown** — Population statistics broken down by continent with hover/touch tooltips
- **VANTA.js Globe Background** — Animated 3D globe background for cinematic atmosphere
- **Contact Form** — Server-side validation, math captcha, rate limiting, CSRF protection, SMTP email integration
- **Mobile Responsive** — Touch-optimized with adaptive layouts for all screen sizes
- **Security** — HTTPS redirect, CSP headers, HSTS, rate limiting, input validation

## Quick Start

### Local Development

```bash
git clone https://github.com/GnuJason/pulse-of-humanity.git
cd pulse-of-humanity
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Edit with your configuration
python app.py
```

Open `http://localhost:10000` in your browser.

### Production (Gunicorn)

```bash
gunicorn --config gunicorn.conf.py app:app
```

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `FLASK_SECRET_KEY` | Flask session secret key (required in production) |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `10000` |
| `FLASK_DEBUG` | Debug mode | `0` |
| `RUN_UPDATER` | Enable background population sync | `1` |
| `API_NINJAS_KEY` | API Ninjas key for population data | — |
| `SMTP_SERVER` | SMTP server for contact form | `smtp.mailfence.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USERNAME` | SMTP username | — |
| `SMTP_PASSWORD` | SMTP password | — |
| `RECIPIENT_EMAIL` | Contact form recipient | — |
| `DOMAIN` | Production domain (for sitemap/robots) | `localhost:5000` |

## Technology Stack

- **Backend**: Python / Flask 3.x
- **Frontend**: HTML5, Tailwind CSS, vanilla JavaScript
- **Visualization**: Embedded SVG world map, VANTA.js 3D globe
- **Security**: Flask-WTF (CSRF), Flask-Limiter, comprehensive security headers
- **Deployment**: Gunicorn, Render-ready (`render.yaml` included)

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main population visualization |
| `GET /api/live-state` | JSON: current population, births, deaths, continent breakdown |
| `GET /population` | JSON: current population and source |
| `GET /health` | Health check for monitoring |
| `GET /contact` | Contact form |
| `GET /about` | About page |
| `GET /privacy` | Privacy policy |

## Development

```bash
# Environment validation
python validate_env.py

# Security audit
python security_audit.py

# Run tests
python -m pytest tests/
```

## Deployment (Render)

1. Fork this repository
2. Create a new Web Service on [Render](https://render.com) connected to your fork
3. Render will use the included `render.yaml` configuration
4. Set `FLASK_SECRET_KEY` and optional SMTP variables in the Render dashboard

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgments

- [API Ninjas](https://api-ninjas.com/) and [Worldometer](https://www.worldometers.info/) for population data
- [VANTA.js](https://www.vantajs.com/) for animated backgrounds
- [Tailwind CSS](https://tailwindcss.com/) for utility-first styling
- [Natural Earth](https://www.naturalearthdata.com/) for geographic data
