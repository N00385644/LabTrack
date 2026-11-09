"""Fixtures de las pruebas de LabTrack."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("LABTRACK_SECRET_KEY", "test-secret-key-labtrack")

from app.factory import create_app  # noqa: E402
from app.seed import seed_database  # noqa: E402


@pytest.fixture
def app(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'labtrack_test.db').as_posix()}"
    application = create_app(
        database_url=database_url,
        secret_key="test-secret-key-labtrack",
        seed=False,
    )
    with application.state.session_factory() as db:
        seed_database(db, include_load_users=False, with_demo_reservations=False)
    yield application
    application.state.engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db(app):
    with app.state.session_factory() as session:
        yield session
