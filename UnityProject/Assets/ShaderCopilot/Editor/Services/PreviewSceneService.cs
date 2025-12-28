using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace ShaderCopilot.Editor.Services
{
    /// <summary>
    /// Manages the preview scene for shader visualization.
    /// </summary>
    public class PreviewSceneService : IDisposable
    {
        private PreviewRenderUtility _previewUtility;
        private GameObject _previewObject;
        private Material _currentMaterial;
        private float _rotationX;
        private float _rotationY;
        private RenderTexture _renderTexture;

        public string CurrentPreviewObject { get; private set; } = "Sphere";

        /// <summary>
        /// Initialize the preview scene.
        /// </summary>
        public void Initialize()
        {
            _previewUtility = new PreviewRenderUtility();
            _previewUtility.cameraFieldOfView = 30f;
            _previewUtility.camera.nearClipPlane = 0.1f;
            _previewUtility.camera.farClipPlane = 100f;
            _previewUtility.camera.transform.position = new Vector3(0, 0, -5);
            _previewUtility.camera.transform.LookAt(Vector3.zero);

            CreatePreviewObject("Sphere");
        }

        private void CreatePreviewObject(string objectType)
        {
            if (_previewObject != null)
            {
                UnityEngine.Object.DestroyImmediate(_previewObject);
            }

            CurrentPreviewObject = objectType;

            switch (objectType)
            {
                case "Sphere":
                    _previewObject = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                    break;
                case "Cube":
                    _previewObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    break;
                case "Plane":
                    _previewObject = GameObject.CreatePrimitive(PrimitiveType.Plane);
                    _previewObject.transform.localScale = Vector3.one * 0.3f;
                    break;
                case "Cylinder":
                    _previewObject = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                    break;
                case "Capsule":
                    _previewObject = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                    break;
                default:
                    _previewObject = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                    break;
            }

            _previewObject.hideFlags = HideFlags.HideAndDontSave;

            if (_currentMaterial != null)
            {
                _previewObject.GetComponent<Renderer>().sharedMaterial = _currentMaterial;
            }
        }

        /// <summary>
        /// Switch preview object by name.
        /// </summary>
        /// <param name="objectType">Name of the object (Sphere, Cube, Plane, etc.)</param>
        public void SwitchPreviewObject(string objectType)
        {
            CreatePreviewObject(objectType);
        }

        /// <summary>
        /// Get list of available preview object types.
        /// </summary>
        public List<string> GetPreviewObjects()
        {
            return new List<string> { "Sphere", "Cube", "Plane", "Cylinder", "Capsule" };
        }

        /// <summary>
        /// Get available background presets.
        /// </summary>
        public Dictionary<string, Color> GetAvailableBackgrounds()
        {
            return new Dictionary<string, Color>
            {
                { "Dark", new Color(0.1f, 0.1f, 0.1f) },
                { "Light", new Color(0.8f, 0.8f, 0.8f) },
                { "Black", Color.black },
                { "White", Color.white },
                { "Blue", new Color(0.1f, 0.2f, 0.4f) },
                { "Gray", new Color(0.3f, 0.3f, 0.3f) },
                { "Green", new Color(0.1f, 0.3f, 0.1f) }
            };
        }

        /// <summary>
        /// Set background by preset name.
        /// </summary>
        public void SetBackground(string presetName)
        {
            var backgrounds = GetAvailableBackgrounds();
            if (backgrounds.TryGetValue(presetName, out var color))
            {
                SetBackgroundColor(color);
            }
        }

        /// <summary>
        /// Set background color.
        /// </summary>
        public void SetBackgroundColor(Color color)
        {
            if (_previewUtility != null)
            {
                _previewUtility.camera.backgroundColor = color;
            }
        }

        /// <summary>
        /// Apply material to the preview object.
        /// </summary>
        public void SetMaterial(Material material)
        {
            _currentMaterial = material;
            if (_previewObject != null)
            {
                _previewObject.GetComponent<Renderer>().sharedMaterial = material;
            }
        }

        /// <summary>
        /// Rotate the preview object.
        /// </summary>
        public void Rotate(float deltaX, float deltaY)
        {
            _rotationY += deltaX;
            _rotationX += deltaY;
            _rotationX = Mathf.Clamp(_rotationX, -90f, 90f);
        }

        /// <summary>
        /// Reset preview object rotation.
        /// </summary>
        public void ResetRotation()
        {
            _rotationX = 0;
            _rotationY = 0;
        }

        /// <summary>
        /// Render the preview scene.
        /// </summary>
        public void Render(int width, int height)
        {
            if (_previewUtility == null || _previewObject == null) return;
            if (width <= 0 || height <= 0) return;

            _previewUtility.BeginPreview(new Rect(0, 0, width, height), GUIStyle.none);

            _previewObject.transform.rotation = Quaternion.Euler(_rotationX, _rotationY, 0);

            _previewUtility.AddSingleGO(_previewObject);
            _previewUtility.camera.Render();

            _renderTexture = _previewUtility.EndPreview() as RenderTexture;
        }

        /// <summary>
        /// Get the render texture.
        /// </summary>
        public Texture GetRenderTexture()
        {
            return _renderTexture;
        }

        /// <summary>
        /// Capture screenshot as Base64 string.
        /// </summary>
        public string CaptureScreenshotBase64()
        {
            if (_renderTexture == null) return null;

            var oldRT = RenderTexture.active;
            RenderTexture.active = _renderTexture;

            var tex = new Texture2D(_renderTexture.width, _renderTexture.height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, _renderTexture.width, _renderTexture.height), 0, 0);
            tex.Apply();

            RenderTexture.active = oldRT;

            var bytes = tex.EncodeToPNG();
            UnityEngine.Object.DestroyImmediate(tex);

            return Convert.ToBase64String(bytes);
        }

        public void Dispose()
        {
            if (_previewObject != null)
            {
                UnityEngine.Object.DestroyImmediate(_previewObject);
                _previewObject = null;
            }

            _previewUtility?.Cleanup();
            _previewUtility = null;
        }
    }
}
