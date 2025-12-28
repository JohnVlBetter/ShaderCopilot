using System;
using System.Diagnostics;
using System.Threading.Tasks;
using UnityEngine;

namespace ShaderCopilot.Editor.Communication
{
    /// <summary>
    /// Manages the lifecycle of the Python backend process.
    /// </summary>
    public class BackendLauncher : IDisposable
    {
        private Process _backendProcess;

        public event Action OnStarted;
        public event Action OnStopped;
        public event Action<string> OnError;

        public bool IsRunning => _backendProcess != null && !_backendProcess.HasExited;

        /// <summary>
        /// Start the Python backend process.
        /// </summary>
        public async Task<bool> StartAsync()
        {
            try
            {
                // For now, assume backend is started externally
                // TODO: Implement actual backend launching
                await Task.Delay(100);
                OnStarted?.Invoke();
                return true;
            }
            catch (Exception ex)
            {
                OnError?.Invoke(ex.Message);
                return false;
            }
        }

        /// <summary>
        /// Stop the Python backend process.
        /// </summary>
        public void Stop()
        {
            try
            {
                if (_backendProcess != null && !_backendProcess.HasExited)
                {
                    _backendProcess.Kill();
                    _backendProcess.Dispose();
                }
            }
            catch (Exception ex)
            {
                UnityEngine.Debug.LogWarning($"[BackendLauncher] Stop warning: {ex.Message}");
            }
            finally
            {
                _backendProcess = null;
                OnStopped?.Invoke();
            }
        }

        public void Dispose()
        {
            Stop();
        }
    }
}
