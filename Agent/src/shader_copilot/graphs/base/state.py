"""
Base state definitions shared across all graphs.

Defines the session-level state that persists across graph invocations.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class SessionStatus(str, Enum):
    """Session lifecycle status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    """Role of a message in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A single message in the conversation."""

    message_id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    images: list[dict] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Configuration for LLM models."""

    router_model: str = "qwen-turbo"
    code_model: str = "qwen-max"
    vl_model: str = "qwen-vl-plus"


class SessionConfig(BaseModel):
    """Configuration for a session."""

    output_directory: str = "Assets/Shaders/Generated"
    max_retry_count: int = 3
    model_config: ModelConfig = Field(default_factory=ModelConfig)


class SessionState(BaseModel):
    """
    Global shared state for a session.

    This state persists across multiple graph invocations within the same session.
    """

    # Session identity
    session_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE

    # Configuration
    config: SessionConfig = Field(default_factory=SessionConfig)
    project_path: str = ""

    # Conversation history
    conversation_history: list[Message] = Field(default_factory=list)

    # Current task tracking
    current_task_id: Optional[UUID] = None

    def add_message(self, role: MessageRole, content: str, **kwargs) -> Message:
        """Add a message to conversation history."""
        message = Message(role=role, content=content, **kwargs)
        self.conversation_history.append(message)
        self.updated_at = datetime.utcnow()
        return message

    def get_context_messages(self, max_messages: int = 10) -> list[Message]:
        """Get recent messages for context."""
        return self.conversation_history[-max_messages:]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """Create from dictionary."""
        return cls.model_validate(data)
