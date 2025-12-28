"""
Integration tests for shader iteration flow.
Tests the ability to modify and improve shaders through conversation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestShaderIteration:
    """Integration tests for iterative shader modification."""

    @pytest.fixture
    def initial_shader_code(self):
        """Create an initial shader for modification tests."""
        return """Shader "Custom/ToonShader"
{
    Properties
    {
        _BaseColor ("Base Color", Color) = (1, 1, 1, 1)
        _ShadowColor ("Shadow Color", Color) = (0.3, 0.3, 0.3, 1)
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
            };
            
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 normalWS : TEXCOORD0;
            };
            
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseColor;
                float4 _ShadowColor;
            CBUFFER_END
            
            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                OUT.positionCS = TransformObjectToHClip(IN.positionOS.xyz);
                OUT.normalWS = TransformObjectToWorldNormal(IN.normalOS);
                return OUT;
            }
            
            half4 frag(Varyings IN) : SV_Target
            {
                Light mainLight = GetMainLight();
                float NdotL = dot(IN.normalWS, mainLight.direction);
                float toonShade = step(0, NdotL);
                
                half4 color = lerp(_ShadowColor, _BaseColor, toonShade);
                return color;
            }
            ENDHLSL
        }
    }
}"""

    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        manager = MagicMock()
        manager.generate = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_add_rim_lighting_to_existing_shader(
        self, initial_shader_code, mock_model_manager
    ):
        """Test adding rim lighting to an existing toon shader."""
        from shader_copilot.tools.llm_tools import suggest_shader_modifications

        # Mock the modification response
        modified_shader = initial_shader_code.replace(
            "half4 color = lerp(_ShadowColor, _BaseColor, toonShade);",
            """half4 color = lerp(_ShadowColor, _BaseColor, toonShade);
                
                // Add rim lighting
                float3 viewDirWS = GetWorldSpaceNormalizeViewDir(IN.positionWS);
                float rim = 1.0 - saturate(dot(IN.normalWS, viewDirWS));
                rim = pow(rim, _RimPower);
                color.rgb += _RimColor.rgb * rim;""",
        )

        mock_model_manager.generate.return_value = modified_shader

        with patch(
            "shader_copilot.tools.llm_tools.get_model_manager",
            return_value=mock_model_manager,
        ):
            result = await suggest_shader_modifications(
                current_code=initial_shader_code,
                modification_request="添加边缘光效果",
                model_manager=mock_model_manager,
            )

        assert result is not None
        # The modification should preserve the original shader structure
        assert "Shader" in result
        mock_model_manager.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_color_in_existing_shader(
        self, initial_shader_code, mock_model_manager
    ):
        """Test changing colors in an existing shader."""
        from shader_copilot.tools.llm_tools import suggest_shader_modifications

        # Mock changing base color to blue
        modified_shader = initial_shader_code.replace(
            '_BaseColor ("Base Color", Color) = (1, 1, 1, 1)',
            '_BaseColor ("Base Color", Color) = (0.2, 0.4, 1, 1)',
        )

        mock_model_manager.generate.return_value = modified_shader

        with patch(
            "shader_copilot.tools.llm_tools.get_model_manager",
            return_value=mock_model_manager,
        ):
            result = await suggest_shader_modifications(
                current_code=initial_shader_code,
                modification_request="把基础颜色改成蓝色",
                model_manager=mock_model_manager,
            )

        assert result is not None
        assert "Shader" in result

    @pytest.mark.asyncio
    async def test_session_preserves_shader_history(self):
        """Test that session manager preserves shader modification history."""
        from shader_copilot.session.session_manager import SessionManager

        session_manager = SessionManager()
        session_id = "test-session-123"

        # Create a new session
        session = session_manager.create_session(session_id)

        # Add initial shader generation
        session.add_message("user", "创建一个卡通着色器")
        session.add_message("assistant", "好的，我来创建一个卡通着色器。")
        session.set_current_shader('Shader "Custom/Toon" { ... }')

        # Add modification request
        session.add_message("user", "添加边缘光")
        session.add_message("assistant", "已添加边缘光效果。")
        session.set_current_shader('Shader "Custom/ToonWithRim" { ... }')

        # Verify history is preserved
        assert len(session.messages) == 4
        assert session.current_shader == 'Shader "Custom/ToonWithRim" { ... }'

        # Get previous shader for context
        history = session.get_shader_history()
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_context_aware_modification(
        self, initial_shader_code, mock_model_manager
    ):
        """Test that modifications are context-aware of previous changes."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState

        # Create state with existing shader
        state = ShaderGenState(
            user_requirement="把边缘光改成蓝色",
            session_id="test-123",
            generated_code=initial_shader_code,
        )

        assert state.generated_code == initial_shader_code
        assert state.user_requirement == "把边缘光改成蓝色"

    @pytest.mark.asyncio
    async def test_modify_shader_with_compile_error_feedback(self, mock_model_manager):
        """Test shader modification with compile error feedback."""
        from shader_copilot.graphs.shader_gen.state import (
            ShaderGenState,
            CompileResult,
            CompileError,
            CompileStatus,
        )

        # Create state with compile errors
        state = ShaderGenState(
            user_requirement="修复编译错误",
            session_id="test-123",
            generated_code='Shader "Broken" { invalid code }',
            compile_result=CompileResult(
                status=CompileStatus.FAILED,
                errors=[
                    CompileError(line=1, message="unexpected token 'invalid'"),
                    CompileError(line=1, message="missing SubShader block"),
                ],
            ),
            retry_count=1,
        )

        assert state.has_compile_errors
        assert len(state.compile_result.errors) == 2
        assert state.can_retry

    @pytest.mark.asyncio
    async def test_iteration_preserves_user_customizations(self):
        """Test that iterations don't lose user-specified properties."""
        from shader_copilot.session.session_manager import Session

        session = Session(session_id="test-123")

        # Track user customizations
        session.set_property("_RimColor", "(1, 0.5, 0, 1)")  # Orange rim
        session.set_property("_RimPower", "3.0")

        # Ensure customizations are tracked
        props = session.get_properties()
        assert props.get("_RimColor") == "(1, 0.5, 0, 1)"
        assert props.get("_RimPower") == "3.0"


