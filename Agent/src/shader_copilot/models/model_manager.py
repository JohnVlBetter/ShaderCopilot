"""
Model manager for LLM routing and invocation.
Supports multiple model configurations for different tasks.
"""

from enum import Enum
from typing import AsyncIterator

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from shader_copilot.models.config import get_llm_config


class ModelRole(str, Enum):
    """Role-based model selection."""

    ROUTER = "router"
    CODE = "code"
    VISION = "vision"


class ModelManager:
    """
    Manages multiple LLM models for different tasks.

    - router_model: Fast model for intent classification
    - code_model: Powerful model for code generation
    - vl_model: Vision-language model for image analysis
    """

    def __init__(
        self,
        router_model: str | None = None,
        code_model: str | None = None,
        vl_model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize the model manager.

        Args:
            router_model: Model name for routing/classification
            code_model: Model name for code generation
            vl_model: Model name for vision-language tasks
            api_key: API key for the LLM service
            base_url: Base URL for the LLM API
        """
        config = get_llm_config()

        self._api_key = api_key or config.api_key
        self._base_url = base_url or config.base_url

        self._router_model_name = router_model or config.router_model
        self._code_model_name = code_model or config.code_model
        self._vl_model_name = vl_model or config.vl_model

        # Lazy initialization of models
        self._router_model: ChatOpenAI | None = None
        self._code_model: ChatOpenAI | None = None
        self._vl_model: ChatOpenAI | None = None

    def _create_model(self, model_name: str, temperature: float = 0.7) -> ChatOpenAI:
        """Create a ChatOpenAI model instance."""
        return ChatOpenAI(
            model=model_name,
            api_key=self._api_key,
            base_url=self._base_url,
            temperature=temperature,
        )

    @property
    def router(self) -> ChatOpenAI:
        """Get the router model for intent classification."""
        if self._router_model is None:
            self._router_model = self._create_model(
                self._router_model_name,
                temperature=0.0,  # Deterministic for classification
            )
        return self._router_model

    @property
    def coder(self) -> ChatOpenAI:
        """Get the code generation model."""
        if self._code_model is None:
            self._code_model = self._create_model(
                self._code_model_name, temperature=0.3  # Low temperature for code
            )
        return self._code_model

    @property
    def vision(self) -> ChatOpenAI:
        """Get the vision-language model."""
        if self._vl_model is None:
            self._vl_model = self._create_model(self._vl_model_name, temperature=0.5)
        return self._vl_model

    def get_model(self, role: ModelRole) -> ChatOpenAI:
        """Get model by role."""
        if role == ModelRole.ROUTER:
            return self.router
        elif role == ModelRole.CODE:
            return self.coder
        elif role == ModelRole.VISION:
            return self.vision
        else:
            raise ValueError(f"Unknown model role: {role}")

    async def generate(
        self,
        messages: list[BaseMessage],
        role: ModelRole = ModelRole.CODE,
    ) -> str:
        """
        Generate a response using the specified model.

        Args:
            messages: List of messages for the conversation
            role: Which model to use

        Returns:
            Generated text response
        """
        model = self.get_model(role)
        response = await model.ainvoke(messages)
        return response.content

    async def stream(
        self,
        messages: list[BaseMessage],
        role: ModelRole = ModelRole.CODE,
    ) -> AsyncIterator[str]:
        """
        Stream a response using the specified model.

        Args:
            messages: List of messages for the conversation
            role: Which model to use

        Yields:
            Chunks of generated text
        """
        model = self.get_model(role)
        async for chunk in model.astream(messages):
            if chunk.content:
                yield chunk.content

    async def classify_intent(self, user_message: str) -> str:
        """
        Classify user intent using the router model.

        Args:
            user_message: User's input message

        Returns:
            Classified intent string
        """
        system_prompt = """You are an intent classifier for a shader generation assistant.
Classify the user's message into one of these intents:
- GENERATE_SHADER: User wants to create a new shader
- MODIFY_SHADER: User wants to modify an existing shader
- EXPLAIN_SHADER: User wants explanation about shaders
- QUESTION: User has a general question
- OTHER: None of the above

Respond with ONLY the intent name, nothing else."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        response = await self.generate(messages, ModelRole.ROUTER)
        return response.strip().upper()

    async def generate_shader(
        self,
        requirement: str,
        context: str = "",
        compile_errors: str | None = None,
    ) -> str:
        """
        Generate shader code based on requirements.

        Args:
            requirement: User's shader requirement
            context: Additional context (e.g., previous code)
            compile_errors: Compilation errors from previous attempt

        Returns:
            Generated shader code
        """
        system_prompt = """You are an expert Unity shader programmer.
Generate valid HLSL shader code for Unity's Universal Render Pipeline (URP).
Your response should contain ONLY the shader code, wrapped in a code block.
The shader must be syntactically correct and ready to compile.

Guidelines:
- Use URP shader structure with proper includes
- Follow Unity shader naming conventions
- Include appropriate properties for customization
- Handle common edge cases gracefully"""

        user_content = f"Create a shader with these requirements:\n{requirement}"

        if context:
            user_content += f"\n\nAdditional context:\n{context}"

        if compile_errors:
            user_content += f"\n\nPrevious compilation failed with errors:\n{compile_errors}\n\nPlease fix these errors."

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]

        return await self.generate(messages, ModelRole.CODE)

    def update_model(
        self,
        role: ModelRole,
        model_name: str,
    ) -> None:
        """
        Update a model configuration at runtime.

        Args:
            role: Which model to update
            model_name: New model name
        """
        if role == ModelRole.ROUTER:
            self._router_model_name = model_name
            self._router_model = None  # Reset for lazy init
        elif role == ModelRole.CODE:
            self._code_model_name = model_name
            self._code_model = None
        elif role == ModelRole.VISION:
            self._vl_model_name = model_name
            self._vl_model = None


# Global instance for convenience
_model_manager: ModelManager | None = None


def get_model_manager() -> ModelManager:
    """Get or create the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


def reset_model_manager() -> None:
    """Reset the global model manager (for testing)."""
    global _model_manager
    _model_manager = None
