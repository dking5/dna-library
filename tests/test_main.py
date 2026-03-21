# tests/test_main.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app, get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

pytestmark = pytest.mark.asyncio

BASE_URL = "http://testserver"
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        from app.database import Base
        await conn.run_sync(Base.metadata.create_all)
    yield

async def test_create_gene():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        
        response = await ac.post("/genes/",json={
            "label": "TEST-1",
            "sequence": "ATCG"
        })
    
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "TEST-1"
        assert "id" in data

async def test_get_non_existent_gene():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        response = await ac.get("/genes/9999")
        assert response.status_code == 404

async def test_get_gene_with_stats():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        # First, create a gene
        response = await ac.post("/genes/", json={
            "label": "TEST-2",
            "sequence": "ATCGATCG"
        })
        if response.status_code == 400:
            print(response.text)
            response = await ac.get("/genes/search?q=TEST-2")
            assert response.status_code == 200
        else:
            assert response.status_code == 200
        data = response.json()
        gene_id = data["id"]

        # Now, retrieve the gene and check stats
        response = await ac.get(f"/genes/{gene_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["a_count"] == 2
        assert data["stats"]["t_count"] == 2
        assert data["stats"]["c_count"] == 2
        assert data["stats"]["g_count"] == 2
        assert data["stats"]["gc_content"] == 0.5
    