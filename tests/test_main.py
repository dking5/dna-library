# tests/test_main.py
import json

import json

import pytest
import pytest_asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch as mock_patch
from httpx import AsyncClient, ASGITransport, patch
from sqlalchemy import text
from app import crud
from app import database
from app.api.genes import process_fasta_in_background
from app.main import app
from app.database import engine, AsyncSessionLocal, get_db, get_redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base

pytestmark = pytest.mark.asyncio

BASE_URL = "http://testserver"
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        if "postgresql" in str(test_engine.url):
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        from app.database import Base
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()

@pytest_asyncio.fixture
async def client():
    # 使用 ASGITransport 直接调用 FastAPI 应用，无需启动真实服务器
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac

async def test_create_gene():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        
        response = await ac.post("/api/v1/genes/",json={
            "label": "TEST-1",
            "sequence": "ATCG"
        })
    
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "TEST-1"
        assert "id" in data

async def test_search_genes_with_cache():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        await ac.post("/api/v1/genes/", json={"label": "CACHE-TEST", "sequence": "AAAA"})
        res1 = await ac.get("/api/v1/genes/search", params={"q": "AAAA"})
        assert res1.status_code == 200
        
        res2 = await ac.get("/api/v1/genes/search", params={"q": "AAAA"})
        assert res2.status_code == 200
        

async def test_get_non_existent_gene():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        response = await ac.get("/api/v1/genes/9999")
        assert response.status_code == 404

