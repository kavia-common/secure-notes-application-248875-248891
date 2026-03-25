"""
Regression test for a current SQLAlchemy model definition error.

At present, importing src.api.models crashes with:

sqlalchemy.exc.ArgumentError: Can't add unnamed column to column collection

This happens because Tag.__table_args__ includes func.lower("name") inside a
UniqueConstraint, which SQLAlchemy does not accept as a "column" without a
proper label / text construct.

Once the application code is fixed, this test should be updated to assert the
import succeeds (or removed and replaced with a more specific schema test).
"""

from __future__ import annotations

import os

import pytest


def test_models_import_currently_fails_due_to_uniqueconstraint_expression() -> None:
    # Ensure required env exists if any module transitively reads settings.
    os.environ.setdefault("POSTGRES_URL", "postgresql://localhost:5000/myapp")
    os.environ.setdefault("POSTGRES_USER", "appuser")
    os.environ.setdefault("POSTGRES_PASSWORD", "dbuser123")
    os.environ.setdefault("POSTGRES_DB", "myapp")
    os.environ.setdefault("POSTGRES_PORT", "5000")
    os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_change_me")

    with pytest.raises(Exception) as excinfo:
        # Import triggers SQLAlchemy declarative mapping
        import src.api.models  # noqa: F401,WPS433

    # Assert a stable substring so we know exactly what broke.
    assert "Can't add unnamed column" in str(excinfo.value)
