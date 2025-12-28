using System;
using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEngine;

namespace ShaderCopilot.Editor.Communication
{
    /// <summary>
    /// Message types for client → server communication.
    /// </summary>
    public static class MessageType
    {
        public const string UserMessage = "user_message";
        public const string ToolResponse = "tool_response";
        public const string SessionInit = "session_init";
        public const string UserConfirm = "user_confirm";
        public const string CancelTask = "cancel_task";
        public const string Ping = "ping";
    }

    /// <summary>
    /// Message types for server → client communication.
    /// </summary>
    public static class ServerMessageType
    {
        public const string Thinking = "thinking";
        public const string ToolCall = "tool_call";
        public const string ToolResult = "tool_result";
        public const string StreamText = "stream_text";
        public const string Progress = "progress";
        public const string RequireConfirm = "require_confirm";
        public const string Complete = "complete";
        public const string Error = "error";
        public const string Pong = "pong";
        public const string SessionReady = "session_ready";
    }

    /// <summary>
    /// Base message structure.
    /// </summary>
    [Serializable]
    public class BaseMessage
    {
        public string id;
        public string type;
        public string timestamp;
        public JObject payload;

        public static BaseMessage Create(string messageType, object payloadObj = null)
        {
            return new BaseMessage
            {
                id = Guid.NewGuid().ToString(),
                type = messageType,
                timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ"),
                payload = payloadObj != null ? JObject.FromObject(payloadObj) : new JObject()
            };
        }

        public string ToJson()
        {
            return JsonConvert.SerializeObject(this, Formatting.None, new JsonSerializerSettings
            {
                NullValueHandling = NullValueHandling.Ignore
            });
        }

        public static BaseMessage FromJson(string json)
        {
            return JsonConvert.DeserializeObject<BaseMessage>(json);
        }

        public T GetPayload<T>() where T : class
        {
            return payload?.ToObject<T>();
        }
    }

    /// <summary>
    /// Handles parsing and creating WebSocket messages.
    /// </summary>
    public class MessageHandler
    {
        private readonly Dictionary<string, Action<BaseMessage>> _handlers;
        private readonly Dictionary<string, Action<JObject>> _toolCallbacks;
        private readonly Dictionary<string, Action<bool, string>> _confirmCallbacks;

        public event Action<string> OnStreamText;
        public event Action<string, string, float?> OnProgress;
        public event Action<string> OnThinking;
        public event Action<string, string> OnError;
        public event Action<string, List<string>> OnComplete;
        public event Action<string, string, JObject> OnToolCall;
        public event Action<string, string, string, string> OnRequireConfirm;
        public event Action<string, bool> OnSessionReady;
        public event Action<string> OnResponseReceived;
        public event Action<string, bool> OnStreamChunkReceived;
        public event Action<string, string, string> OnToolCallReceived;
        public event Action<string, string, string> OnConfirmRequestReceived;
        public event Action<string, string, float?> OnProgressReceived;
        public event Action<string, string> OnErrorReceived;

        public MessageHandler()
        {
            _handlers = new Dictionary<string, Action<BaseMessage>>();
            _toolCallbacks = new Dictionary<string, Action<JObject>>();
            _confirmCallbacks = new Dictionary<string, Action<bool, string>>();
            RegisterDefaultHandlers();
        }

        private void RegisterDefaultHandlers()
        {
            _handlers[ServerMessageType.StreamText] = HandleStreamText;
            _handlers[ServerMessageType.Progress] = HandleProgress;
            _handlers[ServerMessageType.Thinking] = HandleThinking;
            _handlers[ServerMessageType.Error] = HandleError;
            _handlers[ServerMessageType.Complete] = HandleComplete;
            _handlers[ServerMessageType.ToolCall] = HandleToolCall;
            _handlers[ServerMessageType.RequireConfirm] = HandleRequireConfirm;
            _handlers[ServerMessageType.SessionReady] = HandleSessionReady;
            _handlers[ServerMessageType.Pong] = _ => { }; // Ignore pong
        }

