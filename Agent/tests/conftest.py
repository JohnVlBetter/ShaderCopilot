"""
Pytest configuration for ShaderCopilot tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_shader_code():
    """Provide sample shader code for testing."""
    return """Shader "Custom/TestShader"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _MainTex ("Texture", 2D) = "white" {}
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            
            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
            };
            
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
            };
            
            CBUFFER_START(UnityPerMaterial)
                float4 _Color;
                float4 _MainTex_ST;
            CBUFFER_END
            
            TEXTURE2D(_MainTex);
            SAMPLER(sampler_MainTex);
            
            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                OUT.positionCS = TransformObjectToHClip(IN.positionOS.xyz);
                OUT.uv = TRANSFORM_TEX(IN.uv, _MainTex);
                return OUT;
            }
            
            half4 frag(Varyings IN) : SV_Target
            {
                half4 col = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, IN.uv);
                return col * _Color;
            }
            ENDHLSL
        }
    }
}"""


@pytest.fixture
def sample_session_init_message():
    """Provide sample SESSION_INIT message."""
    return {
        "type": "SESSION_INIT",
        "payload": {
            "project_path": "/test/unity/project",
            "config": {
                "output_directory": "Shaders/Generated",
                "max_retry_count": 3,
            },
        },
    }


@pytest.fixture
def sample_user_message():
    """Provide sample USER_MESSAGE."""
    return {
        "type": "USER_MESSAGE",
        "session_id": "test-session-123",
        "payload": {
            "content": "Create a hologram shader with edge glow effect",
            "images": [],
        },
    }
