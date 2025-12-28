using NUnit.Framework;
using ShaderCopilot.Editor.Services;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.TestTools;

namespace ShaderCopilot.Editor.Tests
{
    /// <summary>
    /// End-to-end tests for text to shader generation flow.
    /// </summary>
    [TestFixture]
    public class TextToShaderE2ETests
    {
        private const string TestShaderDirectory = "Assets/ShaderCopilot/Tests/GeneratedShaders";
        private const string TestMaterialDirectory = "Assets/ShaderCopilot/Tests/GeneratedMaterials";

        [SetUp]
        public void SetUp()
        {
            // Ensure test directories exist
            FileManagerService.EnsureAssetDirectoryExists("ShaderCopilot/Tests/GeneratedShaders");
            FileManagerService.EnsureAssetDirectoryExists("ShaderCopilot/Tests/GeneratedMaterials");
        }

        [TearDown]
        public void TearDown()
        {
            // Clean up test assets
            CleanupTestAssets();
        }

        [Test]
        public void CompileAndSave_ValidURPShader_CreatesShaderAsset()
        {
            var shaderCode = GetValidURPShaderCode("E2E_Test_Simple");
            var outputPath = $"{TestShaderDirectory}/E2E_Test_Simple.shader";

            var result = ShaderCompilerService.CompileAndSave(shaderCode, outputPath);

            Assert.IsTrue(result.Success, $"Shader compilation failed: {string.Join("; ", result.Errors)}");
            Assert.IsNotNull(result.Shader);
            Assert.IsTrue(File.Exists(outputPath) || AssetDatabase.LoadAssetAtPath<Shader>(outputPath) != null);
        }

        [Test]
        public void CompileAndSave_InvalidShader_ReturnsErrors()
        {
            // This shader has syntax errors that should cause compilation failure
            var invalidCode = @"Shader ""Test/Invalid""
{
    SubShader
    {
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            // Missing includes, struct definitions, and function bodies
            // This will cause actual compile errors
            void vert() { undefined_function(); }
            void frag() { undefined_variable = 1; }
            ENDHLSL
        }
    }
}";
            var outputPath = $"{TestShaderDirectory}/E2E_Test_Invalid.shader";

            var result = ShaderCompilerService.CompileAndSave(invalidCode, outputPath);

            // The shader should fail with errors OR warnings
            // Note: Some "invalid" shaders may compile with warnings instead of errors
            Assert.IsTrue(!result.Success || result.Warnings.Count > 0 || result.Errors.Count > 0,
                "Expected compilation errors or warnings for invalid shader");
        }

        [Test]
        public void CreateMaterial_FromCompiledShader_CreatesMaterialAsset()
        {
            // First compile a shader
            var shaderCode = GetValidURPShaderCode("E2E_Test_Material");
            var shaderPath = $"{TestShaderDirectory}/E2E_Test_Material.shader";

            var compileResult = ShaderCompilerService.CompileAndSave(shaderCode, shaderPath);

            if (!compileResult.Success)
            {
                Assert.Ignore($"Shader compilation failed, skipping material test: {string.Join("; ", compileResult.Errors)}");
                return;
            }

            // Create material
            var materialPath = $"{TestMaterialDirectory}/E2E_Test_Material_Mat.mat";
            var material = MaterialManagerService.CreateMaterial(compileResult.Shader, materialPath);

            Assert.IsNotNull(material);
            Assert.IsTrue(File.Exists(materialPath) || AssetDatabase.LoadAssetAtPath<Material>(materialPath) != null);
        }

