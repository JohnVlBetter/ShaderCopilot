"""
Shader Generation Graph using LangGraph.

Implements the text-to-shader generation workflow with image support.
"""

from typing import Any, Literal

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from shader_copilot.graphs.shader_gen.nodes import (
    analyze_image,
    analyze_requirement,
    check_should_compile,
    check_should_retry,
    finalize_failure,
    finalize_success,
    fix_validation_errors,
    generate_shader,
    handle_compile_result,
    prepare_retry,
    validate_shader,
)
from shader_copilot.graphs.shader_gen.state import ShaderGenState


def check_has_image(state: ShaderGenState) -> Literal["analyze_image", "analyze"]:
    """Conditional edge: check if image analysis is needed."""
    if state.reference_image:
        return "analyze_image"
    return "analyze"


def create_shader_gen_graph() -> CompiledStateGraph:
    """
    Create the shader generation graph.

    Graph Structure:

    START --+--[has_image]--> analyze_image -> analyze -> generate -> validate --+
            |                                                                     |
            +--[no_image]--> analyze ---------> generate -> validate --+          |
                                                                       |          |
                    +-- fix <--[invalid]-------------------------------+----------+
                    |                                                             |
                    +-> validate <----+                                      [valid]
                                      |                                           |
                                      |                                           v
                    retry <-[retry]-- compile_check <--[compile]-- (wait for tool response)
                      |                    |
                      |               [success]
                      |                    |
                      +--[fail]--> FAIL    +-> SUCCESS -> END

    Returns:
        Compiled state graph
    """
    # Create the graph builder
    builder = StateGraph(ShaderGenState)

    # Add nodes
    builder.add_node("analyze_image", analyze_image)
    builder.add_node("analyze", analyze_requirement)
    builder.add_node("generate", generate_shader)
    builder.add_node("validate", validate_shader)
    builder.add_node("fix", fix_validation_errors)
    builder.add_node("compile_check", handle_compile_result)
    builder.add_node("retry", prepare_retry)
    builder.add_node("success", finalize_success)
    builder.add_node("fail", finalize_failure)

    # Add conditional entry: check if we have an image to analyze
    builder.set_conditional_entry_point(
        check_has_image,
        {
            "analyze_image": "analyze_image",
            "analyze": "analyze",
        },
    )

    # Image analysis leads to requirement analysis
    builder.add_edge("analyze_image", "analyze")
    builder.add_edge("analyze", "generate")
    builder.add_edge("generate", "validate")

    # Conditional: validate -> compile or fix
    builder.add_conditional_edges(
        "validate",
        check_should_compile,
        {
            "compile": END,  # Pause for tool call (compile_shader)
            "fix": "fix",
        },
    )

    builder.add_edge("fix", "validate")

    # After compilation result received (via state update):
    # compile_check -> retry, fail, or success
    builder.add_conditional_edges(
        "compile_check",
        check_should_retry,
        {
            "retry": "retry",
            "fail": "fail",
            "success": "success",
        },
    )

    builder.add_edge("retry", "generate")
    builder.add_edge("success", END)
    builder.add_edge("fail", END)

    return builder.compile()


class ShaderGenRunner:
    """
    Runner for the shader generation graph.

    Handles the full lifecycle including tool calls and image input.
    """

    def __init__(self):
        self.graph = create_shader_gen_graph()

    async def run(
        self,
        user_requirement: str,
        session_id: str,
        max_retries: int = 3,
        reference_image: bytes | str | None = None,
        reference_image_mime: str | None = None,
        previous_code: str | None = None,
        is_modification: bool = False,
        conversation_context: str = "",
        on_progress: callable = None,
        on_tool_call: callable = None,
    ) -> ShaderGenState:
        """
        Run the shader generation graph.

        Args:
            user_requirement: User's shader description
            session_id: Session identifier
            max_retries: Maximum compilation retries
            reference_image: Optional reference image (bytes or base64 string)
            reference_image_mime: MIME type of the reference image
            previous_code: Existing shader code for modifications
            is_modification: Whether this is modifying an existing shader
            conversation_context: Recent conversation for context
            on_progress: Callback for progress updates
            on_tool_call: Callback for tool calls (compile_shader)

        Returns:
            Final state with generated shader
        """
        # Handle image input
        image_bytes = None
        if reference_image:
            if isinstance(reference_image, str):
                # Assume base64 encoded
                from shader_copilot.utils.image_utils import (
                    decode_base64_to_bytes,
                    extract_mime_type,
                )

                image_bytes = decode_base64_to_bytes(reference_image)
                if not reference_image_mime:
                    reference_image_mime = extract_mime_type(reference_image)
            else:
                image_bytes = reference_image

        # Initialize state
        initial_state = ShaderGenState(
            user_requirement=user_requirement,
            session_id=session_id,
            max_retries=max_retries,
            reference_image=image_bytes,
            reference_image_mime=reference_image_mime or "image/png",
            previous_code=previous_code,
            is_modification=is_modification,
            conversation_context=conversation_context,
        )

        # Run graph until it needs a tool call
        current_state = initial_state

        while True:
            # Run the graph
            result = await self.graph.ainvoke(current_state)
            current_state = ShaderGenState(**result)

            # Check if we need to compile
            if current_state.validation_passed and not current_state.is_complete:
                # Request compilation from Unity
                if on_tool_call:
                    compile_result = await on_tool_call(
                        "compile_shader",
                        {
                            "code": current_state.generated_code,
                            "shader_name": self._extract_shader_name(
                                current_state.generated_code
                            ),
                        },
                    )

                    # Update state with compile result
                    current_state.compile_result = compile_result

                    # Resume from compile_check node
                    result = await self.graph.ainvoke(
                        current_state, {"checkpoint_id": "compile_check"}
                    )
                    current_state = ShaderGenState(**result)
                else:
                    # No tool call handler, assume success for testing
                    break

            if current_state.is_complete:
                break

        return current_state

    def _extract_shader_name(self, code: str) -> str:
        """Extract shader name from code."""
        import re

        match = re.search(r'Shader\s+"([^"]+)"', code)
        return match.group(1) if match else "Generated/Shader"


# Create default instance
_shader_gen_graph: CompiledStateGraph | None = None


def get_shader_gen_graph() -> CompiledStateGraph:
    """Get or create the shader generation graph."""
    global _shader_gen_graph
    if _shader_gen_graph is None:
        _shader_gen_graph = create_shader_gen_graph()
    return _shader_gen_graph
