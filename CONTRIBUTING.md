# Contributing to AgentLighthouse

Thanks for your interest in contributing! This guide covers the basics.

## Development Setup

```bash
git clone https://github.com/phrixus-ai/agent-lighthouse.git
cd agent-lighthouse
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m webaudit
```

## Adding a New Audit Check

1. Open `src/webaudit/auditor.py`
2. Add a new `_check_*` method to the `WebAuditor` class
3. Use `self._add(name, status, score, max_score, value, rec, category)` to record results
4. Call the method in the `run()` method
5. Update the score total in README.md

**Status values:** `pass`, `warning`, `fail`
**Categories:** `security`, `meta`, `social`, `structured`, `content`, `seo`, `mobile`, `accessibility`, `crawling`, `ai`, `performance`

## Code Style

- Python 3.10+ with type hints where practical
- Follow existing naming conventions (methods: `_check_*`, helpers: `_add`, `_build_*`)
- Keep audit methods focused — one check per method
- Recommendations should be actionable and specific

## Reporting Bugs

Open an issue with:
- The URL you audited
- Expected vs actual result
- Browser and OS (for UI bugs)

## Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b my-feature`
3. Commit with clear messages
4. Push and open a PR against `main`

Keep PRs small and focused. One audit check per PR is ideal.

## License

By contributing, you agree that your code will be licensed under the MIT License.
