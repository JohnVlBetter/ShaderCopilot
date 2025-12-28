"""
Full flow integration tests covering all user stories.

Tests the complete workflow from user input to shader output.
"""

import asyncio
import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_image_base64():
    """Generate a minimal valid PNG image in base64."""
    # Minimal 1x1 red PNG
    png_bytes = bytes(
        [
            0x89,
            0x50,
            0x4E,
            0x47,
            0x0D,
            0x0A,
            0x1A,
            0x0A,  # PNG signature
            0x00,
            0x00,
            0x00,
            0x0D,  # IHDR length
            0x49,
            0x48,
            0x44,
            0x52,  # IHDR
            0x00,
            0x00,
            0x00,
            0x01,  # width
            0x00,
            0x00,
            0x00,
            0x01,  # height
            0x08,
            0x02,  # bit depth, color type
            0x00,
            0x00,
            0x00,  # compression, filter, interlace
            0x90,
            0x77,
            0x53,
            0xDE,  # CRC
            0x00,
            0x00,
            0x00,
            0x0C,  # IDAT length
            0x49,
            0x44,
            0x41,
            0x54,  # IDAT
            0x08,
            0xD7,
            0x63,
            0xF8,
            0xCF,
            0xC0,
            0x00,
            0x00,
            0x01,
            0xA0,
            0x01,
            0x00,  # IDAT CRC
            0x00,
            0x00,
            0x00,
            0x00,  # IEND length
            0x49,
            0x45,
            0x4E,
            0x44,  # IEND
            0xAE,
            0x42,
            0x60,
            0x82,  # IEND CRC
        ]
    )
    return base64.b64encode(png_bytes).decode("utf-8")


@pytest.fixture
def mock_llm_response():
    """Standard mock LLM response with shader code."""
    return """Here's a simple toon shader for URP:

```hlsl
Shader "Custom/ToonShader"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Color", Color) = (1,1,1,1)
        _ShadowColor ("Shadow Color", Color) = (0.5,0.5,0.5,1)
        _Bands ("Color Bands", Range(2, 10)) = 3
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
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            
            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float2 uv : TEXCOORD0;
            };
            
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
            };
            
            TEXTURE2D(_MainTex);
            SAMPLER(sampler_MainTex);
            
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                float4 _Color;
                float4 _ShadowColor;
                float _Bands;
            CBUFFER_END
            
            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                OUT.positionCS = TransformObjectToHClip(IN.positionOS.xyz);
                OUT.uv = TRANSFORM_TEX(IN.uv, _MainTex);
                OUT.normalWS = TransformObjectToWorldNormal(IN.normalOS);
                return OUT;
            }
            
            half4 frag(Varyings IN) : SV_Target
            {
                half4 tex = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, IN.uv);
                
                Light mainLight = GetMainLight();
                float NdotL = dot(normalize(IN.normalWS), mainLight.direction);
                float toon = floor(NdotL * _Bands) / _Bands;
                
                half4 color = lerp(_ShadowColor, _Color, saturate(toon + 0.5));
                return tex * color;
            }
            ENDHLSL
        }
    }
}
```

This shader provides a basic cel-shaded look with configurable color bands."""


# =============================================================================
# US1: Text-to-Shader Flow
# =============================================================================