        /// <summary>
        /// Process an incoming message.
        /// </summary>
        public void HandleMessage(string json)
        {
            try
            {
                var message = JObject.Parse(json);
                var type = message["type"]?.ToString();

                switch (type)
                {
                    case "RESPONSE":
                        var content = message["payload"]?["content"]?.ToString();
                        OnResponseReceived?.Invoke(content ?? "");
                        break;

                    case "STREAM_CHUNK":
                        var chunk = message["payload"]?["content"]?.ToString();
                        var isFinal = message["payload"]?["is_final"]?.Value<bool>() ?? false;
                        OnStreamChunkReceived?.Invoke(chunk ?? "", isFinal);
                        break;

                    case "TOOL_CALL":
                        var toolCallId = message["payload"]?["tool_call_id"]?.ToString();
                        var toolName = message["payload"]?["tool_name"]?.ToString();
                        var arguments = message["payload"]?["arguments"]?.ToString();
                        OnToolCallReceived?.Invoke(toolCallId ?? "", toolName ?? "", arguments ?? "{}");
                        break;

                    case "CONFIRM_REQUEST":
                        var confirmId = message["payload"]?["confirm_id"]?.ToString();
                        var action = message["payload"]?["action"]?.ToString();
                        var details = message["payload"]?["details"]?.ToString();
                        OnConfirmRequestReceived?.Invoke(confirmId ?? "", action ?? "", details ?? "");
                        break;

                    case "PROGRESS":
                        var stage = message["payload"]?["stage"]?.ToString();
                        var progressMessage = message["payload"]?["message"]?.ToString();
                        var progress = message["payload"]?["progress"]?.Value<float?>();
                        OnProgressReceived?.Invoke(stage ?? "", progressMessage ?? "", progress);
                        break;

                    case "ERROR":
                        var errorCode = message["payload"]?["code"]?.ToString();
                        var errorMessage = message["payload"]?["message"]?.ToString();
                        OnErrorReceived?.Invoke(errorCode ?? "UNKNOWN", errorMessage ?? "Unknown error");
                        break;

                    default:
                        Debug.LogWarning($"[MessageHandler] Unknown message type: {type}");
                        break;
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[MessageHandler] Failed to parse message: {ex.Message}");
            }
        }

        #region Message Handlers

        private void HandleStreamText(BaseMessage message)
        {
            var content = message.payload?["content"]?.ToString() ?? "";
            OnStreamText?.Invoke(content);
        }

        private void HandleProgress(BaseMessage message)
        {
            var stage = message.payload?["stage"]?.ToString() ?? "";
            var msg = message.payload?["message"]?.ToString() ?? "";
            float? progress = message.payload?["progress"]?.ToObject<float?>();
            OnProgress?.Invoke(stage, msg, progress);
        }

        private void HandleThinking(BaseMessage message)
        {
            var msg = message.payload?["message"]?.ToString() ?? "Processing...";
            OnThinking?.Invoke(msg);
        }

        private void HandleError(BaseMessage message)
        {
            var code = message.payload?["code"]?.ToString() ?? "UNKNOWN";
            var msg = message.payload?["message"]?.ToString() ?? "Unknown error";
            OnError?.Invoke(code, msg);
            OnErrorReceived?.Invoke(code, msg);
        }

        private void HandleComplete(BaseMessage message)
        {
            var msg = message.payload?["message"]?.ToString() ?? "Task completed";
            var artifacts = message.payload?["artifacts"]?.ToObject<List<string>>() ?? new List<string>();
            OnComplete?.Invoke(msg, artifacts);
        }

        private void HandleToolCall(BaseMessage message)
        {
            var requestId = message.payload?["request_id"]?.ToString() ?? "";
            var toolName = message.payload?["tool_name"]?.ToString() ?? "";
            var arguments = message.payload?["arguments"] as JObject ?? new JObject();
            OnToolCall?.Invoke(requestId, toolName, arguments);
            OnToolCallReceived?.Invoke(requestId, toolName, arguments.ToString());
        }

        private void HandleRequireConfirm(BaseMessage message)
        {
            var confirmId = message.payload?["confirm_id"]?.ToString() ?? "";
            var title = message.payload?["title"]?.ToString() ?? "";
            var msg = message.payload?["message"]?.ToString() ?? "";
            var confirmText = message.payload?["confirm_text"]?.ToString() ?? "Confirm";
            OnRequireConfirm?.Invoke(confirmId, title, msg, confirmText);
            OnConfirmRequestReceived?.Invoke(confirmId, title, msg);
        }

        private void HandleSessionReady(BaseMessage message)
        {
            var sessionId = message.payload?["session_id"]?.ToString() ?? "";
            var isNew = message.payload?["is_new"]?.ToObject<bool>() ?? true;
            OnSessionReady?.Invoke(sessionId, isNew);
        }

        #endregion

        #region Message Creation

        /// <summary>
        /// Create a session init message.
        /// </summary>
        public static BaseMessage CreateSessionInit(
            string projectPath,
            string outputDirectory,
            int maxRetryCount,
            string routerModel,
            string codeModel,
            string vlModel,
            string sessionId = null)
        {
            var payload = new
            {
                session_id = sessionId,
                project_path = projectPath,
                config = new
                {
                    output_directory = outputDirectory,
                    max_retry_count = maxRetryCount,
                    model_config = new
                    {
                        router_model = routerModel,
                        code_model = codeModel,
                        vl_model = vlModel
                    }
                }
            };
            return BaseMessage.Create(MessageType.SessionInit, payload);
        }

        /// <summary>
        /// Create a user message.
        /// </summary>
        public static BaseMessage CreateUserMessage(string content, string sessionId = null, List<ImageData> images = null)
        {
            var payload = new
            {
                session_id = sessionId,
                content = content,
                images = images ?? new List<ImageData>()
            };
            return BaseMessage.Create(MessageType.UserMessage, payload);
        }

        /// <summary>
        /// Create a tool response message.
        /// </summary>
        public static BaseMessage CreateToolResponse(string requestId, string toolName, bool success, object result = null, string error = null)
        {
            var payload = new
            {
                request_id = requestId,
                tool_name = toolName,
                success = success,
                result = result,
                error = error
            };
            return BaseMessage.Create(MessageType.ToolResponse, payload);
        }

        /// <summary>
        /// Create a user confirm message.
        /// </summary>
        public static BaseMessage CreateUserConfirm(string confirmId, bool confirmed, string message = null)
        {
            var payload = new
            {
                confirm_id = confirmId,
                confirmed = confirmed,
                message = message
            };
            return BaseMessage.Create(MessageType.UserConfirm, payload);
        }

        /// <summary>
        /// Create a cancel task message.
        /// </summary>
        public static BaseMessage CreateCancelTask(string taskId)
        {
            var payload = new
            {
                task_id = taskId
            };
            return BaseMessage.Create(MessageType.CancelTask, payload);
        }

        /// <summary>
        /// Create a ping message.
        /// </summary>
        public static BaseMessage CreatePing()
        {
            return BaseMessage.Create(MessageType.Ping);
        }

        #endregion

        #region Callbacks

        /// <summary>
        /// Register a callback for a tool response.
        /// </summary>
        public void RegisterToolCallback(string requestId, Action<JObject> callback)
        {
            _toolCallbacks[requestId] = callback;
        }

        /// <summary>
        /// Register a callback for a confirmation response.
        /// </summary>
        public void RegisterConfirmCallback(string confirmId, Action<bool, string> callback)
        {
            _confirmCallbacks[confirmId] = callback;
        }

        #endregion
    }

    /// <summary>
    /// Image data for messages.
    /// </summary>
    [Serializable]
    public class ImageData
    {
        public string image_id;
        public string data; // Base64 encoded
        public string mime_type;

        public static ImageData FromTexture(Texture2D texture, string mimeType = "image/png")
        {
            byte[] bytes;
            if (mimeType == "image/jpeg")
            {
                bytes = texture.EncodeToJPG();
            }
            else
            {
                bytes = texture.EncodeToPNG();
                mimeType = "image/png";
            }

            return new ImageData
            {
                image_id = Guid.NewGuid().ToString(),
                data = Convert.ToBase64String(bytes),
                mime_type = mimeType
            };
        }
    }
}
