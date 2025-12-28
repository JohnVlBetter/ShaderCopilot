using System;
using ShaderCopilot.Editor.Services;
using UnityEngine;
using UnityEngine.UIElements;

namespace ShaderCopilot.Editor.Window
{
    /// <summary>
    /// Preview panel for displaying shader preview render.
    /// </summary>
    public class PreviewPanel : VisualElement, IDisposable
    {
        private IMGUIContainer _previewContainer;
        private Label _statusLabel;
        private PreviewSceneService _previewService;

        public PreviewSceneService PreviewService => _previewService;

        public PreviewPanel()
        {
            BuildUI();
        }

        private void BuildUI()
        {
            style.flexGrow = 1;
            style.flexDirection = FlexDirection.Column;
            style.backgroundColor = new Color(0.12f, 0.12f, 0.12f);

            // Preview area
            _previewContainer = new IMGUIContainer(OnPreviewGUI);
            _previewContainer.style.flexGrow = 1;
            Add(_previewContainer);

            // Status bar
            _statusLabel = new Label("Ready");
            _statusLabel.style.fontSize = 10;
            _statusLabel.style.paddingLeft = 8;
            _statusLabel.style.paddingTop = 4;
            _statusLabel.style.paddingBottom = 4;
            _statusLabel.style.color = new Color(0.6f, 0.6f, 0.6f);
            _statusLabel.style.borderTopWidth = 1;
            _statusLabel.style.borderTopColor = new Color(0.1f, 0.1f, 0.1f);
            Add(_statusLabel);
        }

        public void Initialize()
        {
            _previewService = new PreviewSceneService();
            _previewService.Initialize();
        }

        private void OnPreviewGUI()
        {
            if (_previewService == null) return;

            var rect = _previewContainer.contentRect;
            if (rect.width <= 0 || rect.height <= 0) return;

            _previewService.Render((int)rect.width, (int)rect.height);
            var texture = _previewService.GetRenderTexture();

            if (texture != null)
            {
                GUI.DrawTexture(rect, texture, ScaleMode.ScaleToFit);
            }

            // Handle mouse input for rotation
            var e = Event.current;
            if (e.type == EventType.MouseDrag && e.button == 0)
            {
                _previewService.Rotate(e.delta.x * 0.5f, e.delta.y * 0.5f);
                e.Use();
            }
        }

        public void ApplyShader(Shader shader)
        {
            if (_previewService != null && shader != null)
            {
                var material = new Material(shader);
                _previewService.SetMaterial(material);
                SetStatus($"Applied shader: {shader.name}");
            }
        }

        public void ApplyMaterial(Material material)
        {
            if (_previewService != null && material != null)
            {
                _previewService.SetMaterial(material);
                SetStatus($"Applied material: {material.name}");
            }
        }

        public void Clear()
        {
            _previewService?.SetMaterial(null);
            SetStatus("Preview cleared");
        }

        public void SetStatus(string status)
        {
            if (_statusLabel != null)
            {
                _statusLabel.text = status;
            }
        }

        public void Dispose()
        {
            _previewService?.Dispose();
            _previewService = null;
        }
    }
}
