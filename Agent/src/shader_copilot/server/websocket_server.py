"""
WebSocket server for ShaderCopilot.

Main entry point for the Python backend.
Handles WebSocket connections from Unity Editor.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional
from uuid import UUID

import websockets
from websockets.server import WebSocketServerProtocol

from ..models.config import (
    get_server_config,
    get_log_config,
    get_llm_config,
    setup_logging,
)
from ..graphs.base.state import SessionState, SessionConfig, ModelConfig
from .message_handler import MessageHandler, serialize_message
from .messages import (
    BaseMessage,
    MessageType,
    ServerMessageType,
    SessionInitPayload,
    UserMessagePayload,
    SessionReadyPayload,
    create_error_message,
    create_message,
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and their associated sessions."""

    def __init__(self):
        self.connections: dict[WebSocketServerProtocol, Optional[SessionState]] = {}
        self.sessions: dict[UUID, SessionState] = {}

    def add_connection(self, websocket: WebSocketServerProtocol) -> None:
        """Register a new connection."""
        self.connections[websocket] = None
        logger.info(f"New connection from {websocket.remote_address}")

    def remove_connection(self, websocket: WebSocketServerProtocol) -> None:
        """Remove a connection."""
        session = self.connections.pop(websocket, None)
        if session:
            logger.info(f"Connection closed for session {session.session_id}")
        else:
            logger.info(f"Connection closed from {websocket.remote_address}")

    def get_session(self, websocket: WebSocketServerProtocol) -> Optional[SessionState]:
        """Get the session for a connection."""
        return self.connections.get(websocket)

    def set_session(
        self, websocket: WebSocketServerProtocol, session: SessionState
    ) -> None:
        """Associate a session with a connection."""
        self.connections[websocket] = session
        self.sessions[session.session_id] = session

    def get_session_by_id(self, session_id: UUID) -> Optional[SessionState]:
        """Get a session by ID."""
        return self.sessions.get(session_id)


class ShaderCopilotServer:
    """
    Main WebSocket server for ShaderCopilot.

    Handles client connections, message routing, and session management.
    """

    def __init__(self):
        self.config = get_server_config()
        self.llm_config = get_llm_config()
        self.connection_manager = ConnectionManager()
        self.message_handler = MessageHandler()
        self._setup_handlers()
        self._server: Optional[websockets.WebSocketServer] = None
        self._shutdown_event = asyncio.Event()

    def _setup_handlers(self) -> None:
        """Register message handlers."""
        self.message_handler.register_handler(
            MessageType.SESSION_INIT, self._handle_session_init
        )
        self.message_handler.register_handler(
            MessageType.USER_MESSAGE, self._handle_user_message
        )
        self.message_handler.register_handler(
            MessageType.CANCEL_TASK, self._handle_cancel_task
        )

    async def _handle_session_init(
        self,
        message: BaseMessage,
        context: dict,
    ) -> BaseMessage:
        """Handle session initialization."""
        websocket = context["websocket"]

        try:
            payload = SessionInitPayload.model_validate(message.payload)
        except Exception as e:
            return create_error_message(
                code="INVALID_SESSION_INIT",
                message=f"Invalid session init payload: {e}",
            )

        # Check if resuming existing session
        is_new = True
        if payload.session_id:
            existing = self.connection_manager.get_session_by_id(payload.session_id)
            if existing:
                self.connection_manager.set_session(websocket, existing)
                is_new = False
                logger.info(f"Resumed session {payload.session_id}")

        if is_new:
            # Create new session
            model_config = ModelConfig(
                router_model=payload.config.model_config.router_model,
                code_model=payload.config.model_config.code_model,
                vl_model=payload.config.model_config.vl_model,
            )
            session_config = SessionConfig(
                output_directory=payload.config.output_directory,
                max_retry_count=payload.config.max_retry_count,
                model_config=model_config,
            )
            session = SessionState(
                config=session_config,
                project_path=payload.project_path,
            )
            self.connection_manager.set_session(websocket, session)
            logger.info(f"Created new session {session.session_id}")

        session = self.connection_manager.get_session(websocket)
        return create_message(
            ServerMessageType.SESSION_READY,
            SessionReadyPayload(session_id=session.session_id, is_new=is_new),
        )

    async def _handle_user_message(
        self,
        message: BaseMessage,
        context: dict,
    ) -> Optional[BaseMessage]:
        """Handle user message."""
        websocket = context["websocket"]
        session = self.connection_manager.get_session(websocket)

        if not session:
            return create_error_message(
                code="NO_SESSION",
                message="No active session. Send session_init first.",
            )

        try:
            payload = UserMessagePayload.model_validate(message.payload)
        except Exception as e:
            return create_error_message(
                code="INVALID_USER_MESSAGE",
                message=f"Invalid user message payload: {e}",
            )

        # Add message to history
        from ..graphs.base.state import MessageRole

        session.add_message(MessageRole.USER, payload.content)

        # TODO: Route to appropriate graph based on intent
        # For now, just acknowledge
        logger.info(f"Received user message: {payload.content[:100]}...")

        # Placeholder response
        return create_message(
            ServerMessageType.STREAM_TEXT,
            {"content": f"Received: {payload.content}", "is_final": True},
        )

    async def _handle_cancel_task(
        self,
        message: BaseMessage,
        context: dict,
    ) -> Optional[BaseMessage]:
        """Handle task cancellation."""
        # TODO: Implement task cancellation
        logger.info("Task cancellation requested")
        return None

    async def _connection_handler(self, websocket: WebSocketServerProtocol) -> None:
        """Handle a WebSocket connection."""
        self.connection_manager.add_connection(websocket)

        try:
            async for raw_message in websocket:
                context = {"websocket": websocket}
                response = await self.message_handler.handle_message(
                    raw_message, context
                )
                if response:
                    await websocket.send(serialize_message(response))
        except websockets.ConnectionClosed as e:
            logger.info(f"Connection closed: {e}")
        except Exception as e:
            logger.exception(f"Connection error: {e}")
        finally:
            self.connection_manager.remove_connection(websocket)

    async def start(self) -> None:
        """Start the WebSocket server."""
        # Validate configuration
        if not self.llm_config.is_configured:
            logger.warning("LLM API key not configured. Set LLM_API_KEY in .env file.")

        logger.info(f"Starting server on {self.config.uri}")

        self._server = await websockets.serve(
            self._connection_handler,
            self.config.host,
            self.config.port,
        )

        logger.info(f"Server listening on {self.config.uri}")

        # Wait for shutdown signal
        await self._shutdown_event.wait()

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        logger.info("Shutting down server...")
        self._shutdown_event.set()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logger.info("Server stopped")


async def main_async() -> None:
    """Async main entry point."""
    setup_logging()
    logger.info("Starting ShaderCopilot server...")

    server = ShaderCopilotServer()

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(server.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await server.stop()
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        await server.stop()
        raise


def main() -> None:
    """Main entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
