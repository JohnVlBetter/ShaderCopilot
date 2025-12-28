"""
Integration tests for image-to-shader generation flow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import base64


class TestImageShaderFlow:
    """Integration tests for image-based shader generation."""

    @pytest.fixture
    def sample_image_base64(self):
        """Create a minimal sample image."""
        # Minimal 1x1 PNG
        png_bytes = bytes(
            [
                0x89,
                0x50,
                0x4E,
                0x47,
                0x0D,
                0x0A,
                0x1A,
                0x0A,
                0x00,
                0x00,
                0x00,
                0x0D,
                0x49,
                0x48,
                0x44,
                0x52,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x00,
                0x00,
                0x01,
                0x08,
                0x02,
                0x00,
                0x00,
                0x00,
                0x90,
                0x77,
                0x53,
                0xDE,
                0x00,
                0x00,
                0x00,
                0x0C,
                0x49,
                0x44,
                0x41,
                0x54,
                0x08,
                0xD7,
                0x63,
                0xF8,
                0xCF,
                0xC0,
                0x00,
                0x00,
                0x00,
                0x03,
                0x00,
                0x01,
                0x00,
                0x05,
                0xFE,
                0xD4,
                0xEF,
                0x00,
                0x00,
                0x00,
                0x00,
                0x49,
                0x45,
                0x4E,
                0x44,
                0xAE,
                0x42,
                0x60,
                0x82,
            ]
        )
        return base64.b64encode(png_bytes).decode("utf-8")

    @pytest.fixture
    def mock_vl_model(self):
        """Mock vision-language model."""
        model = MagicMock()
        model.generate = AsyncMock(
            return_value="""
I analyzed the image and found the following visual style:

