import sys
import os
from unittest.mock import MagicMock, patch

import pytest

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
