"""
Entity models for data persistence and transfer.

Defines the core entities used throughout the system.
See: data-model.md for full specification.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


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


class CompileStatus(str, Enum):
    """Status of shader compilation."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class PreviewObjectType(str, Enum):
    """Available preview object types."""

    SPHERE = "Sphere"
    CUBE = "Cube"
    PLANE = "Plane"
    CYLINDER = "Cylinder"
    CAPSULE = "Capsule"


class BackgroundType(str, Enum):
    """Available background types for preview."""

    SOLID = "Solid"
    GRADIENT = "Gradient"
    SKYBOX = "Skybox"


# =============================================================================
# Sub-entities
# =============================================================================


class ImageData(BaseModel):
    """Image data attached to a message."""

    image_id: str = Field(default_factory=lambda: str(uuid4()))
    data: bytes
    mime_type: str = "image/png"


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


class CameraSettings(BaseModel):
    """Camera settings for preview scene."""

    distance: float = 3.0
    rotation_x: float = 15.0
    rotation_y: float = -30.0
    field_of_view: float = 60.0


class PreviewConfig(BaseModel):
    """Preview scene configuration."""

    object_type: PreviewObjectType = PreviewObjectType.SPHERE
    background_type: BackgroundType = BackgroundType.SOLID
    background_color: str = "#303030"  # Hex color
    camera_settings: CameraSettings = Field(default_factory=CameraSettings)


# =============================================================================
# Main Entities
# =============================================================================


class Message(BaseModel):
    """A single message in the conversation."""

    message_id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    images: list[dict] = Field(default_factory=list)  # Serialized ImageData
    artifacts: list[str] = Field(default_factory=list)  # Asset paths
    metadata: dict = Field(default_factory=dict)


class Session(BaseModel):
    """
    User session entity.

    Represents a complete interaction session with conversation history.
    """

    session_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE
    config: SessionConfig = Field(default_factory=SessionConfig)
    messages: list[Message] = Field(default_factory=list)

    # Associated assets
    shader_assets: list[str] = Field(default_factory=list)  # Paths
    material_assets: list[str] = Field(default_factory=list)  # Paths

    def add_message(self, role: MessageRole, content: str, **kwargs) -> Message:
        """Add a new message to the session."""
        message = Message(role=role, content=content, **kwargs)
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message


class ShaderAsset(BaseModel):
    """
    Generated shader asset.

    Represents a shader file with its metadata and compilation status.
    """

    asset_id: UUID = Field(default_factory=uuid4)
    shader_name: str
    code: str
    compile_status: CompileStatus = CompileStatus.PENDING
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    description: str = ""
    tags: list[str] = Field(default_factory=list)

    # Compilation details
    compile_errors: list[dict] = Field(default_factory=list)
    compile_warnings: list[dict] = Field(default_factory=list)


class MaterialAsset(BaseModel):
    """
    Generated material asset.

    Represents a material file with its shader reference and properties.
    """

    asset_id: UUID = Field(default_factory=uuid4)
    material_name: str
    shader_ref: str  # Shader name or path
    properties: dict = Field(default_factory=dict)  # Property name → value
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Texture references
    textures: dict[str, str] = Field(default_factory=dict)  # Slot name → texture path


# =============================================================================
# Session Index (for listing sessions)
# =============================================================================


class SessionSummary(BaseModel):
    """Summary of a session for listing purposes."""

    session_id: UUID
    created_at: datetime
    updated_at: datetime
    status: SessionStatus
    message_count: int
    preview_message: str = ""  # First user message truncated


class SessionIndex(BaseModel):
    """Index of all sessions for quick lookup."""

    sessions: list[SessionSummary] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def add_session(self, session: Session) -> None:
        """Add or update a session in the index."""
        # Remove existing entry if present
        self.sessions = [s for s in self.sessions if s.session_id != session.session_id]

        # Get preview message
        preview = ""
        for msg in session.messages:
            if msg.role == MessageRole.USER:
                preview = msg.content[:100] + ("..." if len(msg.content) > 100 else "")
                break

        # Add new entry
        summary = SessionSummary(
            session_id=session.session_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            status=session.status,
            message_count=len(session.messages),
            preview_message=preview,
        )
        self.sessions.insert(0, summary)  # Most recent first
        self.last_updated = datetime.utcnow()

    def remove_session(self, session_id: UUID) -> None:
        """Remove a session from the index."""
        self.sessions = [s for s in self.sessions if s.session_id != session_id]
        self.last_updated = datetime.utcnow()
