"""
WebSocket message types and base models.

Defines the communication protocol between Unity client and Python backend.
See: contracts/websocket-protocol.md for full specification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Message types for client → server communication."""

    SESSION_INIT = "SESSION_INIT"
    USER_MESSAGE = "USER_MESSAGE"
    TOOL_RESPONSE = "TOOL_RESPONSE"
    CONFIRM_RESPONSE = "CONFIRM_RESPONSE"
    CANCEL_TASK = "CANCEL_TASK"
    SESSION_END = "SESSION_END"
    PING = "ping"


class ServerMessageType(str, Enum):
    """Message types for server → client communication."""

    SESSION_READY = "SESSION_READY"
    RESPONSE = "RESPONSE"
    STREAM_CHUNK = "STREAM_CHUNK"
    ERROR = "ERROR"
    TOOL_CALL_REQUEST = "TOOL_CALL_REQUEST"
    CONFIRM_REQUEST = "CONFIRM_REQUEST"
    PROGRESS_UPDATE = "PROGRESS_UPDATE"
    SHADER_PREVIEW = "SHADER_PREVIEW"
    TASK_COMPLETE = "TASK_COMPLETE"
    SESSION_ENDED = "SESSION_ENDED"
    PONG = "pong"


class BaseMessage(BaseModel):
    """Base message structure shared by all messages."""

    id: UUID = Field(default_factory=uuid4)
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z",
            UUID: str,
        }


# =============================================================================
# Client → Server Messages
# =============================================================================


class ImageData(BaseModel):
    """Image data attached to a message."""

    image_id: str = ""
    data: str = ""  # Base64 encoded
    mime_type: str = "image/png"


class UserMessagePayload(BaseModel):
    """Payload for USER_MESSAGE type."""

    content: str = ""
    images: list[str] = Field(default_factory=list)  # Base64 encoded images


class ModelConfigPayload(BaseModel):
    """Model configuration for session initialization."""

    router_model: str = "qwen-turbo"
    code_model: str = "qwen-max"
    vl_model: str = "qwen-vl-plus"


class SessionInitPayload(BaseModel):
    """Payload for SESSION_INIT type."""

    project_path: Optional[str] = None
    config: dict[str, Any] = Field(default_factory=dict)


class ToolResponsePayload(BaseModel):
    """Payload for TOOL_RESPONSE type."""

    tool_call_id: str
    result: dict[str, Any] = Field(default_factory=dict)


class ConfirmResponsePayload(BaseModel):
    """Payload for CONFIRM_RESPONSE type."""

    confirm_id: str
    approved: bool


# =============================================================================
# Server → Client Messages
# =============================================================================


class StreamChunkPayload(BaseModel):
    """Payload for STREAM_CHUNK type."""

    content: str
    is_final: bool = False


class ProgressPayload(BaseModel):
    """Payload for PROGRESS_UPDATE type."""

    stage: str
    message: str
    progress: Optional[float] = None  # 0.0 - 1.0


class ToolCallRequest(BaseModel):
    """Payload for TOOL_CALL_REQUEST type."""

    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ConfirmRequestPayload(BaseModel):
    """Payload for CONFIRM_REQUEST type."""

    confirm_id: str
    action: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorPayload(BaseModel):
    """Payload for ERROR type."""

    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ShaderPreviewPayload(BaseModel):
    """Payload for SHADER_PREVIEW type."""

    code: str
    shader_name: Optional[str] = None


class SessionReadyPayload(BaseModel):
    """Payload for SESSION_READY type."""

    session_id: str
    is_new: bool = True


# =============================================================================
# Message Factory Functions
# =============================================================================


def create_message(msg_type: str, session_id: str, payload: dict) -> dict:
    """Create a message dict with the given type and payload."""
    return {
        "type": msg_type,
        "session_id": session_id,
        "payload": payload,
    }


def create_response(session_id: str, content: str) -> dict:
    """Create a RESPONSE message."""
    return create_message(
        ServerMessageType.RESPONSE,
        session_id,
        {"content": content},
    )


def create_stream_chunk(session_id: str, content: str, is_final: bool = False) -> dict:
    """Create a STREAM_CHUNK message."""
    return create_message(
        ServerMessageType.STREAM_CHUNK,
        session_id,
        {"content": content, "is_final": is_final},
    )


def create_error(
    session_id: str, code: str, message: str, details: Optional[dict] = None
) -> dict:
    """Create an ERROR message."""
    payload = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return create_message(ServerMessageType.ERROR, session_id, payload)


def create_tool_call_request(
    session_id: str,
    tool_call_id: str,
    tool_name: str,
    arguments: dict,
) -> dict:
    """Create a TOOL_CALL_REQUEST message."""
    return create_message(
        ServerMessageType.TOOL_CALL_REQUEST,
        session_id,
        {
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "arguments": arguments,
        },
    )


def create_confirm_request(
    session_id: str,
    confirm_id: str,
    action: str,
    details: dict,
) -> dict:
    """Create a CONFIRM_REQUEST message."""
    return create_message(
        ServerMessageType.CONFIRM_REQUEST,
        session_id,
        {
            "confirm_id": confirm_id,
            "action": action,
            "details": details,
        },
    )


def create_progress_update(
    session_id: str,
    stage: str,
    message: str,
    progress: Optional[float] = None,
) -> dict:
    """Create a PROGRESS_UPDATE message."""
    payload = {"stage": stage, "message": message}
    if progress is not None:
        payload["progress"] = progress
    return create_message(ServerMessageType.PROGRESS_UPDATE, session_id, payload)


def create_shader_preview(
    session_id: str,
    code: str,
    shader_name: Optional[str] = None,
) -> dict:
    """Create a SHADER_PREVIEW message."""
    payload = {"code": code}
    if shader_name:
        payload["shader_name"] = shader_name
    return create_message(ServerMessageType.SHADER_PREVIEW, session_id, payload)


def create_session_ready(session_id: str, is_new: bool = True) -> dict:
    """Create a SESSION_READY message."""
    return create_message(
        ServerMessageType.SESSION_READY,
        session_id,
        {"session_id": session_id, "is_new": is_new},
    )


def create_task_complete(session_id: str, message: str = "Task completed") -> dict:
    """Create a TASK_COMPLETE message."""
    return create_message(
        ServerMessageType.TASK_COMPLETE,
        session_id,
        {"message": message},
    )


# =============================================================================
# Message Parsing
# =============================================================================


class ParsedMessage(BaseModel):
    """A parsed incoming message."""

    type: MessageType
    session_id: Optional[str] = None
    payload: Any = None


def parse_message(raw: dict) -> Optional[ParsedMessage]:
    """
    Parse a raw message dict into a typed message.

    Returns None if the message type is invalid.
    """
    type_str = raw.get("type")
    if not type_str:
        return None

    try:
        msg_type = MessageType(type_str)
    except ValueError:
        return None

    session_id = raw.get("session_id")
    raw_payload = raw.get("payload", {})

    # Parse payload based on type
    payload: Any = raw_payload

    if msg_type == MessageType.SESSION_INIT:
        payload = SessionInitPayload(**raw_payload)
    elif msg_type == MessageType.USER_MESSAGE:
        payload = UserMessagePayload(**raw_payload)
    elif msg_type == MessageType.TOOL_RESPONSE:
        payload = ToolResponsePayload(**raw_payload)
    elif msg_type == MessageType.CONFIRM_RESPONSE:
        payload = ConfirmResponsePayload(**raw_payload)

    return ParsedMessage(type=msg_type, session_id=session_id, payload=payload)
