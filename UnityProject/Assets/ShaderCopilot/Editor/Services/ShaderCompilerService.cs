using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace ShaderCopilot.Editor.Services
{
    /// <summary>
    /// Result of shader compilation.
    /// </summary>
    public class ShaderCompileResult
    {
        public bool Success;
        public Shader Shader;
        public string ShaderPath;
        public List<string> Errors = new List<string>();
        public List<string> Warnings = new List<string>();
    }

    /// <summary>
    /// Service for compiling and validating shaders.
    /// </summary>
    public static class ShaderCompilerService
    {
        /// <summary>
        /// Get full output path for a shader.
        /// </summary>
        public static string GetOutputPath(string shaderName, string outputDirectory)
        {
            if (!Directory.Exists(outputDirectory))
            {
                Directory.CreateDirectory(outputDirectory);
            }

            var safeName = Regex.Replace(shaderName, @"[^a-zA-Z0-9_]", "_");
            return Path.Combine(outputDirectory, $"{safeName}.shader");
        }

        /// <summary>
        /// Compile shader from source code and save to file.
        /// </summary>
        public static ShaderCompileResult CompileAndSave(string shaderCode, string outputPath)
        {
            var result = new ShaderCompileResult { ShaderPath = outputPath };

            try
            {
                // Ensure directory exists
                var directory = Path.GetDirectoryName(outputPath);
                if (!Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                // Write shader file
                File.WriteAllText(outputPath, shaderCode);
                AssetDatabase.Refresh();

                // Load and check for errors
                var shader = AssetDatabase.LoadAssetAtPath<Shader>(outputPath);

                if (shader == null)
                {
                    result.Success = false;
                    result.Errors.Add("Failed to load shader asset");
                    return result;
                }

                // Check for compilation errors
                var errorCount = ShaderUtil.GetShaderMessageCount(shader);

                if (errorCount > 0)
                {
                    for (int i = 0; i < errorCount; i++)
                    {
                        var messages = ShaderUtil.GetShaderMessages(shader);
                        if (i < messages.Length)
                        {
                            var msg = messages[i];
                            var errorText = $"Line {msg.line}: {msg.message}";

                            if (msg.severity == UnityEditor.Rendering.ShaderCompilerMessageSeverity.Error)
                            {
                                result.Errors.Add(errorText);
                            }
                            else
                            {
                                result.Warnings.Add(errorText);
                            }
                        }
                    }
                }

                result.Success = result.Errors.Count == 0;
                result.Shader = shader;
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.Errors.Add(ex.Message);
            }

            return result;
        }

        /// <summary>
        /// Extract shader name from code.
        /// </summary>
        public static string ExtractShaderName(string shaderCode)
        {
            var match = Regex.Match(shaderCode, @"Shader\s+""([^""]+)""");
            return match.Success ? match.Groups[1].Value : null;
        }
    }
}