**Style Analysis**:
- Art Style: Cel-shaded / Toon
- Dominant Colors: Orange (#FF6600), White (#FFFFFF)
- Lighting: Strong directional with rim highlights
- Shading: Hard-edge cartoon style with 2-3 color bands

**Shader Recommendations**:
1. Use a toon shader with discrete color bands
2. Add rim lighting for edge highlighting
3. Include outline effect for cartoon look
4. Main properties: _BaseColor, _ShadowColor, _RimColor, _RimPower
"""
        )
        return model

    @pytest.fixture
    def mock_code_model(self):
        """Mock code generation model."""
        model = MagicMock()
        model.generate = AsyncMock(
            return_value="""Shader "Custom/ToonFromImage"
{
    Properties
    {
        _BaseColor ("Base Color", Color) = (1, 0.4, 0, 1)
        _ShadowColor ("Shadow Color", Color) = (0.3, 0.1, 0, 1)
        _RimColor ("Rim Color", Color) = (1, 1, 1, 1)
        _RimPower ("Rim Power", Range(0.5, 8)) = 3
        _OutlineWidth ("Outline Width", Range(0, 0.1)) = 0.02
        _OutlineColor ("Outline Color", Color) = (0, 0, 0, 1)
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
                float3 viewDirWS : TEXCOORD1;
            };
            
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseColor;
                float4 _ShadowColor;
                float4 _RimColor;
                float _RimPower;
            CBUFFER_END
            
            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                OUT.positionCS = TransformObjectToHClip(IN.positionOS.xyz);
                OUT.normalWS = TransformObjectToWorldNormal(IN.normalOS);
                float3 posWS = TransformObjectToWorld(IN.positionOS.xyz);
                OUT.viewDirWS = GetWorldSpaceNormalizeViewDir(posWS);
                return OUT;
            }
            
            half4 frag(Varyings IN) : SV_Target
            {
                Light mainLight = GetMainLight();
                float NdotL = dot(IN.normalWS, mainLight.direction);
                float toonShade = step(0, NdotL);
                
                half4 color = lerp(_ShadowColor, _BaseColor, toonShade);
                
                float rim = 1.0 - saturate(dot(IN.normalWS, IN.viewDirWS));
                rim = pow(rim, _RimPower);
                color.rgb += _RimColor.rgb * rim;
                
                return color;
            }
            ENDHLSL
        }
    }
}"""
        )
        return model

    @pytest.mark.asyncio
    async def test_full_image_to_shader_flow(
        self, sample_image_base64, mock_vl_model, mock_code_model
    ):
        """Test the complete flow from image to shader code."""
        from shader_copilot.tools.llm_tools import analyze_image, generate_shader_code
        from shader_copilot.models.model_manager import ModelManager

        # Create mock model manager
        model_manager = MagicMock(spec=ModelManager)
        model_manager.generate = AsyncMock()

        # Step 1: Analyze image
        model_manager.generate.return_value = await mock_vl_model.generate()

        with patch(
            "shader_copilot.tools.llm_tools.get_model_manager",
            return_value=model_manager,
        ):
            analysis = await analyze_image(
                image_base64=sample_image_base64,
                model_manager=model_manager,
            )

        assert "toon" in analysis.lower() or "cartoon" in analysis.lower()

        # Step 2: Generate shader from analysis
        model_manager.generate.return_value = await mock_code_model.generate()

        with patch(
            "shader_copilot.tools.llm_tools.get_model_manager",
            return_value=model_manager,
        ):
            shader_code = await generate_shader_code(
                requirement="Create a shader matching this style",
                context=analysis,
                model_manager=model_manager,
            )

        assert shader_code is not None
        assert "Shader" in shader_code
        assert "_RimColor" in shader_code or "_BaseColor" in shader_code

    @pytest.mark.asyncio
    async def test_image_with_text_description(
        self, sample_image_base64, mock_vl_model, mock_code_model
    ):
        """Test combining image analysis with text description."""
        from shader_copilot.tools.llm_tools import analyze_image, generate_shader_code
        from shader_copilot.models.model_manager import ModelManager

        model_manager = MagicMock(spec=ModelManager)

        # Analyze image
        model_manager.generate = AsyncMock(return_value=await mock_vl_model.generate())

        with patch(
            "shader_copilot.tools.llm_tools.get_model_manager",
            return_value=model_manager,
        ):
            analysis = await analyze_image(
                image_base64=sample_image_base64,
                model_manager=model_manager,
            )

        # Combine with user text
        user_text = "Make it similar to this image but with a blue color scheme"
        combined_context = f"User request: {user_text}\n\nImage analysis:\n{analysis}"

        # Generate shader
        model_manager.generate = AsyncMock(
            return_value=await mock_code_model.generate()
        )

        with patch(
            "shader_copilot.tools.llm_tools.get_model_manager",
            return_value=model_manager,
        ):
            shader_code = await generate_shader_code(
                requirement=user_text,
                context=combined_context,
                model_manager=model_manager,
            )

        assert shader_code is not None
        assert "Shader" in shader_code

    @pytest.mark.asyncio
    async def test_router_detects_image_input(self):
        """Test that router correctly identifies image input."""
        from shader_copilot.router.router_agent import RouterAgent, Intent
        from shader_copilot.models.model_manager import ModelManager

        model_manager = MagicMock(spec=ModelManager)
        model_manager.generate = AsyncMock(return_value="GENERATE_SHADER")

        router = RouterAgent(model_manager=model_manager)

        intent = await router.classify(
            message="Create a shader like this",
            has_image=True,
        )

        assert intent == Intent.GENERATE_SHADER

    @pytest.mark.asyncio
    async def test_shader_gen_state_with_image(self):
        """Test ShaderGenState handles image data."""
        from shader_copilot.graphs.shader_gen.state import ShaderGenState

        state = ShaderGenState(
            user_requirement="Make this effect",
            session_id="test-123",
        )

        # Add image analysis to the correct field
        state.image_analysis = "Toon style with rim lighting from image analysis"

        assert state.image_analysis is not None
        assert "rim lighting" in state.image_analysis

    def test_image_message_payload(self, sample_image_base64):
        """Test message payload with image data."""
        from shader_copilot.server.messages import UserMessagePayload

        payload = UserMessagePayload(
            content="Create a shader like this image",
            images=[sample_image_base64],
        )

        assert len(payload.images) == 1
        assert payload.images[0] == sample_image_base64
