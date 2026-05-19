"""Core audit engine - scans a URL and returns a structured report."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
import re
import ssl
import socket
from datetime import datetime
from . import __version__

UA = f"AgentLighthouse/{__version__}"


class AuditResult:
    """Single check result."""
    def __init__(self, name, status, score, max_score, value=None, recommendation=None, category="general"):
        self.name = name
        self.status = status  # "pass", "warning", "fail"
        self.score = score
        self.max_score = max_score
        self.value = value
        self.recommendation = recommendation
        self.category = category

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "score": self.score,
            "max_score": self.max_score,
            "value": self.value,
            "recommendation": self.recommendation,
            "category": self.category,
        }


class WebAuditor:
    """Scans a website and produces an agent-readiness report."""

    def __init__(self, url, timeout=15):
        self.url = url if url.startswith("http") else f"https://{url}"
        self.timeout = timeout
        self.parsed = urlparse(self.url)
        self.domain = self.parsed.hostname
        self.base_url = f"{self.parsed.scheme}://{self.parsed.netloc}"
        self.results = []
        self.html = None
        self.soup = None
        self.response = None
        self.ssl_days_left = None
        self.domain_days_left = None
        self._robots_txt = None  # cached robots.txt content

    def run(self):
        try:
            self.response = requests.get(
                self.url, timeout=self.timeout,
                headers={"User-Agent": UA},
                allow_redirects=True, verify=True
            )
            self.html = self.response.text
            self.soup = BeautifulSoup(self.html, "lxml")
        except requests.exceptions.SSLError:
            self.results.append(AuditResult("SSL Certificate", "fail", 0, 10,
                                            "SSL error — site is not accessible over HTTPS",
                                            "Install a valid SSL certificate", "security"))
            self.results.append(AuditResult("Site Accessible", "fail", 0, 5,
                                            "Site could not be reached",
                                            "Check your DNS and server configuration", "accessibility"))
            return self._build_report()
        except requests.exceptions.ConnectionError:
            self.results.append(AuditResult("Site Accessible", "fail", 0, 5,
                                            "Connection refused or DNS failure",
                                            "Check your DNS and server configuration", "accessibility"))
            return self._build_report()
        except requests.exceptions.Timeout:
            self.results.append(AuditResult("Site Accessible", "fail", 0, 5,
                                            "Request timed out",
                                            "Your server is too slow to respond", "accessibility"))
            return self._build_report()
        except Exception as e:
            self.results.append(AuditResult("Site Accessible", "fail", 0, 5,
                                            f"Error: {str(e)}",
                                            "Check your website", "accessibility"))
            return self._build_report()

        self._fetch_robots_txt()

        self._check_accessibility()
        self._check_ssl()
        self._check_security_headers()
        self._check_meta_title()
        self._check_meta_description()
        self._check_og_tags()
        self._check_twitter_card()
        self._check_jsonld()
        self._check_headings()
        self._check_image_alts()
        self._check_canonical()
        self._check_viewport()
        self._check_lang()
        self._check_charset()
        self._check_robots_txt()
        self._check_robots_ai_bots()
        self._check_sitemap()
        self._check_llms_txt()
        self._check_markdown_agents()
        self._check_semantic_html()
        self._check_llms_full_txt()
        self._check_schema_coverage()
        self._check_x_robots_tag()
        self._check_error_page_quality()
        self._check_domain_expiry()
        self._check_performance()
        self._check_modern_web()

        return self._build_report()

    def _add(self, name, status, score, max_score, value=None, rec=None, cat="general"):
        self.results.append(AuditResult(name, status, score, max_score, value, rec, cat))

    def _fetch_robots_txt(self):
        """Fetch robots.txt once and cache it."""
        try:
            resp = requests.get(f"{self.base_url}/robots.txt", timeout=5,
                                headers={"User-Agent": UA})
            if resp.status_code == 200:
                self._robots_txt = resp.text
        except Exception:
            self._robots_txt = None

    # ── Accessibility ──────────────────────────────────────────────────────────

    def _check_accessibility(self):
        code = self.response.status_code
        if 200 <= code < 300:
            self._add("Site Accessible", "pass", 5, 5, f"HTTP {code}", cat="accessibility")
        elif 300 <= code < 400:
            self._add("Site Accessible", "warning", 3, 5, f"HTTP {code} (redirect)",
                      "Avoid unnecessary redirects", "accessibility")
        else:
            self._add("Site Accessible", "fail", 0, 5, f"HTTP {code}",
                      "Fix server errors", "accessibility")

    # ── Security ───────────────────────────────────────────────────────────────

    def _check_ssl(self):
        if self.parsed.scheme != "https":
            self._add("SSL Certificate", "fail", 0, 10, "No HTTPS",
                      "Install SSL certificate", "security")
            return
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=self.domain) as s:
                s.settimeout(5)
                s.connect((self.domain, 443))
                cert = s.getpeercert()
                expiry = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                days_left = (expiry - datetime.utcnow()).days
                self.ssl_days_left = days_left
                if days_left > 30:
                    self._add("SSL Certificate", "pass", 10, 10,
                              f"Valid ({days_left} days remaining)", cat="security")
                elif days_left > 0:
                    self._add("SSL Certificate", "warning", 6, 10,
                              f"Expires in {days_left} days",
                              "Renew your SSL certificate soon", "security")
                else:
                    self._add("SSL Certificate", "fail", 0, 10, "Expired",
                              "Renew immediately", "security")
        except ssl.SSLError as e:
            self._add("SSL Certificate", "fail", 0, 10, f"SSL error: {e.reason}",
                      "Fix SSL configuration", "security")
        except Exception:
            # Connection succeeded (we got a response) but cert details unavailable
            self._add("SSL Certificate", "pass", 8, 10, "HTTPS active (cert details unavailable)",
                      cat="security")

    def _check_security_headers(self):
        headers = {k.lower(): v for k, v in self.response.headers.items()}

        checks = [
            # (header, display_name, score, recommendation)
            (
                "strict-transport-security",
                "HSTS",
                4,
                "Add: Strict-Transport-Security: max-age=31536000; includeSubDomains"
            ),
            (
                "x-frame-options",
                "X-Frame-Options",
                3,
                "Add: X-Frame-Options: DENY  (prevents clickjacking)"
            ),
            (
                "x-content-type-options",
                "X-Content-Type-Options",
                3,
                "Add: X-Content-Type-Options: nosniff"
            ),
            (
                "content-security-policy",
                "Content-Security-Policy",
                4,
                "Add a Content-Security-Policy header to restrict resource loading"
            ),
            (
                "referrer-policy",
                "Referrer-Policy",
                2,
                "Add: Referrer-Policy: strict-origin-when-cross-origin"
            ),
            (
                "permissions-policy",
                "Permissions-Policy",
                2,
                "Add a Permissions-Policy header to restrict browser feature access"
            ),
        ]

        present = []
        missing = []

        for header_key, name, _, _ in checks:
            if header_key in headers:
                present.append(name)
            else:
                missing.append(name)

        total_score = sum(s for h, _, s, _ in checks if h in headers)
        max_score = sum(s for _, _, s, _ in checks)

        if not missing:
            self._add("Security Headers", "pass", max_score, max_score,
                      f"All {len(checks)} headers present", cat="security")
        elif len(missing) <= 2:
            self._add("Security Headers", "warning", total_score, max_score,
                      f"Missing: {', '.join(missing)}",
                      f"Add missing headers: {'; '.join(r for h, n, _, r in checks if n in missing)}",
                      "security")
        else:
            self._add("Security Headers", "fail", total_score, max_score,
                      f"Missing {len(missing)}/{len(checks)}: {', '.join(missing)}",
                      "Configure security headers on your web server or CDN",
                      "security")

    # ── Meta / SEO ─────────────────────────────────────────────────────────────

    def _check_meta_title(self):
        title = self.soup.find("title")
        if not title or not title.string:
            self._add("Title Tag", "fail", 0, 5, "Missing",
                      "Add a <title> tag (30-60 chars recommended)", "meta")
            return
        t = title.string.strip()
        length = len(t)
        if 30 <= length <= 60:
            self._add("Title Tag", "pass", 5, 5, f"{t} ({length} chars)", cat="meta")
        elif length < 30:
            self._add("Title Tag", "warning", 3, 5, f"{t} ({length} chars — too short)",
                      "Title should be 30-60 characters", "meta")
        else:
            self._add("Title Tag", "warning", 3, 5, f"{t} ({length} chars — too long)",
                      "Title should be 30-60 characters", "meta")

    def _check_meta_description(self):
        desc = self.soup.find("meta", attrs={"name": "description"})
        if not desc or not desc.get("content"):
            self._add("Meta Description", "fail", 0, 5, "Missing",
                      "Add a meta description (120-160 chars recommended)", "meta")
            return
        d = desc["content"].strip()
        length = len(d)
        if 120 <= length <= 160:
            self._add("Meta Description", "pass", 5, 5, f"{length} chars", cat="meta")
        elif length < 120:
            self._add("Meta Description", "warning", 3, 5, f"{length} chars — too short",
                      "Description should be 120-160 characters", "meta")
        else:
            self._add("Meta Description", "warning", 3, 5, f"{length} chars — too long",
                      "Description should be 120-160 characters", "meta")

    # ── Social ─────────────────────────────────────────────────────────────────

    def _check_og_tags(self):
        og_tags = {}
        for tag in ["og:title", "og:description", "og:image", "og:url", "og:type"]:
            meta = self.soup.find("meta", attrs={"property": tag})
            if meta and meta.get("content"):
                og_tags[tag] = meta["content"]

        total = len(og_tags)
        if total >= 4:
            self._add("Open Graph Tags", "pass", 5, 5, f"{total}/5 present", cat="social")
        elif total >= 2:
            missing = [t for t in ["og:title", "og:description", "og:image", "og:url", "og:type"]
                       if t not in og_tags]
            self._add("Open Graph Tags", "warning", 3, 5, f"{total}/5 present",
                      f"Missing: {', '.join(missing)}", "social")
        else:
            self._add("Open Graph Tags", "fail", 0, 5, f"{total}/5 present",
                      "Add Open Graph meta tags for social sharing and AI understanding", "social")

    def _check_twitter_card(self):
        tc = {}
        for tag in ["twitter:card", "twitter:title", "twitter:description", "twitter:image"]:
            meta = self.soup.find("meta", attrs={"name": tag})
            if meta and meta.get("content"):
                tc[tag] = meta["content"]
        total = len(tc)
        if total >= 3:
            self._add("Twitter Card", "pass", 3, 3, f"{total}/4 present", cat="social")
        elif total >= 1:
            self._add("Twitter Card", "warning", 1, 3, f"{total}/4 present",
                      "Add missing Twitter Card tags", "social")
        else:
            self._add("Twitter Card", "fail", 0, 3, "Missing",
                      "Add Twitter Card meta tags", "social")

    # ── Structured data ────────────────────────────────────────────────────────

    def _check_jsonld(self):
        scripts = self.soup.find_all("script", attrs={"type": "application/ld+json"})
        if not scripts:
            self._add("Structured Data (JSON-LD)", "fail", 0, 8, "Missing",
                      "Add JSON-LD structured data for AI understanding", "structured")
            return

        schemas = []
        for s in scripts:
            try:
                text = s.get_text(strip=True)
                if not text:
                    continue
                data = json.loads(text)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    schema_type = item.get("@type", "Unknown") if isinstance(item, dict) else "Unknown"
                    schemas.append(schema_type)
            except (json.JSONDecodeError, TypeError):
                pass

        if schemas:
            self._add("Structured Data (JSON-LD)", "pass", 8, 8,
                      f"{len(schemas)} schema(s): {', '.join(schemas)}", cat="structured")
        else:
            self._add("Structured Data (JSON-LD)", "warning", 3, 8,
                      "JSON-LD found but could not be parsed",
                      "Fix JSON-LD syntax errors", "structured")

    # ── Content ────────────────────────────────────────────────────────────────

    def _check_headings(self):
        headings = {}
        for level in range(1, 7):
            tags = self.soup.find_all(f"h{level}")
            if tags:
                headings[f"h{level}"] = [t.get_text(strip=True)[:50] for t in tags]

        h1_count = len(headings.get("h1", []))
        total = sum(len(v) for v in headings.values())
        if h1_count == 1:
            self._add("Heading Structure", "pass", 5, 5,
                      f"H1: 1, Total headings: {total}", cat="content")
        elif h1_count == 0:
            self._add("Heading Structure", "fail", 1, 5, "No H1 tag found",
                      "Add exactly one H1 tag per page", "content")
        else:
            self._add("Heading Structure", "warning", 3, 5,
                      f"{h1_count} H1 tags found (should be 1)",
                      "Use only one H1 tag per page", "content")

    def _check_image_alts(self):
        imgs = self.soup.find_all("img")
        if not imgs:
            self._add("Image Alt Text", "pass", 3, 3, "No images found", cat="content")
            return
        missing = [img.get("src", "")[:40] for img in imgs if not img.get("alt")]
        total = len(imgs)
        if not missing:
            self._add("Image Alt Text", "pass", 3, 3,
                      f"All {total} image(s) have alt text", cat="content")
        elif len(missing) <= total * 0.3:
            self._add("Image Alt Text", "warning", 2, 3,
                      f"{len(missing)}/{total} images missing alt text",
                      "Add descriptive alt text to all images for accessibility and AI understanding",
                      "content")
        else:
            self._add("Image Alt Text", "fail", 0, 3,
                      f"{len(missing)}/{total} images missing alt text",
                      "Add alt text to all images", "content")

    # ── SEO ────────────────────────────────────────────────────────────────────

    def _check_canonical(self):
        canon = self.soup.find("link", attrs={"rel": "canonical"})
        if canon and canon.get("href"):
            self._add("Canonical URL", "pass", 3, 3, canon["href"], cat="seo")
        else:
            self._add("Canonical URL", "warning", 0, 3, "Missing",
                      "Add a canonical URL to prevent duplicate content", "seo")

    # ── Mobile ─────────────────────────────────────────────────────────────────

    def _check_viewport(self):
        vp = self.soup.find("meta", attrs={"name": "viewport"})
        if vp and "width" in vp.get("content", ""):
            self._add("Mobile Viewport", "pass", 3, 3, vp.get("content", ""), cat="mobile")
        else:
            self._add("Mobile Viewport", "fail", 0, 3, "Missing",
                      "Add viewport meta tag for mobile compatibility", "mobile")

    def _check_lang(self):
        html = self.soup.find("html")
        lang = html.get("lang") if html else None
        if lang:
            self._add("HTML Lang Attribute", "pass", 2, 2, f'lang="{lang}"', cat="accessibility")
        else:
            self._add("HTML Lang Attribute", "warning", 0, 2, "Missing",
                      "Add lang attribute for accessibility and AI understanding", "accessibility")

    def _check_charset(self):
        charset = self.soup.find("meta", attrs={"charset": True})
        if charset:
            self._add("Charset Declaration", "pass", 1, 1,
                      charset.get("charset", "").upper(), cat="accessibility")
        else:
            self._add("Charset Declaration", "warning", 0, 1, "Missing",
                      "Add <meta charset='UTF-8'>", "accessibility")

    # ── Crawling ───────────────────────────────────────────────────────────────

    def _check_robots_txt(self):
        if self._robots_txt is not None:
            if "user-agent" in self._robots_txt.lower():
                self._add("robots.txt", "pass", 5, 5, "Present and valid", cat="crawling")
            else:
                self._add("robots.txt", "warning", 1, 5, "Present but empty/malformed",
                          "Add proper user-agent directives to robots.txt", "crawling")
        else:
            self._add("robots.txt", "warning", 1, 5, "Not found",
                      "Add robots.txt to guide crawlers", "crawling")

    def _check_robots_ai_bots(self):
        if self._robots_txt is None:
            self._add("AI Bot Access", "warning", 1, 5, "robots.txt not found",
                      "Add robots.txt with explicit AI bot permissions", "ai")
            return

        text = self._robots_txt.lower()
        lines = [l.strip() for l in text.splitlines()]

        ai_bots = {
            "GPTBot": "gptbot",
            "ClaudeBot": "claudebot",
            "PerplexityBot": "perplexitybot",
            "ChatGPT-User": "chatgpt-user",
            "Bytespider": "bytespider",
            "GoogleBot": "googlebot",
            "Bingbot": "bingbot",
            "Applebot": "applebot",
        }

        # Parse robots.txt into sections: {user-agent: [disallow/allow rules]}
        sections = {}  # pattern -> list of (directive, path)
        current_agents = []
        for line in lines:
            if line.startswith("#") or not line:
                if line == "" and current_agents:
                    current_agents = []
                continue
            if line.startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                current_agents.append(agent)
                if agent not in sections:
                    sections[agent] = []
            elif line.startswith("disallow:") or line.startswith("allow:"):
                directive, _, path = line.partition(":")
                path = path.strip()
                for agent in current_agents:
                    sections.setdefault(agent, []).append((directive.strip(), path))

        def is_blocked(bot_pattern):
            """Return True if bot is explicitly blocked from /."""
            # Check specific bot section first, then wildcard
            for key in (bot_pattern, "*"):
                rules = sections.get(key, [])
                for directive, path in rules:
                    if directive == "disallow" and (path == "/" or path == "/*"):
                        return True
            return False

        def is_explicitly_mentioned(bot_pattern):
            return bot_pattern in sections

        blocked = []
        allowed_explicit = []

        for name, pattern in ai_bots.items():
            if is_blocked(pattern):
                blocked.append(name)
            elif is_explicitly_mentioned(pattern):
                allowed_explicit.append(name)

        if blocked:
            self._add("AI Bot Access", "warning", 2, 5,
                      f"Blocked: {', '.join(blocked)}",
                      "Allow AI crawlers to improve visibility in AI-powered search", "ai")
        elif allowed_explicit:
            self._add("AI Bot Access", "pass", 5, 5,
                      f"Explicitly allowed: {', '.join(allowed_explicit)}", cat="ai")
        else:
            self._add("AI Bot Access", "pass", 4, 5,
                      "No AI bot restrictions (default allow)", cat="ai")

    def _check_sitemap(self):
        try:
            # Also check if robots.txt references a sitemap
            sitemap_url = f"{self.base_url}/sitemap.xml"
            if self._robots_txt:
                for line in self._robots_txt.splitlines():
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        break
            resp = requests.get(sitemap_url, timeout=5,
                                headers={"User-Agent": UA})
            if resp.status_code == 200 and ("<urlset" in resp.text or "<sitemapindex" in resp.text):
                self._add("sitemap.xml", "pass", 4, 4, "Present and valid", cat="crawling")
            else:
                self._add("sitemap.xml", "warning", 0, 4, "Not found or invalid",
                          "Add sitemap.xml for better crawlability", "crawling")
        except Exception:
            self._add("sitemap.xml", "warning", 0, 4, "Could not check", cat="crawling")

    # ── AI readiness ───────────────────────────────────────────────────────────

    def _check_llms_txt(self):
        try:
            resp = requests.get(f"{self.base_url}/llms.txt", timeout=5,
                                headers={"User-Agent": UA})
            if resp.status_code == 200 and len(resp.text.strip()) > 10:
                self._add("llms.txt", "pass", 5, 5,
                          f"Present ({len(resp.text)} chars)", cat="ai")
            else:
                self._add("llms.txt", "fail", 0, 5, "Not found",
                          "Add llms.txt — the emerging standard for AI crawler instructions. See llms-txt.org",
                          "ai")
        except Exception:
            self._add("llms.txt", "fail", 0, 5, "Could not check", cat="ai")

    def _check_markdown_agents(self):
        """Check if the site returns text/markdown when Accept: text/markdown is sent."""
        try:
            resp = requests.get(self.url, timeout=self.timeout,
                                headers={
                                    "User-Agent": UA,
                                    "Accept": "text/markdown"
                                },
                                allow_redirects=True, verify=True)
            content_type = resp.headers.get("Content-Type", "").lower()
            if "text/markdown" in content_type:
                self._add("Markdown for Agents", "pass", 5, 5,
                          "Returns text/markdown", cat="ai")
            elif resp.status_code == 406:
                self._add("Markdown for Agents", "fail", 0, 5,
                          "Server rejects text/markdown (406)",
                          "Enable Markdown for Agents — Cloudflare offers this as a one-click feature",
                          "ai")
            else:
                self._add("Markdown for Agents", "warning", 2, 5,
                          f"Returns {content_type.split(';')[0].strip() or 'unknown'} instead of text/markdown",
                          "Configure server to return markdown for Accept: text/markdown requests",
                          "ai")
        except Exception:
            self._add("Markdown for Agents", "warning", 2, 5, "Could not check", cat="ai")

    def _check_semantic_html(self):
        semantic_tags = ["article", "nav", "main", "aside", "section", "header", "footer"]
        # Re-parse with html.parser — lxml can silently drop HTML5 semantic elements
        # in some environments, so html.parser gives a more reliable result here.
        soup_hp = BeautifulSoup(self.html, "html.parser")
        found = [tag for tag in semantic_tags if soup_hp.find(tag)]
        count = len(found)
        score = min(5, count)
        if count >= 5:
            status = "pass"
        elif count >= 3:
            status = "warning"
        else:
            status = "fail"
        missing = [t for t in semantic_tags if t not in found]
        rec = f"Add semantic HTML5 tags: {', '.join(f'<{t}>' for t in missing)}" if missing else None
        self._add("Semantic HTML", status, score, 5,
                  f"{count}/7 tags found: {', '.join(f'<{t}>' for t in found) or 'none'}", rec, "structured")

    def _check_llms_full_txt(self):
        try:
            resp = requests.get(f"{self.base_url}/llms-full.txt", timeout=5,
                                headers={"User-Agent": UA})
            if resp.status_code != 200 or not resp.text.strip():
                self._add("llms-full.txt", "fail", 0, 4, "Not found",
                          "Add llms-full.txt with detailed sections (lines starting with >) for AI agents",
                          "ai")
                return
            text = resp.text
            sections = [line for line in text.splitlines() if line.startswith(">")]
            has_links = "http" in text.lower()
            section_count = len(sections)
            if section_count >= 3:
                score, status = 4, "pass"
            elif section_count >= 1:
                score, status = 2, "warning"
            else:
                score, status = 1, "warning"
            value = f"Present — {section_count} section(s), links: {'yes' if has_links else 'no'}"
            rec = "Add more > sections and links to help AI agents navigate your content" if section_count < 3 else None
            self._add("llms-full.txt", status, score, 4, value, rec, "ai")
        except Exception:
            self._add("llms-full.txt", "fail", 0, 4, "Could not check", cat="ai")

    def _check_schema_coverage(self):
        common_types = {
            "organization", "webpage", "article", "person", "product",
            "localbusiness", "faqpage", "howto", "breadcrumblist", "searchaction",
            "webapplication", "softwareapplication", "softwareapplication", "website", "service",
            "softwaresourcecode"
        }
        found_types = set()

        # JSON-LD
        for script in self.soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(script.get_text(strip=True))
                items = data if isinstance(data, list) else [data]
                for item in items:
                    t = item.get("@type", "")
                    if isinstance(t, list):
                        for x in t:
                            found_types.add(str(x).lower())
                    elif t:
                        found_types.add(str(t).lower())
            except Exception:
                pass

        # Microdata
        for tag in self.soup.find_all(attrs={"itemtype": True}):
            itemtype = tag.get("itemtype", "")
            if "schema.org/" in itemtype:
                t = itemtype.rstrip("/").split("/")[-1].lower()
                found_types.add(t)

        # RDFa
        for tag in self.soup.find_all(attrs={"typeof": True}):
            for t in tag.get("typeof", "").split():
                found_types.add(t.lower().split(":")[-1])

        recognized = found_types & common_types
        score = min(6, len(recognized))
        if len(recognized) >= 4:
            status = "pass"
        elif len(recognized) >= 2:
            status = "warning"
        else:
            status = "fail"
        value = f"{len(recognized)} type(s): {', '.join(sorted(recognized)) or 'none'}"
        rec = "Add more schema.org types (Organization, Article, FAQPage, etc.) for richer AI understanding" if len(recognized) < 4 else None
        self._add("Schema Coverage", status, score, 6, value, rec, "structured")

    def _check_x_robots_tag(self):
        headers = {k.lower(): v for k, v in self.response.headers.items()}
        x_robots = headers.get("x-robots-tag", "")
        if not x_robots:
            self._add("X-Robots-Tag", "pass", 3, 3, "Not set (AI-friendly)", cat="ai")
            return
        directives = [d.strip().lower() for d in x_robots.split(",")]
        if "noai" in directives or "noimageai" in directives:
            blocking = [d for d in directives if d in ("noai", "noimageai")]
            self._add("X-Robots-Tag", "fail", 0, 3,
                      f"Blocks AI: {', '.join(blocking)}",
                      "Remove noai/noimageai directives to allow AI agents to use your content", "ai")
        else:
            self._add("X-Robots-Tag", "pass", 3, 3, f"Present, no AI blocks: {x_robots}", cat="ai")

    def _check_error_page_quality(self):
        try:
            resp = requests.get(f"{self.base_url}/nonexistent-page-404-test", timeout=5,
                                headers={"User-Agent": UA},
                                allow_redirects=True)
            real_404 = resp.status_code == 404
            if not real_404:
                self._add("Error Page Quality", "fail", 0, 3,
                          f"Soft 404 (HTTP {resp.status_code})",
                          "Return real HTTP 404 status for missing pages", "api")
                return
            soup = BeautifulSoup(resp.text, "lxml")
            has_semantic = bool(soup.find("main") or soup.find("article") or soup.find("section"))
            if has_semantic:
                self._add("Error Page Quality", "pass", 3, 3,
                          "Real 404 with semantic markup", cat="api")
            else:
                self._add("Error Page Quality", "warning", 1, 3,
                          "Real 404 but plain HTML",
                          "Add semantic HTML structure to your 404 error page", "api")
        except Exception:
            self._add("Error Page Quality", "fail", 0, 3, "Could not check", cat="api")

    # ── Domain ─────────────────────────────────────────────────────────────────

    def _check_domain_expiry(self):
        try:
            import whois
            w = whois.whois(self.domain)
            expiry_dates = w.expiration_date
            if not expiry_dates:
                return
            if isinstance(expiry_dates, list):
                expiry_dates = [d for d in expiry_dates if d is not None]
                expiry = min(expiry_dates) if expiry_dates else None
            else:
                expiry = expiry_dates
            if not expiry:
                return
            if expiry.tzinfo is not None:
                expiry = expiry.replace(tzinfo=None)
            days_left = (expiry - datetime.utcnow()).days
            self.domain_days_left = days_left
            if days_left > 60:
                self._add("Domain Expiry", "pass", 3, 3,
                          f"{days_left} days remaining ({expiry.strftime('%Y-%m-%d')})", cat="security")
            elif days_left > 30:
                self._add("Domain Expiry", "warning", 2, 3,
                          f"{days_left} days remaining — renew soon",
                          "Set up auto-renewal to avoid losing your domain", "security")
            else:
                self._add("Domain Expiry", "fail", 0, 3,
                          f"Only {days_left} days remaining!",
                          "Renew your domain immediately", "security")
        except ImportError:
            pass
        except Exception:
            pass

    # ── Performance ────────────────────────────────────────────────────────────

    def _check_performance(self):
        elapsed = round(self.response.elapsed.total_seconds(), 2)
        if elapsed < 1.0:
            self._add("Response Time", "pass", 4, 4, f"{elapsed}s", cat="performance")
        elif elapsed < 3.0:
            self._add("Response Time", "warning", 2, 4, f"{elapsed}s",
                      "Optimize server response time (target: <1s)", "performance")
        else:
            self._add("Response Time", "fail", 0, 4, f"{elapsed}s",
                      "Very slow response — optimize server or use a CDN", "performance")

        size_kb = round(len(self.html) / 1024, 1)
        if size_kb < 500:
            self._add("Page Size", "pass", 3, 3, f"{size_kb} KB", cat="performance")
        elif size_kb < 1500:
            self._add("Page Size", "warning", 2, 3, f"{size_kb} KB",
                      "Large page — consider optimizing assets", "performance")
        else:
            self._add("Page Size", "fail", 0, 3, f"{size_kb} KB",
                      "Very large page — optimize images and assets", "performance")

        encoding = self.response.headers.get("Content-Encoding", "")
        if encoding in ("gzip", "br", "zstd", "deflate"):
            self._add("Compression", "pass", 2, 2, f"{encoding} encoding", cat="performance")
        else:
            self._add("Compression", "warning", 0, 2, "No compression detected",
                      "Enable gzip or Brotli compression on your server", "performance")

    def _check_modern_web(self):
        """Modern Web Compliance — based on Google Chrome Modern Web Guidance."""
        cat = "modern_web"

        # 1. <dialog> element (native modal)
        if self.html.find("<dialog") >= 0 or self.html.find("<dialog ") >= 0:
            self._add("Native Dialog Element", "pass", 2, 2,
                      "<dialog> element found", cat=cat)
        else:
            self._add("Native Dialog Element", "info", 0, 2,
                      "No <dialog> element detected",
                      "Use <dialog> instead of custom modal implementations (Modern Web Guidance)", cat=cat)

        # 2. <picture> element (responsive images)
        if self.html.find("<picture") >= 0:
            self._add("Responsive Images", "pass", 2, 2,
                      "<picture> element found", cat=cat)
        else:
            self._add("Responsive Images", "info", 0, 2,
                      "No <picture> element detected",
                      "Use <picture> + srcset for responsive image delivery", cat=cat)

        # 3. CSS Container Queries
        has_css = self._extract_css()
        cq_count = has_css.lower().count("container") if has_css else 0
        if cq_count >= 3:
            self._add("Container Queries", "pass", 2, 2,
                      "Container query usage detected", cat=cat)
        else:
            self._add("Container Queries", "info", 0, 2,
                      "No container queries detected",
                      "Use @container for component-level responsive design", cat=cat)

        # 4. Popover API
        if self.html.find("popover") >= 0:
            self._add("Popover API", "pass", 2, 2,
                      "Popover attribute found", cat=cat)
        else:
            self._add("Popover API", "info", 0, 2,
                      "No popover usage detected",
                      "Use popover attribute instead of custom tooltip libraries", cat=cat)

        # 5. View Transitions API
        if has_css and "view-transition" in has_css.lower():
            self._add("View Transitions", "pass", 2, 2,
                      "View Transitions API detected", cat=cat)
        else:
            self._add("View Transitions", "info", 0, 2,
                      "No view transitions detected",
                      "Use View Transitions API for smooth page transitions", cat=cat)

        # 6. prefers-color-scheme / prefers-reduced-motion
        motion = has_css.lower().count("prefers-reduced-motion") if has_css else 0
        color = has_css.lower().count("prefers-color-scheme") if has_css else 0
        if motion > 0 and color > 0:
            self._add("User Preference Queries", "pass", 2, 2,
                      "prefers-reduced-motion + prefers-color-scheme detected", cat=cat)
        elif motion > 0 or color > 0:
            self._add("User Preference Queries", "warning", 1, 2,
                      f"{'prefers-reduced-motion' if motion else 'prefers-color-scheme'} detected",
                      f"Add {'prefers-color-scheme' if motion else 'prefers-reduced-motion'} for full accessibility", cat=cat)
        else:
            self._add("User Preference Queries", "fail", 0, 2,
                      "No user preference media queries detected",
                      "Add prefers-reduced-motion and prefers-color-scheme (accessibility + UX)", cat=cat)

        # 7. <main>, <nav>, <header>, <footer> landmark elements
        landmarks = sum(1 for tag in ["<main", "<nav", "<header", "<footer", "<aside", "<article", "<section"]
                       if tag in self.html)
        if landmarks >= 4:
            self._add("Landmark Elements", "pass", 2, 2,
                      f"{landmarks} semantic landmarks found", cat=cat)
        else:
            self._add("Landmark Elements", "warning", 1, 2,
                      f"Only {landmarks} landmarks found",
                      "Use <main>, <nav>, <header>, <footer> for proper landmark structure", cat=cat)

        # 8. Preload / prefetch hints
        has_preload = "preload" in self.html or "prefetch" in self.html or "preconnect" in self.html
        if has_preload:
            self._add("Resource Hints", "pass", 2, 2,
                      "preload/prefetch/preconnect detected", cat=cat)
        else:
            self._add("Resource Hints", "info", 0, 2,
                      "No resource hints detected",
                      "Use <link rel=\"preload\">, preconnect, or prefetch for critical resources", cat=cat)

        # 9. <time> element for dates
        if "<time" in self.html:
            self._add("Time Element", "pass", 1, 1,
                      "<time> element found", cat=cat)
        else:
            self._add("Time Element", "info", 0, 1,
                      "No <time> element detected",
                      "Use <time datetime=\"...\"> for machine-readable dates", cat=cat)

        # 10. <details>/<summary> (native disclosure)
        if "<details" in self.html:
            self._add("Native Disclosure", "pass", 1, 1,
                      "<details>/<summary> found", cat=cat)
        else:
            self._add("Native Disclosure", "info", 0, 1,
                      "No <details>/<summary> detected",
                      "Use native <details>/<summary> for accordion/disclosure widgets", cat=cat)

        # 11. No inline event handlers (onclick, onload, etc.)
        inline_events = re.findall(r'\bon(click|load|error|mouseover|focus|blur|submit|change|input|keydown|keyup|resize|scroll)=', self.html, re.IGNORECASE)
        if len(inline_events) == 0:
            self._add("Inline Event Handlers", "pass", 1, 1,
                      "No inline event handlers detected", cat=cat)
        else:
            self._add("Inline Event Handlers", "warning", 0, 1,
                      f"{len(inline_events)} inline event handler(s) found",
                      "Move inline handlers to addEventListener for CSP compatibility", cat=cat)

        # 12. CSP in meta tag (additional to header check)
        csp_meta = re.search(r'<meta\s+http-equiv=["\']Content-Security-Policy["\']', self.html, re.IGNORECASE)
        if csp_meta:
            self._add("CSP Meta Tag", "pass", 1, 1,
                      "CSP defined in <meta> tag", cat=cat)
        else:
            self._add("CSP Meta Tag", "info", 0, 1,
                      "No CSP meta tag (header may still have CSP)",
                      "Add CSP in <meta> tag as fallback for pages without server headers", cat=cat)

    def _extract_css(self):
        """Extract inline <style> content and linked <link rel=stylesheet> CSS from HTML."""
        # Inline styles
        styles = re.findall(r'<style[^>]*>(.*?)</style>', self.html, re.DOTALL | re.IGNORECASE)
        css = "\n".join(styles) if styles else ""

        # Linked external stylesheets (first 5, limited to avoid over-fetching)
        links = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', self.html, re.IGNORECASE)
        links = links[:5]
        for href in links:
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = self.base_url + href
            elif not href.startswith("http"):
                href = self.base_url + "/" + href
            try:
                resp = requests.get(href, timeout=5, headers={"User-Agent": UA})
                if resp.status_code == 200:
                    css += "\n" + resp.text
            except Exception:
                pass
        return css

    # ── Report ─────────────────────────────────────────────────────────────────

    def _build_report(self):
        total_score = sum(r.score for r in self.results)
        max_score = sum(r.max_score for r in self.results)
        percentage = round((total_score / max_score) * 100) if max_score > 0 else 0

        passed = sum(1 for r in self.results if r.status == "pass")
        warnings = sum(1 for r in self.results if r.status == "warning")
        failed = sum(1 for r in self.results if r.status == "fail")

        if percentage >= 80:
            level = "excellent"
        elif percentage >= 60:
            level = "good"
        elif percentage >= 40:
            level = "fair"
        else:
            level = "poor"

        return {
            "url": self.url,
            "domain": self.domain,
            "timestamp": datetime.utcnow().isoformat(),
            "score": percentage,
            "raw_score": total_score,
            "max_score": max_score,
            "level": level,
            "ssl_days_left": self.ssl_days_left,
            "domain_days_left": self.domain_days_left,
            "summary": {
                "passed": passed,
                "warnings": warnings,
                "failed": failed,
                "total_checks": len(self.results),
            },
            "checks": [r.to_dict() for r in self.results],
        }
