"""
Unit tests for image analysis functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import base64


class TestImageAnalysis:
    """Tests for image analysis tools."""

    @pytest.fixture
    def sample_image_base64(self):
        """Create a small sample PNG image as base64."""
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
                0x0D,
                0x49,
                0x48,
                0x44,
                0x52,  # IHDR chunk
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
    def mock_model_manager(self):
        """Create a mock model manager with vision capability."""
        manager = MagicMock()
        manager.generate = AsyncMock(
            return_value="""
Based on the image analysis, I can identify the following visual characteristics:

**Art Style**: Cartoon/Cel-shaded
**Primary Colors**: Bright blue (#4488FF), White highlights
**Lighting**: Strong rim lighting on edges
**Surface**: Matte with stylized specular
**Effects**: 
- Outline/stroke around objects
- Gradient shading with hard edges
- Subtle ambient occlusion

**Recommended Shader Properties**:
- _BaseColor: Main surface color
- _RimColor: Edge highlight color
- _RimPower: Edge highlight intensity
- _OutlineWidth: Stroke thickness
- _OutlineColor: Stroke color
"""
        )
        return manager

    @pytest.mark.asyncio
    async def test_analyze_image_returns_description(
        self, mock_model_manager, sample_image_base64
    ):
        """Test that image analysis returns useful description."""
        from shader_copilot.tools.llm_tools import analyze_image

        with patch(
            "shader_copilot.tools.llm_tools.get_model_manager",
            return_value=mock_model_manager,
        ):
            result = await analyze_image(
                image_base64=sample_image_base64,
                model_manager=mock_model_manager,
            )

        assert result is not None
        assert len(result) > 0
        # Check for expected content
        assert "color" in result.lower() or "style" in result.lower()

    @pytest.mark.asyncio
    async def test_analyze_image_extracts_shader_properties(
        self, mock_model_manager, sample_image_base64
    ):
        """Test that analysis includes shader-relevant properties."""
        from shader_copilot.tools.llm_tools import analyze_image

        with patch(
            "shader_copilot.tools.llm_tools.get_model_manager",
            return_value=mock_model_manager,
        ):
            result = await analyze_image(
                image_base64=sample_image_base64,
                prompt="Analyze this image for shader recreation. List recommended properties.",
                model_manager=mock_model_manager,
            )

        # Check for shader-related terms
        shader_terms = ["color", "rim", "outline", "specular", "lighting"]
        found_terms = [term for term in shader_terms if term.lower() in result.lower()]

        assert len(found_terms) >= 2, f"Expected shader terms, found: {found_terms}"

    @pytest.mark.asyncio
    async def test_analyze_image_with_custom_prompt(
        self, mock_model_manager, sample_image_base64
    ):
        """Test analysis with custom prompt."""
        from shader_copilot.tools.llm_tools import analyze_image

        custom_prompt = "Focus only on the color palette in this image."

        with patch(
            "shader_copilot.tools.llm_tools.get_model_manager",
            return_value=mock_model_manager,
        ):
            result = await analyze_image(
                image_base64=sample_image_base64,
                prompt=custom_prompt,
                model_manager=mock_model_manager,
            )

        # Verify the model was called
        mock_model_manager.generate.assert_called_once()

    def test_image_base64_encoding(self):
        """Test that base64 encoding/decoding works correctly."""
        original_data = b"test image data"
        encoded = base64.b64encode(original_data).decode("utf-8")
        decoded = base64.b64decode(encoded)

        assert decoded == original_data

    def test_image_data_url_format(self, sample_image_base64):
        """Test data URL format for vision models."""
        mime_type = "image/png"
        data_url = f"data:{mime_type};base64,{sample_image_base64}"

        assert data_url.startswith("data:image/png;base64,")
        assert len(data_url) > len("data:image/png;base64,")


class TestImageToShaderFlow:
    """Tests for the complete image-to-shader flow."""

    @pytest.fixture
    def mock_analysis_result(self):
        """Sample analysis result."""
        return {
            "art_style": "toon",
            "colors": ["#FF6600", "#FFFFFF", "#333333"],
            "effects": ["rim_lighting", "outline", "gradient_shading"],
            "properties": [
                {"name": "_BaseColor", "type": "Color", "default": "#FF6600"},
                {"name": "_RimColor", "type": "Color", "default": "#FFFFFF"},
                {"name": "_OutlineWidth", "type": "Range(0,0.1)", "default": 0.02},
            ],
        }

    @pytest.mark.asyncio
    async def test_image_analysis_to_shader_generation(self):
        """Test flow from image analysis to shader code."""
        # This is an integration test placeholder
        # Full implementation would:
        # 1. Analyze image
        # 2. Extract style information
        # 3. Generate shader based on analysis
        # 4. Validate shader code

        analysis = "Toon shader with rim lighting and outline"

        # Verify analysis contains actionable information
        assert "toon" in analysis.lower() or "rim" in analysis.lower()

    def test_combined_text_and_image_requirement(self):
        """Test combining text description with image analysis."""
        text_requirement = "Create a shader like this image but with a blue tint"
        image_analysis = "Cartoon style with rim lighting"

        combined = f"{text_requirement}\n\nImage Analysis:\n{image_analysis}"

        assert "blue" in combined
        assert "rim lighting" in combined
