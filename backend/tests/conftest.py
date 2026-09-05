"""
tests/conftest.py
-----------------
Pytest configuration and fixtures.
"""

import sys
from pathlib import Path
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.database import engine

@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    await engine.dispose()
