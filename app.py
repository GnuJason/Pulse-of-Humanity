import json
import os
import secrets
import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, make_response, request, redirect, render_template, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect

from population import (
    BASE_CONTINENTS,
    BIRTHS_PER_SEC,
    DEATHS_PER_SEC,
    STATE_PATH,
    STATE_SCHEMA_VERSION,
    _CACHE,
    build_initial_state,
    calculate_current_state,
    get_authoritative_state,
    get_current_state,
    get_live_state_contract,
    parse_timestamp,
    refresh_population_baseline,
    serialize_continent_model,
    serialize_current_state,
    serialize_live_state_contract,
    start_updater,
    utc_now,
)
import population as _pop_module

def _sync_to_pop():
    """Sync app-level references to the population module (supports test patching)."""
    _pop_module.STATE_PATH = STATE_PATH


def load_state():
    _sync_to_pop()
    return _pop_module.load_state()


def save_state(state):
    _sync_to_pop()
    return _pop_module.save_state(state)


def get_current_state(now=None):
    _sync_to_pop()
    return _pop_module.get_current_state(now=now)


def get_authoritative_state(now=None):
    _sync_to_pop()
    return _pop_module.get_authoritative_state(now=now)


def get_live_state_contract(now=None):
    _sync_to_pop()
    return _pop_module.get_live_state_contract(now=now)


def refresh_population_baseline(force=False, now=None, target_year=None):
    _sync_to_pop()
    return _pop_module.refresh_population_baseline(force=force, now=now, target_year=target_year)

UPDATER_ENABLED = os.getenv("RUN_UPDATER", "0") == "1"
BOOTSTRAP_LOCK = threading.Lock()
BUILD_ID = str(int(time.time()))
VERSION_PATH = os.path.join(os.path.dirname(__file__), "VERSION")
RELEASES_DIR = os.path.join(os.path.dirname(__file__), "dist", "releases")


def read_app_version():
    with open(VERSION_PATH, encoding="utf-8") as version_file:
        return version_file.read().strip()


def read_release_manifest():
    manifest_path = os.path.join(RELEASES_DIR, "artifact-manifest.json")
    if not os.path.exists(manifest_path):
        return None

    with open(manifest_path, encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def release_month_label():
    ts = os.path.getmtime(VERSION_PATH)
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%B %Y")


def artifact_href(relative_path):
    return "/" + relative_path.replace(os.sep, "/")


def artifact_exists(relative_path):
    return os.path.exists(os.path.join(app.root_path, relative_path))


def bootstrap_population_system():
    """Start the baseline refresher in local runs and Gunicorn workers."""
    _sync_to_pop()
    if not UPDATER_ENABLED:
        return False

    with BOOTSTRAP_LOCK:
        return start_updater()

app = Flask(__name__)


@app.context_processor
def inject_build_id():
    return {"build_id": BUILD_ID}

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

DEBUG = os.getenv("FLASK_DEBUG") == "1"
PORT = int(os.getenv("PORT", "10000"))  # Default to 10000 for Render
ADMIN_REANCHOR_TOKEN = os.getenv("ADMIN_REANCHOR_TOKEN")

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
        "script-src 'self' data: https://unpkg.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' data:; "
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

    return resp

LIVE_STATE_LIMIT = "120 per minute; 5000 per hour"

@app.route("/pulse")
def pulse_redirect():
    return redirect("/screensaver/index.html", code=302)


@app.route("/home")
def home_redirect():
    return redirect("/screensaver/index.html", code=302)

@app.route("/")
def root_redirect():
    return screensaver_download()

@app.route("/population")
def population():
    state = serialize_current_state(get_current_state())
    pop = state["population"]
    src = state["source"]
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"[{ts}] [INFO] Using static annual anchor source {src}: {pop:,}")
    return jsonify({"population": pop, "source": src, "cached": True, "last_updated": state["last_updated"]})


@app.route("/api/live-state")
@limiter.limit(LIVE_STATE_LIMIT, override_defaults=True)
def live_state():
    return jsonify(get_live_state_contract())