class TestConversationContext:
    """Test conversation context handling for iterations."""

    @pytest.mark.asyncio
    async def test_build_context_from_history(self):
        """Test building context from conversation history."""
        from shader_copilot.session.session_manager import SessionManager

        session_manager = SessionManager()
        session = session_manager.create_session("ctx-test")

        # Build up conversation
        session.add_message("user", "创建一个卡通着色器")
        session.add_message("assistant", "我已创建了一个基础的卡通着色器。")
        session.add_message("user", "添加边缘光")

        # Build context for next generation
        context = session.build_context(max_messages=10)

        assert "卡通着色器" in context
        assert "边缘光" in context

    @pytest.mark.asyncio
    async def test_detect_modification_intent(self):
        """Test detecting modification vs new shader intent."""
        from shader_copilot.router.router_agent import RouterAgent, Intent
        from shader_copilot.models.model_manager import ModelManager

        model_manager = MagicMock(spec=ModelManager)
        model_manager.generate = AsyncMock(return_value="MODIFY_SHADER")

        router = RouterAgent(model_manager=model_manager)

        intent = await router.classify(
            message="把边缘光改成蓝色",
            has_existing_shader=True,
        )

        assert intent == Intent.MODIFY_SHADER

    @pytest.mark.asyncio
    async def test_new_shader_vs_modify(self):
        """Test distinguishing new shader request from modification."""
        from shader_copilot.router.router_agent import RouterAgent, Intent
        from shader_copilot.models.model_manager import ModelManager

        model_manager = MagicMock(spec=ModelManager)
        router = RouterAgent(model_manager=model_manager)

        # New shader request
        model_manager.generate = AsyncMock(return_value="GENERATE_SHADER")
        intent1 = await router.classify(
            message="创建一个水面效果着色器",
            has_existing_shader=True,
        )
        assert intent1 == Intent.GENERATE_SHADER

        # Modification request
        model_manager.generate = AsyncMock(return_value="MODIFY_SHADER")
        intent2 = await router.classify(
            message="把颜色改成红色",
            has_existing_shader=True,
        )
        assert intent2 == Intent.MODIFY_SHADER
