"""Tests for RAGSystem.query() flow."""

from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass


class TestRAGSystemQuery:
    """Test RAGSystem.query() with mocked components."""

    def _make_rag_system(self, tool_manager, ai_generator, session_manager):
        """Create a RAGSystem with injected mocks (bypass __init__)."""
        from rag_system import RAGSystem

        # Create instance without calling __init__
        rag = object.__new__(RAGSystem)
        rag.tool_manager = tool_manager
        rag.ai_generator = ai_generator
        rag.session_manager = session_manager
        return rag

    def test_query_returns_answer_and_sources(self, tool_manager, ai_generator, mock_anthropic_client, session_manager):
        """Full flow: query returns (answer, sources) tuple."""
        from helpers import make_text_block, make_tool_use_block, make_response

        tool_block = make_tool_use_block("search_course_content", {"query": "Python"})
        tool_resp = make_response([tool_block], stop_reason="tool_use")
        final_resp = make_response([make_text_block("Python is great")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [tool_resp, final_resp]

        rag = self._make_rag_system(tool_manager, ai_generator, session_manager)
        answer, sources = rag.query("What is Python?")

        assert answer == "Python is great"
        assert isinstance(sources, list)

    def test_query_sources_are_dicts_with_name_url(self, tool_manager, ai_generator, mock_anthropic_client, session_manager):
        """Sources format matches what app.py Source model expects."""
        from helpers import make_text_block, make_tool_use_block, make_response

        tool_block = make_tool_use_block("search_course_content", {"query": "Python"})
        tool_resp = make_response([tool_block], stop_reason="tool_use")
        final_resp = make_response([make_text_block("Answer")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [tool_resp, final_resp]

        rag = self._make_rag_system(tool_manager, ai_generator, session_manager)
        _, sources = rag.query("Python question")

        # Sources should be populated by the tool execution
        for source in sources:
            assert isinstance(source, dict)
            assert "name" in source
            assert "url" in source

    def test_query_resets_sources_after_retrieval(self, tool_manager, ai_generator, mock_anthropic_client, session_manager):
        """After query, tool_manager.get_last_sources() returns empty."""
        from helpers import make_text_block, make_tool_use_block, make_response

        tool_block = make_tool_use_block("search_course_content", {"query": "test"})
        tool_resp = make_response([tool_block], stop_reason="tool_use")
        final_resp = make_response([make_text_block("Answer")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [tool_resp, final_resp]

        rag = self._make_rag_system(tool_manager, ai_generator, session_manager)
        rag.query("test")

        assert tool_manager.get_last_sources() == []

    def test_query_updates_session_history(self, tool_manager, ai_generator, mock_anthropic_client, session_manager):
        """query() with session_id saves exchange to session manager."""
        from helpers import make_text_block, make_response

        text_resp = make_response([make_text_block("Hello")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.return_value = text_resp

        rag = self._make_rag_system(tool_manager, ai_generator, session_manager)
        sid = session_manager.create_session()
        rag.query("Hi", session_id=sid)

        history = session_manager.get_conversation_history(sid)
        assert history is not None
        assert "Hi" in history or "Hello" in history

    def test_query_without_session(self, tool_manager, ai_generator, mock_anthropic_client, session_manager):
        """query() works with session_id=None."""
        from helpers import make_text_block, make_response

        text_resp = make_response([make_text_block("Answer")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.return_value = text_resp

        rag = self._make_rag_system(tool_manager, ai_generator, session_manager)
        answer, sources = rag.query("test", session_id=None)

        assert answer == "Answer"
        assert isinstance(sources, list)

    def test_query_passes_tools_to_ai_generator(self, tool_manager, ai_generator, mock_anthropic_client, session_manager):
        """Tool definitions are passed to ai_generator.generate_response()."""
        from helpers import make_text_block, make_response

        text_resp = make_response([make_text_block("OK")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.return_value = text_resp

        rag = self._make_rag_system(tool_manager, ai_generator, session_manager)
        rag.query("test")

        # Check that the first API call included tools
        call_kwargs = mock_anthropic_client.messages.create.call_args[1]
        assert "tools" in call_kwargs
        assert len(call_kwargs["tools"]) > 0
        assert call_kwargs["tools"][0]["name"] == "search_course_content"
