"""Shared test helpers for creating mock Anthropic responses."""

from unittest.mock import MagicMock


def make_text_block(text):
    """Create a mock text content block."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def make_tool_use_block(tool_name, tool_input, tool_id="tool_abc123"):
    """Create a mock tool_use content block."""
    block = MagicMock()
    block.type = "tool_use"
    block.name = tool_name
    block.input = tool_input
    block.id = tool_id
    return block


def make_response(content_blocks, stop_reason="end_turn"):
    """Create a mock Anthropic API response."""
    resp = MagicMock()
    resp.content = content_blocks
    resp.stop_reason = stop_reason
    return resp
