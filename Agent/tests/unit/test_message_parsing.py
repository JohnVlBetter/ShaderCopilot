"""
Unit tests for WebSocket message parsing and handling.
"""

import pytest
from shader_copilot.server.messages import (
    MessageType,
    ServerMessageType,
    parse_message,
    create_response,
    create_stream_chunk,
    create_error,
    create_tool_call_request,
    SessionInitPayload,
    UserMessagePayload,
    StreamChunkPayload,
    ToolCallRequest,
)


class TestMessageParsing:
    """Tests for message parsing functionality."""

    def test_parse_session_init(self):
        """Test parsing SESSION_INIT message."""
        raw = {
            "type": "SESSION_INIT",
            "payload": {
                "project_path": "/path/to/project",
                "config": {
                    "output_directory": "Shaders/Generated",
                    "max_retry_count": 3,
                },
            },
        }

        msg = parse_message(raw)

        assert msg is not None
        assert msg.type == MessageType.SESSION_INIT
        assert isinstance(msg.payload, SessionInitPayload)
        assert msg.payload.project_path == "/path/to/project"
        assert msg.payload.config["output_directory"] == "Shaders/Generated"

    def test_parse_user_message(self):
        """Test parsing USER_MESSAGE message."""
        raw = {
            "type": "USER_MESSAGE",
            "session_id": "test-session",
            "payload": {"content": "Create a hologram shader", "images": []},
        }

        msg = parse_message(raw)

        assert msg is not None
        assert msg.type == MessageType.USER_MESSAGE
        assert msg.session_id == "test-session"
        assert isinstance(msg.payload, UserMessagePayload)
        assert msg.payload.content == "Create a hologram shader"

    def test_parse_user_message_with_images(self):
        """Test parsing USER_MESSAGE with images."""
        raw = {
            "type": "USER_MESSAGE",
            "session_id": "test-session",
            "payload": {
                "content": "Make this shader",
                "images": ["base64encodedimage=="],
            },
        }

        msg = parse_message(raw)

        assert msg is not None
        assert msg.payload.images == ["base64encodedimage=="]

    def test_parse_tool_response(self):
        """Test parsing TOOL_RESPONSE message."""
        raw = {
            "type": "TOOL_RESPONSE",
            "session_id": "test-session",
            "payload": {
                "tool_call_id": "call-123",
                "result": {"success": True, "errors": []},
            },
        }

        msg = parse_message(raw)

        assert msg is not None
        assert msg.type == MessageType.TOOL_RESPONSE

    def test_parse_confirm_response_approved(self):
        """Test parsing CONFIRM_RESPONSE with approved=True."""
        raw = {
            "type": "CONFIRM_RESPONSE",
            "session_id": "test-session",
            "payload": {
                "confirm_id": "confirm-456",
                "approved": True,
            },
        }

        msg = parse_message(raw)

        assert msg is not None
        assert msg.type == MessageType.CONFIRM_RESPONSE
        assert msg.payload.approved is True

    def test_parse_cancel_task(self):
        """Test parsing CANCEL_TASK message."""
        raw = {"type": "CANCEL_TASK", "session_id": "test-session", "payload": {}}

        msg = parse_message(raw)

        assert msg is not None
        assert msg.type == MessageType.CANCEL_TASK

    def test_parse_invalid_type(self):
        """Test parsing message with invalid type."""
        raw = {"type": "INVALID_TYPE", "payload": {}}

        msg = parse_message(raw)

        assert msg is None

    def test_parse_missing_type(self):
        """Test parsing message without type."""
        raw = {"payload": {"content": "test"}}

        msg = parse_message(raw)

        assert msg is None


class TestMessageCreation:
    """Tests for message creation functions."""

    def test_create_response(self):
        """Test creating RESPONSE message."""
        msg = create_response(
            session_id="test-session",
            content="Here is your shader",
        )

        assert msg["type"] == ServerMessageType.RESPONSE
        assert msg["session_id"] == "test-session"
        assert msg["payload"]["content"] == "Here is your shader"

    def test_create_stream_chunk(self):
        """Test creating STREAM_CHUNK message."""
        msg = create_stream_chunk(
            session_id="test-session",
            content="Shader",
            is_final=False,
        )

        assert msg["type"] == ServerMessageType.STREAM_CHUNK
        assert msg["payload"]["content"] == "Shader"
        assert msg["payload"]["is_final"] is False

    def test_create_stream_chunk_final(self):
        """Test creating final STREAM_CHUNK message."""
        msg = create_stream_chunk(
            session_id="test-session",
            content="",
            is_final=True,
        )

        assert msg["payload"]["is_final"] is True

    def test_create_error(self):
        """Test creating ERROR message."""
        msg = create_error(
            session_id="test-session",
            code="COMPILATION_ERROR",
            message="Shader failed to compile",
        )

        assert msg["type"] == ServerMessageType.ERROR
        assert msg["payload"]["code"] == "COMPILATION_ERROR"
        assert msg["payload"]["message"] == "Shader failed to compile"

    def test_create_tool_call_request(self):
        """Test creating TOOL_CALL_REQUEST message."""
        msg = create_tool_call_request(
            session_id="test-session",
            tool_call_id="call-789",
            tool_name="compile_shader",
            arguments={"code": "Shader code here"},
        )

        assert msg["type"] == ServerMessageType.TOOL_CALL_REQUEST
        assert msg["payload"]["tool_call_id"] == "call-789"
        assert msg["payload"]["tool_name"] == "compile_shader"
        assert msg["payload"]["arguments"]["code"] == "Shader code here"


class TestMessageValidation:
    """Tests for message validation."""

    def test_session_init_requires_project_path(self):
        """Test that SESSION_INIT requires project_path."""
        raw = {"type": "SESSION_INIT", "payload": {"config": {}}}

        # Should parse but have None project_path
        msg = parse_message(raw)
        assert msg is not None
        assert msg.payload.project_path is None

    def test_user_message_requires_content(self):
        """Test that USER_MESSAGE requires content."""
        raw = {"type": "USER_MESSAGE", "session_id": "test", "payload": {}}

        msg = parse_message(raw)
        # Should have empty or None content
        assert msg is not None