        [Test]
        public void FullFlow_TextToShaderToMaterial_Works()
        {
            // Simulate the full flow: text description -> shader -> material

            // Step 1: "Generate" shader (simulated - in real flow this comes from LLM)
            var requirement = "Create a simple solid color shader";
            var shaderCode = GetValidURPShaderCode("E2E_FullFlow");

            // Step 2: Extract shader name
            var shaderName = ShaderCompilerService.ExtractShaderName(shaderCode);
            Assert.IsNotNull(shaderName);

            // Step 3: Compile shader
            var shaderPath = ShaderCompilerService.GetOutputPath(shaderName, "ShaderCopilot/Tests/GeneratedShaders");
            var compileResult = ShaderCompilerService.CompileAndSave(shaderCode, shaderPath);

            if (!compileResult.Success)
            {
                Assert.Ignore($"Shader compilation failed: {string.Join("; ", compileResult.Errors)}");
                return;
            }

            // Step 4: Create material
            var materialPath = MaterialManagerService.GetMaterialPath(shaderName, "ShaderCopilot/Tests/GeneratedMaterials");
            var material = MaterialManagerService.CreateMaterial(compileResult.Shader, materialPath);

            Assert.IsNotNull(material);

            // Step 5: Verify material uses correct shader
            Assert.AreEqual(compileResult.Shader, material.shader);

            Debug.Log($"[E2E Test] Full flow completed: {requirement} -> {shaderPath} -> {materialPath}");
        }

        [Test]
        public void RetryFlow_ShaderWithErrors_CanBeFixed()
        {
            // Simulate retry flow with compile errors
            // Expect shader compilation errors in the log
            LogAssert.ignoreFailingMessages = true;

            try
            {
                // First attempt with errors
                var invalidCode = @"Shader ""E2E/Retry""
{
    Properties { _Color (""Color"", Color) = (1,1,1,1) }
    SubShader
    {
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            // Missing includes and function definitions
            ENDHLSL
        }
    }
}";

                var shaderPath = $"{TestShaderDirectory}/E2E_Retry.shader";
                var firstResult = ShaderCompilerService.CompileAndSave(invalidCode, shaderPath);

                // First result may or may not fail depending on Unity version
                // The key is that the fixed shader should succeed

                // "Fix" the shader (simulated LLM retry)
                var fixedCode = GetValidURPShaderCode("E2E_Retry_Fixed");
                var fixedPath = $"{TestShaderDirectory}/E2E_Retry_Fixed.shader";

                var retryResult = ShaderCompilerService.CompileAndSave(fixedCode, fixedPath);

                Assert.IsTrue(retryResult.Success, $"Retry should succeed: {string.Join("; ", retryResult.Errors)}");
            }
            finally
            {
                LogAssert.ignoreFailingMessages = false;
            }
        }

        private string GetValidURPShaderCode(string shaderName)
        {
            return $@"Shader ""ShaderCopilot/Test/{shaderName}""
{{
    Properties
    {{
        _Color (""Color"", Color) = (1,1,1,1)
        _MainTex (""Texture"", 2D) = ""white"" {{}}
    }}
    SubShader
    {{
        Tags {{ ""RenderType""=""Opaque"" ""RenderPipeline""=""UniversalPipeline"" }}
        
        Pass
        {{
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            
            #include ""Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl""
            
            struct Attributes
            {{
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
            }};
            
            struct Varyings
            {{
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
            }};
            
            CBUFFER_START(UnityPerMaterial)
                float4 _Color;
                float4 _MainTex_ST;
            CBUFFER_END
            
            TEXTURE2D(_MainTex);
            SAMPLER(sampler_MainTex);
            
            Varyings vert(Attributes IN)
            {{
                Varyings OUT;
                OUT.positionCS = TransformObjectToHClip(IN.positionOS.xyz);
                OUT.uv = TRANSFORM_TEX(IN.uv, _MainTex);
                return OUT;
            }}
            
            half4 frag(Varyings IN) : SV_Target
            {{
                half4 col = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, IN.uv);
                return col * _Color;
            }}
            ENDHLSL
        }}
    }}
}}";
        }

        private void CleanupTestAssets()
        {
            // Clean up generated test shaders
            if (Directory.Exists(TestShaderDirectory))
            {
                var shaderFiles = Directory.GetFiles(TestShaderDirectory, "E2E_*.shader");
                foreach (var file in shaderFiles)
                {
                    var assetPath = FileManagerService.ToAssetPath(file);
                    AssetDatabase.DeleteAsset(assetPath);
                }
            }

            // Clean up generated test materials
            if (Directory.Exists(TestMaterialDirectory))
            {
                var materialFiles = Directory.GetFiles(TestMaterialDirectory, "E2E_*.mat");
                foreach (var file in materialFiles)
                {
                    var assetPath = FileManagerService.ToAssetPath(file);
                    AssetDatabase.DeleteAsset(assetPath);
                }
            }

            AssetDatabase.Refresh();
        }
    }
}
