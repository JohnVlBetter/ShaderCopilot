using System;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

namespace ShaderCopilot.Editor.Communication
{
    /// <summary>
    /// Connection state for health monitoring.
    /// </summary>
    public enum ConnectionHealth
    {
        Healthy,
        Degraded,
        Unhealthy,
        Disconnected
    }

    /// <summary>
    /// WebSocket client for communicating with the Python backend.
    /// Uses .NET ClientWebSocket for native support.
    /// </summary>
    public class WebSocketClient : IDisposable
    {
        private ClientWebSocket _webSocket;
        private CancellationTokenSource _cancellationTokenSource;
        private readonly ConcurrentQueue<string> _messageQueue;
        private readonly object _lock = new object();

        private string _uri;
        private bool _isConnected;
        private bool _isConnecting;
        private bool _autoReconnect;
        private int _reconnectInterval;
        private int _connectionTimeout;

        // Health check state
        private DateTime _lastMessageReceived;
        private DateTime _lastPingSent;
        private bool _awaitingPong;
        private int _healthCheckInterval = 30; // seconds
        private int _unhealthyThreshold = 90; // seconds without message
        private int _consecutiveFailures;
        private const int MaxConsecutiveFailures = 3;

        public event Action OnConnected;
        public event Action OnDisconnected;
        public event Action<string> OnMessage;
        public event Action<string> OnError;
        public event Action<ConnectionHealth> OnHealthChanged;
        public event Action<string> OnMessageReceived;

        public bool IsConnected => _isConnected && _webSocket?.State == WebSocketState.Open;

        public ConnectionHealth Health
        {
            get
            {
                if (!IsConnected) return ConnectionHealth.Disconnected;

                var timeSinceLastMessage = (DateTime.UtcNow - _lastMessageReceived).TotalSeconds;
                if (timeSinceLastMessage < _healthCheckInterval)
                    return ConnectionHealth.Healthy;
                if (timeSinceLastMessage < _unhealthyThreshold)
                    return ConnectionHealth.Degraded;
                return ConnectionHealth.Unhealthy;
            }
        }

        public WebSocketClient()
        {
            _messageQueue = new ConcurrentQueue<string>();
            _lastMessageReceived = DateTime.UtcNow;
        }

        /// <summary>
        /// Configure the WebSocket client.
        /// </summary>
        public void Configure(string uri, bool autoReconnect = true, int reconnectInterval = 3, int connectionTimeout = 10)
        {
            _uri = uri;
            _autoReconnect = autoReconnect;
            _reconnectInterval = reconnectInterval;
            _connectionTimeout = connectionTimeout;
        }

        /// <summary>
        /// Configure health check settings.
        /// </summary>
        public void ConfigureHealthCheck(int healthCheckInterval = 30, int unhealthyThreshold = 90)
        {
            _healthCheckInterval = healthCheckInterval;
            _unhealthyThreshold = unhealthyThreshold;
        }

        /// <summary>
        /// Connect to the WebSocket server.
        /// </summary>
        public async Task ConnectAsync()
        {
            if (_isConnecting || IsConnected)
            {
                Debug.Log("[ShaderCopilot] Already connected or connecting");
                return;
            }

            _isConnecting = true;

            try
            {
                _webSocket = new ClientWebSocket();
                _cancellationTokenSource = new CancellationTokenSource();

                var timeoutCts = new CancellationTokenSource(TimeSpan.FromSeconds(_connectionTimeout));
                var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(
                    _cancellationTokenSource.Token,
                    timeoutCts.Token
                );

                Debug.Log($"[ShaderCopilot] Connecting to {_uri}...");
                await _webSocket.ConnectAsync(new Uri(_uri), linkedCts.Token);

                _isConnected = true;
                _isConnecting = false;
                _consecutiveFailures = 0;
                _lastMessageReceived = DateTime.UtcNow;
                Debug.Log("[ShaderCopilot] Connected successfully");
                OnConnected?.Invoke();
                OnHealthChanged?.Invoke(ConnectionHealth.Healthy);

                // Start receive loop
                _ = ReceiveLoopAsync();

                // Start health check loop
                _ = HealthCheckLoopAsync();
            }
            catch (OperationCanceledException)
            {
                Debug.LogWarning("[ShaderCopilot] Connection timeout");
                OnError?.Invoke("Connection timeout");
                await HandleDisconnectionAsync();
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Connection failed: {ex.Message}");
                OnError?.Invoke($"Connection failed: {ex.Message}");
                await HandleDisconnectionAsync();
            }
        }

        /// <summary>
        /// Disconnect from the WebSocket server.
        /// </summary>
        public async Task DisconnectAsync()
        {
            _autoReconnect = false;

            if (_webSocket != null && _webSocket.State == WebSocketState.Open)
            {
                try
                {
                    await _webSocket.CloseAsync(
                        WebSocketCloseStatus.NormalClosure,
                        "Client disconnecting",
                        CancellationToken.None
                    );
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"[ShaderCopilot] Error during disconnect: {ex.Message}");
                }
            }

            Cleanup();
        }

        /// <summary>
        /// Send a message to the server.
        /// </summary>
        public async Task SendAsync(string message)
        {
            if (!IsConnected)
            {
                Debug.LogWarning("[ShaderCopilot] Cannot send: not connected");
                OnError?.Invoke("Not connected to server");
                return;
            }

            try
            {
                var bytes = Encoding.UTF8.GetBytes(message);
                var segment = new ArraySegment<byte>(bytes);
                await _webSocket.SendAsync(segment, WebSocketMessageType.Text, true, _cancellationTokenSource.Token);
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Send failed: {ex.Message}");
                OnError?.Invoke($"Send failed: {ex.Message}");
                await HandleDisconnectionAsync();
            }
        }

