"""Tests for AIGenerator tool-call integration."""

from unittest.mock import MagicMock, call
from helpers import make_text_block, make_tool_use_block, make_response


class TestAIGeneratorDirectResponse:
    def test_direct_response_no_tools(self, ai_generator, mock_anthropic_client):
        """When Claude returns text directly, it's returned as-is."""
        text_resp = make_response([make_text_block("Hello, world!")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.return_value = text_resp

        result = ai_generator.generate_response(query="Hi")

        assert result == "Hello, world!"
        assert mock_anthropic_client.messages.create.call_count == 1


class TestAIGeneratorToolUse:
    def test_tool_use_triggers_execution(self, ai_generator, mock_anthropic_client, tool_manager):
        """When Claude returns tool_use, tool_manager.execute_tool() is called."""
        tool_block = make_tool_use_block("search_course_content", {"query": "Python basics"})
        tool_resp = make_response([tool_block], stop_reason="tool_use")
        final_resp = make_response([make_text_block("Here's what I found...")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [tool_resp, final_resp]

        result = ai_generator.generate_response(
            query="Tell me about Python",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        assert result == "Here's what I found..."

    def test_tool_use_second_api_call(self, ai_generator, mock_anthropic_client, tool_manager):
        """Tool use triggers a second API call with tool results in messages."""
        tool_block = make_tool_use_block("search_course_content", {"query": "test"})
        tool_resp = make_response([tool_block], stop_reason="tool_use")
        final_resp = make_response([make_text_block("Answer")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [tool_resp, final_resp]

        ai_generator.generate_response(
            query="test query",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        assert mock_anthropic_client.messages.create.call_count == 2
        # Second call's messages should contain tool_result
        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        messages = second_call_kwargs["messages"]
        last_msg = messages[-1]
        assert last_msg["role"] == "user"
        tool_results = last_msg["content"]
        assert any(item["type"] == "tool_result" for item in tool_results)

    def test_single_round_second_call_includes_tools(self, ai_generator, mock_anthropic_client, tool_manager):
        """After round 1 (< MAX_TOOL_ROUNDS), the second call still includes tools."""
        tool_block = make_tool_use_block("search_course_content", {"query": "test"})
        tool_resp = make_response([tool_block], stop_reason="tool_use")
        final_resp = make_response([make_text_block("Answer")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [tool_resp, final_resp]

        ai_generator.generate_response(
            query="test",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        assert "tools" in second_call_kwargs

    def test_tool_result_format(self, ai_generator, mock_anthropic_client, tool_manager):
        """Tool results are sent as {type: tool_result, tool_use_id: ..., content: ...}."""
        tool_block = make_tool_use_block("search_course_content", {"query": "test"}, tool_id="tool_xyz")
        tool_resp = make_response([tool_block], stop_reason="tool_use")
        final_resp = make_response([make_text_block("Answer")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [tool_resp, final_resp]

        ai_generator.generate_response(
            query="test",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        tool_results_msg = second_call_kwargs["messages"][-1]["content"]
        assert len(tool_results_msg) == 1
        tr = tool_results_msg[0]
        assert tr["type"] == "tool_result"
        assert tr["tool_use_id"] == "tool_xyz"
        assert isinstance(tr["content"], str)


class TestAIGeneratorMultiRound:
    def test_two_sequential_tool_rounds(self, ai_generator, mock_anthropic_client, tool_manager):
        """Two tool rounds: tool_use -> tool_use -> text. 3 API calls, 2 tool executions."""
        tool_block_1 = make_tool_use_block("search_course_content", {"query": "lesson 4"}, tool_id="t1")
        tool_block_2 = make_tool_use_block("search_course_content", {"query": "related"}, tool_id="t2")
        resp_1 = make_response([tool_block_1], stop_reason="tool_use")
        resp_2 = make_response([tool_block_2], stop_reason="tool_use")
        resp_3 = make_response([make_text_block("Combined answer")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [resp_1, resp_2, resp_3]

        result = ai_generator.generate_response(
            query="compare topics",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        assert result == "Combined answer"
        assert mock_anthropic_client.messages.create.call_count == 3

    def test_max_rounds_strips_tools(self, ai_generator, mock_anthropic_client, tool_manager):
        """On the final round (round == MAX_TOOL_ROUNDS), tools are omitted."""
        tool_block_1 = make_tool_use_block("search_course_content", {"query": "q1"}, tool_id="t1")
        tool_block_2 = make_tool_use_block("search_course_content", {"query": "q2"}, tool_id="t2")
        resp_1 = make_response([tool_block_1], stop_reason="tool_use")
        resp_2 = make_response([tool_block_2], stop_reason="tool_use")
        resp_3 = make_response([make_text_block("Final")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [resp_1, resp_2, resp_3]

        ai_generator.generate_response(
            query="test",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        # 3rd call (round 2 == MAX_TOOL_ROUNDS) should not have tools
        third_call_kwargs = mock_anthropic_client.messages.create.call_args_list[2][1]
        assert "tools" not in third_call_kwargs

    def test_exits_early_on_text_response(self, ai_generator, mock_anthropic_client, tool_manager):
        """If Claude returns text after round 1, loop exits early (2 API calls, not 3)."""
        tool_block = make_tool_use_block("search_course_content", {"query": "q1"}, tool_id="t1")
        resp_1 = make_response([tool_block], stop_reason="tool_use")
        resp_2 = make_response([make_text_block("Done")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [resp_1, resp_2]

        result = ai_generator.generate_response(
            query="test",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        assert result == "Done"
        assert mock_anthropic_client.messages.create.call_count == 2

    def test_tool_execution_error(self, ai_generator, mock_anthropic_client, tool_manager):
        """Tool execution errors are sent as is_error tool_results; method doesn't raise."""
        tool_block = make_tool_use_block("search_course_content", {"query": "fail"}, tool_id="t_err")
        resp_1 = make_response([tool_block], stop_reason="tool_use")
        resp_2 = make_response([make_text_block("Sorry, search failed")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [resp_1, resp_2]

        # Make execute_tool raise
        tool_manager.execute_tool = MagicMock(side_effect=RuntimeError("connection lost"))

        result = ai_generator.generate_response(
            query="test",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        assert result == "Sorry, search failed"
        # Verify error tool_result was sent
        second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1][1]
        tool_results_msg = second_call_kwargs["messages"][-1]["content"]
        tr = tool_results_msg[0]
        assert tr["is_error"] is True
        assert "connection lost" in tr["content"]

    def test_messages_accumulate_across_rounds(self, ai_generator, mock_anthropic_client, tool_manager):
        """After 2 rounds, the 3rd call has: [user, assistant_1, tool_results_1, assistant_2, tool_results_2]."""
        tb1 = make_tool_use_block("search_course_content", {"query": "q1"}, tool_id="t1")
        tb2 = make_tool_use_block("search_course_content", {"query": "q2"}, tool_id="t2")
        resp_1 = make_response([tb1], stop_reason="tool_use")
        resp_2 = make_response([tb2], stop_reason="tool_use")
        resp_3 = make_response([make_text_block("Final")], stop_reason="end_turn")
        mock_anthropic_client.messages.create.side_effect = [resp_1, resp_2, resp_3]

        ai_generator.generate_response(
            query="multi-step",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager,
        )

        third_call_kwargs = mock_anthropic_client.messages.create.call_args_list[2][1]
        messages = third_call_kwargs["messages"]
        assert len(messages) == 5
        assert messages[0]["role"] == "user"       # original query
        assert messages[1]["role"] == "assistant"   # tool_use round 1
        assert messages[2]["role"] == "user"        # tool_results round 1
        assert messages[3]["role"] == "assistant"   # tool_use round 2
        assert messages[4]["role"] == "user"        # tool_results round 2