async def test_get_gene_with_stats():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        # First, create a gene
        response = await ac.post("/api/v1/genes/", json={
            "label": "TEST-2",
            "sequence": "ATCGATCG"
        })
        if response.status_code == 400:
            response = await ac.get("/api/v1/genes/search?q=TEST-2")
            assert response.status_code == 200
        else:
            assert response.status_code == 200
        data = response.json()
        gene_id = data["id"]

        # Now, retrieve the gene and check stats
        response = await ac.get(f"/api/v1/genes/{gene_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["gc_content"] == 0.5

async def test_update_gene_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        response = await ac.put("/api/v1/genes/genes/99999", json={"label": "NEW", "sequence": "ATCG"})
        assert response.status_code == 404

async def test_delete_gene_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        res = await ac.post("/api/v1/genes/", json={"label": "TO-DEL", "sequence": "ATCG"})
        gid = res.json()["id"]
        del_res = await ac.delete(f"/api/v1/genes/{gid}")
        assert del_res.status_code == 200

async def test_upload_fasta_invalid_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        files = {"file": ("test.txt", b"ATCG", "text/plain")}
        response = await ac.post("/api/v1/genes/upload-fasta/", files=files)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

@pytest.mark.asyncio
async def test_process_fasta_logic_directly():
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal(bind=conn) as db:
            fasta_str = ">DIRECT-1\nATCG\n>DIRECT-2\nGCTA"
            mock_cache = AsyncMock()
            mock_cache.scan_iter = MagicMock()
            mock_cache.scan_iter.return_value.__aiter__.return_value = []
            await process_fasta_in_background(db=db, fasta_str=fasta_str, cache=mock_cache)        
            
            from sqlalchemy import select
            from app.models import Gene
            result = await db.execute(select(Gene))
            genes = result.scalars().all()
            assert len(genes) >= 2
            assert any(g.label == "DIRECT-1" for g in genes)
            mock_cache.scan_iter.assert_called_with("search:*")
            await db.commit() 

async def test_update_genes_with_cache():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        res = await ac.post("/api/v1/genes/", json={"label": "TO-DEL", "sequence": "ATCG"})
        gid = res.json()["id"]
        res1 = await ac.put(f"/api/v1/genes/{gid}", json={"label": "UPDATED", "sequence": "ATCG"})
        assert res1.status_code == 200
        res2 = await ac.get(f"/api/v1/genes/{gid}")
        assert res2.status_code == 200
        assert res2.json()["sequence"] == "ATCG"

@pytest.mark.asyncio
async def test_get_gene_metadata_pure_mock():
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    
    mock_gene = MagicMock()
    mock_gene.id = 123
    mock_gene.label = "MOCK_GENE"
    mock_meta_json = json.dumps({"id": 123, "label": "MOCK_GENE"})

    mock_redis.hget.return_value = None  # 缓存没命中
    
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = mock_gene
    mock_db.execute.return_value = mock_execute_result
    
    with mock_patch("app.crud.serialize_gene_meta") as mocked_serialize:
        mocked_serialize.return_value = mock_meta_json
        result = await crud.get_gene_metadata(mock_db, mock_redis, gene_id=123)        
        assert result["label"] == "MOCK_GENE"
        mock_db.execute.assert_called_once()
        mock_redis.hset.assert_called_with("genes_meta_hash", "123", mock_meta_json)

    mock_redis.hget.return_value = json.dumps({"id": 123, "label": "FROM_CACHE"})    
    result_from_cache = await crud.get_gene_metadata(mock_db, mock_redis, gene_id=123)    
    assert result_from_cache["label"] == "FROM_CACHE"
    assert mock_db.execute.call_count == 1

@pytest.mark.asyncio
async def test_merge_genes_atomic_success():
    mock_db = MagicMock()
    mock_redis = AsyncMock()
    class AsyncCM:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
    mock_db.begin.return_value = AsyncCM()
    mock_db.execute = AsyncMock()
    mock_db.flush = AsyncMock()

    gene_a = MagicMock(id=1, sequence="AT", label="A")
    gene_b = MagicMock(id=2, sequence="GC", label="B")

    res_a = MagicMock()
    res_a.scalar_one_or_none.return_value = gene_a
    res_b = MagicMock()
    res_b.scalar_one_or_none.return_value = gene_b
    
    mock_db.execute.side_effect = [res_a, res_b, AsyncMock()] # 前两次查询，第三次是 delete

    with mock_patch("app.crud.calculate_dna_stats") as mock_calc:
        mock_calc.return_value = {"gc_content": 0.5}
        
        result = await crud.merge_genes_atomic(
            mock_db, mock_redis, id_a=1, id_b=2, new_label="MERGED"
        )

        assert result.label == "MERGED"
        assert result.sequence == "ATGC"
        
        mock_redis.hdel.assert_called_with("genes_meta_hash", "1", "2")
        mock_db.add.assert_called_once()

@pytest.mark.asyncio
async def test_merge_genes_atomic_not_found():
    mock_db = MagicMock()
    mock_redis = AsyncMock()
    class AsyncCM:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): pass
    mock_db.begin.return_value = AsyncCM()
    mock_db.execute = AsyncMock()
    mock_db.flush = AsyncMock()

    res = MagicMock()
    res.scalar_one_or_none.return_value = None # 模拟找不到
    mock_db.execute.return_value = res

    with pytest.raises(ValueError, match="One or both genes not found"):
        await crud.merge_genes_atomic(mock_db, mock_redis, 1, 2, "FAIL")

@pytest.mark.asyncio
async def test_merge_genes_api_full_flow(client: AsyncClient):
    mock_redis = AsyncMock()
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        res1 = await ac.post("/api/v1/genes/", json={"label": "G11", "sequence": "AT"})
        g1 = res1.json()["id"]
        res2 = await ac.post("/api/v1/genes/", json={"label": "G22", "sequence": "GC"})
        g2 = res2.json()["id"]
        res3 = await ac.post(
            "/api/v1/genes/merge/", 
            params={
                "id_a": g1, 
                "id_b": g2, 
                "label": "MERGED_API"
            }
        )
        assert res3.status_code == 200
        assert res3.json()["sequence"] == "ATGC"
        assert res3.json()["label"] == "MERGED_API"

        res4 = await ac.post(
            "/api/v1/genes/merge/", 
            params={
                "id_a": 999998, 
                "id_b": 999999, 
                "label": "MERGED_API"
            }
        )
        assert res4.status_code == 404
        assert "not found" in res4.json()["detail"]
        
    app.dependency_overrides.clear()
