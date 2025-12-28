# Tools module
"""Tool implementations for LLM and Unity interactions"""
from shader_copilot.tools.llm_tools import (
    analyze_image,
    analyze_shader_requirement,
    explain_shader_code,
    generate_shader_code,
    suggest_shader_modifications,
)
from shader_copilot.tools.unity_tools import (
    UNITY_TOOL_DEFINITIONS,
    UnityToolError,
    UnityTools,
)

__all__ = [
    # LLM tools
    "generate_shader_code",
    "analyze_shader_requirement",
    "explain_shader_code",
    "analyze_image",
    "suggest_shader_modifications",
    # Unity tools
    "UnityTools",
    "UnityToolError",
    "UNITY_TOOL_DEFINITIONS",
]
