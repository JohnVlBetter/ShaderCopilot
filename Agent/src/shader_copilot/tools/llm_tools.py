"""
LLM-powered tools for shader generation.
"""

from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from shader_copilot.models.model_manager import (
    ModelManager,
    ModelRole,
    get_model_manager,
)


async def generate_shader_code(
    requirement: str,
    context: str = "",
    previous_code: str = "",
    compile_errors: str = "",
    model_manager: Optional[ModelManager] = None,
) -> str:
    """
    Generate shader code using LLM.

    Args:
        requirement: User's shader requirement
        context: Additional context (conversation history, etc.)
        previous_code: Previous shader code (for modifications)
        compile_errors: Compilation errors from previous attempt
        model_manager: Optional model manager

    Returns:
        Generated shader code
    """
    if model_manager is None:
        model_manager = get_model_manager()

    system_prompt = """You are an expert Unity shader programmer.
Generate valid HLSL shader code for Unity's Universal Render Pipeline (URP).

Requirements:
1. Use proper URP shader structure
2. Include necessary pragmas and includes
3. Use HLSL syntax (not CG)
4. Follow Unity naming conventions
5. Include appropriate Properties for customization

Your response must contain ONLY the complete shader code.
Do not include any explanations before or after the code."""

    user_content = f"Create a shader with these requirements:\n{requirement}"

    if context:
        user_content += f"\n\nContext:\n{context}"

    if previous_code:
        user_content += f"\n\nPrevious code to modify:\n```hlsl\n{previous_code}\n```"

    if compile_errors:
        user_content += f"\n\nThe previous code had these compilation errors:\n{compile_errors}\n\nPlease fix these errors."

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    response = await model_manager.generate(messages, ModelRole.CODE)

    # Extract code from markdown if present
    return _extract_code(response)


async def analyze_shader_requirement(
    requirement: str,
    model_manager: Optional[ModelManager] = None,
) -> dict[str, Any]:
    """
    Analyze user requirement to extract shader features.

    Args:
        requirement: User's shader description
        model_manager: Optional model manager

    Returns:
        Dictionary with extracted features
    """
    if model_manager is None:
        model_manager = get_model_manager()

    system_prompt = """Analyze the shader requirement and extract key features.
Return a JSON object with these fields:
{
    "shader_type": "surface|unlit|postprocess|custom",
    "render_type": "opaque|transparent|cutout",
    "effects": ["list", "of", "effects"],
    "properties": ["list", "of", "properties"],
    "technical_notes": "any special requirements"
}

Return ONLY the JSON object, no other text."""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=requirement)]

    response = await model_manager.generate(messages, ModelRole.ROUTER)

    # Parse JSON response
    import json

    try:
        # Clean up response
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "shader_type": "custom",
            "render_type": "opaque",
            "effects": [],
            "properties": [],
            "technical_notes": requirement,
        }


async def explain_shader_code(
    code: str,
    question: str = "",
    model_manager: Optional[ModelManager] = None,
) -> str:
    """
    Explain shader code in natural language.

    Args:
        code: Shader code to explain
        question: Specific question about the code
        model_manager: Optional model manager

    Returns:
        Explanation text
    """
    if model_manager is None:
        model_manager = get_model_manager()

    system_prompt = """You are a shader expert explaining code to developers.
Explain the shader code clearly and concisely.
Focus on what the shader does visually and how it achieves the effect."""

    user_content = f"Shader code:\n```hlsl\n{code}\n```"

    if question:
        user_content += f"\n\nSpecific question: {question}"
    else:
        user_content += "\n\nPlease explain what this shader does."

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    return await model_manager.generate(messages, ModelRole.CODE)


async def analyze_image(
    image_base64: str,
    prompt: str = "Describe the visual style and effects in this image for shader recreation.",
    model_manager: Optional[ModelManager] = None,
) -> str:
    """
    Analyze an image to extract visual style information.

    Args:
        image_base64: Base64 encoded image data
        prompt: Analysis prompt
        model_manager: Optional model manager

    Returns:
        Analysis text describing visual style
    """
    if model_manager is None:
        model_manager = get_model_manager()

    # Note: This uses the vision model
    # The actual implementation depends on the VL model's API

    system_prompt = """You are a visual effects expert analyzing images for shader recreation.
Describe the visual elements, lighting, colors, and special effects visible in the image.
Focus on aspects that can be recreated with shaders:
- Color grading and tones
- Lighting effects (rim light, ambient, etc.)
- Surface properties (metallic, rough, glossy)
- Special effects (glow, outline, distortion)
- Art style (realistic, toon, pixel art, etc.)"""

    # For VL models, the image needs to be included in the message
    user_content = f"[Image attached]\n\n{prompt}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=[
                {"type": "text", "text": user_content},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                },
            ]
        ),
    ]

    return await model_manager.generate(messages, ModelRole.VISION)


async def suggest_shader_modifications(
    current_code: str,
    modification_request: str,
    model_manager: Optional[ModelManager] = None,
) -> str:
    """
    Suggest modifications to existing shader code.

    Args:
        current_code: Current shader code
        modification_request: What changes the user wants
        model_manager: Optional model manager

    Returns:
        Modified shader code
    """
    if model_manager is None:
        model_manager = get_model_manager()

    system_prompt = """You are modifying an existing Unity URP shader.
Apply the requested changes while preserving the existing functionality.
Return the COMPLETE modified shader code."""

    user_content = f"""Current shader:
```hlsl
{current_code}
```

Modification request: {modification_request}

Apply the changes and return the complete modified shader."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    response = await model_manager.generate(messages, ModelRole.CODE)
    return _extract_code(response)


def _extract_code(response: str) -> str:
    """Extract code from markdown response."""
    if "```" in response:
        lines = response.split("\n")
        in_block = False
        code_lines = []

        for line in lines:
            if line.strip().startswith("```"):
                if in_block:
                    break
                in_block = True
                continue
            if in_block:
                code_lines.append(line)

        if code_lines:
            return "\n".join(code_lines)

    # Find Shader declaration
    if 'Shader "' in response:
        idx = response.find('Shader "')
        return response[idx:].strip()

    return response.strip()
