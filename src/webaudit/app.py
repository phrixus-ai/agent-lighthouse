"""AgentLighthouse Flask Application — AI & Agent Readiness Scanner"""

import os
import time
import sqlite3
import threading
from functools import wraps
from collections import defaultdict
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_compress import Compress
from dotenv import load_dotenv

load_dotenv()

from webaudit.auditor import WebAuditor


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("AGENTLIGHTHOUSE_SECRET_KEY", "dev-key-change-in-production")
    Compress(app)
    site_url = os.environ.get("SITE_URL", "")
    ga_id = os.environ.get("GA_MEASUREMENT_ID", "")

    # ── Scan Log DB ──
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "audits.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def get_db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                score INTEGER,
                level TEXT,
                total_checks INTEGER,
                passed INTEGER,
                warnings INTEGER,
                failed INTEGER,
                scanned_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    init_db()

    def log_scan(url, report):
        try:
            checks = report.get("checks", [])
            conn = get_db()
            conn.execute(
                "INSERT INTO scan_log (url, score, level, total_checks, passed, warnings, failed, scanned_at) VALUES (?,?,?,?,?,?,?,?)",
                (
                    url,
                    report.get("score", 0),
                    report.get("level", ""),
                    len(checks),
                    sum(1 for c in checks if c.get("status") == "pass"),
                    sum(1 for c in checks if c.get("status") == "warning"),
                    sum(1 for c in checks if c.get("status") == "fail"),
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ── Rate Limiter ──
    _rate_store = defaultdict(list)
    _rate_lock = threading.Lock()
    RATE_LIMIT = 5
    RATE_WINDOW = 60

    def check_rate_limit():
        client = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        now = time.time()
        with _rate_lock:
            _rate_store[client] = [t for t in _rate_store[client] if now - t < RATE_WINDOW]
            if len(_rate_store[client]) >= RATE_LIMIT:
                return False
            _rate_store[client].append(now)
        return True

    # ── Favicon route (browsers request /favicon.ico automatically) ──
    @app.route("/favicon.ico")
    def favicon_ico():
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), "static"),
            "favicon.png",
            mimetype="image/png",
        )

    @app.route("/")
    def index():
        remote = request.remote_addr or ""
        is_production = bool(site_url)
        accept = request.headers.get("Accept", "")
        if "text/markdown" in accept:
            su = site_url or "https://example.com"
            md = (
                "# AgentLighthouse\n\n"
                "> AI & Agent Readiness Scanner\n\n"
                "AgentLighthouse is a free, open-source tool that evaluates any website for AI and Agent Readiness.\n\n"
                "## Features\n\n"
                "- 40 audit checks across Modern Web Guidance, security headers, SEO, accessibility & performance\n"
                "- Score normalized to 0-100 with detailed breakdown\n"
                "- Structured data and semantic HTML validation\n"
                "- Security headers analysis (HSTS, CSP, X-Frame-Options, etc.)\n"
                "- llms.txt and llms-full.txt detection\n\n"
                f"## Try It\n\n"
                f"Visit [AgentLighthouse]({su}/) to scan any URL.\n"
                f"Or use the API: `POST {su}/api/audit` with `{{\"url\": \"https://example.com\"}}`\n\n"
                f"## Links\n\n"
                f"- [GitHub](https://github.com/phrixus-ai/agent-lighthouse)\n"
                f"- [llms.txt]({su}/llms.txt)\n"
                f"- [Full Docs]({su}/llms-full.txt)\n"
            )
            return md, 200, {"Content-Type": "text/markdown; charset=utf-8"}
        return render_template("index.html", site_url=site_url, is_production=is_production, ga_id=ga_id)

    @app.route("/api/audit", methods=["POST"])
    def audit():
        if not check_rate_limit():
            return jsonify({"error": "Rate limit exceeded. Max 5 audits per minute."}), 429

        data = request.get_json(silent=True) or {}
        url = data.get("url", "").strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400

        if not url.startswith("http"):
            url = "https://" + url

        if "." not in url:
            return jsonify({"error": "Invalid URL"}), 400

        try:
            auditor = WebAuditor(url)
            report = auditor.run()
            log_scan(url, report)
            return jsonify(report)
        except Exception as e:
            return jsonify({"error": f"Audit failed: {str(e)}"}), 500

    @app.route("/api/recent")
    def recent_scans():
        try:
            conn = get_db()
            rows = conn.execute(
                "SELECT url, score, level, total_checks, passed, warnings, failed, scanned_at FROM scan_log ORDER BY id DESC LIMIT 20"
            ).fetchall()
            conn.close()
            return jsonify([dict(r) for r in rows])
        except Exception:
            return jsonify([])

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "version": __import__("webaudit").__version__})

    @app.route("/robots.txt")
    def robots():
        return """User-agent: *
Disallow: /api/
Disallow: /health
Allow: /

User-agent: Googlebot
Allow: /

User-agent: GPTBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: PerplexityBot
Allow: /
""", 200, {"Content-Type": "text/plain"}

    @app.route("/llms.txt")
    def llms_txt():
        content = (
            "# AgentLighthouse\n"
            "> AI Readiness & Modern Web Compliance Scanner\n\n"
            "AgentLighthouse analyzes any website for AI/Agent readiness, modern web compliance, "
            "structured data coverage, semantic HTML, AI crawler compatibility, security headers, and more.\n\n"
        )
        if site_url:
            content += f" url: {site_url}\n"
        content += (
            f"\n## Features\n"
            f"- 40 audit checks across security, SEO, AI readiness, modern web compliance, and performance\n"
            f"- Modern Web Compliance: dialog, popover, container queries, view transitions, user preference queries\n"
            f"- Score normalized to 0-100 with raw score breakdown\n"
            f"- Detailed findings with actionable recommendations\n"
            f"- JSON-LD and Schema.org coverage analysis\n"
            f"- llms.txt and llms-full.txt detection\n"
            f"- Semantic HTML and heading structure validation\n"
            f"- Google Chrome Modern Web Guidance checks\n"
            f"\n## Endpoints\n"
            f"- POST /api/audit — Run full audit on a URL\n"
            f"- GET /health — Health check\n"
            f"- GET /llms-full.txt — Detailed documentation for AI agents\n"
        )
        return content, 200, {"Content-Type": "text/plain"}

    @app.route("/llms-full.txt")
    def llms_full_txt():
        content = (
            "# AgentLighthouse — Full Documentation for AI Agents\n"
            "> AI Readiness & Modern Web Compliance Scanner by PHRIXUS\n\n"
            "AgentLighthouse is an open-source tool that evaluates websites for AI and Agent Readiness, "
            "Modern Web Compliance, structured data, semantic HTML, AI crawler compatibility, "
            "security headers, and performance metrics.\n\n"
            f"> Core Audit Categories\n\n"
            "### Security (18pts)\n"
            "- SSL certificate validation and expiry tracking\n"
            "- Security headers: HSTS, X-Frame-Options, X-Content-Type-Options, CSP, Referrer-Policy, Permissions-Policy\n\n"
            "### SEO & Metadata (8pts)\n"
            "- Title tag, meta description, Open Graph, Twitter Card\n"
            "- Canonical URL, robots.txt, sitemap.xml\n\n"
            "### AI & Agent Readiness (21pts)\n"
            "- llms.txt and llms-full.txt detection and quality scoring\n"
            "- Markdown for Agents (Accept header negotiation)\n"
            "- Semantic HTML tag usage (header, nav, main, footer, section, article)\n"
            "- Heading structure hierarchy (H1-H6)\n"
            "- X-Robots-Tag and AI bot access verification\n\n"
            "### Structured Data (14pts)\n"
            "- JSON-LD presence and parse validation\n"
            "- Schema.org type coverage (WebApplication, Organization, SoftwareSourceCode, etc.)\n\n"
            "### Modern Web Compliance (20pts)\n"
            "- Native Dialog element usage (<dialog>)\n"
            "- Responsive images with <picture> element\n"
            "- CSS Container Queries for component-level responsive design\n"
            "- Popover API usage\n"
            "- View Transitions API\n"
            "- User preference queries: prefers-reduced-motion, prefers-color-scheme\n"
            "- Semantic landmark elements: <main>, <nav>, <header>, <footer>\n"
            "- Resource hints: preload, prefetch, preconnect\n"
            "- <time> element for machine-readable dates\n"
            "- Native disclosure: <details>/<summary>\n"
            "- No inline event handlers (CSP compatibility)\n"
            "- CSP meta tag fallback\n\n"
            f"> API Reference\n\n"
            "### POST /api/audit\n"
            "Request: {\"url\": \"<target-url>\"}\n"
            "Response: {score, raw_score, max_score, level, checks[], url}\n\n"
            "### GET /health\n"
            f"Response: {{\"status\": \"ok\", \"version\": \"{__import__('webaudit').__version__}\"}}\n\n"
            f"> Scoring System\n\n"
            "Each check has a max_score. Total raw_score / max_score normalized to 0-100.\n"
            "Status levels: excellent (90+), good (70+), fair (50+), poor (<50)\n\n"
            f"> Integration\n\n"
            "AgentLighthouse can be integrated into CI/CD pipelines for continuous AI readiness monitoring.\\n"
            "POST /api/audit accepts any public URL and returns machine-readable JSON.\\\n\\\n"
            "## Project\\\n"
            "- Repository: https://github.com/phrixus-ai/agent-lighthouse\\\n"
            "- License: MIT\n"
            "- Author: PHRIXUS\n"
        )
        return content, 200, {"Content-Type": "text/plain"}

    @app.route("/sitemap.xml")
    def sitemap():
        su = site_url or "https://example.com"
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'  <url><loc>{su}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>\n'
            f'  <url><loc>{su}/llms.txt</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>\n'
            f'  <url><loc>{su}/llms-full.txt</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
            '</urlset>'
        )
        return xml, 200, {"Content-Type": "application/xml"}

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html", site_url=site_url, ga_id=ga_id), 404

    return app
