"""
Contract tests for WebSocket protocol compliance.
Tests that messages conform to the defined protocol specification.
"""

import pytest
import json
from shader_copilot.server.messages import (
    MessageType,
    ServerMessageType,
    parse_message,
    create_response,
    create_stream_chunk,
    create_error,
    create_tool_call_request,
    create_confirm_request,
    create_progress_update,
    create_shader_preview,
)


class TestClientToServerMessages:
    """Tests for client-to-server message contract compliance."""

    def test_session_init_contract(self):
        """SESSION_INIT must have type and payload with project_path."""
        raw = {
            "type": "SESSION_INIT",
            "payload": {
                "project_path": "/path/to/unity/project",
                "config": {
                    "output_directory": "Shaders/Generated",
                    "max_retry_count": 3,
                    "model_config": {
                        "router_model": "qwen-turbo",
                        "code_model": "qwen-max",
                        "vl_model": "qwen-vl-plus",
                    },
                },
            },
        }

        msg = parse_message(raw)

        assert msg is not None
        assert msg.type == MessageType.SESSION_INIT
        assert msg.payload.project_path is not None

    def test_user_message_contract(self):
        """USER_MESSAGE must have type, session_id, and payload with content."""
        raw = {
            "type": "USER_MESSAGE",
            "session_id": "sess-abc123",
            "payload": {"content": "Create a dissolve shader", "images": []},
        }

        msg = parse_message(raw)

        assert msg is not None
        assert msg.type == MessageType.USER_MESSAGE
        assert msg.session_id is not None
        assert msg.payload.content is not None

    def test_tool_response_contract(self):
        """TOOL_RESPONSE must have type, session_id, and payload with tool_call_id and result."""
        raw = {
            "type": "TOOL_RESPONSE",
            "session_id": "sess-abc123",
            "payload": {
                "tool_call_id": "call-xyz789",
                "result": {
                    "success": True,
                    "shader_path": "Assets/Shaders/Generated/Dissolve.shader",
                    "errors": [],
                },
            },
        }

        msg = parse_message(raw)

        assert msg is not None
        assert msg.type == MessageType.TOOL_RESPONSE

    def test_confirm_response_contract(self):
        """CONFIRM_RESPONSE must have confirm_id and approved boolean."""
        raw = {
            "type": "CONFIRM_RESPONSE",
            "session_id": "sess-abc123",
            "payload": {"confirm_id": "confirm-456", "approved": True},
        }

        msg = parse_message(raw)

        assert msg is not None
        assert msg.type == MessageType.CONFIRM_RESPONSE
        assert isinstance(msg.payload.approved, bool)


