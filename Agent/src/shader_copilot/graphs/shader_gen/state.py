"""
Shader generation graph state.

Defines the state specific to the shader generation workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CompileStatus(str, Enum):
    """Status of shader compilation."""

    PENDING = "pending"
    COMPILING = "compiling"
    SUCCESS = "success"
    FAILED = "failed"


class CompileError(BaseModel):
    """A single shader compilation error."""

    line: int
    column: int = 0
    message: str
    severity: str = "error"  # error, warning


class CompileResult(BaseModel):
    """Result of shader compilation."""

    status: CompileStatus = CompileStatus.PENDING
    shader_id: Optional[str] = None
    errors: list[CompileError] = Field(default_factory=list)
    warnings: list[CompileError] = Field(default_factory=list)
    compile_time_ms: Optional[float] = None


class TextureSlot(BaseModel):
    """A texture slot required by the shader."""

    name: str  # e.g., "_MainTex", "_NormalMap"
    texture_type: str  # e.g., "2D", "Cube"
    description: str = ""
    required: bool = True


class ShaderGenState(BaseModel):
    """
    State for the shader generation graph.

    Tracks the progress of generating a single shader from user requirements.
    """

    # Task identity
    task_id: UUID = Field(default_factory=uuid4)
    session_id: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # User input
    user_requirement: str = ""
    reference_image: Optional[bytes] = None
    reference_image_mime: Optional[str] = None

    # Context for modifications
    previous_code: Optional[str] = None  # Existing shader to modify
    is_modification: bool = False  # Whether this is a modification vs new shader
    conversation_context: str = ""  # Recent conversation for context

    # Analysis results
    image_analysis: Optional[str] = None
    requirement_analysis: Optional[str] = None

    # Generation results
    shader_name: str = ""
    generated_code: str = ""
    shader_properties: dict = Field(default_factory=dict)

    # Validation
    validation_passed: bool = False
    validation_errors: list[str] = Field(default_factory=list)

    # Compilation
    compile_result: CompileResult = Field(default_factory=CompileResult)

    # Material and preview
    material_id: Optional[str] = None
    material_properties: dict = Field(default_factory=dict)
    preview_object: str = "Sphere"
    screenshot: Optional[bytes] = None

    # Retry tracking
    retry_count: int = 0
    max_retries: int = 3
    error_history: list[str] = Field(default_factory=list)

    # Texture requirements (for future texture generation)
    pending_textures: list[TextureSlot] = Field(default_factory=list)

    # Output
    saved_shader_path: Optional[str] = None
    saved_material_path: Optional[str] = None

    # Workflow tracking
    current_stage: str = "init"
    is_complete: bool = False
    error: Optional[str] = None

    @property
    def can_retry(self) -> bool:
        """Check if retry is allowed."""
        return self.retry_count < self.max_retries

    @property
    def has_compile_errors(self) -> bool:
        """Check if there are compilation errors."""
        return self.compile_result.status == CompileStatus.FAILED

    def increment_retry(self) -> None:
        """Increment retry count and record error."""
        self.retry_count += 1
        if self.compile_result.errors:
            error_msg = "; ".join(e.message for e in self.compile_result.errors)
            self.error_history.append(f"Attempt {self.retry_count}: {error_msg}")

    def reset_for_retry(self) -> None:
        """Reset state for a new generation attempt."""
        self.generated_code = ""
        self.compile_result = CompileResult()
        self.material_id = None
        self.screenshot = None
