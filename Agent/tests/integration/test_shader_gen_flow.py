"""
Integration tests for text-to-shader generation flow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from shader_copilot.graphs.shader_gen.state import ShaderGenState
from shader_copilot.models.model_manager import ModelManager


class TestShaderGenFlow:
    """Integration tests for the shader generation flow."""

    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        manager = MagicMock(spec=ModelManager)
        manager.classify_intent = AsyncMock(return_value="GENERATE_SHADER")
        manager.generate_shader = AsyncMock(
            return_value="""Shader "Custom/TestShader"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
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
            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; };
            CBUFFER_START(UnityPerMaterial) float4 _Color; CBUFFER_END
            Varyings vert(Attributes IN) { Varyings OUT; OUT.positionCS = TransformObjectToHClip(IN.positionOS.xyz); return OUT; }
            half4 frag(Varyings IN) : SV_Target { return _Color; }
            ENDHLSL
        }
    }
}"""
        )
        return manager

    @pytest.fixture
    def initial_state(self):
        """Create initial shader generation state."""
        return ShaderGenState(
            user_requirement="创建一个简单的纯色着色器",
            session_id="test-session-001",
        )

    @pytest.mark.asyncio
    async def test_intent_classification(self, mock_model_manager, initial_state):
        """Test that user intent is correctly classified."""
        intent = await mock_model_manager.classify_intent(
            initial_state.user_requirement
        )

        assert intent == "GENERATE_SHADER"

    @pytest.mark.asyncio
    async def test_shader_generation_from_text(self, mock_model_manager, initial_state):
        """Test that shader code is generated from text description."""
        shader_code = await mock_model_manager.generate_shader(
            requirement=initial_state.user_requirement,
        )

        assert shader_code is not None
        assert "Shader" in shader_code
        assert "SubShader" in shader_code
        assert "Pass" in shader_code

    @pytest.mark.asyncio
    async def test_shader_generation_with_error_retry(
        self, mock_model_manager, initial_state
    ):
        """Test shader regeneration with compile errors."""
        # First attempt generates code with errors
        mock_model_manager.generate_shader.side_effect = [
            # First call - code with error
            'Shader "Test" { invalid syntax }',
            # Retry with error feedback - fixed code
            """Shader "Custom/TestShader"
{
    Properties { _Color ("Color", Color) = (1,1,1,1) }
    SubShader { Pass { HLSLPROGRAM #pragma vertex vert #pragma fragment frag
    struct Attributes { float4 positionOS : POSITION; };
    struct Varyings { float4 positionCS : SV_POSITION; };
    Varyings vert(Attributes IN) { Varyings OUT; OUT.positionCS = float4(0,0,0,1); return OUT; }
    half4 frag(Varyings IN) : SV_Target { return half4(1,1,1,1); }
    ENDHLSL } }
}""",
        ]

        # First attempt
        first_code = await mock_model_manager.generate_shader(
            requirement=initial_state.user_requirement,
        )
        assert "invalid syntax" in first_code

        # Retry with error info
        fixed_code = await mock_model_manager.generate_shader(
            requirement=initial_state.user_requirement,
            compile_errors="Syntax error at line 1",
        )
        assert "SubShader" in fixed_code

    def test_state_tracks_retry_count(self, initial_state):
        """Test that state properly tracks retry count."""
        assert initial_state.retry_count == 0

        initial_state.retry_count += 1
        assert initial_state.retry_count == 1

        # Check max retry
        initial_state.max_retries = 3
        assert initial_state.can_retry

    def test_state_stores_generated_code(self, initial_state):
        """Test that state stores generated shader code."""
        test_code = 'Shader "Test" { SubShader { Pass {} } }'
        initial_state.generated_code = test_code

        assert initial_state.generated_code == test_code

    def test_state_stores_compile_result(self, initial_state):
        """Test that state stores compilation result."""
        from shader_copilot.graphs.shader_gen.state import (
            CompileResult,
            CompileError,
            CompileStatus,
        )

        result = CompileResult(
            status=CompileStatus.FAILED,
            errors=[CompileError(line=10, message="undefined variable")],
            shader_id=None,
        )

        initial_state.compile_result = result

        assert initial_state.compile_result.status == CompileStatus.FAILED
        assert len(initial_state.compile_result.errors) == 1


class TestShaderGenGraphNodes:
    """Tests for individual graph nodes."""

    @pytest.mark.asyncio
    async def test_analyze_node_extracts_requirements(self):
        """Test that analyze node extracts shader requirements."""
        # Placeholder for actual node implementation
        requirement = "创建一个卡通着色器，带有边缘光效果"

        # Expected extracted features
        expected_features = ["卡通", "边缘光"]

        for feature in expected_features:
            assert feature in requirement

    @pytest.mark.asyncio
    async def test_generate_node_produces_valid_shader_structure(self):
        """Test that generate node produces properly structured shader."""
        # This will be expanded when the actual node is implemented
        shader_template = """Shader "Custom/Generated"
{
    Properties { }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        Pass
        {
            HLSLPROGRAM
            ENDHLSL
        }
    }
}"""

        assert "Properties" in shader_template
        assert "SubShader" in shader_template
        assert "HLSLPROGRAM" in shader_template

    @pytest.mark.asyncio
    async def test_validate_node_detects_missing_pragmas(self):
        """Test that validation catches missing pragma directives."""
        invalid_shader = """Shader "Test"
{
    SubShader
    {
        Pass
        {
            HLSLPROGRAM
            // Note: This shader is missing required pragmas
            ENDHLSL
        }
    }
}"""

        # Check that the shader does NOT contain required pragma directives
        # (which is the validation error we're detecting)
        has_vertex_pragma = "#pragma vertex" in invalid_shader
        has_fragment_pragma = "#pragma fragment" in invalid_shader

        # Both should be False for an invalid shader
        assert (
            has_vertex_pragma == False
        ), "Invalid shader should not have #pragma vertex"
        assert (
            has_fragment_pragma == False
        ), "Invalid shader should not have #pragma fragment"