class TestServerToClientMessages:
    """Tests for server-to-client message contract compliance."""

    def test_response_contract(self):
        """RESPONSE must have type, session_id, and payload with content."""
        msg = create_response(
            session_id="sess-abc123",
            content="I'll create a dissolve shader for you.",
        )

        assert msg["type"] == ServerMessageType.RESPONSE
        assert msg["session_id"] == "sess-abc123"
        assert "content" in msg["payload"]

        # Verify JSON serializable
        json_str = json.dumps(msg)
        parsed = json.loads(json_str)
        assert parsed["type"] == "RESPONSE"

    def test_stream_chunk_contract(self):
        """STREAM_CHUNK must have content and is_final."""
        msg = create_stream_chunk(
            session_id="sess-abc123",
            content="Shader code chunk...",
            is_final=False,
        )

        assert msg["type"] == ServerMessageType.STREAM_CHUNK
        assert "content" in msg["payload"]
        assert "is_final" in msg["payload"]
        assert isinstance(msg["payload"]["is_final"], bool)

    def test_error_contract(self):
        """ERROR must have code and message."""
        msg = create_error(
            session_id="sess-abc123",
            code="COMPILATION_ERROR",
            message="Shader failed to compile at line 42",
        )

        assert msg["type"] == ServerMessageType.ERROR
        assert "code" in msg["payload"]
        assert "message" in msg["payload"]

    def test_tool_call_request_contract(self):
        """TOOL_CALL_REQUEST must have tool_call_id, tool_name, and arguments."""
        msg = create_tool_call_request(
            session_id="sess-abc123",
            tool_call_id="call-xyz789",
            tool_name="compile_shader",
            arguments={
                "code": 'Shader "Test" { SubShader { Pass {} } }',
                "output_path": "Assets/Shaders/Test.shader",
            },
        )

        assert msg["type"] == ServerMessageType.TOOL_CALL_REQUEST
        assert "tool_call_id" in msg["payload"]
        assert "tool_name" in msg["payload"]
        assert "arguments" in msg["payload"]

    def test_confirm_request_contract(self):
        """CONFIRM_REQUEST must have confirm_id, action, and details."""
        msg = create_confirm_request(
            session_id="sess-abc123",
            confirm_id="confirm-456",
            action="save_shader",
            details={
                "path": "Assets/Shaders/Generated/Dissolve.shader",
                "overwrite": True,
            },
        )

        assert msg["type"] == ServerMessageType.CONFIRM_REQUEST
        assert "confirm_id" in msg["payload"]
        assert "action" in msg["payload"]
        assert "details" in msg["payload"]

    def test_progress_update_contract(self):
        """PROGRESS_UPDATE must have stage and message."""
        msg = create_progress_update(
            session_id="sess-abc123",
            stage="generating",
            message="Generating shader code...",
            progress=0.5,
        )

        assert msg["type"] == ServerMessageType.PROGRESS_UPDATE
        assert "stage" in msg["payload"]
        assert "message" in msg["payload"]

    def test_shader_preview_contract(self):
        """SHADER_PREVIEW must have code and optional metadata."""
        msg = create_shader_preview(
            session_id="sess-abc123",
            code='Shader "Custom/Test" { SubShader { Pass {} } }',
            shader_name="Custom/Test",
        )

        assert msg["type"] == ServerMessageType.SHADER_PREVIEW
        assert "code" in msg["payload"]


class TestMessageSerializationRoundtrip:
    """Tests for message serialization and deserialization."""

    def test_session_init_roundtrip(self):
        """SESSION_INIT survives JSON roundtrip."""
        original = {
            "type": "SESSION_INIT",
            "payload": {
                "project_path": "/path/to/project",
                "config": {"max_retry_count": 3},
            },
        }

        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        msg = parse_message(parsed)

        assert msg is not None
        assert msg.payload.project_path == "/path/to/project"

    def test_unicode_content_roundtrip(self):
        """Messages with Unicode content survive roundtrip."""
        original = {
            "type": "USER_MESSAGE",
            "session_id": "sess-123",
            "payload": {"content": "创建一个全息着色器 🎨", "images": []},
        }

        json_str = json.dumps(original, ensure_ascii=False)
        parsed = json.loads(json_str)
        msg = parse_message(parsed)

        assert msg is not None
        assert "全息着色器" in msg.payload.content
        assert "🎨" in msg.payload.content

    def test_large_shader_code_roundtrip(self):
        """Large shader code survives roundtrip without truncation."""
        shader_code = 'Shader "Test" {\n' + "// " * 10000 + "\n}"

        msg = create_shader_preview(
            session_id="sess-123",
            code=shader_code,
        )

        json_str = json.dumps(msg)
        parsed = json.loads(json_str)

        assert len(parsed["payload"]["code"]) == len(shader_code)


class TestMessageTypeEnums:
    """Tests for message type enum values."""

    def test_client_message_types(self):
        """All client message types are defined."""
        expected_types = [
            "SESSION_INIT",
            "USER_MESSAGE",
            "TOOL_RESPONSE",
            "CONFIRM_RESPONSE",
            "CANCEL_TASK",
            "SESSION_END",
        ]

        for type_name in expected_types:
            assert hasattr(MessageType, type_name), f"Missing type: {type_name}"

    def test_server_message_types(self):
        """All server message types are defined."""
        expected_types = [
            "SESSION_READY",
            "RESPONSE",
            "STREAM_CHUNK",
            "ERROR",
            "TOOL_CALL_REQUEST",
            "CONFIRM_REQUEST",
            "PROGRESS_UPDATE",
            "SHADER_PREVIEW",
            "TASK_COMPLETE",
            "SESSION_ENDED",
        ]

        for type_name in expected_types:
            assert hasattr(ServerMessageType, type_name), f"Missing type: {type_name}"
