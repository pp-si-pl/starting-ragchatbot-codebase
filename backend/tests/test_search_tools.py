"""Tests for CourseSearchTool and ToolManager."""

from unittest.mock import MagicMock
from vector_store import SearchResults
from search_tools import CourseSearchTool, ToolManager


class TestCourseSearchToolExecute:
    def test_execute_returns_formatted_results(self, search_tool, sample_search_results):
        """Search with results → formatted output contains headers and text."""
        result = search_tool.execute(query="Python basics")

        assert "[Intro to Python - Lesson 1]" in result
        assert "Chunk about Python basics" in result
        assert "[Intro to Python - Lesson 2]" in result
        assert "Chunk about Python functions" in result

    def test_execute_populates_last_sources(self, search_tool):
        """After execute, last_sources contains dicts with name and url keys."""
        search_tool.execute(query="Python basics")

        assert len(search_tool.last_sources) == 2
        for source in search_tool.last_sources:
            assert "name" in source
            assert "url" in source
        assert search_tool.last_sources[0]["name"] == "Intro to Python - Lesson 1"

    def test_execute_empty_results(self, search_tool, mock_vector_store, empty_search_results):
        """Empty results → 'No relevant content found' message."""
        mock_vector_store.search.return_value = empty_search_results

        result = search_tool.execute(query="nonexistent topic")

        assert "No relevant content found" in result

    def test_execute_with_error(self, search_tool, mock_vector_store, error_search_results):
        """Error in SearchResults → error message returned."""
        mock_vector_store.search.return_value = error_search_results

        result = search_tool.execute(query="anything")

        assert "Search error: connection failed" in result

    def test_execute_with_course_filter(self, search_tool, mock_vector_store):
        """course_name is forwarded to VectorStore.search()."""
        search_tool.execute(query="test", course_name="Python")

        mock_vector_store.search.assert_called_once_with(
            query="test", course_name="Python", lesson_number=None
        )

    def test_execute_with_lesson_filter(self, search_tool, mock_vector_store):
        """lesson_number is forwarded to VectorStore.search()."""
        search_tool.execute(query="test", lesson_number=3)

        mock_vector_store.search.assert_called_once_with(
            query="test", course_name=None, lesson_number=3
        )


class TestCourseSearchToolDefinition:
    def test_get_tool_definition_schema(self, search_tool):
        """Tool definition has required name, description, and input_schema."""
        defn = search_tool.get_tool_definition()

        assert defn["name"] == "search_course_content"
        assert "description" in defn
        schema = defn["input_schema"]
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "query" in schema["required"]


class TestToolManager:
    def test_register_and_execute(self, tool_manager):
        """Registered tool can be executed by name."""
        result = tool_manager.execute_tool("search_course_content", query="test")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_last_sources(self, tool_manager):
        """Sources are populated after execute and cleared after reset."""
        tool_manager.execute_tool("search_course_content", query="test")

        sources = tool_manager.get_last_sources()
        assert len(sources) > 0
        assert "name" in sources[0]
        assert "url" in sources[0]

        tool_manager.reset_sources()
        assert tool_manager.get_last_sources() == []

    def test_execute_unknown_tool(self, tool_manager):
        """Executing an unregistered tool returns an error message."""
        result = tool_manager.execute_tool("nonexistent_tool", query="test")

        assert "not found" in result
