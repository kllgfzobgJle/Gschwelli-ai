"""Pytest configuration and environment fixtures for gschwelli-ai test suite."""

import sys
from pathlib import Path

# Ensure project root is at the front of sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Install re-entrant sync_playwright wrapper to allow multiple test modules
# with different fixture scopes (session, module, function) to share the
# single underlying Playwright driver instance without asyncio loop collisions.
try:
    import playwright.sync_api
    _orig_sync_playwright = playwright.sync_api.sync_playwright

    class _PlaywrightContextProxy:
        _instance = None
        _ref_count = 0

        def __enter__(self):
            if _PlaywrightContextProxy._instance is None:
                _PlaywrightContextProxy._instance = _orig_sync_playwright().start()
            _PlaywrightContextProxy._ref_count += 1
            return _PlaywrightContextProxy._instance

        def __exit__(self, exc_type, exc_val, exc_tb):
            _PlaywrightContextProxy._ref_count -= 1
            # Keep instance alive until all scopes exit at end of pytest session
            if _PlaywrightContextProxy._ref_count <= 0:
                if _PlaywrightContextProxy._instance is not None:
                    try:
                        _PlaywrightContextProxy._instance.stop()
                    except Exception:
                        pass
                    _PlaywrightContextProxy._instance = None
                _PlaywrightContextProxy._ref_count = 0

    playwright.sync_api.sync_playwright = _PlaywrightContextProxy
except ImportError:
    pass
