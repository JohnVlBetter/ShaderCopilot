"""
Session management for ShaderCopilot.

Handles conversation history, shader state, and persistence.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in the conversation."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ShaderVersion(BaseModel):
    """A version of the shader in the conversation."""

    code: str
    name: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    compile_success: bool = False
    notes: str = ""


class Session(BaseModel):
    """A conversation session with shader state."""

    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Conversation
    messages: list[Message] = Field(default_factory=list)

    # Shader state
    current_shader: str = ""
    shader_history: list[ShaderVersion] = Field(default_factory=list)

    # User customizations
    properties: dict[str, str] = Field(default_factory=dict)

    # Preview state
    preview_object: str = "Sphere"
    background_color: str = "#1E1E1E"

    def add_message(self, role: str, content: str, **metadata):
        """Add a message to the conversation."""
        msg = Message(role=role, content=content, metadata=metadata)
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()

    def set_current_shader(
        self, code: str, name: str = "", compile_success: bool = True
    ):
        """Set the current shader and add to history."""
        # Add previous to history if exists
        if self.current_shader:
            # Find if we have a version with this exact code
            existing = [v for v in self.shader_history if v.code == self.current_shader]
            if not existing:
                version = ShaderVersion(
                    code=self.current_shader,
                    name=self._extract_shader_name(self.current_shader),
                )
                self.shader_history.append(version)

        self.current_shader = code
        self.updated_at = datetime.utcnow()

        # Add new version to history
        version = ShaderVersion(
            code=code,
            name=name or self._extract_shader_name(code),
            compile_success=compile_success,
        )
        self.shader_history.append(version)

    def get_shader_history(self) -> list[ShaderVersion]:
        """Get the shader history."""
        return self.shader_history

    def set_property(self, name: str, value: str):
        """Set a user property customization."""
        self.properties[name] = value
        self.updated_at = datetime.utcnow()

    def get_properties(self) -> dict[str, str]:
        """Get all user property customizations."""
        return self.properties.copy()

    def build_context(self, max_messages: int = 10) -> str:
        """Build context string from conversation history."""
        recent = (
            self.messages[-max_messages:]
            if len(self.messages) > max_messages
            else self.messages
        )

        context_parts = []
        for msg in recent:
            prefix = {"user": "User", "assistant": "Assistant", "system": "System"}.get(
                msg.role, msg.role
            )
            context_parts.append(f"{prefix}: {msg.content}")

        return "\n\n".join(context_parts)

    def _extract_shader_name(self, code: str) -> str:
        """Extract shader name from code."""
        import re

        match = re.search(r'Shader\s+"([^"]+)"', code)
        return match.group(1) if match else "Unknown"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create from dictionary."""
        return cls.model_validate(data)


class SessionManager:
    """
    Manages conversation sessions.

    Handles creation, persistence, and retrieval of sessions.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the session manager.

        Args:
            storage_path: Optional path for session persistence
        """
        self._sessions: dict[str, Session] = {}
        self._storage_path = storage_path

        if storage_path:
            storage_path.mkdir(parents=True, exist_ok=True)

    def create_session(self, session_id: Optional[str] = None) -> Session:
        """
        Create a new session.

        Args:
            session_id: Optional session ID, generates one if not provided

        Returns:
            New session
        """
        if session_id is None:
            session_id = str(uuid4())

        session = Session(session_id=session_id)
        self._sessions[session_id] = session

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get an existing session.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session if found, None otherwise
        """
        # Try memory first
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Try loading from storage
        if self._storage_path:
            session = self._load_session(session_id)
            if session:
                self._sessions[session_id] = session
                return session

        return None

    def get_or_create_session(self, session_id: str) -> Session:
        """
        Get an existing session or create a new one.

        Args:
            session_id: Session ID

        Returns:
            Existing or new session
        """
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        return session

    def save_session(self, session_id: str) -> bool:
        """
        Save a session to storage.

        Args:
            session_id: Session ID to save

        Returns:
            True if saved successfully
        """
        if not self._storage_path:
            return False

        session = self._sessions.get(session_id)
        if not session:
            return False

        try:
            file_path = self._storage_path / f"{session_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted
        """
        if session_id in self._sessions:
            del self._sessions[session_id]

        if self._storage_path:
            file_path = self._storage_path / f"{session_id}.json"
            if file_path.exists():
                file_path.unlink()
                return True

        return False

    def list_sessions(self) -> list[str]:
        """
        List all available session IDs.

        Returns:
            List of session IDs
        """
        session_ids = set(self._sessions.keys())

        if self._storage_path:
            for f in self._storage_path.glob("*.json"):
                session_ids.add(f.stem)

        return sorted(session_ids)

    def _load_session(self, session_id: str) -> Optional[Session]:
        """Load a session from storage."""
        if not self._storage_path:
            return None

        file_path = self._storage_path / f"{session_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception:
            return None


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def set_session_manager(manager: SessionManager):
    """Set the global session manager."""
    global _session_manager
    _session_manager = manager
