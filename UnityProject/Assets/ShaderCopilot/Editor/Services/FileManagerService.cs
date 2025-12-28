using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace ShaderCopilot.Editor.Services
{
    /// <summary>
    /// Service for file operations related to shader and material assets.
    /// </summary>
    public static class FileManagerService
    {
        /// <summary>
        /// Ensure a directory exists, creating it if necessary.
        /// </summary>
        public static bool EnsureDirectoryExists(string path)
        {
            try
            {
                if (!Directory.Exists(path))
                {
                    Directory.CreateDirectory(path);
                    Debug.Log($"[ShaderCopilot] Created directory: {path}");
                }
                return true;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to create directory: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Ensure an Assets-relative directory exists.
        /// </summary>
        public static bool EnsureAssetDirectoryExists(string relativePath)
        {
            var fullPath = Path.Combine(Application.dataPath, relativePath);
            var success = EnsureDirectoryExists(fullPath);

            if (success)
            {
                AssetDatabase.Refresh();
            }

            return success;
        }

        /// <summary>
        /// Read file contents as text.
        /// </summary>
        public static string ReadFile(string path)
        {
            try
            {
                if (File.Exists(path))
                {
                    return File.ReadAllText(path);
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[FileManagerService] Failed to read file: {ex.Message}");
            }
            return null;
        }

        /// <summary>
        /// Write text content to file.
        /// </summary>
        public static bool WriteFile(string path, string content)
        {
            try
            {
                var directory = Path.GetDirectoryName(path);
                if (!Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                File.WriteAllText(path, content);
                return true;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[FileManagerService] Failed to write file: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Copy a file to a new location.
        /// </summary>
        public static bool CopyFile(string sourcePath, string destinationPath, bool overwrite = false)
        {
            try
            {
                if (!File.Exists(sourcePath))
                {
                    Debug.LogWarning($"[ShaderCopilot] Source file not found: {sourcePath}");
                    return false;
                }

                if (File.Exists(destinationPath) && !overwrite)
                {
                    Debug.LogWarning($"[ShaderCopilot] Destination file exists: {destinationPath}");
                    return false;
                }

                var directory = Path.GetDirectoryName(destinationPath);
                EnsureDirectoryExists(directory);

                File.Copy(sourcePath, destinationPath, overwrite);
                Debug.Log($"[ShaderCopilot] File copied: {sourcePath} -> {destinationPath}");
                return true;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to copy file: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Delete a file.
        /// </summary>
        public static bool DeleteFile(string path)
        {
            try
            {
                if (File.Exists(path))
                {
                    File.Delete(path);
                    Debug.Log($"[ShaderCopilot] File deleted: {path}");
                }
                return true;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to delete file: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Delete an asset and its meta file.
        /// </summary>
        public static bool DeleteAsset(string assetPath)
        {
            try
            {
                return AssetDatabase.DeleteAsset(assetPath);
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to delete asset: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Get all shader files in a directory.
        /// </summary>
        public static List<string> GetShaderFiles(string directory, bool recursive = true)
        {
            var searchOption = recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;

            try
            {
                if (!Directory.Exists(directory))
                {
                    return new List<string>();
                }

                return Directory.GetFiles(directory, "*.shader", searchOption)
                    .Select(p => p.Replace("\\", "/"))
                    .ToList();
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to get shader files: {ex.Message}");
                return new List<string>();
            }
        }

        /// <summary>
        /// Get all material files in a directory.
        /// </summary>
        public static List<string> GetMaterialFiles(string directory, bool recursive = true)
        {
            var searchOption = recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;

            try
            {
                if (!Directory.Exists(directory))
                {
                    return new List<string>();
                }

                return Directory.GetFiles(directory, "*.mat", searchOption)
                    .Select(p => p.Replace("\\", "/"))
                    .ToList();
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to get material files: {ex.Message}");
                return new List<string>();
            }
        }

        /// <summary>
        /// Convert a full path to an Assets-relative path.
        /// </summary>
        public static string ToAssetPath(string fullPath)
        {
            fullPath = fullPath.Replace("\\", "/");
            var dataPath = Application.dataPath.Replace("\\", "/");

            if (fullPath.StartsWith(dataPath))
            {
                return "Assets" + fullPath.Substring(dataPath.Length);
            }

            return fullPath;
        }

        /// <summary>
        /// Convert an Assets-relative path to a full path.
        /// </summary>
        public static string ToFullPath(string assetPath)
        {
            if (assetPath.StartsWith("Assets/") || assetPath.StartsWith("Assets\\"))
            {
                return Path.Combine(
                    Path.GetDirectoryName(Application.dataPath),
                    assetPath
                ).Replace("\\", "/");
            }

            return assetPath;
        }

        /// <summary>
        /// Reveal a file in the system file explorer.
        /// </summary>
        public static void RevealInExplorer(string path)
        {
            path = path.Replace("/", "\\");

            if (File.Exists(path))
            {
                System.Diagnostics.Process.Start("explorer.exe", $"/select,\"{path}\"");
            }
            else if (Directory.Exists(path))
            {
                System.Diagnostics.Process.Start("explorer.exe", path);
            }
            else
            {
                Debug.LogWarning($"[ShaderCopilot] Path not found: {path}");
            }
        }

        /// <summary>
        /// Select an asset in the Project window.
        /// </summary>
        public static void SelectAsset(string assetPath)
        {
            var asset = AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(assetPath);
            if (asset != null)
            {
                Selection.activeObject = asset;
                EditorGUIUtility.PingObject(asset);
            }
        }

        /// <summary>
        /// Open a file in the default external editor.
        /// </summary>
        public static void OpenInExternalEditor(string path)
        {
            if (File.Exists(path))
            {
                System.Diagnostics.Process.Start(path);
            }
            else
            {
                Debug.LogWarning($"[ShaderCopilot] File not found: {path}");
            }
        }

        /// <summary>
        /// Create a backup of a file.
        /// </summary>
        public static string CreateBackup(string path)
        {
            if (!File.Exists(path))
            {
                return null;
            }

            var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            var directory = Path.GetDirectoryName(path);
            var filename = Path.GetFileNameWithoutExtension(path);
            var extension = Path.GetExtension(path);

            var backupPath = Path.Combine(directory, $"{filename}_backup_{timestamp}{extension}");

            try
            {
                File.Copy(path, backupPath);
                Debug.Log($"[ShaderCopilot] Backup created: {backupPath}");
                return backupPath;
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ShaderCopilot] Failed to create backup: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Get file info for a path.
        /// </summary>
        public static FileInfo GetFileInfo(string path)
        {
            try
            {
                return new FileInfo(path);
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// Check if a path is within the Assets folder.
        /// </summary>
        public static bool IsAssetPath(string path)
        {
            path = path.Replace("\\", "/");
            return path.StartsWith("Assets/") ||
                   path.StartsWith(Application.dataPath.Replace("\\", "/"));
        }

        /// <summary>
        /// Result of a save operation that may require confirmation.
        /// </summary>
        public class SaveResult
        {
            public bool Success { get; set; }
            public bool RequiresConfirmation { get; set; }
            public string ConfirmationMessage { get; set; }
            public string ExistingPath { get; set; }
            public string NewPath { get; set; }
            public string Error { get; set; }
        }

        /// <summary>
        /// Check if save operation would overwrite an existing file.
        /// </summary>
        /// <param name="destinationPath">Path to save to</param>
        /// <returns>SaveResult indicating if confirmation is needed</returns>
        public static SaveResult CheckSaveOperation(string destinationPath)
        {
            var fullPath = ToFullPath(destinationPath);

            if (File.Exists(fullPath))
            {
                var fileInfo = GetFileInfo(fullPath);
                var size = fileInfo?.Length ?? 0;
                var modTime = fileInfo?.LastWriteTime ?? DateTime.MinValue;

                return new SaveResult
                {
                    Success = false,
                    RequiresConfirmation = true,
                    ConfirmationMessage = $"File already exists:\n{destinationPath}\n\nLast modified: {modTime:g}\nSize: {size} bytes\n\nOverwrite?",
                    ExistingPath = destinationPath,
                    NewPath = destinationPath,
                };
            }

            return new SaveResult
            {
                Success = true,
                RequiresConfirmation = false,
                NewPath = destinationPath,
            };
        }

        /// <summary>
        /// Save file with optional backup of existing file.
        /// </summary>
        /// <param name="path">Destination path</param>
        /// <param name="content">Content to write</param>
        /// <param name="createBackup">Whether to backup existing file</param>
        /// <returns>SaveResult with operation status</returns>
        public static SaveResult SafeWriteFile(string path, string content, bool createBackup = true)
        {
            var fullPath = ToFullPath(path);

            try
            {
                // Create backup if file exists
                if (File.Exists(fullPath) && createBackup)
                {
                    var backupPath = CreateBackup(fullPath);
                    if (backupPath == null)
                    {
                        Debug.LogWarning("[ShaderCopilot] Could not create backup, proceeding anyway");
                    }
                }

                // Ensure directory exists
                var directory = Path.GetDirectoryName(fullPath);
                EnsureDirectoryExists(directory);

                // Write file
                File.WriteAllText(fullPath, content);

                // Refresh AssetDatabase
                AssetDatabase.Refresh();

                return new SaveResult
                {
                    Success = true,
                    RequiresConfirmation = false,
                    NewPath = path,
                };
            }
            catch (Exception ex)
            {
                return new SaveResult
                {
                    Success = false,
                    RequiresConfirmation = false,
                    Error = ex.Message,
                };
            }
        }

        /// <summary>
        /// Move or copy asset with confirmation support.
        /// </summary>
        /// <param name="sourcePath">Source asset path</param>
        /// <param name="destinationPath">Destination asset path</param>
        /// <param name="move">If true, move the asset; if false, copy it</param>
        /// <returns>SaveResult with operation status</returns>
        public static SaveResult SaveAsset(string sourcePath, string destinationPath, bool move = false)
        {
            try
            {
                var checkResult = CheckSaveOperation(destinationPath);
                if (checkResult.RequiresConfirmation)
                {
                    return checkResult;
                }

                // Ensure destination directory exists
                var destDir = Path.GetDirectoryName(ToFullPath(destinationPath));
                EnsureDirectoryExists(destDir);

                string error;
                if (move)
                {
                    error = AssetDatabase.MoveAsset(sourcePath, destinationPath);
                }
                else
                {
                    if (!AssetDatabase.CopyAsset(sourcePath, destinationPath))
                    {
                        error = "Failed to copy asset";
                    }
                    else
                    {
                        error = null;
                    }
                }

                if (!string.IsNullOrEmpty(error))
                {
                    return new SaveResult
                    {
                        Success = false,
                        Error = error,
                    };
                }

                AssetDatabase.Refresh();

                return new SaveResult
                {
                    Success = true,
                    NewPath = destinationPath,
                };
            }
            catch (Exception ex)
            {
                return new SaveResult
                {
                    Success = false,
                    Error = ex.Message,
                };
            }
        }
    }
}
