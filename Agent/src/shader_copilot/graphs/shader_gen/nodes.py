"""
Shader generation graph nodes.

Each node is a function that takes state and returns updates.
"""

import base64
from typing import Any, Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from shader_copilot.graphs.shader_gen.state import (
    CompileResult,
    CompileStatus,
    ShaderGenState,
)
from shader_copilot.models.model_manager import (
    ModelManager,
    ModelRole,
    get_model_manager,
)


# =============================================================================
# Node Functions
# =============================================================================


async def analyze_image(state: ShaderGenState) -> dict[str, Any]:
    """
    Analyze reference image to extract visual style information.

    Uses the vision-language model to identify:
    - Art style (toon, realistic, pixel art, etc.)
    - Color palette and dominant colors
    - Lighting effects (rim light, ambient, etc.)
    - Surface properties (metallic, rough, glossy)
    - Special effects (glow, outline, distortion)
    """
    if not state.reference_image:
        return {
            "image_analysis": None,
            "current_stage": "no_image",
        }

    model_manager = get_model_manager()

    analysis_prompt = """You are a visual effects expert analyzing images for shader recreation.
Describe the visual elements, lighting, colors, and special effects visible in the image.

Focus on aspects that can be recreated with shaders:
- **Art Style**: Is it toon/cel-shaded, realistic PBR, pixel art, watercolor, etc.?
- **Color Palette**: What are the dominant colors and their relationships?
- **Lighting**: What kind of lighting is used (rim light, ambient, directional)?
- **Surface Properties**: Is it metallic, rough, glossy, matte?
- **Special Effects**: Any glow, outline, distortion, gradient effects?
- **Shading Model**: Number of color bands, gradient smoothness, shadow colors

Provide a structured analysis that can guide shader generation."""

    # Convert bytes to base64 if needed
    if isinstance(state.reference_image, bytes):
        image_b64 = base64.b64encode(state.reference_image).decode("utf-8")
    else:
        image_b64 = state.reference_image

    # Determine MIME type
    mime_type = state.reference_image_mime or "image/png"

    messages = [
        SystemMessage(content=analysis_prompt),
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"Analyze this image for shader recreation.\n\nUser context: {state.user_requirement}",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                },
            ]
        ),
    ]

    analysis = await model_manager.generate(messages, ModelRole.VISION)

    return {
        "image_analysis": analysis,
        "current_stage": "image_analyzed",
    }


async def analyze_requirement(state: ShaderGenState) -> dict[str, Any]:
    """
    Analyze user requirement and extract shader features.

    This node parses the user's description to identify:
    - Shader type (surface, unlit, post-process, etc.)
    - Visual effects (rim lighting, dissolve, outline, etc.)
    - Technical requirements (transparency, shadows, etc.)

    If image analysis is available, it incorporates that context.
    """
    model_manager = get_model_manager()

    analysis_prompt = """You are a shader expert. Analyze the user's shader requirement and extract:

1. **Shader Type**: What kind of shader is needed (surface shader, unlit, post-process effect, etc.)
2. **Visual Effects**: What visual effects are requested (rim lighting, outline, dissolve, etc.)
3. **Properties**: What parameters should be exposed (colors, textures, floats, etc.)
4. **Technical Notes**: Any special requirements (transparency, double-sided, etc.)

Format your response as a structured analysis.
Keep it concise and technical."""

    # Build user content with optional image analysis
    user_content = f"Shader requirement: {state.user_requirement}"

    if state.image_analysis:
        user_content += f"\n\n---\nReference Image Analysis:\n{state.image_analysis}"
        user_content += "\n\nIncorporate the visual style from the image analysis into your shader analysis."

    messages = [
        SystemMessage(content=analysis_prompt),
        HumanMessage(content=user_content),
    ]

    analysis = await model_manager.generate(messages, ModelRole.ROUTER)

    # Combine with image analysis for the next stage
    combined_analysis = analysis
    if state.image_analysis:
        combined_analysis = f"User Requirement Analysis:\n{analysis}\n\nImage Style Analysis:\n{state.image_analysis}"

    return {
        "requirement_analysis": combined_analysis,
        "current_stage": "analyzed",
    }


