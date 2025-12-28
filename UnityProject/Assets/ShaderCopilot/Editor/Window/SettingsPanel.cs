using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.UIElements;
using UnityEngine;
using UnityEngine.UIElements;

namespace ShaderCopilot.Editor.Window
{
    /// <summary>
    /// Settings panel for preview configuration.
    /// </summary>
    public class SettingsPanel : VisualElement
    {
        private DropdownField _previewObjectDropdown;
        private DropdownField _backgroundDropdown;
        private ColorField _customColorField;
        private Slider _rotationSpeedSlider;
        private Toggle _autoRotateToggle;

        private Services.PreviewSceneService _previewService;

        public event Action<string> OnPreviewObjectChanged;
        public event Action<Color> OnBackgroundColorChanged;

        public SettingsPanel()
        {
            BuildUI();
        }

        public void Initialize(Services.PreviewSceneService previewService)
        {
            _previewService = previewService;
            UpdateDropdownOptions();
        }

        private void BuildUI()
        {
            style.flexDirection = FlexDirection.Column;
            style.paddingLeft = 12;
            style.paddingRight = 12;
            style.paddingTop = 8;
            style.paddingBottom = 8;
            style.backgroundColor = new Color(0.18f, 0.18f, 0.18f);
            style.borderTopWidth = 1;
            style.borderTopColor = new Color(0.1f, 0.1f, 0.1f);

            // Header
            var header = new Label("Preview Settings");
            header.style.fontSize = 12;
            header.style.unityFontStyleAndWeight = FontStyle.Bold;
            header.style.marginBottom = 8;
            Add(header);

            // Preview Object Selection
            var previewObjectRow = new VisualElement();
            previewObjectRow.style.flexDirection = FlexDirection.Row;
            previewObjectRow.style.alignItems = Align.Center;
            previewObjectRow.style.marginBottom = 8;

            var previewObjectLabel = new Label("Object:");
            previewObjectLabel.style.width = 80;
            previewObjectRow.Add(previewObjectLabel);

            _previewObjectDropdown = new DropdownField();
            _previewObjectDropdown.style.flexGrow = 1;
            _previewObjectDropdown.RegisterValueChangedCallback(OnPreviewObjectDropdownChanged);
            previewObjectRow.Add(_previewObjectDropdown);

            Add(previewObjectRow);

            // Background Selection
            var backgroundRow = new VisualElement();
            backgroundRow.style.flexDirection = FlexDirection.Row;
            backgroundRow.style.alignItems = Align.Center;
            backgroundRow.style.marginBottom = 8;

            var backgroundLabel = new Label("Background:");
            backgroundLabel.style.width = 80;
            backgroundRow.Add(backgroundLabel);

            _backgroundDropdown = new DropdownField();
            _backgroundDropdown.choices = new List<string> { "Dark", "Light", "Black", "White", "Blue", "Gray", "Green", "Custom" };
            _backgroundDropdown.value = "Dark";
            _backgroundDropdown.style.flexGrow = 1;
            _backgroundDropdown.RegisterValueChangedCallback(OnBackgroundDropdownChanged);
            backgroundRow.Add(_backgroundDropdown);

            Add(backgroundRow);

            // Custom Color Field
            var customColorRow = new VisualElement();
            customColorRow.style.flexDirection = FlexDirection.Row;
            customColorRow.style.alignItems = Align.Center;
            customColorRow.style.marginBottom = 8;

            var customColorLabel = new Label("Custom Color:");
            customColorLabel.style.width = 80;
            customColorRow.Add(customColorLabel);

            _customColorField = new ColorField();
            _customColorField.value = new Color(0.1f, 0.1f, 0.1f, 1f);
            _customColorField.style.flexGrow = 1;
            _customColorField.RegisterValueChangedCallback(OnCustomColorChanged);
            customColorRow.Add(_customColorField);

            Add(customColorRow);

            // Auto Rotate Toggle
            var autoRotateRow = new VisualElement();
            autoRotateRow.style.flexDirection = FlexDirection.Row;
            autoRotateRow.style.alignItems = Align.Center;
            autoRotateRow.style.marginBottom = 8;

            var autoRotateLabel = new Label("Auto Rotate:");
            autoRotateLabel.style.width = 80;
            autoRotateRow.Add(autoRotateLabel);

            _autoRotateToggle = new Toggle();
            _autoRotateToggle.value = false;
            autoRotateRow.Add(_autoRotateToggle);

            Add(autoRotateRow);

            // Reset Button
            var buttonRow = new VisualElement();
            buttonRow.style.flexDirection = FlexDirection.Row;
            buttonRow.style.justifyContent = Justify.FlexEnd;
            buttonRow.style.marginTop = 4;

            var resetButton = new Button(OnResetClicked) { text = "Reset" };
            buttonRow.Add(resetButton);

            Add(buttonRow);
        }

        private void UpdateDropdownOptions()
        {
            if (_previewService != null)
            {
                var objects = _previewService.GetPreviewObjects();
                _previewObjectDropdown.choices = objects;
                _previewObjectDropdown.value = _previewService.CurrentPreviewObject;
            }
            else
            {
                _previewObjectDropdown.choices = new List<string> { "Sphere", "Cube", "Plane", "Cylinder", "Capsule" };
                _previewObjectDropdown.value = "Sphere";
            }
        }

        private void OnPreviewObjectDropdownChanged(ChangeEvent<string> evt)
        {
            if (_previewService != null)
            {
                _previewService.SwitchPreviewObject(evt.newValue);
            }
            OnPreviewObjectChanged?.Invoke(evt.newValue);
        }

        private void OnBackgroundDropdownChanged(ChangeEvent<string> evt)
        {
            if (evt.newValue == "Custom")
            {
                // Use custom color
                ApplyBackgroundColor(_customColorField.value);
            }
            else
            {
                // Use preset
                _previewService?.SetBackground(evt.newValue);

                // Get the color for the preset
                var backgrounds = _previewService?.GetAvailableBackgrounds();
                if (backgrounds != null && backgrounds.TryGetValue(evt.newValue, out var color))
                {
                    OnBackgroundColorChanged?.Invoke(color);
                }
            }
        }

        private void OnCustomColorChanged(ChangeEvent<Color> evt)
        {
            if (_backgroundDropdown.value == "Custom")
            {
                ApplyBackgroundColor(evt.newValue);
            }
        }

        private void ApplyBackgroundColor(Color color)
        {
            _previewService?.SetBackgroundColor(color);
            OnBackgroundColorChanged?.Invoke(color);
        }

        private void OnResetClicked()
        {
            // Reset to defaults
            _previewObjectDropdown.value = "Sphere";
            _backgroundDropdown.value = "Dark";
            _customColorField.value = new Color(0.1f, 0.1f, 0.1f, 1f);
            _autoRotateToggle.value = false;

            _previewService?.SwitchPreviewObject("Sphere");
            _previewService?.SetBackground("Dark");
            _previewService?.ResetRotation();
        }

        public void SetPreviewObject(string objectName)
        {
            _previewObjectDropdown.value = objectName;
        }

        public void SetBackground(string presetName)
        {
            _backgroundDropdown.value = presetName;
        }

        public void SetCustomBackgroundColor(Color color)
        {
            _customColorField.value = color;
            _backgroundDropdown.value = "Custom";
            ApplyBackgroundColor(color);
        }
    }
}
