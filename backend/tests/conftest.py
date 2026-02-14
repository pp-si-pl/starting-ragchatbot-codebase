import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional

# Add backend to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vector_store import SearchResults
from search_tools import CourseSearchTool, ToolManager
from ai_generator import AIGenerator
from session_manager import SessionManager


# --- SearchResults fixtures ---

@pytest.fixture
def sample_search_results():
    """SearchResults with two matching documents."""
    return SearchResults(
        documents=["Chunk about Python basics", "Chunk about Python functions"],
        metadata=[
            {"course_title": "Intro to Python", "lesson_number": 1, "chunk_index": 0},
            {"course_title": "Intro to Python", "lesson_number": 2, "chunk_index": 1},
        ],
        distances=[0.3, 0.5],
    )


@pytest.fixture
def empty_search_results():
    """SearchResults with no documents."""
    return SearchResults(documents=[], metadata=[], distances=[])


@pytest.fixture
def error_search_results():
    """SearchResults with an error."""
    return SearchResults(documents=[], metadata=[], distances=[], error="Search error: connection failed")


# --- Mock VectorStore ---

@pytest.fixture
def mock_vector_store(sample_search_results):
    """VectorStore mock that returns sample results by default."""
    store = MagicMock()
    store.search.return_value = sample_search_results
    store.get_lesson_link.return_value = "https://example.com/lesson/1"
    return store


# --- CourseSearchTool & ToolManager fixtures ---

@pytest.fixture
def search_tool(mock_vector_store):
    """CourseSearchTool backed by a mock VectorStore."""
    return CourseSearchTool(mock_vector_store)


@pytest.fixture
def tool_manager(search_tool):
    """ToolManager with a registered CourseSearchTool."""
    tm = ToolManager()
    tm.register_tool(search_tool)
    return tm


# --- AIGenerator fixture ---

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    return MagicMock()


@pytest.fixture
def ai_generator(mock_anthropic_client):
    """AIGenerator with a mocked Anthropic client."""
    with patch("ai_generator.anthropic.Anthropic", return_value=mock_anthropic_client):
        gen = AIGenerator(api_key="test-key", model="test-model")
    return gen


# --- SessionManager fixture ---

@pytest.fixture
def session_manager():
    return SessionManager(max_history=5)


# --- API test fixtures ---

# Pydantic models mirroring app.py (avoids importing app.py which mounts static files)
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class Source(BaseModel):
    name: str
    url: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    session_id: str

class CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


@pytest.fixture
def mock_rag_system():
    """Mock RAGSystem for API endpoint tests."""
    rag = MagicMock()
    rag.query.return_value = (
        "Python is a programming language.",
        [{"name": "Intro to Python - Lesson 1", "url": "https://example.com/lesson/1"}],
    )
    rag.session_manager.create_session.return_value = "test-session-123"
    rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Intro to Python", "Advanced ML"],
    }
    return rag


@pytest.fixture
def test_app(mock_rag_system):
    """FastAPI test app with the same endpoints as app.py but no static file mount."""
    app = FastAPI()

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()
            answer, sources = mock_rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


@pytest.fixture
def client(test_app):
    """TestClient for the test FastAPI app."""
    return TestClient(test_app)