async def generate_shader(state: ShaderGenState) -> dict[str, Any]:
    """
    Generate shader code based on requirements.

    Uses the code model to generate URP-compatible HLSL shader code.
    Handles both new shader generation and modifications to existing shaders.
    """
    model_manager = get_model_manager()

    # Choose system prompt based on whether this is a modification
    if state.is_modification and state.previous_code:
        system_prompt = """You are an expert Unity shader programmer specializing in URP (Universal Render Pipeline).
You are MODIFYING an existing shader based on the user's request.

CRITICAL RULES:
1. Preserve the overall structure of the existing shader
2. Only change what the user specifically requests
3. Keep all existing properties unless explicitly asked to remove
4. Maintain URP compatibility
5. Keep the shader working and compilable

Respond with ONLY the complete modified shader code. No explanations before or after."""
    else:
        system_prompt = """You are an expert Unity shader programmer specializing in URP (Universal Render Pipeline).
Generate a complete, valid HLSL shader for Unity URP based on the requirements.

CRITICAL RULES:
1. Use URP shader structure with proper includes
2. Include all necessary pragmas (#pragma vertex, #pragma fragment)
3. Use HLSL syntax, not CG
4. Include proper CBUFFER for material properties
5. Use TEXTURE2D and SAMPLER macros for textures
6. Include proper Tags for URP compatibility

Shader Structure Template:
```hlsl
Shader "Custom/ShaderName"
{
    Properties
    {
        // Exposed properties
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            
            // Structs, CBUFFER, functions
            ENDHLSL
        }
    }
}
```

Respond with ONLY the complete shader code. No explanations before or after."""

    # Build the request
    user_content = f"Requirement: {state.user_requirement}"

    # Include conversation context if available
    if state.conversation_context:
        user_content = f"Conversation context:\n{state.conversation_context}\n\nCurrent request: {state.user_requirement}"

    # Include previous code for modifications
    if state.is_modification and state.previous_code:
        user_content += (
            f"\n\nExisting shader to modify:\n```hlsl\n{state.previous_code}\n```"
        )

    # Include requirement analysis (may contain image analysis if available)
    if state.requirement_analysis:
        user_content += f"\n\nAnalysis:\n{state.requirement_analysis}"

    # If retrying, include error information
    if (
        state.compile_result
        and state.compile_result.status == CompileStatus.FAILED
        and state.retry_count > 0
    ):
        user_content += f"\n\nPrevious code had compilation errors:\n"
        user_content += "\n".join(e.message for e in state.compile_result.errors)
        user_content += "\n\nPlease fix these errors in the new version."

        if state.generated_code:
            user_content += f"\n\nPrevious code:\n```hlsl\n{state.generated_code}\n```"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    shader_code = await model_manager.generate(messages, ModelRole.CODE)

    # Extract code from markdown code block if present
    shader_code = extract_shader_code(shader_code)

    return {
        "generated_code": shader_code,
        "current_stage": "generated",
    }


async def validate_shader(state: ShaderGenState) -> dict[str, Any]:
    """
    Validate shader code structure before compilation.

    Checks for common issues that would cause compilation to fail.
    """
    code = state.generated_code or ""

    validation_errors: list[str] = []

    # Check for required elements
    if 'Shader "' not in code and 'Shader "' not in code:
        validation_errors.append("Missing Shader declaration")

    if "SubShader" not in code:
        validation_errors.append("Missing SubShader block")

    if "Pass" not in code:
        validation_errors.append("Missing Pass block")

    if "#pragma vertex" not in code:
        validation_errors.append("Missing #pragma vertex directive")

    if "#pragma fragment" not in code:
        validation_errors.append("Missing #pragma fragment directive")

    # Check for URP includes
    if "com.unity.render-pipelines" not in code:
        validation_errors.append(
            "Missing URP include (Packages/com.unity.render-pipelines.universal/...)"
        )

    # Check for HLSLPROGRAM block
    if "HLSLPROGRAM" not in code:
        validation_errors.append(
            "Missing HLSLPROGRAM block (using CGPROGRAM instead of HLSL?)"
        )

    if "ENDHLSL" not in code:
        validation_errors.append("Missing ENDHLSL")

    is_valid = len(validation_errors) == 0

    return {
        "validation_passed": is_valid,
        "validation_errors": validation_errors,
        "current_stage": "validated" if is_valid else "validation_failed",
    }


