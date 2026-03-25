"""
Regression test to ensure ORM models import cleanly.

Previously, importing src.api.models crashed at import time with:

sqlalchemy.exc.ArgumentError: Can't add unnamed column to column collection

Root cause was an invalid expression in Tag's uniqueness constraint
(func.lower("name") used a string literal rather than the Tag.name column).

This test ensures the import stays healthy so the app can start and the suite can run.
"""

from __future__ import annotations

import os


def test_models_import_succeeds() -> None:
    # Ensure required env exists if any module transitively reads settings.
    os.environ.setdefault("POSTGRES_URL", "postgresql://localhost:5000/myapp")
    os.environ.setdefault("POSTGRES_USER", "appuser")
    os.environ.setdefault("POSTGRES_PASSWORD", "dbuser123")
    os.environ.setdefault("POSTGRES_DB", "myapp")
    os.environ.setdefault("POSTGRES_PORT", "5000")
    os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_change_me")

    # Import triggers SQLAlchemy declarative mapping; should not raise.
    import src.api.models  # noqa: F401,WPS433
