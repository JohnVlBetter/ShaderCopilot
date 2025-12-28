using System;
using System.Threading.Tasks;
using ShaderCopilot.Editor.Communication;
using ShaderCopilot.Editor.Services;
using ShaderCopilot.Editor.Settings;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace ShaderCopilot.Editor.Window
{
    /// <summary>
    /// Main ShaderCopilot Editor Window.
    /// </summary>
    public class ShaderCopilotWindow : EditorWindow
    {
        private ChatPanel _chatPanel;
        private PreviewPanel _previewPanel;
        private VisualElement _statusBar;
        private Label _connectionStatusLabel;
        private Button _connectButton;
        private VisualElement _sessionPanel;
        private ListView _sessionListView;
        private Label _sessionLabel;

        private WebSocketClient _webSocketClient;
        private MessageHandler _messageHandler;
        private BackendLauncher _backendLauncher;

        private string _currentSessionId;
        private bool _isConnected;
        private System.Collections.Generic.List<string> _sessionList = new System.Collections.Generic.List<string>();
        private bool _sessionPanelVisible = false;

        [MenuItem("Window/ShaderCopilot/Shader Assistant")]
        public static void ShowWindow()
        {
            var window = GetWindow<ShaderCopilotWindow>();
            window.titleContent = new GUIContent("ShaderCopilot", EditorGUIUtility.IconContent("d_Shader Icon").image);
            window.minSize = new Vector2(800, 600);
        }

        private void OnEnable()
        {
            InitializeComponents();
        }

        private void OnDisable()
        {
            CleanupComponents();
        }

        private void CreateGUI()
        {
            BuildUI();
            InitializePreview();
        }

        private void InitializeComponents()
        {
            _webSocketClient = new WebSocketClient();
            _messageHandler = new MessageHandler();
            _backendLauncher = new BackendLauncher();

            // Wire up events
            _webSocketClient.OnConnected += OnWebSocketConnected;
            _webSocketClient.OnDisconnected += OnWebSocketDisconnected;
            _webSocketClient.OnMessageReceived += OnWebSocketMessageReceived;
            _webSocketClient.OnError += OnWebSocketError;

            _messageHandler.OnResponseReceived += OnServerResponse;
            _messageHandler.OnStreamChunkReceived += OnStreamChunk;
            _messageHandler.OnToolCallReceived += OnToolCallRequest;
            _messageHandler.OnConfirmRequestReceived += OnConfirmRequest;
            _messageHandler.OnProgressReceived += OnProgressUpdate;
            _messageHandler.OnErrorReceived += OnServerError;

            _backendLauncher.OnStarted += OnBackendStarted;
            _backendLauncher.OnStopped += OnBackendStopped;
            _backendLauncher.OnError += OnBackendError;
        }

        private void CleanupComponents()
        {
            _webSocketClient?.DisconnectAsync();
            _webSocketClient = null;

            _backendLauncher?.Stop();
            _backendLauncher?.Dispose();
            _backendLauncher = null;

            _previewPanel?.Dispose();
        }

        private void BuildUI()
        {
            var root = rootVisualElement;
            root.style.flexDirection = FlexDirection.Column;
            root.style.flexGrow = 1;

            // Toolbar
            var toolbar = new VisualElement();
            toolbar.style.flexDirection = FlexDirection.Row;
            toolbar.style.justifyContent = Justify.SpaceBetween;
            toolbar.style.alignItems = Align.Center;
            toolbar.style.paddingLeft = 8;
            toolbar.style.paddingRight = 8;
            toolbar.style.paddingTop = 4;
            toolbar.style.paddingBottom = 4;
            toolbar.style.backgroundColor = new Color(0.22f, 0.22f, 0.22f);
            toolbar.style.borderBottomWidth = 1;
            toolbar.style.borderBottomColor = new Color(0.1f, 0.1f, 0.1f);

            var titleLabel = new Label("ShaderCopilot");
            titleLabel.style.fontSize = 16;
            titleLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            toolbar.Add(titleLabel);

            var toolbarButtons = new VisualElement();
            toolbarButtons.style.flexDirection = FlexDirection.Row;

            // Session controls
            var newSessionButton = new Button(OnNewSession) { text = "New" };
            newSessionButton.tooltip = "Start new session";
            newSessionButton.style.marginRight = 4;
            toolbarButtons.Add(newSessionButton);

            var sessionsButton = new Button(ToggleSessionPanel) { text = "📋" };
            sessionsButton.tooltip = "Session history";
            sessionsButton.style.marginRight = 8;
            toolbarButtons.Add(sessionsButton);

            _sessionLabel = new Label("");
            _sessionLabel.style.color = new Color(0.6f, 0.6f, 0.6f);
            _sessionLabel.style.fontSize = 10;
            _sessionLabel.style.marginRight = 8;
            toolbarButtons.Add(_sessionLabel);

            _connectButton = new Button(ToggleConnection) { text = "Connect" };
            _connectButton.style.marginRight = 4;
            toolbarButtons.Add(_connectButton);

            var settingsButton = new Button(OpenSettings) { text = "⚙" };
            settingsButton.tooltip = "Settings";
            toolbarButtons.Add(settingsButton);

            toolbar.Add(toolbarButtons);
            root.Add(toolbar);

            // Session panel (hidden by default)
            _sessionPanel = CreateSessionPanel();
            root.Add(_sessionPanel);

            // Main content area (split view)
            var mainContent = new VisualElement();
            mainContent.style.flexDirection = FlexDirection.Row;
            mainContent.style.flexGrow = 1;

            // Chat panel (left)
            _chatPanel = new ChatPanel();
            _chatPanel.style.flexGrow = 1;
            _chatPanel.style.flexBasis = Length.Percent(60);
            _chatPanel.OnMessageSent += OnUserMessageSent;
            _chatPanel.OnImageAttached += OnUserImageAttached;
            _chatPanel.OnCancelRequested += OnCancelRequested;
            mainContent.Add(_chatPanel);

            // Splitter
            var splitter = new VisualElement();
            splitter.style.width = 4;
            splitter.style.backgroundColor = new Color(0.15f, 0.15f, 0.15f);
            mainContent.Add(splitter);

            // Preview panel (right)
            _previewPanel = new PreviewPanel();
            _previewPanel.style.flexBasis = Length.Percent(40);
            mainContent.Add(_previewPanel);

            root.Add(mainContent);

            // Status bar
            _statusBar = new VisualElement();
            _statusBar.style.flexDirection = FlexDirection.Row;
            _statusBar.style.justifyContent = Justify.SpaceBetween;
            _statusBar.style.alignItems = Align.Center;
            _statusBar.style.paddingLeft = 8;
            _statusBar.style.paddingRight = 8;
            _statusBar.style.paddingTop = 2;
            _statusBar.style.paddingBottom = 2;
            _statusBar.style.backgroundColor = new Color(0.18f, 0.18f, 0.18f);
            _statusBar.style.borderTopWidth = 1;
            _statusBar.style.borderTopColor = new Color(0.1f, 0.1f, 0.1f);

            _connectionStatusLabel = new Label("⚪ Disconnected");
            _connectionStatusLabel.style.fontSize = 10;
            _statusBar.Add(_connectionStatusLabel);

            var versionLabel = new Label("v0.1.0 PoC");
            versionLabel.style.fontSize = 10;
            versionLabel.style.color = new Color(0.5f, 0.5f, 0.5f);
            _statusBar.Add(versionLabel);

            root.Add(_statusBar);
        }

        private VisualElement CreateSessionPanel()
        {
            var panel = new VisualElement();
            panel.style.display = DisplayStyle.None;
            panel.style.backgroundColor = new Color(0.2f, 0.2f, 0.2f);
            panel.style.paddingLeft = 8;
            panel.style.paddingRight = 8;
            panel.style.paddingTop = 8;
            panel.style.paddingBottom = 8;
            panel.style.borderBottomWidth = 1;
            panel.style.borderBottomColor = new Color(0.1f, 0.1f, 0.1f);

            var header = new VisualElement();
            header.style.flexDirection = FlexDirection.Row;
            header.style.justifyContent = Justify.SpaceBetween;
            header.style.marginBottom = 8;

            var titleLabel = new Label("Sessions");
            titleLabel.style.fontSize = 12;
            titleLabel.style.unityFontStyleAndWeight = FontStyle.Bold;
            header.Add(titleLabel);

            var refreshButton = new Button(RefreshSessionList) { text = "↻" };
            refreshButton.tooltip = "Refresh session list";
            header.Add(refreshButton);

            panel.Add(header);

            // Session list view
            _sessionListView = new ListView();
            _sessionListView.style.height = 150;
            _sessionListView.itemsSource = _sessionList;
            _sessionListView.makeItem = () => new Label();
            _sessionListView.bindItem = (element, index) =>
            {
                var label = element as Label;
                if (label != null && index < _sessionList.Count)
                {
                    var sessionId = _sessionList[index];
                    label.text = TruncateSessionId(sessionId);
                    label.tooltip = sessionId;
                    label.style.paddingTop = 4;
                    label.style.paddingBottom = 4;
                }
            };
            _sessionListView.selectionChanged += OnSessionSelected;
            panel.Add(_sessionListView);

            var buttonRow = new VisualElement();
            buttonRow.style.flexDirection = FlexDirection.Row;
            buttonRow.style.justifyContent = Justify.FlexEnd;
            buttonRow.style.marginTop = 8;

            var deleteButton = new Button(DeleteSelectedSession) { text = "Delete" };
            deleteButton.style.marginRight = 4;
            buttonRow.Add(deleteButton);

            var loadButton = new Button(LoadSelectedSession) { text = "Load" };
            buttonRow.Add(loadButton);

            panel.Add(buttonRow);

            return panel;
        }

        private string TruncateSessionId(string sessionId)
        {
            if (sessionId.Length <= 20)
                return sessionId;
            return sessionId.Substring(0, 8) + "..." + sessionId.Substring(sessionId.Length - 8);
        }

        private void ToggleSessionPanel()
        {
            _sessionPanelVisible = !_sessionPanelVisible;
            _sessionPanel.style.display = _sessionPanelVisible ? DisplayStyle.Flex : DisplayStyle.None;

            if (_sessionPanelVisible)
            {
                RefreshSessionList();
            }
        }

        private void RefreshSessionList()
        {
            // Request session list from backend
            if (_isConnected)
            {
                // TODO: Send request to backend for session list
                // For now, use local file system
            }

            // Load from local sessions folder
            var sessionsPath = System.IO.Path.Combine(Application.dataPath, "ShaderCopilot/Sessions");
            if (System.IO.Directory.Exists(sessionsPath))
            {
                _sessionList.Clear();
                foreach (var file in System.IO.Directory.GetFiles(sessionsPath, "*.json"))
                {
                    var fileName = System.IO.Path.GetFileNameWithoutExtension(file);
                    _sessionList.Add(fileName);
                }
                _sessionListView?.RefreshItems();
            }
        }

        private void OnNewSession()
        {
            // Generate new session ID
            _currentSessionId = Guid.NewGuid().ToString();
            UpdateSessionLabel();

            // Clear chat
            _chatPanel?.ClearMessages();
            _chatPanel?.AddSystemMessage("New session started. Describe the shader you want to create.");

            // Clear preview
            _previewPanel?.Clear();

            // Notify backend if connected
            if (_isConnected)
            {
                var message = new
                {
                    type = "SESSION_INIT",
                    session_id = _currentSessionId,
                    payload = new { is_new = true }
                };
                _ = _webSocketClient?.SendAsync(Newtonsoft.Json.JsonConvert.SerializeObject(message));
            }
        }

        private void OnSessionSelected(System.Collections.Generic.IEnumerable<object> selectedItems)
        {
            // Session selection changed
        }

        private void LoadSelectedSession()
        {
            if (_sessionListView?.selectedIndex >= 0 && _sessionListView.selectedIndex < _sessionList.Count)
            {
                var sessionId = _sessionList[_sessionListView.selectedIndex];
                LoadSession(sessionId);
            }
        }

        private void LoadSession(string sessionId)
        {
            var sessionPath = System.IO.Path.Combine(Application.dataPath, $"ShaderCopilot/Sessions/{sessionId}.json");

            if (!System.IO.File.Exists(sessionPath))
            {
                Debug.LogWarning($"[ShaderCopilot] Session file not found: {sessionPath}");
                return;
            }

            try
            {
                var json = System.IO.File.ReadAllText(sessionPath);
                // TODO: Parse JSON and restore session state

                _currentSessionId = sessionId;
                UpdateSessionLabel();

                _chatPanel?.AddSystemMessage($"Session loaded: {TruncateSessionId(sessionId)}");

                // Hide session panel
                _sessionPanelVisible = false;
                _sessionPanel.style.display = DisplayStyle.None;

                Debug.Log($"[ShaderCopilot] Session loaded: {sessionId}");
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to load session: {ex.Message}");
            }
        }

        private void DeleteSelectedSession()
        {
            if (_sessionListView?.selectedIndex >= 0 && _sessionListView.selectedIndex < _sessionList.Count)
            {
                var sessionId = _sessionList[_sessionListView.selectedIndex];

                if (EditorUtility.DisplayDialog(
                    "Delete Session",
                    $"Are you sure you want to delete session '{TruncateSessionId(sessionId)}'?",
                    "Delete",
                    "Cancel"))
                {
                    var sessionPath = System.IO.Path.Combine(Application.dataPath, $"ShaderCopilot/Sessions/{sessionId}.json");

                    try
                    {
                        if (System.IO.File.Exists(sessionPath))
                        {
                            System.IO.File.Delete(sessionPath);
                        }

                        RefreshSessionList();
                        Debug.Log($"[ShaderCopilot] Session deleted: {sessionId}");
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError($"[ShaderCopilot] Failed to delete session: {ex.Message}");
                    }
                }
            }
        }

        private void UpdateSessionLabel()
        {
            if (_sessionLabel != null)
            {
                if (string.IsNullOrEmpty(_currentSessionId))
                {
                    _sessionLabel.text = "";
                }
                else
                {
                    _sessionLabel.text = $"Session: {TruncateSessionId(_currentSessionId)}";
                }
            }
        }

        private void InitializePreview()
        {
            _previewPanel?.Initialize();
        }

        private async void ToggleConnection()
        {
            if (_isConnected)
            {
                await _webSocketClient?.DisconnectAsync();
            }
            else
            {
                await ConnectToBackend();
            }
        }

        private async Task ConnectToBackend()
        {
            UpdateConnectionStatus("🟡 Starting backend...");

            // Start backend if not running
            if (!_backendLauncher.IsRunning)
            {
                var started = await _backendLauncher.StartAsync();
                if (!started)
                {
                    UpdateConnectionStatus("🔴 Backend failed to start");
                    return;
                }
            }

            // Connect WebSocket
            UpdateConnectionStatus("🟡 Connecting...");
            var settings = ShaderCopilotSettings.Instance;
            _webSocketClient.Configure(settings.WebSocketUri, settings.AutoReconnect, settings.ReconnectInterval, settings.ConnectionTimeout);
            await _webSocketClient.ConnectAsync();
        }

        private void OpenSettings()
        {
            Selection.activeObject = ShaderCopilotSettings.Instance;
            EditorGUIUtility.PingObject(ShaderCopilotSettings.Instance);
        }

        private void UpdateConnectionStatus(string status)
        {
            if (_connectionStatusLabel != null)
            {
                _connectionStatusLabel.text = status;
            }
        }

        private void UpdateConnectButton()
        {
            if (_connectButton != null)
            {
                _connectButton.text = _isConnected ? "Disconnect" : "Connect";
            }
        }

        #region WebSocket Events

        private void OnWebSocketConnected()
        {
            _isConnected = true;
            UpdateConnectionStatus("🟢 Connected");
            UpdateConnectButton();

            // Send session init
            var settings = ShaderCopilotSettings.Instance;
            var initMessage = MessageHandler.CreateSessionInit(
                Application.dataPath,
                settings.ShaderOutputDirectory,
                settings.MaxRetryCount,
                settings.RouterModel,
                settings.CodeModel,
                settings.VlModel,
                _currentSessionId
            );
            _ = _webSocketClient.SendAsync(initMessage.ToJson());
        }

        private void OnWebSocketDisconnected()
        {
            _isConnected = false;
            UpdateConnectionStatus("⚪ Disconnected");
            UpdateConnectButton();
        }

        private void OnWebSocketMessageReceived(string message)
        {
            _messageHandler.HandleMessage(message);
        }

        private void OnWebSocketError(string error)
        {
            Debug.LogError($"[ShaderCopilot] WebSocket error: {error}");
            _chatPanel?.AddSystemMessage($"❌ Connection error: {error}");
        }

        #endregion

        #region Backend Events

        private void OnBackendStarted()
        {
            Debug.Log("[ShaderCopilot] Backend started");
        }

        private void OnBackendStopped()
        {
            Debug.Log("[ShaderCopilot] Backend stopped");
            if (_isConnected)
            {
                _ = _webSocketClient?.DisconnectAsync();
            }
        }

        private void OnBackendError(string error)
        {
            Debug.LogError($"[ShaderCopilot] Backend error: {error}");
            _chatPanel?.AddSystemMessage($"❌ Backend error: {error}");
        }

        #endregion

        #region Message Handler Events

        private void OnServerResponse(string content)
        {
            _chatPanel?.EndStreaming();
            _chatPanel?.AddAssistantMessage(content);
        }

        private void OnStreamChunk(string content, bool isFinal)
        {
            if (!_chatPanel.IsStreaming)
            {
                _chatPanel?.StartStreaming();
            }

            _chatPanel?.AppendStreamingContent(content);

            if (isFinal)
            {
                _chatPanel?.EndStreaming();
            }
        }

        private void OnToolCallRequest(string toolCallId, string toolName, string arguments)
        {
            // Handle tool calls from the server
            Debug.Log($"[ShaderCopilot] Tool call: {toolName}");
            HandleToolCall(toolCallId, toolName, arguments);
        }

        private async void HandleToolCall(string toolCallId, string toolName, string arguments)
        {
            try
            {
                var args = Newtonsoft.Json.JsonConvert.DeserializeObject<System.Collections.Generic.Dictionary<string, object>>(arguments);
                object result = null;

                switch (toolName)
                {
                    case "compile_shader":
                        result = HandleCompileShader(args);
                        break;
                    case "create_material":
                        result = HandleCreateMaterial(args);
                        break;
                    case "apply_to_preview":
                        result = HandleApplyToPreview(args);
                        break;
                    case "capture_screenshot":
                        result = HandleCaptureScreenshot(args);
                        break;
                    default:
                        result = new { error = $"Unknown tool: {toolName}" };
                        break;
                }

                // Send response back
                var response = MessageHandler.CreateToolResponse(toolCallId, toolName, true, result, null);
                _ = _webSocketClient?.SendAsync(response.ToJson());
            }
            catch (Exception ex)
            {
                var errorResponse = MessageHandler.CreateToolResponse(toolCallId, toolName, false, null, ex.Message);
                _ = _webSocketClient?.SendAsync(errorResponse.ToJson());
            }
        }

        private object HandleCompileShader(System.Collections.Generic.Dictionary<string, object> args)
        {
            var code = args["code"]?.ToString();
            var shaderName = args.ContainsKey("shader_name") ? args["shader_name"]?.ToString() : null;

            var settings = ShaderCopilotSettings.Instance;
            var outputPath = ShaderCompilerService.GetOutputPath(shaderName ?? "Generated", settings.ShaderOutputDirectory);

            var result = ShaderCompilerService.CompileAndSave(code, outputPath);

            if (result.Success && result.Shader != null)
            {
                _previewPanel?.ApplyShader(result.Shader);
            }

            return new
            {
                success = result.Success,
                shader_path = result.ShaderPath,
                errors = result.Errors.ConvertAll(e => e.ToString()),
                warnings = result.Warnings
            };
        }

        private object HandleCreateMaterial(System.Collections.Generic.Dictionary<string, object> args)
        {
            var shaderPath = args["shader_path"]?.ToString();
            var settings = ShaderCopilotSettings.Instance;

            var shaderName = ShaderCompilerService.ExtractShaderName(FileManagerService.ReadFile(shaderPath) ?? "");
            var materialPath = MaterialManagerService.GetMaterialPath(shaderName ?? "Generated", settings.MaterialOutputDirectory);

            var material = MaterialManagerService.CreateMaterialFromShaderPath(shaderPath, materialPath);

            if (material != null)
            {
                _previewPanel?.ApplyMaterial(material);
            }

            return new
            {
                success = material != null,
                material_path = materialPath
            };
        }

        private object HandleApplyToPreview(System.Collections.Generic.Dictionary<string, object> args)
        {
            var materialPath = args["material_path"]?.ToString();
            var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);

            if (material != null)
            {
                _previewPanel?.ApplyMaterial(material);
                return new { success = true };
            }

            return new { success = false, error = "Material not found" };
        }

        private object HandleCaptureScreenshot(System.Collections.Generic.Dictionary<string, object> args)
        {
            var base64 = _previewPanel?.PreviewService?.CaptureScreenshotBase64();

            return new
            {
                success = base64 != null,
                image_data = base64,
                mime_type = "image/png"
            };
        }

        private void OnConfirmRequest(string confirmId, string action, string details)
        {
            // Show confirmation dialog
            var confirmed = EditorUtility.DisplayDialog(
                "Confirm Action",
                $"Do you want to proceed with: {action}?\n\n{details}",
                "Confirm",
                "Cancel"
            );

            var response = MessageHandler.CreateUserConfirm(confirmId, confirmed, null);
            _ = _webSocketClient?.SendAsync(response.ToJson());
        }

        private void OnProgressUpdate(string stage, string message, float? progress)
        {
            _previewPanel?.SetStatus($"{stage}: {message}");
        }

        private void OnServerError(string code, string message)
        {
            _chatPanel?.EndStreaming();
            _chatPanel?.AddSystemMessage($"❌ Error ({code}): {message}");
        }

        #endregion

        #region User Input Events

        private void OnUserMessageSent(string message)
        {
            if (!_isConnected)
            {
                _chatPanel?.AddSystemMessage("❌ Not connected. Click 'Connect' to start.");
                return;
            }

            var userMessage = MessageHandler.CreateUserMessage(message, _currentSessionId, null);
            _ = _webSocketClient?.SendAsync(userMessage.ToJson());
        }

        private void OnUserImageAttached(string base64, string mimeType)
        {
            // Store for next message
            Debug.Log($"[ShaderCopilot] Image attached ({mimeType}, {base64.Length} chars)");
        }

        private void OnCancelRequested()
        {
            if (_isConnected)
            {
                var cancelMessage = MessageHandler.CreateCancelTask(_currentSessionId ?? "");
                _ = _webSocketClient?.SendAsync(cancelMessage.ToJson());
            }
            _chatPanel?.EndStreaming();
        }

        #endregion
    }
}
