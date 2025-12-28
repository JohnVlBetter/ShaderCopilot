"""
Unit tests for session manager.
"""

import json
import tempfile
from pathlib import Path

import pytest

from shader_copilot.session.session_manager import (
    Message,
    Session,
    SessionManager,
    ShaderVersion,
    get_session_manager,
    set_session_manager,
)


class TestMessage:
    """Tests for Message model."""

    def test_create_message(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        """Test message with metadata."""
        msg = Message(
            role="assistant",
            content="Response",
            metadata={"model": "gpt-4", "tokens": 100},
        )

        assert msg.metadata["model"] == "gpt-4"
        assert msg.metadata["tokens"] == 100


class TestShaderVersion:
    """Tests for ShaderVersion model."""

    def test_create_shader_version(self):
        """Test creating a shader version."""
        version = ShaderVersion(
            code='Shader "Test" {}',
            name="Custom/Test",
            compile_success=True,
        )

        assert version.code == 'Shader "Test" {}'
        assert version.name == "Custom/Test"
        assert version.compile_success is True


class TestSession:
    """Tests for Session model."""

    def test_create_session(self):
        """Test creating a session."""
        session = Session(session_id="test-123")

        assert session.session_id == "test-123"
        assert len(session.messages) == 0
        assert session.current_shader == ""

    def test_add_message(self):
        """Test adding messages to session."""
        session = Session(session_id="test-123")

        session.add_message("user", "Create a toon shader")
        session.add_message("assistant", "I'll create a toon shader for you.")

        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"

    def test_set_current_shader(self):
        """Test setting current shader."""
        session = Session(session_id="test-123")

        code1 = 'Shader "Custom/Toon" { /* v1 */ }'
        code2 = 'Shader "Custom/Toon" { /* v2 */ }'

        session.set_current_shader(code1)
        assert session.current_shader == code1
        assert len(session.shader_history) == 1

        session.set_current_shader(code2)
        assert session.current_shader == code2
        assert len(session.shader_history) == 2

    def test_get_shader_history(self):
        """Test getting shader history."""
        session = Session(session_id="test-123")

        session.set_current_shader('Shader "V1" {}', compile_success=True)
        session.set_current_shader('Shader "V2" {}', compile_success=False)
        session.set_current_shader('Shader "V3" {}', compile_success=True)

        history = session.get_shader_history()

        assert len(history) == 3
        assert history[0].compile_success is True
        assert history[1].compile_success is False
        assert history[2].compile_success is True

    def test_set_property(self):
        """Test setting user properties."""
        session = Session(session_id="test-123")

        session.set_property("_BaseColor", "(1, 0, 0, 1)")
        session.set_property("_Glossiness", "0.5")

        props = session.get_properties()

        assert props["_BaseColor"] == "(1, 0, 0, 1)"
        assert props["_Glossiness"] == "0.5"

    def test_build_context(self):
        """Test building context from history."""
        session = Session(session_id="test-123")

        session.add_message("user", "Create a shader")
        session.add_message("assistant", "Here's your shader")
        session.add_message("user", "Add rim lighting")

        context = session.build_context()

        assert "Create a shader" in context
        assert "Here's your shader" in context
        assert "Add rim lighting" in context

    def test_build_context_with_limit(self):
        """Test context with message limit."""
        session = Session(session_id="test-123")

        for i in range(20):
            session.add_message("user", f"Message {i}")

        context = session.build_context(max_messages=5)

        # Should only include last 5 messages
        assert "Message 15" in context
        assert "Message 19" in context
        assert "Message 0" not in context

    def test_to_dict(self):
        """Test serialization to dict."""
        session = Session(session_id="test-123")
        session.add_message("user", "Hello")
        session.set_current_shader('Shader "Test" {}')

        data = session.to_dict()

        assert data["session_id"] == "test-123"
        assert len(data["messages"]) == 1
        assert data["current_shader"] == 'Shader "Test" {}'

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "session_id": "test-456",
            "messages": [{"role": "user", "content": "Test", "metadata": {}}],
            "current_shader": 'Shader "X" {}',
            "shader_history": [],
            "properties": {"_Color": "(1,1,1,1)"},
            "preview_object": "Cube",
            "background_color": "#000000",
        }

        session = Session.from_dict(data)

        assert session.session_id == "test-456"
        assert session.preview_object == "Cube"
        assert session.properties["_Color"] == "(1,1,1,1)"


