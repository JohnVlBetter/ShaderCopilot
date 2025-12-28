# ShaderCopilot Agent

AI-powered URP Shader writing assistant - Python Backend

## Overview

ShaderCopilot Agent is the Python backend for the ShaderCopilot Unity Editor extension. It provides:

- **LangGraph-based Workflow**: Orchestrates shader generation through analysis → generation → validation steps
- **Multi-Model Routing**: Uses different LLM models optimized for routing, code generation, and vision tasks
- **WebSocket Communication**: Real-time bidirectional communication with Unity Editor
- **Image Analysis**: Vision-Language model support for analyzing reference images

## Requirements

- Python 3.11+
- UV (Python package manager) - recommended for dependency management
- LLM API access (OpenAI-compatible API)

## Quick Start

### Using UV (Recommended)

```bash
cd Agent

# Install dependencies
uv sync

# Copy environment configuration
cp .env.example .env
# Edit .env with your LLM API keys

# Run the server
uv run python -m shader_copilot.server.websocket_server
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment configuration
cp .env.example .env
# Edit .env with your LLM API keys

# Run the server
python -m shader_copilot.server.websocket_server
```

## Project Structure

```
Agent/
├── src/shader_copilot/
│   ├── server/          # WebSocket server
│   │   ├── websocket_server.py  # Main entry point
│   │   ├── message_handler.py   # Message routing
│   │   └── messages.py          # Protocol definitions
│   ├── router/          # Router Agent (intent routing)
│   │   └── router_agent.py
│   ├── graphs/          # LangGraph workflows
│   │   ├── base/        # Base state definitions
│   │   └── shader_gen/  # Shader generation workflow
│   │       ├── graph.py
│   │       ├── nodes.py
│   │       └── state.py
│   ├── tools/           # Tool implementations
│   │   ├── llm_tools.py    # LLM-based tools
│   │   └── unity_tools.py  # Unity integration
│   ├── models/          # Model management
│   │   ├── config.py       # Configuration
│   │   ├── entities.py     # Data models
│   │   └── model_manager.py
│   ├── session/         # Session persistence
│   │   └── session_manager.py
│   └── utils/           # Utilities
│       └── image_utils.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── pyproject.toml
```

## Configuration

Create a `.env` file with your settings:

```env
# Required: LLM API Configuration
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key-here

# Optional: Model Configuration
ROUTER_MODEL=qwen-turbo      # Fast model for intent routing
CODE_MODEL=qwen-max          # High-quality model for code generation
VL_MODEL=qwen-vl-plus        # Vision-Language model for image analysis

# Optional: Generation Settings
CODE_TEMPERATURE=0.2
ROUTER_TEMPERATURE=0.0
LLM_TIMEOUT=120
MAX_RETRY_COUNT=3

# Optional: Server Configuration
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8765

# Optional: Logging
LOG_LEVEL=INFO
LOG_FILE=shader_copilot.log
```

## WebSocket Protocol

### Client → Server Messages

| Type | Description |
|------|-------------|
| `SESSION_INIT` | Initialize a new session |
| `USER_MESSAGE` | Send user message with optional images |
| `TOOL_RESPONSE` | Response to tool call request |
| `CONFIRM_RESPONSE` | Response to confirmation dialog |
| `CANCEL_TASK` | Cancel current task |
| `ping` | Health check |

### Server → Client Messages

| Type | Description |
|------|-------------|
| `SESSION_READY` | Session initialized |
| `STREAM_CHUNK` | Streaming response |
| `TOOL_CALL_REQUEST` | Request Unity tool execution |
| `CONFIRM_REQUEST` | Request user confirmation |
| `SHADER_PREVIEW` | Preview update |
| `ERROR` | Error message |
| `pong` | Health check response |

## Testing

```bash
# Run all tests
uv run pytest

# Run unit tests
uv run pytest tests/unit/

# Run integration tests
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=shader_copilot --cov-report=html
```

## Troubleshooting

**Connection refused**
- Ensure the server is running before starting Unity
- Check that port 8765 is not in use

**LLM API errors**
- Verify your API key is correct
- Check that the API base URL is accessible

**Debug logging**
Set `LOG_LEVEL=DEBUG` in `.env` for verbose output.

## Architecture

```
Unity Editor ◄──WebSocket──► WebSocket Server
                                    │
                              Router Agent
                                    │
                            ShaderGen Graph
                            ┌───────┴───────┐
                       analyze_image   analyze_requirement
                                    │
                            generate_shader
                                    │
                            validate_shader
                                    │
                        Tool Calls to Unity
```
