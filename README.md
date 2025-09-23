# Pulse of Humanity

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A real-time world population visualization Flask web application that displays the current global population with live updates and interactive features.

## Features

- **Real-time Population Counter**: Live-updating world population display with smooth animations
- **Interactive World Map**: Visualize global demographic data with interactive geographic components using embedded SVG
- **Contact Form**: Professional contact system with:
  - Server-side validation (Flask-WTF)
  - Math captcha spam protection
  - Rate limiting (5 submissions per hour per IP)
  - SMTP email integration via Mailfence
  - CSRF protection and security headers
  - Accessibility-compliant design
- **Security Features**:
  - HTTPS redirect (production mode)
  - Comprehensive security headers
  - Rate limiting with Flask-Limiter
  - CSRF protection
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Embedded SVG World Map**: Interactive continent-based visualization

## Technology Stack

- **Backend**: Flask 3.x with Python
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Email**: SMTP integration (Mailfence)
- **Security**: Flask-WTF, Flask-Limiter, comprehensive headers
- **Visualization**: Embedded SVG world map with interactive continents
- **Deployment**: Gunicorn-ready with environment configuration

## Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- SMTP email account (for contact form)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pulse-of-humanity
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Configure environment variables** in `.env`:
   ```env
   # Flask Configuration
   SECRET_KEY=your-super-secret-key-here
   FLASK_ENV=development

   # SMTP Configuration
   SMTP_SERVER=mail.mailfence.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@mailfence.com
   SMTP_PASSWORD=your-app-password
   SMTP_FROM_EMAIL=your-email@mailfence.com
   CONTACT_TO_EMAIL=your-email@mailfence.com
   ```

### Running the Application

**Development mode**:
```bash
python app.py
```

**Production mode with Gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

The application will be available at `http://localhost:5000` (development) or `http://localhost:8000` (production).

## Deployment

### Environment Variables for Production

Set the following environment variables in your production environment:

- `SECRET_KEY`: Strong secret key for Flask sessions
- `FLASK_ENV`: Set to `production`
- `SMTP_SERVER`: Your SMTP server hostname
- `SMTP_PORT`: SMTP port (usually 587 for TLS)
- `SMTP_USERNAME`: Your SMTP username
- `SMTP_PASSWORD`: Your SMTP password or app-specific password
- `SMTP_FROM_EMAIL`: From email address
- `CONTACT_TO_EMAIL`: Email address to receive contact form submissions

### Production Deployment Options

**Docker** (recommended):
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

**Traditional Server**:
- Use a reverse proxy (nginx) to handle HTTPS
- Configure firewall for ports 80/443
- Set up SSL certificates (Let's Encrypt recommended)
- Use process manager (systemd/supervisor) for auto-restart

## Contact Form Features

The contact form includes advanced features:

- **Validation**: Server-side validation for all fields
- **Security**: CSRF protection, rate limiting, math captcha
- **Accessibility**: ARIA labels, semantic HTML, keyboard navigation
- **Responsive**: Mobile-optimized with Tailwind CSS
- **Email Integration**: Professional HTML email formatting

## API Endpoints

- `GET /` - Main population visualization page
- `GET /api/population` - JSON API for current population data
- `GET /contact` - Contact form page
- `POST /contact` - Submit contact form

## Security Features

- HTTPS redirect in production mode
- Comprehensive security headers (CSP, HSTS, X-Frame-Options, etc.)
- Rate limiting on contact form (5 submissions per hour per IP)
- CSRF protection on all forms
- Math captcha for spam prevention
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Flask Community**: For the excellent web framework and extensions
- **Tailwind CSS**: For the utility-first CSS framework
- **World Map Data**: Interactive SVG world map for geographic visualizations

## Support

For support, please use the contact form on the website or open an issue on GitHub.

---

*Pulse of Humanity - Visualizing our shared human experience through data*
