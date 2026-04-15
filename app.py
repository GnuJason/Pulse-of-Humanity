import os
import secrets
from datetime import datetime, timezone

from flask import (
    Flask, jsonify, render_template, make_response,
    request, flash, redirect, session,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect

from population import (
    BASE_CONTINENTS, BIRTHS_PER_SEC, DEATHS_PER_SEC, NET_PER_SEC,
    STATE_PATH, STATE_LOCK, STATE_SCHEMA_VERSION,
    _CACHE, CACHE_TTL, SYNC_INTERVAL_SECONDS,
    get_population_api, get_population_worldometer, get_population_cached,
    utc_now, isoformat_z, parse_timestamp, midnight_utc,
    normalize_named_distribution, build_share_model, canonicalize_share_state,
    reconcile_integer_distribution, reanchor_continent_shares,
    build_initial_state, migrate_state, ensure_state_shape,
    calculate_current_state, serialize_current_state,
    updater_loop, start_updater, current_population_and_today,
)
import population as _pop_module

from forms import ContactForm, generate_captcha, send_contact_email


def _sync_to_pop():
    """Sync app-level references to the population module (supports test patching)."""
    _pop_module.STATE_PATH = STATE_PATH
    _pop_module.get_population_cached = get_population_cached


def load_state():
    _sync_to_pop()
    return _pop_module.load_state()


def save_state(state):
    _sync_to_pop()
    return _pop_module.save_state(state)


def get_current_state(now=None):
    _sync_to_pop()
    return _pop_module.get_current_state(now=now)


def refresh_population_baseline(force=False, now=None):
    _sync_to_pop()
    return _pop_module.refresh_population_baseline(force=force, now=now)

UPDATER_ENABLED = os.getenv("RUN_UPDATER", "0") == "1"

app = Flask(__name__)

# Configuration
secret_key = os.getenv('FLASK_SECRET_KEY')
if not secret_key:
    secret_key = secrets.token_hex(32)
    print('[WARN] FLASK_SECRET_KEY not set — using random key (sessions won\'t survive restarts)')
app.config['SECRET_KEY'] = secret_key
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF tokens don't expire

# Initialize extensions
csrf = CSRFProtect(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

API_KEY = os.getenv("API_NINJAS_KEY")
DEBUG = os.getenv("FLASK_DEBUG") == "1"
PORT = int(os.getenv("PORT", "10000"))  # Default to 10000 for Render

@app.before_request
def force_https():
    """Redirect HTTP requests to HTTPS in production environments only."""
    # Only redirect to HTTPS if:
    # 1. Not in debug mode AND
    # 2. Not localhost/127.0.0.1 (for local testing) AND  
    # 3. Request is HTTP AND
    # 4. Has a valid endpoint
    if (not DEBUG and 
        request.endpoint and 
        request.url.startswith('http://') and
        not any(host in request.host for host in ['localhost', '127.0.0.1', '0.0.0.0'])):
        # Get the HTTPS version of the URL
        https_url = request.url.replace('http://', 'https://', 1)
        return redirect(https_url, code=301)

@app.after_request
def add_security_headers(resp):
    csp = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
        "style-src 'self' https://fonts.googleapis.com https://cdn.tailwindcss.com 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "form-action 'self'"
    )
    resp.headers["Content-Security-Policy"] = csp
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    resp.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    
    # Prevent browser caching for dynamic content
    if request.endpoint in ['index', 'population']:
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    
    return resp

LIVE_STATE_LIMIT = "120 per minute; 5000 per hour"

@app.route("/")
def index():
  try:
    state = serialize_current_state(get_current_state())
    return render_template(
      'index.html',
      population=state["population"],
      births_today=state["births_today"],
      deaths_today=state["deaths_today"],
      last_updated=state["last_updated"],
      continents_json=state["continents"]
    )
  except Exception as e:
    print(f"[ERROR] Index route failed: {e}")
    fallback_continents = {
      name: {
        "population": data["population"],
        "births_today": 0,
        "deaths_today": 0,
        "births_per_sec": data["births_per_sec"],
        "deaths_per_sec": data["deaths_per_sec"]
      }
      for name, data in BASE_CONTINENTS.items()
    }
    return render_template(
      'index.html',
      population=8000000000,
      births_today=372000,
      deaths_today=155000,
      last_updated="Fallback data - service initializing",
      continents_json=fallback_continents
    )

@app.route("/population")
def population():
    state = serialize_current_state(get_current_state())
    pop = state["population"]
    src = state["source"]
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if src == "api_ninjas":
        print(f"[{ts}] [INFO] Using API Ninjas data: {pop:,}")
    elif src == "worldometer":
        print(f"[{ts}] [INFO] Using Worldometer fallback: {pop:,}")
    else:
        print(f"[{ts}] [WARN] Both sources failed — using hardcoded fallback: {pop:,}")
    return jsonify({"population": pop, "source": src, "cached": True, "last_updated": state["last_updated"]})


@app.route("/api/live-state")
@limiter.limit(LIVE_STATE_LIMIT, override_defaults=True)
def live_state():
    return jsonify(serialize_current_state(get_current_state()))

@app.route("/contact", methods=["GET", "POST"])
@limiter.limit("5 per hour")  # Rate limit for contact form
def contact():
    form = ContactForm()
    
    # Generate captcha for GET requests
    if request.method == "GET":
        captcha_question, captcha_answer = generate_captcha()
        session['captcha_answer'] = captcha_answer
        session['captcha_question'] = captcha_question
    
    # Get current captcha question
    captcha_question = session.get('captcha_question', '1 + 1')
    
    if request.method == "POST" and form.validate_on_submit():
        # Validate captcha
        captcha_valid = False
        if 'captcha_answer' in session and form.captcha_answer.data is not None:
            captcha_valid = form.captcha_answer.data == session['captcha_answer']
        
        if not captcha_valid:
            flash('Incorrect captcha answer. Please try again.', 'error')
            # Generate new captcha
            captcha_question, captcha_answer = generate_captcha()
            session['captcha_answer'] = captcha_answer
            session['captcha_question'] = captcha_question
        else:
            # All validation passed, send email
            name = form.name.data.strip()
            email = form.email.data.strip()
            message = form.message.data.strip()
            
            success, result = send_contact_email(name, email, message)
            
            if success:
                flash('Thank you for your message! We\'ll get back to you soon.', 'success')
                # Clear form and generate new captcha
                form = ContactForm()
                captcha_question, captcha_answer = generate_captcha()
                session['captcha_answer'] = captcha_answer
                session['captcha_question'] = captcha_question
            else:
                flash('Sorry, there was an error sending your message. Please try again later.', 'error')
                # Keep the same captcha since we want user to retry
    elif request.method == "POST":
        # Form validation failed, generate new captcha
        captcha_question, captcha_answer = generate_captcha()
        session['captcha_answer'] = captcha_answer
        session['captcha_question'] = captcha_question
    
    return render_template(
        'contact.html',
        form=form,
        captcha_question=captcha_question
    )

@app.route("/health")
def health():
  """Enhanced health check endpoint for Render monitoring"""
  try:
    state = serialize_current_state(get_current_state())
    health_status = {
      "status": "healthy",
      "timestamp": datetime.now(timezone.utc).isoformat(),
      "version": "1.0.0",
      "population": int(state.get("population", 0)),
      "debug_mode": DEBUG
    }
    return jsonify(health_status), 200
  except Exception as e:
    return jsonify({
      "status": "unhealthy",
      "error": str(e),
      "timestamp": datetime.now(timezone.utc).isoformat()
    }), 500

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/robots.txt")
def robots_txt():
    """Serve robots.txt file allowing all crawlers"""
    # Get domain from environment or use default
    domain = os.getenv('DOMAIN', 'your-domain.com')
    
    robots_content = f"""User-agent: *
Allow: /

Sitemap: https://{domain}/sitemap.xml
"""
    response = make_response(robots_content)
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route("/sitemap.xml")
def sitemap_xml():
    """Serve XML sitemap with all public pages"""
    from datetime import datetime
    
    # Get domain from environment or use default
    domain = os.getenv('DOMAIN', 'your-domain.com')
    
    # Get current date in ISO format for lastmod
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://{domain}/</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://{domain}/about</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://{domain}/privacy</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>
    <url>
        <loc>https://{domain}/contact</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>"""
    
    response = make_response(sitemap_content)
    response.headers['Content-Type'] = 'application/xml'
    return response

if __name__ == "__main__":
    if UPDATER_ENABLED:
      print("[INFO] Starting updater loop (RUN_UPDATER=1)")
      start_updater()
    else:
      print("[INFO] Skipping updater loop (RUN_UPDATER not set to 1)")

    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)