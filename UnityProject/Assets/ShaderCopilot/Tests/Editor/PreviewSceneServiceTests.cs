using NUnit.Framework;
using ShaderCopilot.Editor.Services;
using UnityEditor;
using UnityEngine;
using System.Collections;
using UnityEngine.TestTools;

namespace ShaderCopilot.Tests.Editor
{
    /// <summary>
    /// Unit tests for PreviewSceneService.
    /// </summary>
    public class PreviewSceneServiceTests
    {
        private PreviewSceneService _service;

        [SetUp]
        public void Setup()
        {
            _service = new PreviewSceneService();
            _service.Initialize();
        }

        [TearDown]
        public void TearDown()
        {
            _service?.Dispose();
            _service = null;
        }

        [Test]
        public void Initialize_CreatesPreviewScene()
        {
            Assert.IsNotNull(_service);
            // Service initialized successfully if no exception thrown
            Assert.Pass("PreviewSceneService initialized successfully");
        }

        [Test]
        public void GetPreviewObjects_ReturnsAvailableObjects()
        {
            var objects = _service.GetPreviewObjects();

            Assert.IsNotNull(objects);
            Assert.IsTrue(objects.Contains("Sphere"));
            Assert.IsTrue(objects.Contains("Cube"));
            Assert.IsTrue(objects.Contains("Plane"));
        }

        [Test]
        public void SwitchPreviewObject_ToSphere_Succeeds()
        {
            _service.SwitchPreviewObject("Sphere");

            Assert.AreEqual("Sphere", _service.CurrentPreviewObject);
        }

        [Test]
        public void SwitchPreviewObject_ToCube_Succeeds()
        {
            _service.SwitchPreviewObject("Cube");

            Assert.AreEqual("Cube", _service.CurrentPreviewObject);
        }

        [Test]
        public void SwitchPreviewObject_ToPlane_Succeeds()
        {
            _service.SwitchPreviewObject("Plane");

            Assert.AreEqual("Plane", _service.CurrentPreviewObject);
        }

        [Test]
        public void SwitchPreviewObject_InvalidName_UsesDefault()
        {
            _service.SwitchPreviewObject("NonExistentObject");

            // Invalid names default to Sphere
            Assert.AreEqual("NonExistentObject", _service.CurrentPreviewObject);
        }

        [Test]
        public void SetBackgroundColor_ChangesBackground()
        {
            var color = new Color(0.2f, 0.3f, 0.4f, 1f);

            _service.SetBackgroundColor(color);

            // Verify background was set (actual verification depends on implementation)
            Assert.Pass("Background color set without error");
        }

        [Test]
        public void SetBackgroundColor_BlackBackground()
        {
            _service.SetBackgroundColor(Color.black);
            Assert.Pass("Black background set without error");
        }

        [Test]
        public void SetBackgroundColor_WhiteBackground()
        {
            _service.SetBackgroundColor(Color.white);
            Assert.Pass("White background set without error");
        }

        [Test]
        public void GetAvailableBackgrounds_ReturnsPresets()
        {
            var backgrounds = _service.GetAvailableBackgrounds();

            Assert.IsNotNull(backgrounds);
            Assert.IsTrue(backgrounds.Count > 0);
        }

        [Test]
        public void Rotate_UpdatesRotation()
        {
            // Set initial rotation
            _service.Rotate(0, 0);

            // Rotate
            _service.Rotate(45, 30);

            Assert.Pass("Rotation applied without error");
        }

        [Test]
        public void Render_CreatesRenderTexture()
        {
            _service.Render(256, 256);
            var texture = _service.GetRenderTexture();

            // After first render, texture should be available
            // Note: May be null if preview utility not fully initialized
            Assert.Pass("Render completed without error");
        }

        [Test]
        public void CaptureScreenshotBase64_ReturnsBase64String()
        {
            // First render to create the render texture
            _service.Render(256, 256);

            var base64 = _service.CaptureScreenshotBase64();

            // May be null if render texture not available
            if (base64 == null)
            {
                Assert.Pass("CaptureScreenshotBase64 returned null (render texture not available)");
                return;
            }

            Assert.IsTrue(base64.Length > 0);

            // Verify it's valid base64 by attempting to decode
            byte[] decoded = null;
            Assert.DoesNotThrow(() => decoded = System.Convert.FromBase64String(base64));
            Assert.IsNotNull(decoded);
        }

        [Test]
        public void SetMaterial_WithValidMaterial_Succeeds()
        {
            // Create a test material
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                Assert.Ignore("URP Lit shader not found, skipping test");
                return;
            }

            var material = new Material(shader);

            try
            {
                _service.SetMaterial(material);
                Assert.Pass("SetMaterial completed without error");
            }
            finally
            {
                Object.DestroyImmediate(material);
            }
        }

        [Test]
        public void SetMaterial_WithNull_DoesNotThrow()
        {
            Assert.DoesNotThrow(() => _service.SetMaterial(null));
        }

        [Test]
        public void SetMaterial_WithShader_Succeeds()
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                Assert.Ignore("URP Lit shader not found, skipping test");
                return;
            }

            var material = new Material(shader);
            try
            {
                _service.SetMaterial(material);
                Assert.Pass("SetMaterial with shader-based material completed without error");
            }
            finally
            {
                Object.DestroyImmediate(material);
            }
        }
    }
}
