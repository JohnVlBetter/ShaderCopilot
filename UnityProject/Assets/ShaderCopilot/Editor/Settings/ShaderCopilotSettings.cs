using System;
using UnityEditor;
using UnityEngine;

namespace ShaderCopilot.Editor.Settings
{
    /// <summary>
    /// ScriptableObject for storing ShaderCopilot configuration.
    /// Persists user preferences for the shader generation assistant.
    /// </summary>
    [CreateAssetMenu(fileName = "ShaderCopilotSettings", menuName = "ShaderCopilot/Settings")]
    public class ShaderCopilotSettings : ScriptableObject
    {
        private const string SettingsPath = "Assets/ShaderCopilot/Editor/Settings/ShaderCopilotSettings.asset";
        private static ShaderCopilotSettings _instance;

        [Header("Backend Configuration")]
        [Tooltip("WebSocket server host address")]
        [SerializeField] private string _backendHost = "localhost";

        [Tooltip("WebSocket server port")]
        [SerializeField] private int _backendPort = 8765;

        [Tooltip("Path to Python executable (leave empty to use system Python)")]
        [SerializeField] private string _pythonPath = "";

        [Tooltip("Path to Agent directory (relative to project root)")]
        [SerializeField] private string _agentPath = "../Agent";

        [Header("Output Configuration")]
        [Tooltip("Directory for generated Shader files (relative to Assets/)")]
        [SerializeField] private string _shaderOutputDirectory = "Shaders/Generated";

        [Tooltip("Directory for generated Material files (relative to Assets/)")]
        [SerializeField] private string _materialOutputDirectory = "Materials/Generated";

        [Header("Generation Settings")]
        [Tooltip("Maximum retry attempts for shader compilation")]
        [Range(1, 10)]
        [SerializeField] private int _maxRetryCount = 3;

        [Header("Model Configuration")]
        [Tooltip("Router model name for intent classification")]
        [SerializeField] private string _routerModel = "qwen-turbo";

        [Tooltip("Code generation model name")]
        [SerializeField] private string _codeModel = "qwen-max";

        [Tooltip("Vision-Language model name for image analysis")]
        [SerializeField] private string _vlModel = "qwen-vl-plus";

        [Header("Connection Settings")]
        [Tooltip("WebSocket connection timeout in seconds")]
        [Range(5, 60)]
        [SerializeField] private int _connectionTimeout = 10;

        [Tooltip("Auto-reconnect on connection loss")]
        [SerializeField] private bool _autoReconnect = true;

        [Tooltip("Reconnect interval in seconds")]
        [Range(1, 30)]
        [SerializeField] private int _reconnectInterval = 3;

        #region Properties

        public string BackendHost => _backendHost;
        public int BackendPort => _backendPort;
        public string PythonPath => _pythonPath;
        public string AgentPath => _agentPath;
        public string ShaderOutputDirectory => _shaderOutputDirectory;
        public string MaterialOutputDirectory => _materialOutputDirectory;
        public int MaxRetryCount => _maxRetryCount;
        public string RouterModel => _routerModel;
        public string CodeModel => _codeModel;
        public string VlModel => _vlModel;
        public int ConnectionTimeout => _connectionTimeout;
        public bool AutoReconnect => _autoReconnect;
        public int ReconnectInterval => _reconnectInterval;

        public string WebSocketUri => $"ws://{_backendHost}:{_backendPort}";

        #endregion

        #region Singleton Access

        /// <summary>
        /// Get or create the settings instance.
        /// </summary>
        public static ShaderCopilotSettings Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = AssetDatabase.LoadAssetAtPath<ShaderCopilotSettings>(SettingsPath);

                    if (_instance == null)
                    {
                        _instance = CreateInstance<ShaderCopilotSettings>();

                        // Ensure directory exists
                        var directory = System.IO.Path.GetDirectoryName(SettingsPath);
                        if (!System.IO.Directory.Exists(directory))
                        {
                            System.IO.Directory.CreateDirectory(directory);
                        }

                        AssetDatabase.CreateAsset(_instance, SettingsPath);
                        AssetDatabase.SaveAssets();
                        Debug.Log($"[ShaderCopilot] Created settings asset at {SettingsPath}");
                    }
                }
                return _instance;
            }
        }

        #endregion

        #region Validation

        private void OnValidate()
        {
            // Ensure port is in valid range
            _backendPort = Mathf.Clamp(_backendPort, 1024, 65535);

            // Ensure paths don't have leading slashes
            if (_shaderOutputDirectory.StartsWith("/") || _shaderOutputDirectory.StartsWith("\\"))
            {
                _shaderOutputDirectory = _shaderOutputDirectory.TrimStart('/', '\\');
            }
            if (_materialOutputDirectory.StartsWith("/") || _materialOutputDirectory.StartsWith("\\"))
            {
                _materialOutputDirectory = _materialOutputDirectory.TrimStart('/', '\\');
            }
        }

        #endregion

        #region Helper Methods

        /// <summary>
        /// Get the full path for shader output directory.
        /// </summary>
        public string GetShaderOutputFullPath()
        {
            return System.IO.Path.Combine(Application.dataPath, _shaderOutputDirectory);
        }

        /// <summary>
        /// Get the full path for material output directory.
        /// </summary>
        public string GetMaterialOutputFullPath()
        {
            return System.IO.Path.Combine(Application.dataPath, _materialOutputDirectory);
        }

        /// <summary>
        /// Get the full path for the Agent directory.
        /// </summary>
        public string GetAgentFullPath()
        {
            var projectRoot = System.IO.Path.GetDirectoryName(Application.dataPath);
            return System.IO.Path.GetFullPath(System.IO.Path.Combine(projectRoot, _agentPath));
        }

        /// <summary>
        /// Creates a configuration object for session initialization.
        /// </summary>
        public SessionConfig ToSessionConfig()
        {
            return new SessionConfig
            {
                OutputDirectory = _shaderOutputDirectory,
                MaxRetryCount = _maxRetryCount,
                ModelConfig = new ModelConfig
                {
                    RouterModel = _routerModel,
                    CodeModel = _codeModel,
                    VlModel = _vlModel
                }
            };
        }

        #endregion
    }

    /// <summary>
    /// Session configuration for WebSocket initialization.
    /// </summary>
    [Serializable]
    public class SessionConfig
    {
        public string OutputDirectory;
        public int MaxRetryCount;
        public ModelConfig ModelConfig;
    }

    /// <summary>
    /// Model configuration for LLM routing.
    /// </summary>
    [Serializable]
    public class ModelConfig
    {
        public string RouterModel;
        public string CodeModel;
        public string VlModel;
    }
}