@app.route("/admin/reanchor", methods=["POST"])
@csrf.exempt
@limiter.limit("10 per hour")
def admin_reanchor():
    if not ADMIN_REANCHOR_TOKEN:
        return jsonify({"error": "admin re-anchor token not configured"}), 503

    provided_token = request.headers.get("X-Admin-Token")
    if not provided_token or not secrets.compare_digest(provided_token, ADMIN_REANCHOR_TOKEN):
        return jsonify({"error": "forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    target_year = payload.get("year")
    if target_year is not None:
        try:
            target_year = int(target_year)
        except (TypeError, ValueError):
            return jsonify({"error": "year must be an integer"}), 400

    refreshed = refresh_population_baseline(force=True, now=utc_now(), target_year=target_year)
    if not refreshed:
        return jsonify({"error": "re-anchor failed", "liveState": get_live_state_contract()}), 502

    return jsonify({
        "status": "ok",
        "anchor": get_live_state_contract(),
    })

@app.route("/contact", methods=["GET", "POST"])
def contact_redirect():
    return redirect("/screensaver/index.html", code=302)

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
def about_redirect():
    return redirect("/screensaver/index.html", code=302)

@app.route("/privacy")
def privacy_redirect():
    return redirect("/screensaver/index.html", code=302)


@app.route("/screensaver")
def screensaver_download():
    version_value = read_app_version()
    manifest = read_release_manifest() or {"generatedArtifacts": []}
    artifact_index = {item["key"]: item for item in manifest.get("generatedArtifacts", [])}

    windows_download = os.path.join(app.static_folder, "native", "windows", "PulseOfHumanity.scr")
    macos_download = os.path.join(app.static_folder, "native", "macos", "PulseOfHumanity.saver.zip")
    zip_download = os.path.join(app.static_folder, "screensaver.zip")
    versioned_zip = artifact_index.get("screensaverZip")
    versioned_windows = artifact_index.get("windowsScr")
    versioned_macos = artifact_index.get("macosSaverArchive")

    version = {
        "tag": f"v{version_value}",
        "number": version_value,
        "name": "Cinematic Earth",
        "released": release_month_label(),
    }

    downloads = {
        "windows": {
            "label": "Download Windows .scr",
            "href": artifact_href(versioned_windows["path"]) if versioned_windows else "#",
            "available": bool(versioned_windows and artifact_exists(versioned_windows["path"]) and os.path.exists(windows_download)),
            "meta": "Offline WebView2 wrapper",
        },
        "macos": {
            "label": "Download macOS .saver",
            "href": artifact_href(versioned_macos["path"]) if versioned_macos else "#",
            "available": bool(versioned_macos and artifact_exists(versioned_macos["path"]) and os.path.exists(macos_download)),
            "meta": "Offline ScreenSaver bundle",
        },
        "zip": {
            "label": "Download ZIP bundle",
            "href": artifact_href(versioned_zip["path"]) if versioned_zip else "#",
            "available": bool(versioned_zip and artifact_exists(versioned_zip["path"])),
            "meta": "Versioned universal offline bundle",
            "fallback_href": "/static/screensaver.zip",
            "fallback_available": os.path.exists(zip_download),
        },
        "browser": {
            "label": "Run in Browser",
            "href": "/screensaver/index.html",
            "available": True,
            "meta": "Launch the live cinematic map",
        },
    }

    instructions = {
        "windows": [
            "Download the .scr build and copy it into your Windows system or personal screensaver folder.",
            "Open Windows Screen Saver Settings and select Pulse of Humanity from the list.",
            "Use Preview to test the WebView2 wrapper, then apply to enable full-screen playback.",
        ],
        "macos": [
            "Download the .saver package and unzip it if your browser wraps the bundle in an archive.",
            "Double-click the .saver bundle or copy it into ~/Library/Screen Savers.",
            "Enable Pulse of Humanity in System Settings and use the built-in preview before saving.",
        ],
        "linux": [
            "Download the fallback ZIP and extract it anywhere local; no network access is required.",
            "Launch index.html in a kiosk-capable browser or your preferred screensaver host wrapper.",
            "For the cleanest result, run the browser in full-screen mode and point it at the bundled entry file.",
        ],
    }

    changelog = [
        "New cinematic download hub with OS-aware recommendations and browser launch path.",
        f"Versioned release presentation for {version['tag']} {version['name']}.",
        "Installation instructions for Windows, macOS, and Linux fallback deployments.",
    ]

    screenshots = [
        {
            "src": "/static/screensaver-preview.png",
            "alt": "Pulse of Humanity counter and map composition",
            "caption": "The live counter, net change ribbon, and equal-earth projection in motion.",
        },
        {
            "src": "/static/screensaver-cinematic-v2.png",
            "alt": "Pulse of Humanity version 2 cinematic map view",
            "caption": f"The {version['tag']} {version['name']} grade with deeper contrast and atmospheric glow.",
        },
    ]

    return render_template(
        "screensaver_download.html",
        version=version,
        downloads=downloads,
        instructions=instructions,
        changelog=changelog,
        screenshots=screenshots,
    )


@app.route("/dist/releases/<path:path>")
def release_artifacts(path):
    return send_from_directory(RELEASES_DIR, path)


@app.route("/screensaver/<path:path>")
def screensaver_static(path):
    """Serve the self-contained screensaver bundle from /screensaver/*."""
    return send_from_directory(
        os.path.join(app.root_path, "screensaver"), path
    )

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


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    if bootstrap_population_system():
        print("[INFO] Started annual anchor watcher (RUN_UPDATER=1)")
    else:
        print("[INFO] Skipping annual anchor watcher (RUN_UPDATER not set to 1 or already running)")

    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)