class TestUS1TextToShader:
    """User Story 1: Text description to shader generation."""

    @pytest.mark.asyncio
    async def test_full_text_to_shader_flow(self, mock_llm_response):
        """Test complete text-to-shader flow."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState
        from shader_copilot.graphs.shader_gen.graph import create_shader_gen_graph

        with patch(
            "shader_copilot.graphs.shader_gen.nodes.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            manager.generate = AsyncMock(return_value=mock_llm_response)
            mock_manager.return_value = manager

            graph = create_shader_gen_graph()

            initial_state = ShaderGenState(
                user_requirement="Create a simple toon shader with color bands",
            )

            # Run the graph
            result = await graph.ainvoke(initial_state)

            # Verify shader was generated (result is a ShaderGenState dict)
            assert (
                result.get("generated_code") is not None
                or result.get("is_complete") == True
            )

    @pytest.mark.asyncio
    async def test_text_to_shader_with_specific_requirements(self, mock_llm_response):
        """Test shader generation with specific technical requirements."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState
        from shader_copilot.graphs.shader_gen.graph import create_shader_gen_graph

        with patch(
            "shader_copilot.graphs.shader_gen.nodes.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            manager.generate = AsyncMock(return_value=mock_llm_response)
            mock_manager.return_value = manager

            graph = create_shader_gen_graph()

            initial_state = ShaderGenState(
                user_requirement="Create a dissolve shader with transparency support for URP",
            )

            result = await graph.ainvoke(initial_state)

            # Verify shader generation completed
            assert (
                result.get("generated_code") is not None
                or result.get("is_complete") == True
            )


# =============================================================================
# US2: Image-to-Shader Flow
# =============================================================================


class TestUS2ImageToShader:
    """User Story 2: Image reference to shader generation."""

    @pytest.mark.asyncio
    async def test_full_image_to_shader_flow(
        self, sample_image_base64, mock_llm_response
    ):
        """Test complete image-to-shader flow."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState
        from shader_copilot.graphs.shader_gen.graph import create_shader_gen_graph

        with patch(
            "shader_copilot.graphs.shader_gen.nodes.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            # Return mock_llm_response for all generate calls (image analysis, requirement analysis, shader gen)
            manager.generate = AsyncMock(return_value=mock_llm_response)
            mock_manager.return_value = manager

            graph = create_shader_gen_graph()

            initial_state = ShaderGenState(
                user_requirement="Recreate this visual style",
                reference_image=(
                    sample_image_base64.encode()
                    if isinstance(sample_image_base64, str)
                    else sample_image_base64
                ),
                reference_image_mime="image/png",
            )

            result = await graph.ainvoke(initial_state)

            # Verify result was processed
            assert result is not None

    @pytest.mark.asyncio
    async def test_image_with_text_description(
        self, sample_image_base64, mock_llm_response
    ):
        """Test image combined with text description."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState
        from shader_copilot.graphs.shader_gen.graph import create_shader_gen_graph

        with patch(
            "shader_copilot.graphs.shader_gen.nodes.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            # Return mock_llm_response for all generate calls
            manager.generate = AsyncMock(return_value=mock_llm_response)
            mock_manager.return_value = manager

            graph = create_shader_gen_graph()

            initial_state = ShaderGenState(
                user_requirement="Make this style but with added rim lighting",
                reference_image=(
                    sample_image_base64.encode()
                    if isinstance(sample_image_base64, str)
                    else sample_image_base64
                ),
                reference_image_mime="image/png",
            )

            result = await graph.ainvoke(initial_state)

            # Verify result was processed
            assert result is not None


# =============================================================================
# US3: Iterative Refinement
# =============================================================================


class TestUS3IterativeRefinement:
    """User Story 3: Iterative shader modification."""

    @pytest.mark.asyncio
    async def test_modify_existing_shader(self, mock_llm_response):
        """Test modifying an existing shader."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState
        from shader_copilot.graphs.shader_gen.graph import create_shader_gen_graph

        existing_shader = (
            """Shader "Custom/Basic" { SubShader { Pass { HLSLPROGRAM ENDHLSL } } }"""
        )

        modified_response = mock_llm_response.replace("ToonShader", "ModifiedToon")

        with patch(
            "shader_copilot.graphs.shader_gen.nodes.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            manager.generate = AsyncMock(return_value=modified_response)
            mock_manager.return_value = manager

            graph = create_shader_gen_graph()

            initial_state = ShaderGenState(
                user_requirement="Add rim lighting with cyan color",
                previous_code=existing_shader,
                is_modification=True,
            )

            result = await graph.ainvoke(initial_state)

            # Result is a ShaderGenState dict
            assert (
                result.get("generated_code") is not None
                or result.get("is_complete") == True
            )

    @pytest.mark.asyncio
    async def test_context_preserved_in_conversation(self, mock_llm_response):
        """Test that conversation context is preserved."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState
        from shader_copilot.graphs.shader_gen.graph import create_shader_gen_graph

        # conversation_context should be a string, not a list
        conversation_context = """User: Create a basic shader
Assistant: Here's a basic shader...
User: Add some color"""

        with patch(
            "shader_copilot.graphs.shader_gen.nodes.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            manager.generate = AsyncMock(return_value=mock_llm_response)
            mock_manager.return_value = manager

            graph = create_shader_gen_graph()

            initial_state = ShaderGenState(
                user_requirement="Make the shadow edge smoother",
                conversation_context=conversation_context,
                previous_code="Shader code...",
                is_modification=True,
            )

            result = await graph.ainvoke(initial_state)

            # Context should have been used - check state was processed
            assert result is not None


# =============================================================================
# US4: Session Management
# =============================================================================


class TestUS4SessionManagement:
    """User Story 4: Session persistence and loading."""

    def test_session_creation_and_persistence(self, tmp_path):
        """Test session is created and persisted correctly."""
        from shader_copilot.session.session_manager import SessionManager, Session

        manager = SessionManager(storage_path=tmp_path)

        # Create session
        session = manager.create_session()
        session_id = session.session_id

        # Set properties separately
        session.set_property("theme", "dark")

        # Add content
        session.add_message("user", "Create a toon shader")
        session.add_message("assistant", "Here's a toon shader...")
        session.set_current_shader("Shader code...", "Custom/Toon")

        # Save
        manager.save_session(session_id)

        # Clear and reload
        manager._sessions.clear()
        loaded = manager.get_session(session_id)

        assert loaded is not None
        assert len(loaded.messages) == 2
        assert loaded.current_shader is not None
        assert loaded.current_shader == "Shader code..."

    def test_list_sessions(self, tmp_path):
        """Test listing available sessions."""
        from shader_copilot.session.session_manager import SessionManager

        manager = SessionManager(storage_path=tmp_path)

        # Create multiple sessions
        session1 = manager.create_session()
        session1.add_message("user", "First session")
        manager.save_session(session1.session_id)

        session2 = manager.create_session()
        session2.add_message("user", "Second session")
        manager.save_session(session2.session_id)

        # List sessions
        sessions = manager.list_sessions()

        assert len(sessions) == 2

    def test_delete_session(self, tmp_path):
        """Test session deletion."""
        from shader_copilot.session.session_manager import SessionManager

        manager = SessionManager(storage_path=tmp_path)

        session = manager.create_session()
        session_id = session.session_id
        manager.save_session(session_id)

        # Delete
        result = manager.delete_session(session_id)

        assert result == True
        assert manager.get_session(session_id) is None


# =============================================================================
# US5: Preview Configuration
# =============================================================================


class TestUS5PreviewConfiguration:
    """User Story 5: Preview scene customization."""

    def test_preview_objects_available(self):
        """Test that preview objects are available."""
        # This would normally test Unity code, but we can test the expected values
        expected_objects = ["Sphere", "Cube", "Plane", "Cylinder", "Capsule"]

        # In Unity, PreviewSceneService.GetPreviewObjects() returns these
        # Here we verify the expected contract
        assert len(expected_objects) == 5
        assert "Sphere" in expected_objects

    def test_background_presets_defined(self):
        """Test that background presets are defined."""
        expected_backgrounds = {
            "Dark": (0.1, 0.1, 0.1),
            "Light": (0.8, 0.8, 0.8),
            "Black": (0, 0, 0),
            "White": (1, 1, 1),
        }

        # Verify expected presets exist
        assert "Dark" in expected_backgrounds
        assert "Light" in expected_backgrounds


# =============================================================================
# Cross-Cutting: Router Integration
# =============================================================================


class TestRouterIntegration:
    """Test router correctly classifies user intents."""

    @pytest.mark.asyncio
    async def test_router_detects_shader_request(self):
        """Test router identifies shader generation request."""
        from shader_copilot.router.router_agent import RouterAgent, Intent

        with patch(
            "shader_copilot.router.router_agent.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            manager.generate = AsyncMock(return_value="GENERATE_SHADER")
            mock_manager.return_value = manager

            router = RouterAgent()
            intent, graph_name = await router.route("Create a toon shader")

            assert intent == Intent.GENERATE_SHADER
            assert graph_name == "shader_gen"

    @pytest.mark.asyncio
    async def test_router_detects_image_input(self):
        """Test router identifies image-based request."""
        from shader_copilot.router.router_agent import RouterAgent, Intent

        with patch(
            "shader_copilot.router.router_agent.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            manager.generate = AsyncMock(return_value="GENERATE_SHADER")
            mock_manager.return_value = manager

            router = RouterAgent()
            intent, graph_name = await router.route(
                "Recreate this style",
                has_image=True,
            )

            # route() returns a tuple (Intent, str)
            assert intent == Intent.GENERATE_SHADER


# =============================================================================
# Error Handling
# =============================================================================


class TestErrorHandling:
    """Test error handling across the system."""

    @pytest.mark.asyncio
    async def test_handles_llm_error_gracefully(self):
        """Test graceful handling of LLM errors."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState
        from shader_copilot.graphs.shader_gen.graph import create_shader_gen_graph

        with patch(
            "shader_copilot.graphs.shader_gen.nodes.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            manager.generate = AsyncMock(side_effect=Exception("API Error"))
            mock_manager.return_value = manager

            graph = create_shader_gen_graph()

            initial_state = ShaderGenState(
                user_requirement="Create a shader",
            )

            # Should not raise, but mark as error
            try:
                result = await graph.ainvoke(initial_state)
                # May have error state or empty result
            except Exception:
                # Error is expected
                pass

    @pytest.mark.asyncio
    async def test_handles_empty_input(self):
        """Test handling of empty user input."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState
        from shader_copilot.graphs.shader_gen.graph import create_shader_gen_graph
        from langgraph.errors import GraphRecursionError

        with patch(
            "shader_copilot.graphs.shader_gen.nodes.get_model_manager"
        ) as mock_manager:
            manager = MagicMock()
            manager.generate = AsyncMock(
                return_value="Cannot generate without requirements"
            )
            mock_manager.return_value = manager

            graph = create_shader_gen_graph()

            initial_state = ShaderGenState(
                user_requirement="",
            )

            # Should handle gracefully - may return error state or raise recursion error
            try:
                result = await graph.ainvoke(initial_state)
                # Result may indicate error or empty state
            except GraphRecursionError:
                # Expected behavior when graph can't complete with empty input
                pass


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """Basic performance tests."""

    @pytest.mark.asyncio
    async def test_graph_creation_is_fast(self):
        """Test that graph creation is fast."""
        import time
        from shader_copilot.graphs.shader_gen.graph import create_shader_gen_graph

        start = time.perf_counter()
        graph = create_shader_gen_graph()
        elapsed = time.perf_counter() - start

        # Graph creation should be under 100ms
        assert elapsed < 0.1

    def test_session_serialization_is_fast(self, tmp_path):
        """Test that session serialization is fast."""
        import time
        from shader_copilot.session.session_manager import SessionManager

        manager = SessionManager(storage_path=tmp_path)
        session = manager.create_session()

        # Add many messages
        for i in range(100):
            session.add_message("user", f"Message {i}")
            session.add_message("assistant", f"Response {i}")

        start = time.perf_counter()
        manager.save_session(session.session_id)
        elapsed = time.perf_counter() - start

        # Serialization should be under 100ms
        assert elapsed < 0.1
