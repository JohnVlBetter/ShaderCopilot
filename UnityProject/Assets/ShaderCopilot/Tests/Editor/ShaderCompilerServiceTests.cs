using NUnit.Framework;
using ShaderCopilot.Editor.Services;
using UnityEngine;

namespace ShaderCopilot.Editor.Tests
{
    /// <summary>
    /// Unit tests for ShaderCompilerService.
    /// </summary>
    [TestFixture]
    public class ShaderCompilerServiceTests
    {
        [Test]
        public void ExtractShaderName_ValidShader_ReturnsName()
        {
            var code = @"Shader ""Custom/MyShader""
{
    Properties {}
    SubShader {}
}";
            var name = ShaderCompilerService.ExtractShaderName(code);

            Assert.AreEqual("Custom/MyShader", name);
        }

        [Test]
        public void ExtractShaderName_NoShaderDeclaration_ReturnsNull()
        {
            var code = "// This is not a valid shader";

            var name = ShaderCompilerService.ExtractShaderName(code);

            Assert.IsNull(name);
        }

        [Test]
        public void ExtractShaderName_URPShader_ReturnsCorrectName()
        {
            var code = @"Shader ""Universal Render Pipeline/Lit""
{
    Properties
    {
        _BaseColor(""Base Color"", Color) = (1, 1, 1, 1)
    }
    SubShader
    {
        Tags { ""RenderType"" = ""Opaque"" ""RenderPipeline"" = ""UniversalPipeline"" }
        Pass {}
    }
}";
            var name = ShaderCompilerService.ExtractShaderName(code);

            Assert.AreEqual("Universal Render Pipeline/Lit", name);
        }

        [Test]
        public void GetOutputPath_ValidInput_ReturnsCorrectPath()
        {
            var path = ShaderCompilerService.GetOutputPath("Custom/TestShader", "Assets/Shaders/Generated");

            Assert.IsTrue(path.Contains("Custom_TestShader"));
            Assert.IsTrue(path.EndsWith(".shader"));
        }

        [Test]
        public void GetOutputPath_NullShaderName_HandlesGracefully()
        {
            // GetOutputPath with null throws ArgumentNullException
            Assert.Throws<System.ArgumentNullException>(() =>
            {
                ShaderCompilerService.GetOutputPath(null, "Assets/Shaders/Generated");
            });
        }
    }
}