class TestSessionManager:
    """Tests for SessionManager."""

    def test_create_session(self):
        """Test creating a new session."""
        manager = SessionManager()

        session = manager.create_session("new-123")

        assert session.session_id == "new-123"

    def test_create_session_auto_id(self):
        """Test creating session with auto-generated ID."""
        manager = SessionManager()

        session = manager.create_session()

        assert session.session_id is not None
        assert len(session.session_id) > 0

    def test_get_session(self):
        """Test getting an existing session."""
        manager = SessionManager()

        manager.create_session("get-test")
        session = manager.get_session("get-test")

        assert session is not None
        assert session.session_id == "get-test"

    def test_get_nonexistent_session(self):
        """Test getting a non-existent session."""
        manager = SessionManager()

        session = manager.get_session("does-not-exist")

        assert session is None

    def test_get_or_create_session_existing(self):
        """Test get_or_create with existing session."""
        manager = SessionManager()

        created = manager.create_session("existing-123")
        created.add_message("user", "Previous message")

        retrieved = manager.get_or_create_session("existing-123")

        assert len(retrieved.messages) == 1

    def test_get_or_create_session_new(self):
        """Test get_or_create with new session."""
        manager = SessionManager()

        session = manager.get_or_create_session("new-456")

        assert session is not None
        assert session.session_id == "new-456"
        assert len(session.messages) == 0

    def test_list_sessions(self):
        """Test listing sessions."""
        manager = SessionManager()

        manager.create_session("session-a")
        manager.create_session("session-b")
        manager.create_session("session-c")

        sessions = manager.list_sessions()

        assert "session-a" in sessions
        assert "session-b" in sessions
        assert "session-c" in sessions

    def test_delete_session(self):
        """Test deleting a session."""
        manager = SessionManager()

        manager.create_session("to-delete")
        manager.delete_session("to-delete")

        session = manager.get_session("to-delete")
        assert session is None


class TestSessionPersistence:
    """Tests for session persistence."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_save_session(self, temp_storage):
        """Test saving a session to storage."""
        manager = SessionManager(storage_path=temp_storage)

        session = manager.create_session("save-test")
        session.add_message("user", "Test message")
        session.set_current_shader('Shader "Test" {}')

        result = manager.save_session("save-test")

        assert result is True
        assert (temp_storage / "save-test.json").exists()

    def test_load_session(self, temp_storage):
        """Test loading a session from storage."""
        # Create and save a session directly
        session_data = {
            "session_id": "load-test",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "messages": [
                {
                    "role": "user",
                    "content": "Loaded message",
                    "timestamp": "2024-01-01T00:00:00",
                    "metadata": {},
                }
            ],
            "current_shader": 'Shader "Loaded" {}',
            "shader_history": [],
            "properties": {},
            "preview_object": "Sphere",
            "background_color": "#1E1E1E",
        }

        with open(temp_storage / "load-test.json", "w") as f:
            json.dump(session_data, f)

        manager = SessionManager(storage_path=temp_storage)
        session = manager.get_session("load-test")

        assert session is not None
        assert session.session_id == "load-test"
        assert len(session.messages) == 1
        assert session.messages[0].content == "Loaded message"

    def test_list_sessions_from_storage(self, temp_storage):
        """Test listing sessions includes storage."""
        # Create some session files
        for name in ["stored-1", "stored-2"]:
            session_data = {
                "session_id": name,
                "messages": [],
                "current_shader": "",
                "shader_history": [],
                "properties": {},
                "preview_object": "Sphere",
                "background_color": "#1E1E1E",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
            with open(temp_storage / f"{name}.json", "w") as f:
                json.dump(session_data, f)

        manager = SessionManager(storage_path=temp_storage)
        manager.create_session("in-memory")

        sessions = manager.list_sessions()

        assert "stored-1" in sessions
        assert "stored-2" in sessions
        assert "in-memory" in sessions

    def test_delete_session_with_storage(self, temp_storage):
        """Test deleting session also removes from storage."""
        manager = SessionManager(storage_path=temp_storage)

        session = manager.create_session("delete-stored")
        manager.save_session("delete-stored")

        assert (temp_storage / "delete-stored.json").exists()

        manager.delete_session("delete-stored")

        assert not (temp_storage / "delete-stored.json").exists()


class TestGlobalSessionManager:
    """Tests for global session manager."""

    def test_get_session_manager(self):
        """Test getting global session manager."""
        manager = get_session_manager()

        assert manager is not None
        assert isinstance(manager, SessionManager)

    def test_set_session_manager(self):
        """Test setting custom session manager."""
        custom_manager = SessionManager()
        set_session_manager(custom_manager)

        manager = get_session_manager()

        assert manager is custom_manager
