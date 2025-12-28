"""
Router Agent for intent classification and workflow routing.
"""

from enum import Enum
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from shader_copilot.models.model_manager import (
    ModelManager,
    ModelRole,
    get_model_manager,
)


class Intent(str, Enum):
    """User intent classifications."""

    GENERATE_SHADER = "GENERATE_SHADER"
    MODIFY_SHADER = "MODIFY_SHADER"
    EXPLAIN_SHADER = "EXPLAIN_SHADER"
    PREVIEW_CONFIG = "PREVIEW_CONFIG"
    SAVE_ASSET = "SAVE_ASSET"
    QUESTION = "QUESTION"
    OTHER = "OTHER"


class RouterAgent:
    """
    Routes user messages to appropriate workflows.

    Uses a fast LLM model to classify intent and determine
    which graph should handle the request.
    """

    CLASSIFICATION_PROMPT = """You are an intent classifier for a Unity shader generation assistant.
Your job is to classify user messages into one of these intents:

- GENERATE_SHADER: User wants to CREATE a NEW shader (e.g., "创建一个卡通着色器", "make a dissolve shader")
- MODIFY_SHADER: User wants to MODIFY an EXISTING shader (e.g., "把颜色改成蓝色", "add rim lighting")
- EXPLAIN_SHADER: User wants EXPLANATION about shaders (e.g., "什么是法线贴图", "how does PBR work")
- PREVIEW_CONFIG: User wants to change preview settings (e.g., "切换到立方体", "use a dark background")
- SAVE_ASSET: User wants to save the current work (e.g., "保存", "save the shader")
- QUESTION: General question not about shaders (e.g., "你是谁", "what can you do")
- OTHER: None of the above

Context clues:
- If user mentions creating, making, generating, or gives a shader description -> GENERATE_SHADER
- If user mentions changing, modifying, adjusting existing shader -> MODIFY_SHADER
- If user asks "what is", "how does", "explain" about shaders -> EXPLAIN_SHADER
- If user mentions preview, sphere, cube, background -> PREVIEW_CONFIG
- If user explicitly asks to save -> SAVE_ASSET

Respond with ONLY the intent name in UPPERCASE, nothing else."""

    def __init__(self, model_manager: Optional[ModelManager] = None):
        """
        Initialize the router agent.

        Args:
            model_manager: Optional model manager, will use global if not provided
        """
        self._model_manager = model_manager

    @property
    def model_manager(self) -> ModelManager:
        """Get the model manager."""
        if self._model_manager is None:
            self._model_manager = get_model_manager()
        return self._model_manager

    async def classify(
        self,
        message: str,
        has_image: bool = False,
        has_existing_shader: bool = False,
    ) -> Intent:
        """
        Classify user intent from their message.

        Args:
            message: User's input message
            has_image: Whether the message includes an image
            has_existing_shader: Whether there's an existing shader in context

        Returns:
            Classified intent
        """
        # Build context-aware prompt
        context_info = []
        if has_image:
            context_info.append("User has attached an image.")
        if has_existing_shader:
            context_info.append("There is an existing shader in the conversation.")

        context_str = " ".join(context_info) if context_info else ""

        messages = [
            SystemMessage(content=self.CLASSIFICATION_PROMPT),
            HumanMessage(content=f"{context_str}\n\nUser message: {message}".strip()),
        ]

        response = await self.model_manager.generate(messages, ModelRole.ROUTER)

        # Parse response
        intent_str = response.strip().upper()

        try:
            return Intent(intent_str)
        except ValueError:
            # Default to GENERATE_SHADER for unrecognized intents
            # as it's the most common use case
            return Intent.GENERATE_SHADER

    async def route(
        self,
        message: str,
        has_image: bool = False,
        has_existing_shader: bool = False,
    ) -> tuple[Intent, str]:
        """
        Route message to appropriate handler.

        Args:
            message: User's input message
            has_image: Whether the message includes an image
            has_existing_shader: Whether there's an existing shader in context

        Returns:
            Tuple of (intent, graph_name) for routing
        """
        intent = await self.classify(message, has_image, has_existing_shader)

        # Map intent to graph
        graph_mapping = {
            Intent.GENERATE_SHADER: "shader_gen",
            Intent.MODIFY_SHADER: "shader_gen",  # Same graph, different context
            Intent.EXPLAIN_SHADER: "explain",
            Intent.PREVIEW_CONFIG: "preview_config",
            Intent.SAVE_ASSET: "save",
            Intent.QUESTION: "chat",
            Intent.OTHER: "chat",
        }

        graph_name = graph_mapping.get(intent, "chat")

        return intent, graph_name

    def quick_route(self, message: str) -> Optional[Intent]:
        """
        Quick keyword-based routing without LLM call.

        Useful for obvious cases to save API calls.

        Args:
            message: User's input message

        Returns:
            Intent if confidently detected, None if LLM should be used
        """
        message_lower = message.lower()

        # Save commands
        if any(kw in message_lower for kw in ["保存", "save", "export"]):
            return Intent.SAVE_ASSET

        # Preview commands
        if any(
            kw in message_lower
            for kw in [
                "切换",
                "switch to",
                "preview",
                "sphere",
                "cube",
                "plane",
                "background",
            ]
        ):
            return Intent.PREVIEW_CONFIG

        # Generation keywords
        gen_keywords = ["创建", "生成", "制作", "create", "generate", "make", "build"]
        shader_keywords = ["shader", "着色器", "材质效果"]

        has_gen = any(kw in message_lower for kw in gen_keywords)
        has_shader = any(kw in message_lower for kw in shader_keywords)

        if has_gen and has_shader:
            return Intent.GENERATE_SHADER

        # Can't determine confidently
        return None


# Global instance
_router_agent: Optional[RouterAgent] = None


def get_router_agent() -> RouterAgent:
    """Get or create the global router agent."""
    global _router_agent
    if _router_agent is None:
        _router_agent = RouterAgent()
    return _router_agent
