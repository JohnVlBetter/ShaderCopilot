"""
Unity tool wrappers for interacting with Unity Editor.

These tools send requests to Unity via WebSocket and wait for responses.
"""

from typing import Any, Callable, Optional
from uuid import uuid4

from shader_copilot.graphs.shader_gen.state import CompileResult


class UnityToolError(Exception):
    """Error from Unity tool execution."""

    pass


class UnityTools:
    """
    Unity tool wrappers for shader workflow.

    These tools communicate with Unity Editor via WebSocket.
    """

    def __init__(
        self,
        send_tool_call: Callable[[str, str, dict], None],
        wait_for_response: Callable[[str], dict],
    ):
        """
        Initialize Unity tools.

        Args:
            send_tool_call: Function to send tool call to Unity
            wait_for_response: Function to wait for tool response
        """
        self._send_tool_call = send_tool_call
        self._wait_for_response = wait_for_response

    async def compile_shader(
        self,
        code: str,
        output_path: Optional[str] = None,
        shader_name: Optional[str] = None,
    ) -> CompileResult:
        """
        Compile shader code in Unity.

        Args:
            code: HLSL shader code
            output_path: Optional output path (Unity will generate if not provided)
            shader_name: Optional shader name for path generation

        Returns:
            CompileResult with success status and errors
        """
        tool_call_id = str(uuid4())

        arguments = {
            "code": code,
        }

        if output_path:
            arguments["output_path"] = output_path
        if shader_name:
            arguments["shader_name"] = shader_name

        # Send tool call
        await self._send_tool_call(tool_call_id, "compile_shader", arguments)

        # Wait for response
        response = await self._wait_for_response(tool_call_id)

        return CompileResult(
            success=response.get("success", False),
            errors=response.get("errors", []),
            warnings=response.get("warnings", []),
            shader_path=response.get("shader_path"),
        )

    async def create_material(
        self,
        shader_path: str,
        output_path: Optional[str] = None,
        properties: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create a material using the specified shader.

        Args:
            shader_path: Path to the compiled shader
            output_path: Optional output path for the material
            properties: Optional material property values

        Returns:
            Result with material path
        """
        tool_call_id = str(uuid4())

        arguments = {
            "shader_path": shader_path,
        }

        if output_path:
            arguments["output_path"] = output_path
        if properties:
            arguments["properties"] = properties

        await self._send_tool_call(tool_call_id, "create_material", arguments)
        response = await self._wait_for_response(tool_call_id)

        if not response.get("success"):
            raise UnityToolError(response.get("error", "Failed to create material"))

        return response

    async def apply_to_preview(
        self,
        material_path: str,
    ) -> dict[str, Any]:
        """
        Apply material to preview object.

        Args:
            material_path: Path to the material asset

        Returns:
            Result with success status
        """
        tool_call_id = str(uuid4())

        arguments = {
            "material_path": material_path,
        }

        await self._send_tool_call(tool_call_id, "apply_to_preview", arguments)
        return await self._wait_for_response(tool_call_id)

    async def capture_screenshot(
        self,
        output_path: Optional[str] = None,
        width: int = 512,
        height: int = 512,
    ) -> dict[str, Any]:
        """
        Capture a screenshot of the preview.

        Args:
            output_path: Optional path to save the screenshot
            width: Screenshot width
            height: Screenshot height

        Returns:
            Result with screenshot data or path
        """
        tool_call_id = str(uuid4())

        arguments = {
            "width": width,
            "height": height,
        }

        if output_path:
            arguments["output_path"] = output_path

        await self._send_tool_call(tool_call_id, "capture_screenshot", arguments)
        return await self._wait_for_response(tool_call_id)

    async def save_shader(
        self,
        shader_path: str,
        new_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Save/move shader to a permanent location.

        Args:
            shader_path: Current shader path
            new_path: New path to save to

        Returns:
            Result with final path
        """
        tool_call_id = str(uuid4())

        arguments = {
            "shader_path": shader_path,
        }

        if new_path:
            arguments["new_path"] = new_path

        await self._send_tool_call(tool_call_id, "save_shader", arguments)
        return await self._wait_for_response(tool_call_id)

    async def save_material(
        self,
        material_path: str,
        new_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Save/move material to a permanent location.

        Args:
            material_path: Current material path
            new_path: New path to save to

        Returns:
            Result with final path
        """
        tool_call_id = str(uuid4())

        arguments = {
            "material_path": material_path,
        }

        if new_path:
            arguments["new_path"] = new_path

        await self._send_tool_call(tool_call_id, "save_material", arguments)
        return await self._wait_for_response(tool_call_id)

    async def list_preview_objects(self) -> list[str]:
        """
        List available preview objects.

        Returns:
            List of available object names
        """
        tool_call_id = str(uuid4())

        await self._send_tool_call(tool_call_id, "list_preview_objects", {})
        response = await self._wait_for_response(tool_call_id)

        return response.get("objects", [])

    async def switch_preview_object(self, object_name: str) -> dict[str, Any]:
        """
        Switch the preview object.

        Args:
            object_name: Name of the object to switch to

        Returns:
            Result with success status
        """
        tool_call_id = str(uuid4())

        arguments = {
            "object_name": object_name,
        }

        await self._send_tool_call(tool_call_id, "switch_preview_object", arguments)
        return await self._wait_for_response(tool_call_id)

    async def set_background(
        self,
        color: Optional[str] = None,
        hdri_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Set preview background.

        Args:
            color: Background color as hex string (#RRGGBB)
            hdri_path: Path to HDRI texture

        Returns:
            Result with success status
        """
        tool_call_id = str(uuid4())

        arguments = {}

        if color:
            arguments["color"] = color
        if hdri_path:
            arguments["hdri_path"] = hdri_path

        await self._send_tool_call(tool_call_id, "set_background", arguments)
        return await self._wait_for_response(tool_call_id)


# Tool definitions for LangGraph
UNITY_TOOL_DEFINITIONS = [
    {
        "name": "compile_shader",
        "description": "Compile shader code in Unity Editor",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "HLSL shader code"},
                "output_path": {
                    "type": "string",
                    "description": "Output path for the shader file",
                },
                "shader_name": {"type": "string", "description": "Name for the shader"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "create_material",
        "description": "Create a material using a compiled shader",
        "parameters": {
            "type": "object",
            "properties": {
                "shader_path": {
                    "type": "string",
                    "description": "Path to the compiled shader",
                },
                "output_path": {
                    "type": "string",
                    "description": "Output path for the material",
                },
            },
            "required": ["shader_path"],
        },
    },
    {
        "name": "apply_to_preview",
        "description": "Apply material to the preview object",
        "parameters": {
            "type": "object",
            "properties": {
                "material_path": {
                    "type": "string",
                    "description": "Path to the material",
                },
            },
            "required": ["material_path"],
        },
    },
    {
        "name": "capture_screenshot",
        "description": "Capture a screenshot of the shader preview",
        "parameters": {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "description": "Screenshot width"},
                "height": {"type": "integer", "description": "Screenshot height"},
            },
        },
    },
    {
        "name": "save_shader",
        "description": "Save the shader to a permanent location",
        "parameters": {
            "type": "object",
            "properties": {
                "shader_path": {"type": "string", "description": "Current shader path"},
                "new_path": {"type": "string", "description": "New path to save to"},
            },
            "required": ["shader_path"],
        },
    },
    {
        "name": "save_material",
        "description": "Save the material to a permanent location",
        "parameters": {
            "type": "object",
            "properties": {
                "material_path": {
                    "type": "string",
                    "description": "Current material path",
                },
                "new_path": {"type": "string", "description": "New path to save to"},
            },
            "required": ["material_path"],
        },
    },
]
