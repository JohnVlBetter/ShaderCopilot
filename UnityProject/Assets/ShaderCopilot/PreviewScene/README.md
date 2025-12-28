# ShaderCopilot Preview Scene

This folder contains preview scene assets for the ShaderCopilot shader preview functionality.

## Contents

The preview scene is created programmatically by `PreviewSceneService.cs` and includes:

- **Preview Camera**: Renders the shader preview to a RenderTexture
- **Main Light**: Directional light for basic illumination
- **Preview Objects**: Primitive shapes (Sphere, Cube, Plane, Cylinder, Capsule)

## Usage

The preview scene is managed by `PreviewSceneService` and is not meant to be opened directly.
It's created as an EditorPreviewScene for isolated rendering.

## Customization

To add custom preview objects:

1. Create a prefab with the desired mesh
2. Place it in this folder
3. Reference it in `PreviewSceneService.CreatePreviewObject()` with `PreviewObjectType.Custom`

## Background Options

Background can be customized via:
- Solid color (default: dark gray #1A1A1A)
- HDRI environment (future feature)
