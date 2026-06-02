"""Tests for vector store."""
import pytest
from src.memory.vector_store import VectorStore, HybridRetriever


def test_vector_store_adds_embedding():
    """VectorStore 应该能添加嵌入向量。"""
    store = VectorStore(dimension=3)
    
    doc_id = store.add(
        text="Hello World",
        embedding=[1.0, 0.0, 0.0]
    )
    
    assert doc_id is not None
    assert store.size() == 1


def test_vector_store_searches_similar():
    """VectorStore 应该能搜索相似文档。"""
    store = VectorStore(dimension=3)
    
    store.add("Hello", [1.0, 0.0, 0.0])
    store.add("World", [0.0, 1.0, 0.0])
    store.add("Hi", [0.9, 0.1, 0.0])
    
    results = store.search([1.0, 0.0, 0.0], top_k=2)
    
    assert len(results) == 2
    assert results[0]["text"] == "Hello"
    assert results[0]["score"] > 0.9


def test_vector_store_deletes_document():
    """VectorStore 应该能删除文档。"""
    store = VectorStore(dimension=3)
    
    doc_id = store.add("Hello", [1.0, 0.0, 0.0])
    assert store.size() == 1
    
    result = store.delete(doc_id)
    assert result is True
    assert store.size() == 0


def test_vector_store_gets_document():
    """VectorStore 应该能获取文档。"""
    store = VectorStore(dimension=3)
    
    doc_id = store.add(
        text="Hello",
        embedding=[1.0, 0.0, 0.0],
        metadata={"type": "greeting"}
    )
    
    doc = store.get(doc_id)
    assert doc is not None
    assert doc["text"] == "Hello"
    assert doc["metadata"]["type"] == "greeting"


def test_vector_store_clears():
    """VectorStore 应该能清空。"""
    store = VectorStore(dimension=3)
    
    store.add("Hello", [1.0, 0.0, 0.0])
    store.add("World", [0.0, 1.0, 0.0])
    assert store.size() == 2
    
    store.clear()
    assert store.size() == 0


@pytest.mark.asyncio
async def test_hybrid_retriever_combines_results():
    """HybridRetriever 应该能合并向量和关键词结果。"""
    store = VectorStore(dimension=3)
    
    store.add("Python programming", [1.0, 0.0, 0.0])
    store.add("Java programming", [0.0, 1.0, 0.0])
    
    retriever = HybridRetriever(store)
    
    keyword_results = [
        {"id": "Python programming", "text": "Python programming", "score": 0.8}
    ]
    
    results = await retriever.retrieve(
        query="Python",
        query_embedding=[1.0, 0.0, 0.0],
        keyword_results=keyword_results,
        top_k=2
    )
    
    assert len(results) > 0
    assert results[0]["text"] == "Python programming"
