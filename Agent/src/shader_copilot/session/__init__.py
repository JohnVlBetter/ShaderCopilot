"""
Session management module for ShaderCopilot.
"""

from shader_copilot.session.session_manager import (
    Message,
    Session,
    SessionManager,
    ShaderVersion,
    get_session_manager,
    set_session_manager,
)

__all__ = [
    "Message",
    "Session",
    "SessionManager",
    "ShaderVersion",
    "get_session_manager",
    "set_session_manager",
]
