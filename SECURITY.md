# Security Policy

## Reporting a Vulnerability

If you find a security vulnerability in AgentLighthouse, please report it responsibly:

1. **Do not** open a public issue
2. Email: security@phrixus.xyz (or open a [private vulnerability report](../../security/advisories/new))
3. Include: description, steps to reproduce, potential impact

We will acknowledge within 48 hours and aim to resolve within 7 days.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| < 0.2   | No        |

## Scope

AgentLighthouse is a client-side scanner — it sends HTTP requests to user-provided URLs. It does not:
- Store user data beyond scan history in SQLite (local only)
- Execute arbitrary code
- Make authenticated requests

The main attack surface is the Flask web server (port 5000 by default). Ensure it runs behind a reverse proxy with proper security headers in production.