def check_should_compile(state: ShaderGenState) -> Literal["compile", "fix"]:
    """
    Conditional edge: decide whether to compile or fix validation errors.
    """
    if state.validation_passed:
        return "compile"
    return "fix"


async def fix_validation_errors(state: ShaderGenState) -> dict[str, Any]:
    """
    Fix validation errors in the generated shader.
    """
    model_manager = get_model_manager()

    fix_prompt = """You are a shader debugging expert. Fix the following validation errors in the shader code.

Validation Errors:
{errors}

Current Shader Code:
```hlsl
{code}
```

Provide the COMPLETE fixed shader code. Ensure all validation issues are resolved."""

    prompt = fix_prompt.format(
        errors="\n".join(f"- {e}" for e in (state.validation_errors or [])),
        code=state.generated_code or "",
    )

    messages = [
        SystemMessage(
            content="Fix the shader validation errors. Output only the corrected shader code."
        ),
        HumanMessage(content=prompt),
    ]

    fixed_code = await model_manager.generate(messages, ModelRole.CODE)
    fixed_code = extract_shader_code(fixed_code)

    return {
        "generated_code": fixed_code,
        "current_stage": "fixed",
    }


def handle_compile_result(state: ShaderGenState) -> dict[str, Any]:
    """
    Process compilation result from Unity tool call.

    This node is called after receiving TOOL_RESPONSE from Unity.
    """
    if state.compile_result and state.compile_result.success:
        return {
            "current_stage": "compiled",
        }
    else:
        # Increment retry counter
        return {
            "retry_count": state.retry_count + 1,
            "current_stage": "compile_failed",
        }


def check_should_retry(state: ShaderGenState) -> Literal["retry", "fail", "success"]:
    """
    Conditional edge: decide whether to retry, fail, or succeed.
    """
    if state.compile_result and state.compile_result.success:
        return "success"

    if state.can_retry:
        return "retry"

    return "fail"


async def prepare_retry(state: ShaderGenState) -> dict[str, Any]:
    """
    Prepare state for retry attempt.
    """
    return {
        "current_stage": "retrying",
    }


async def finalize_success(state: ShaderGenState) -> dict[str, Any]:
    """
    Finalize successful shader generation.
    """
    return {
        "is_complete": True,
        "current_stage": "complete",
    }


async def finalize_failure(state: ShaderGenState) -> dict[str, Any]:
    """
    Finalize failed shader generation.
    """
    error_summary = "Shader generation failed after maximum retry attempts."

    if state.compile_result and state.compile_result.errors:
        error_summary += "\n\nFinal errors:\n" + "\n".join(state.compile_result.errors)

    return {
        "is_complete": True,
        "error": error_summary,
        "current_stage": "failed",
    }


# =============================================================================
# Helper Functions
# =============================================================================


def extract_shader_code(response: str) -> str:
    """
    Extract shader code from LLM response.

    Handles markdown code blocks and raw code.
    """
    # Check for markdown code block
    if "```" in response:
        # Find code block
        lines = response.split("\n")
        in_code_block = False
        code_lines = []

        for line in lines:
            if line.strip().startswith("```"):
                if in_code_block:
                    break  # End of code block
                else:
                    in_code_block = True
                    continue  # Skip the opening ```

            if in_code_block:
                code_lines.append(line)

        if code_lines:
            return "\n".join(code_lines)

    # No code block found, return as-is but try to find Shader declaration
    if 'Shader "' in response or 'Shader "' in response:
        # Find the start of the shader
        start_idx = response.find('Shader "')
        if start_idx == -1:
            start_idx = response.find('Shader "')

        if start_idx != -1:
            return response[start_idx:].strip()

    return response.strip()
