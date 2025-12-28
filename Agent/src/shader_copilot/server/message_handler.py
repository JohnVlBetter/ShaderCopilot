"""
WebSocket message handler.

Handles parsing, validation, and routing of WebSocket messages.
"""

import json
import logging
from typing import Any, Callable, Optional
from uuid import UUID

from pydantic import ValidationError

from .messages import (
    BaseMessage,
    MessageType,
    ServerMessageType,
    UserMessagePayload,
    SessionInitPayload,
    ToolResponsePayload,
    UserConfirmPayload,
    CancelTaskPayload,
    create_error_message,
)

logger = logging.getLogger(__name__)


class MessageParseError(Exception):
    """Error parsing a WebSocket message."""

    def __init__(self, message: str, raw_data: str = ""):
        super().__init__(message)
        self.raw_data = raw_data


class MessageHandler:
    """
    Handles WebSocket message parsing and routing.

    Registers handlers for different message types and routes
    incoming messages to the appropriate handler.
    """

    def __init__(self):
        self._handlers: dict[MessageType, Callable] = {}
        self._pending_confirms: dict[UUID, Callable] = {}
        self._pending_tool_calls: dict[UUID, Callable] = {}

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[BaseMessage, Any], Any],
    ) -> None:
        """Register a handler for a message type."""
        self._handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type}")

    def parse_message(self, raw_data: str) -> BaseMessage:
        """
        Parse a raw JSON string into a BaseMessage.

        Args:
            raw_data: Raw JSON string from WebSocket

        Returns:
            Parsed BaseMessage

        Raises:
            MessageParseError: If parsing fails
        """
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            raise MessageParseError(f"Invalid JSON: {e}", raw_data)

        # Validate required fields
        if "type" not in data:
            raise MessageParseError("Missing 'type' field", raw_data)

        try:
            return BaseMessage.model_validate(data)
        except ValidationError as e:
            raise MessageParseError(f"Invalid message structure: {e}", raw_data)

    def validate_payload(
        self,
        message: BaseMessage,
        payload_class: type,
    ) -> Any:
        """
        Validate and parse a message's payload.

        Args:
            message: The base message
            payload_class: The expected payload class

        Returns:
            Parsed payload object

        Raises:
            MessageParseError: If validation fails
        """
        try:
            return payload_class.model_validate(message.payload)
        except ValidationError as e:
            raise MessageParseError(
                f"Invalid payload for {message.type}: {e}",
                json.dumps(message.payload),
            )

    async def handle_message(
        self,
        raw_data: str,
        context: Optional[Any] = None,
    ) -> Optional[BaseMessage]:
        """
        Parse and route a message to its handler.

        Args:
            raw_data: Raw JSON string from WebSocket
            context: Optional context to pass to handler

        Returns:
            Response message if handler returns one
        """
        try:
            message = self.parse_message(raw_data)
        except MessageParseError as e:
            logger.error(f"Failed to parse message: {e}")
            return create_error_message(
                code="PARSE_ERROR",
                message=str(e),
                recoverable=True,
            )

        # Get message type
        try:
            msg_type = MessageType(message.type)
        except ValueError:
            logger.warning(f"Unknown message type: {message.type}")
            return create_error_message(
                code="UNKNOWN_MESSAGE_TYPE",
                message=f"Unknown message type: {message.type}",
                recoverable=True,
            )

        # Handle special message types
        if msg_type == MessageType.PING:
            return BaseMessage(type=ServerMessageType.PONG.value, payload={})

        if msg_type == MessageType.USER_CONFIRM:
            return await self._handle_confirm(message)

        if msg_type == MessageType.TOOL_RESPONSE:
            return await self._handle_tool_response(message)

        # Route to registered handler
        handler = self._handlers.get(msg_type)
        if handler is None:
            logger.warning(f"No handler registered for {msg_type}")
            return create_error_message(
                code="NO_HANDLER",
                message=f"No handler for message type: {msg_type}",
                recoverable=True,
            )

        try:
            return await handler(message, context)
        except Exception as e:
            logger.exception(f"Handler error for {msg_type}: {e}")
            return create_error_message(
                code="HANDLER_ERROR",
                message=f"Error processing {msg_type}: {str(e)}",
                recoverable=True,
            )

    async def _handle_confirm(self, message: BaseMessage) -> Optional[BaseMessage]:
        """Handle user confirmation response."""
        try:
            payload = self.validate_payload(message, UserConfirmPayload)
        except MessageParseError as e:
            return create_error_message(
                code="INVALID_CONFIRM",
                message=str(e),
            )

        callback = self._pending_confirms.pop(payload.confirm_id, None)
        if callback:
            try:
                await callback(payload.confirmed, payload.message)
            except Exception as e:
                logger.exception(f"Confirm callback error: {e}")
        else:
            logger.warning(f"No pending confirm for {payload.confirm_id}")

        return None

    async def _handle_tool_response(
        self, message: BaseMessage
    ) -> Optional[BaseMessage]:
        """Handle tool response from Unity."""
        try:
            payload = self.validate_payload(message, ToolResponsePayload)
        except MessageParseError as e:
            return create_error_message(
                code="INVALID_TOOL_RESPONSE",
                message=str(e),
            )

        callback = self._pending_tool_calls.pop(payload.request_id, None)
        if callback:
            try:
                await callback(payload)
            except Exception as e:
                logger.exception(f"Tool response callback error: {e}")
        else:
            logger.warning(f"No pending tool call for {payload.request_id}")

        return None

    def register_confirm_callback(
        self,
        confirm_id: UUID,
        callback: Callable[[bool, Optional[str]], Any],
    ) -> None:
        """Register a callback for a pending confirmation."""
        self._pending_confirms[confirm_id] = callback

    def register_tool_callback(
        self,
        request_id: UUID,
        callback: Callable[[ToolResponsePayload], Any],
    ) -> None:
        """Register a callback for a pending tool call."""
        self._pending_tool_calls[request_id] = callback


def serialize_message(message: BaseMessage) -> str:
    """Serialize a message to JSON string."""
    return message.model_dump_json()
