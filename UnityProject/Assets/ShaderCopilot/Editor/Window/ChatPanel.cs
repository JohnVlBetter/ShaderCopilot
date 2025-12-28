using System;
using System.Text;
using UnityEngine;
using UnityEngine.UIElements;

namespace ShaderCopilot.Editor.Window
{
    public class ChatPanel : VisualElement
    {
        private ScrollView _messagesContainer;
        private TextField _inputField;
        private Button _sendButton;
        private Button _cancelButton;
        private Label _streamingLabel;
        private StringBuilder _streamingContent;

        public event Action<string> OnMessageSent;
        public event Action<string, string> OnImageAttached;
        public event Action OnCancelRequested;

        public bool IsStreaming { get; private set; }

        public ChatPanel()
        {
            BuildUI();
        }

        private void BuildUI()
        {
            style.flexGrow = 1;
            style.flexDirection = FlexDirection.Column;
            style.backgroundColor = new Color(0.16f, 0.16f, 0.16f);

            // Messages container
            _messagesContainer = new ScrollView(ScrollViewMode.Vertical);
            _messagesContainer.style.flexGrow = 1;
            _messagesContainer.style.paddingLeft = 8;
            _messagesContainer.style.paddingRight = 8;
            _messagesContainer.style.paddingTop = 8;
            Add(_messagesContainer);

            // Input area
            var inputArea = new VisualElement();
            inputArea.style.flexDirection = FlexDirection.Row;
            inputArea.style.paddingLeft = 8;
            inputArea.style.paddingRight = 8;
            inputArea.style.paddingTop = 8;
            inputArea.style.paddingBottom = 8;
            inputArea.style.borderTopWidth = 1;
            inputArea.style.borderTopColor = new Color(0.1f, 0.1f, 0.1f);

            _inputField = new TextField();
            _inputField.multiline = true;
            _inputField.style.flexGrow = 1;
            _inputField.style.minHeight = 40;
            _inputField.style.maxHeight = 120;
            _inputField.RegisterCallback<KeyDownEvent>(OnInputKeyDown);
            inputArea.Add(_inputField);

            var buttonContainer = new VisualElement();
            buttonContainer.style.flexDirection = FlexDirection.Column;
            buttonContainer.style.marginLeft = 8;

            _sendButton = new Button(SendMessage) { text = "Send" };
            _sendButton.style.marginBottom = 4;
            buttonContainer.Add(_sendButton);

            _cancelButton = new Button(CancelStreaming) { text = "Cancel" };
            _cancelButton.style.display = DisplayStyle.None;
            buttonContainer.Add(_cancelButton);

            inputArea.Add(buttonContainer);
            Add(inputArea);
        }

        private void OnInputKeyDown(KeyDownEvent evt)
        {
            if (evt.keyCode == KeyCode.Return && !evt.shiftKey)
            {
                evt.StopPropagation();
                evt.PreventDefault();

                // Delay the send to avoid text editing state issues
                _inputField.schedule.Execute(SendMessage);
            }
        }

        private void SendMessage()
        {
            var message = _inputField.value?.Trim();
            if (string.IsNullOrEmpty(message)) return;

            AddUserMessage(message);
            _inputField.SetValueWithoutNotify("");
            _inputField.Blur();
            OnMessageSent?.Invoke(message);
        }

        private void CancelStreaming()
        {
            OnCancelRequested?.Invoke();
        }

        public void AddUserMessage(string content)
        {
            AddMessage("You", content, new Color(0.2f, 0.3f, 0.4f));
        }

        public void AddAssistantMessage(string content)
        {
            AddMessage("Assistant", content, new Color(0.25f, 0.25f, 0.25f));
        }

        public void AddSystemMessage(string content)
        {
            AddMessage("System", content, new Color(0.3f, 0.25f, 0.2f));
        }

        private void AddMessage(string sender, string content, Color backgroundColor)
        {
            var messageContainer = new VisualElement();
            messageContainer.style.marginBottom = 8;
            messageContainer.style.paddingLeft = 8;
            messageContainer.style.paddingRight = 8;
            messageContainer.style.paddingTop = 6;
            messageContainer.style.paddingBottom = 6;
            messageContainer.style.backgroundColor = backgroundColor;
            messageContainer.style.borderTopLeftRadius = 8;
            messageContainer.style.borderTopRightRadius = 8;
            messageContainer.style.borderBottomLeftRadius = 8;
            messageContainer.style.borderBottomRightRadius = 8;

            var senderLabel = new Label(sender);
            senderLabel.style.fontSize = 10;
            senderLabel.style.color = new Color(0.7f, 0.7f, 0.7f);
            senderLabel.style.marginBottom = 4;
            messageContainer.Add(senderLabel);

            var contentLabel = new Label(content);
            contentLabel.style.whiteSpace = WhiteSpace.Normal;
            messageContainer.Add(contentLabel);

            _messagesContainer.Add(messageContainer);
            ScrollToBottom();
        }

        public void StartStreaming()
        {
            IsStreaming = true;
            _streamingContent = new StringBuilder();

            _sendButton.style.display = DisplayStyle.None;
            _cancelButton.style.display = DisplayStyle.Flex;

            var messageContainer = new VisualElement();
            messageContainer.name = "streaming-message";
            messageContainer.style.marginBottom = 8;
            messageContainer.style.paddingLeft = 8;
            messageContainer.style.paddingRight = 8;
            messageContainer.style.paddingTop = 6;
            messageContainer.style.paddingBottom = 6;
            messageContainer.style.backgroundColor = new Color(0.25f, 0.25f, 0.25f);
            messageContainer.style.borderTopLeftRadius = 8;
            messageContainer.style.borderTopRightRadius = 8;
            messageContainer.style.borderBottomLeftRadius = 8;
            messageContainer.style.borderBottomRightRadius = 8;

            var senderLabel = new Label("Assistant");
            senderLabel.style.fontSize = 10;
            senderLabel.style.color = new Color(0.7f, 0.7f, 0.7f);
            senderLabel.style.marginBottom = 4;
            messageContainer.Add(senderLabel);

            _streamingLabel = new Label("▌");
            _streamingLabel.style.whiteSpace = WhiteSpace.Normal;
            messageContainer.Add(_streamingLabel);

            _messagesContainer.Add(messageContainer);
            ScrollToBottom();
        }

        public void AppendStreamingContent(string content)
        {
            if (!IsStreaming || _streamingLabel == null) return;

            _streamingContent.Append(content);
            _streamingLabel.text = _streamingContent.ToString() + "▌";
            ScrollToBottom();
        }

        public void EndStreaming()
        {
            if (!IsStreaming) return;

            IsStreaming = false;

            if (_streamingLabel != null)
            {
                _streamingLabel.text = _streamingContent?.ToString() ?? "";
            }

            _streamingContent = null;
            _streamingLabel = null;

            _sendButton.style.display = DisplayStyle.Flex;
            _cancelButton.style.display = DisplayStyle.None;
        }

        public void ClearMessages()
        {
            _messagesContainer.Clear();
        }

        private void ScrollToBottom()
        {
            schedule.Execute(() =>
            {
                _messagesContainer.scrollOffset = new Vector2(0, _messagesContainer.contentContainer.layout.height);
            });
        }
    }
}