        /// <summary>
        /// Process queued messages on the main thread.
        /// Call this from Update() or a coroutine.
        /// </summary>
        public void ProcessMessageQueue()
        {
            while (_messageQueue.TryDequeue(out var message))
            {
                OnMessage?.Invoke(message);
            }
        }

        private async Task ReceiveLoopAsync()
        {
            var buffer = new byte[8192];
            var messageBuilder = new StringBuilder();

            try
            {
                while (_webSocket.State == WebSocketState.Open && !_cancellationTokenSource.Token.IsCancellationRequested)
                {
                    WebSocketReceiveResult result;
                    messageBuilder.Clear();

                    do
                    {
                        result = await _webSocket.ReceiveAsync(
                            new ArraySegment<byte>(buffer),
                            _cancellationTokenSource.Token
                        );

                        if (result.MessageType == WebSocketMessageType.Close)
                        {
                            Debug.Log("[ShaderCopilot] Server closed connection");
                            await HandleDisconnectionAsync();
                            return;
                        }

                        messageBuilder.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));
                    }
                    while (!result.EndOfMessage);

                    var message = messageBuilder.ToString();
                    _lastMessageReceived = DateTime.UtcNow;

                    // Handle pong response
                    if (message.Contains("\"type\":\"pong\""))
                    {
                        _awaitingPong = false;
                        continue;
                    }

                    _messageQueue.Enqueue(message);
                    OnMessageReceived?.Invoke(message); // Trigger the OnMessageReceived event
                }
            }
            catch (OperationCanceledException)
            {
                // Expected when cancellation is requested
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Receive error: {ex.Message}");
                await HandleDisconnectionAsync();
            }
        }

        private async Task HealthCheckLoopAsync()
        {
            var previousHealth = ConnectionHealth.Healthy;

            while (IsConnected && !_cancellationTokenSource.Token.IsCancellationRequested)
            {
                try
                {
                    await Task.Delay(TimeSpan.FromSeconds(_healthCheckInterval), _cancellationTokenSource.Token);

                    if (!IsConnected) break;

                    var currentHealth = Health;
                    if (currentHealth != previousHealth)
                    {
                        OnHealthChanged?.Invoke(currentHealth);
                        previousHealth = currentHealth;
                    }

                    // Send ping if degraded or we haven't sent recently
                    if (currentHealth == ConnectionHealth.Degraded ||
                        (DateTime.UtcNow - _lastPingSent).TotalSeconds > _healthCheckInterval)
                    {
                        await SendPingAsync();
                    }

                    // If unhealthy and awaiting pong, consider reconnecting
                    if (currentHealth == ConnectionHealth.Unhealthy && _awaitingPong)
                    {
                        _consecutiveFailures++;
                        Debug.LogWarning($"[ShaderCopilot] Connection unhealthy, failure count: {_consecutiveFailures}");

                        if (_consecutiveFailures >= MaxConsecutiveFailures)
                        {
                            Debug.LogWarning("[ShaderCopilot] Too many consecutive failures, reconnecting...");
                            await HandleDisconnectionAsync();
                            break;
                        }
                    }
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"[ShaderCopilot] Health check error: {ex.Message}");
                }
            }
        }

        /// <summary>
        /// Send a ping message to check connection health.
        /// </summary>
        public async Task SendPingAsync()
        {
            if (!IsConnected) return;

            try
            {
                _lastPingSent = DateTime.UtcNow;
                _awaitingPong = true;
                await SendAsync("{\"type\":\"ping\"}");
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[ShaderCopilot] Ping failed: {ex.Message}");
            }
        }

        /// <summary>
        /// Force a health check and reconnect if unhealthy.
        /// </summary>
        public async Task CheckHealthAsync()
        {
            if (!IsConnected)
            {
                if (_autoReconnect)
                {
                    await ConnectAsync();
                }
                return;
            }

            var health = Health;
            if (health == ConnectionHealth.Unhealthy)
            {
                Debug.LogWarning("[ShaderCopilot] Connection unhealthy, forcing reconnect...");
                await HandleDisconnectionAsync();
            }
            else if (health == ConnectionHealth.Degraded)
            {
                await SendPingAsync();
            }
        }

        private async Task HandleDisconnectionAsync()
        {
            var wasConnected = _isConnected;

            lock (_lock)
            {
                if (!_isConnected && !_isConnecting)
                    return;

                _isConnected = false;
                _isConnecting = false;
            }

            Cleanup();

            if (wasConnected)
            {
                OnDisconnected?.Invoke();
                OnHealthChanged?.Invoke(ConnectionHealth.Disconnected);
            }

            if (_autoReconnect)
            {
                Debug.Log($"[ShaderCopilot] Reconnecting in {_reconnectInterval} seconds...");
                await Task.Delay(TimeSpan.FromSeconds(_reconnectInterval));
                await ConnectAsync();
            }
        }

        private void Cleanup()
        {
            _cancellationTokenSource?.Cancel();
            _cancellationTokenSource?.Dispose();
            _cancellationTokenSource = null;

            _webSocket?.Dispose();
            _webSocket = null;

            _isConnected = false;
            _isConnecting = false;
            _awaitingPong = false;
        }

        public void Dispose()
        {
            _autoReconnect = false;
            Cleanup();
        }
    }
}
