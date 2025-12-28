using System;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace ShaderCopilot.Editor.Services
{
    /// <summary>
    /// Service for creating and managing materials.
    /// </summary>
    public static class MaterialManagerService
    {
        /// <summary>
        /// Create a new material using the specified shader.
        /// </summary>
        public static Material CreateMaterial(Shader shader, string outputPath = null)
        {
            if (shader == null)
            {
                Debug.LogError("[ShaderCopilot] Cannot create material: shader is null");
                return null;
            }

            try
            {
                var material = new Material(shader);

                if (!string.IsNullOrEmpty(outputPath))
                {
                    SaveMaterial(material, outputPath);
                }

                Debug.Log($"[ShaderCopilot] Material created with shader: {shader.name}");
                return material;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to create material: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Create a material from a shader at the given path.
        /// </summary>
        public static Material CreateMaterialFromShaderPath(string shaderPath, string materialOutputPath = null)
        {
            var shader = AssetDatabase.LoadAssetAtPath<Shader>(shaderPath);
            if (shader == null)
            {
                Debug.LogError($"[ShaderCopilot] Shader not found at path: {shaderPath}");
                return null;
            }

            return CreateMaterial(shader, materialOutputPath);
        }

        /// <summary>
        /// Save a material to the specified path.
        /// </summary>
        public static bool SaveMaterial(Material material, string outputPath)
        {
            if (material == null)
            {
                Debug.LogError("[ShaderCopilot] Cannot save null material");
                return false;
            }

            try
            {
                // Ensure directory exists
                var directory = Path.GetDirectoryName(outputPath);
                if (!Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                // Check if asset already exists
                var existingMaterial = AssetDatabase.LoadAssetAtPath<Material>(outputPath);
                if (existingMaterial != null)
                {
                    // Update existing material
                    EditorUtility.CopySerialized(material, existingMaterial);
                    EditorUtility.SetDirty(existingMaterial);
                    AssetDatabase.SaveAssets();
                    Debug.Log($"[ShaderCopilot] Updated material at: {outputPath}");
                    return true;
                }

                // Create new asset
                AssetDatabase.CreateAsset(material, outputPath);
                AssetDatabase.SaveAssets();
                Debug.Log($"[ShaderCopilot] Material saved to: {outputPath}");
                return true;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to save material: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Get the output path for a material based on shader name.
        /// </summary>
        public static string GetMaterialPath(string name, string outputDirectory)
        {
            if (!Directory.Exists(outputDirectory))
            {
                Directory.CreateDirectory(outputDirectory);
            }

            var safeName = Regex.Replace(name, @"[^a-zA-Z0-9_]", "_");
            return Path.Combine(outputDirectory, $"{safeName}.mat")
                .Replace("\\", "/");
        }

        /// <summary>
        /// Get a unique path for the material to avoid overwriting.
        /// </summary>
        public static string GetUniqueMaterialPath(string basePath)
        {
            if (!File.Exists(basePath) && AssetDatabase.LoadAssetAtPath<Material>(basePath) == null)
            {
                return basePath;
            }

            var directory = Path.GetDirectoryName(basePath).Replace("\\", "/");
            var filename = Path.GetFileNameWithoutExtension(basePath);
            var extension = Path.GetExtension(basePath);

            int counter = 1;
            string newPath;
            do
            {
                newPath = $"{directory}/{filename}_{counter}{extension}";
                counter++;
            } while ((File.Exists(newPath) || AssetDatabase.LoadAssetAtPath<Material>(newPath) != null) && counter < 100);

            return newPath;
        }

        /// <summary>
        /// Set material properties from a dictionary.
        /// </summary>
        public static void SetMaterialProperties(Material material, System.Collections.Generic.Dictionary<string, object> properties)
        {
            if (material == null || properties == null)
                return;

            foreach (var kvp in properties)
            {
                try
                {
                    SetMaterialProperty(material, kvp.Key, kvp.Value);
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"[ShaderCopilot] Failed to set property '{kvp.Key}': {ex.Message}");
                }
            }
        }

        /// <summary>
        /// Set a single material property.
        /// </summary>
        public static void SetMaterialProperty(Material material, string propertyName, object value)
        {
            if (!material.HasProperty(propertyName))
            {
                Debug.LogWarning($"[ShaderCopilot] Material does not have property: {propertyName}");
                return;
            }

            switch (value)
            {
                case float f:
                    material.SetFloat(propertyName, f);
                    break;
                case int i:
                    material.SetInt(propertyName, i);
                    break;
                case Color c:
                    material.SetColor(propertyName, c);
                    break;
                case Vector4 v4:
                    material.SetVector(propertyName, v4);
                    break;
                case Vector3 v3:
                    material.SetVector(propertyName, new Vector4(v3.x, v3.y, v3.z, 0));
                    break;
                case Vector2 v2:
                    material.SetVector(propertyName, new Vector4(v2.x, v2.y, 0, 0));
                    break;
                case Texture t:
                    material.SetTexture(propertyName, t);
                    break;
                case string s when s.StartsWith("#"):
                    if (ColorUtility.TryParseHtmlString(s, out var color))
                    {
                        material.SetColor(propertyName, color);
                    }
                    break;
                default:
                    Debug.LogWarning($"[ShaderCopilot] Unsupported property type for '{propertyName}': {value?.GetType().Name}");
                    break;
            }
        }

        /// <summary>
        /// Apply material to a game object.
        /// </summary>
        public static void ApplyMaterialToObject(Material material, GameObject gameObject)
        {
            if (material == null || gameObject == null)
                return;

            var renderer = gameObject.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.sharedMaterial = material;
                Debug.Log($"[ShaderCopilot] Applied material to: {gameObject.name}");
            }
            else
            {
                Debug.LogWarning($"[ShaderCopilot] No renderer found on: {gameObject.name}");
            }
        }

        /// <summary>
        /// Create a preview sphere with the material.
        /// </summary>
        public static GameObject CreatePreviewSphere(Material material, Vector3 position = default)
        {
            var sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            sphere.name = $"Preview_{material.name}";
            sphere.transform.position = position;

            var renderer = sphere.GetComponent<Renderer>();
            renderer.sharedMaterial = material;

            // Register for undo
            Undo.RegisterCreatedObjectUndo(sphere, "Create Shader Preview");

            Selection.activeGameObject = sphere;
            SceneView.lastActiveSceneView?.FrameSelected();

            Debug.Log($"[ShaderCopilot] Created preview sphere: {sphere.name}");
            return sphere;
        }
    }
}
