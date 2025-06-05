// your_project_name/static/js/chat.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('chat.js loaded and DOMContentLoaded fired.');

    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    
    const attachmentInput = document.getElementById('attachmentInput'); // The hidden file input
    const attachFileBtn = document.getElementById('attachFileBtn');     // The paperclip button
    const attachmentPreview = document.getElementById('attachmentPreview'); // For displaying selected file name

    // Set 'accept' attribute for a wide range of file types
    // This provides a hint to the browser's file picker
    if (attachmentInput) {
        attachmentInput.setAttribute('accept', 'image/*,video/*,audio/*,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/plain,application/zip,application/x-rar-compressed,application/vnd.rar,application/x-7z-compressed');
    }

    // Get data from hidden inputs set by Django template
    const currentUsername = document.getElementById('currentUsername')?.value;
    const recipientUsername = document.getElementById('recipientUsername')?.value;
    const csrfToken = document.getElementById('csrfToken')?.value;

    // Basic error checking for elements
    if (!chatMessages) console.error('Error: chatMessages element not found!');
    if (!messageInput) console.error('Error: messageInput element not found!');
    if (!sendMessageBtn) console.error('Error: sendMessageBtn element not found!');
    if (!attachmentInput) console.error('Error: attachmentInput element not found!');
    if (!attachFileBtn) console.error('Error: attachFileBtn element not found!');
    if (!currentUsername) console.error('Error: currentUsername not found!');
    if (!recipientUsername) console.error('Error: recipientUsername not found!');
    if (!csrfToken) console.error('Error: csrfToken not found!');
    if (!attachmentPreview) console.warn('Warning: attachmentPreview element not found! (This is for UI feedback)');


    // --- API Endpoints (UPDATE THESE WITH YOUR ACTUAL DJANGO URLS) ---
    const API_FETCH_MESSAGES_URL = `/api/messages/${recipientUsername}/`; 
    const API_SEND_MESSAGE_URL = `/api/messages/${recipientUsername}/send/`; 

    console.log('API_FETCH_MESSAGES_URL:', API_FETCH_MESSAGES_URL);
    console.log('API_SEND_MESSAGE_URL:', API_SEND_MESSAGE_URL);

    let lastMessageTimestamp = null;
    let selectedFile = null; // To store the file selected for attachment

    /**
     * Fetches messages from the API and updates the chat display.
     */
    async function fetchMessages() {
        console.log('fetchMessages function called. lastMessageTimestamp:', lastMessageTimestamp);
        try {
            const url = lastMessageTimestamp 
                ? `${API_FETCH_MESSAGES_URL}?since=${lastMessageTimestamp}` 
                : API_FETCH_MESSAGES_URL;

            const response = await fetch(url);
            console.log('Fetch messages response received:', response);

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const newMessages = await response.json();
            console.log('New messages fetched:', newMessages);

            // Remove loading spinner after first fetch
            const loadingSpinner = chatMessages.querySelector('.messages-loading');
            if (loadingSpinner) {
                loadingSpinner.remove();
            }

            if (newMessages.length > 0) {
                // Check if user is scrolled near bottom before adding new messages
                const isScrolledToBottom = chatMessages.scrollHeight - chatMessages.clientHeight <= chatMessages.scrollTop + 1;
                console.log('Is scrolled to bottom:', isScrolledToBottom);

                newMessages.forEach(msg => {
                    console.log(`Processing message ID: ${msg.id}`);
                    const messageElement = createMessageElement(msg);
                    console.log(`messageElement created:`, messageElement); // Check if it's null or an element
                    if (messageElement) { // Only append if it's a new element (not a duplicate ID)
                        console.log(`Appending message ID: ${msg.id}`);
                        chatMessages.prepend(messageElement); // Prepend for flex-direction: column-reverse
                        
                        const msgTimestamp = new Date(msg.timestamp).toISOString();
                        if (!lastMessageTimestamp || msgTimestamp > lastMessageTimestamp) {
                            lastMessageTimestamp = msgTimestamp;
                            console.log('Updated lastMessageTimestamp:', lastMessageTimestamp);
                        }
                    }
                });

                // Scroll to bottom if user was near bottom or it's the initial load
                // Or if new messages were added and we should go to the bottom
                if (isScrolledToBottom || newMessages.length > 0 && !lastMessageTimestamp) {
                    scrollToBottom();
                }
            } else {
                console.log('No new messages found.');
            }
        } catch (error) {
            console.error('Error fetching messages:', error);
            if (!chatMessages.querySelector('.error-message')) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message text-center text-danger p-3';
                errorDiv.textContent = 'Failed to load messages. Please refresh or try again later.';
                chatMessages.appendChild(errorDiv);
            }
        }
    }

    /**
     * Creates an HTML element for a single message bubble.
     * Includes a check for existing IDs to prevent duplicates.
     * @param {object} message - The message object from the API.
     * @returns {HTMLElement|null} The created message div, or null if it already exists.
     */
    function createMessageElement(message) {
        // Check if message already exists in the DOM by its unique ID
        if (document.getElementById(`message-${message.id}`)) {
            console.log(`Message with ID ${message.id} already exists, skipping.`);
            return null; // Don't create element if it's already there
        }

        const div = document.createElement('div');
        div.id = `message-${message.id}`; // Assign unique ID
        
        const isSent = message.sender_username === currentUsername;
        div.className = `message-bubble ${isSent ? 'sent' : 'received'}`;

        // Only create content P if content exists
        if (message.content) {
            const contentP = document.createElement('p');
            contentP.className = 'mb-1';
            contentP.textContent = message.content; // Use textContent to prevent XSS
            div.appendChild(contentP);
        }

        // Display attachment if message has one
        if (message.file_url && message.file_name) {
            const fileContainer = document.createElement('div');
            fileContainer.className = 'attachment-display mb-1';

            // Image preview
            if (message.is_image) {
                const imgPreview = document.createElement('img');
                imgPreview.src = message.file_url;
                imgPreview.alt = message.file_name;
                imgPreview.style.maxWidth = '100%';
                imgPreview.style.height = 'auto';
                imgPreview.style.borderRadius = '8px';
                imgPreview.style.marginTop = '5px';
                fileContainer.appendChild(imgPreview);
            } 
            // Video preview
            else if (message.is_video) {
                const videoPreview = document.createElement('video');
                videoPreview.src = message.file_url;
                videoPreview.controls = true;
                videoPreview.style.maxWidth = '100%';
                videoPreview.style.height = 'auto';
                videoPreview.style.borderRadius = '8px';
                videoPreview.style.marginTop = '5px';
                fileContainer.appendChild(videoPreview);
            }
            // Audio preview
            else if (message.is_audio) {
                const audioPreview = document.createElement('audio');
                audioPreview.src = message.file_url;
                audioPreview.controls = true;
                audioPreview.style.maxWidth = '100%'; // Constrain audio player width
                audioPreview.style.marginTop = '5px';
                fileContainer.appendChild(audioPreview);
            }

            // Always show a downloadable link for the file
            const fileLink = document.createElement('a');
            fileLink.href = message.file_url;
            fileLink.target = '_blank'; // Open in new tab
            fileLink.download = message.file_name; // Suggest download name
            fileLink.className = 'attachment-link d-block mt-1';
            
            // Choose icon based on file type for better UX
            let fileIconClass = 'bi-file-earmark-fill'; // Default generic file icon
            if (message.is_image) fileIconClass = 'bi-image';
            else if (message.is_video) fileIconClass = 'bi-camera-video-fill';
            else if (message.is_audio) fileIconClass = 'bi-file-earmark-music-fill';
            else if (message.file_type === 'application/pdf') fileIconClass = 'bi-file-earmark-pdf-fill';
            else if (message.file_type && message.file_type.includes('wordprocessingml')) fileIconClass = 'bi-file-earmark-word-fill';
            else if (message.file_type && message.file_type.includes('spreadsheetml')) fileIconClass = 'bi-file-earmark-excel-fill';
            else if (message.file_type && message.file_type.includes('zip') || message.file_type && message.file_type.includes('rar')) fileIconClass = 'bi-file-earmark-zip-fill';


            fileLink.innerHTML = `<i class="bi ${fileIconClass} me-1"></i> ${message.file_name}`; 
            
            fileContainer.appendChild(fileLink);
            div.appendChild(fileContainer);
        }


        const timestampSmall = document.createElement('small');
        const date = new Date(message.timestamp);
        timestampSmall.className = 'message-timestamp d-block text-end';
        timestampSmall.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' + date.toLocaleDateString();

        div.appendChild(timestampSmall);
        return div;
    }

    /**
     * Scrolls the chat message history to the very bottom.
     */
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
        console.log('Scrolled to bottom.');
    }

    /**
     * Sends a new message via AJAX POST request.
     * Handles both text content and file attachments.
     */
    async function sendMessage() {
        console.log('sendMessage function called.');
        const content = messageInput.value.trim();
        
        // If no content and no file, warn and return
        if (content === '' && !selectedFile) {
            console.warn('Attempted to send empty message or no file.');
            return;
        }
        console.log('Sending message with content:', content, 'and file:', selectedFile);

        messageInput.value = ''; // Clear input immediately for responsiveness
        messageInput.style.height = 'auto'; // Reset textarea height
        clearAttachmentPreview(); // Clear UI feedback for attachment

        const formData = new FormData(); // Use FormData for file uploads
        formData.append('content', content); // Append content (can be empty string)
        if (selectedFile) {
            formData.append('file', selectedFile); // Append the file
            selectedFile = null; // Clear selected file after adding to form data
        }

        try {
            const response = await fetch(API_SEND_MESSAGE_URL, {
                method: 'POST',
                headers: {
                    // 'Content-Type': 'application/json', <-- DO NOT SET THIS FOR FormData
                    'X-CSRFToken': csrfToken, // Important for Django's CSRF protection
                },
                body: formData, // Send FormData
            });
            console.log('Send message fetch response received:', response);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`HTTP error! Status: ${response.status}. Server response: ${JSON.stringify(errorData)}`);
            }

            const newMessage = await response.json();
            console.log('New message sent successfully:', newMessage);
            
            // Immediately add the sent message to the chat
            const messageElement = createMessageElement(newMessage);
            if (messageElement) { // Check if element was created (should always be for newly sent)
                chatMessages.prepend(messageElement);
                scrollToBottom();
            }
            
            // Update lastMessageTimestamp with the latest message's timestamp
            const msgTimestamp = new Date(newMessage.timestamp).toISOString();
            if (!lastMessageTimestamp || msgTimestamp > lastMessageTimestamp) {
                lastMessageTimestamp = msgTimestamp;
                console.log('Updated lastMessageTimestamp after sending:', lastMessageTimestamp);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
            messageInput.value = content; // Restore content if sending failed
            // Note: Restoring selectedFile here can be tricky as the file object might be gone.
            // For simplicity, user might need to re-select on failure.
        }
    }

    // NEW: Function to update and clear attachment preview in the UI
    function updateAttachmentPreview(file) {
        if (attachmentPreview) {
            if (file) {
                attachmentPreview.innerHTML = `
                    <span>${file.name}</span>
                    <button type="button" class="btn-close btn-close-white ms-2" aria-label="Remove attachment"></button>
                `;
                attachmentPreview.style.display = 'flex'; // Show the preview container
                const removeBtn = attachmentPreview.querySelector('.btn-close');
                if (removeBtn) {
                    removeBtn.addEventListener('click', clearAttachmentPreview);
                }
            } else {
                clearAttachmentPreview();
            }
        }
    }

    function clearAttachmentPreview() {
        if (attachmentPreview) {
            attachmentPreview.innerHTML = '';
            attachmentPreview.style.display = 'none'; // Hide the preview container
            selectedFile = null; // Clear the selected file in JS
            attachmentInput.value = ''; // Clear the file input itself (important for re-selecting same file)
            console.log('Attachment preview cleared.');
        }
    }

    // --- Event Listeners ---
    if (sendMessageBtn) {
        sendMessageBtn.addEventListener('click', function() {
            console.log('Send button clicked! Calling sendMessage().');
            sendMessage();
        });
    } else {
        console.error('Send button (sendMessageBtn) not found, cannot attach click listener.');
    }

    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) { 
                e.preventDefault(); // Prevent default Enter key behavior (new line)
                console.log('Enter key pressed in message input! Calling sendMessage().');
                sendMessage();
            }
        });

        messageInput.addEventListener('input', function() {
            // Auto-resize textarea based on content
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    } else {
        console.error('Message input (messageInput) not found, cannot attach keypress/input listeners.');
    }

    // Attachment Event Listeners
    if (attachFileBtn && attachmentInput) {
        // When the paperclip button is clicked, trigger the hidden file input's click event
        attachFileBtn.addEventListener('click', function() {
            console.log('Attach file button clicked. Triggering file input.');
            attachmentInput.click();
        });

        // When a file is selected in the hidden input
        attachmentInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                selectedFile = this.files[0]; // Get the first selected file
                console.log('File selected for attachment:', selectedFile.name, selectedFile);
                updateAttachmentPreview(selectedFile); // Update UI to show selected file name
            } else {
                clearAttachmentPreview(); // If user opens file dialog but cancels selection
            }
        });
    } else {
        console.error('Attachment button or input not found, cannot attach listeners.');
    }

    
    // NEW: Function to update and clear attachment preview in the UI
    function updateAttachmentPreview(file) {
        if (!attachmentPreview) { // Added this check for robustness
            console.warn('attachmentPreview element not found!');
            return;
        }

        if (file) {
            attachmentPreview.innerHTML = ''; // Clear previous content

            const fileNameSpan = document.createElement('span');
            fileNameSpan.textContent = file.name;
            fileNameSpan.className = 'ms-2 me-auto'; // Push close button to the right

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn-close btn-close-white ms-2';
            removeBtn.setAttribute('aria-label', 'Remove attachment');
            removeBtn.addEventListener('click', clearAttachmentPreview);

            let previewElement = null;
            let fileUrl = URL.createObjectURL(file); // Create a temporary URL for the file

            if (file.type.startsWith('image/')) {
                previewElement = document.createElement('img');
                previewElement.src = fileUrl;
                previewElement.alt = file.name;
                previewElement.style.maxWidth = '100%';
                previewElement.style.maxHeight = '150px'; // Limit preview height
                previewElement.style.objectFit = 'contain';
                previewElement.style.borderRadius = '5px';
                previewElement.style.marginBottom = '5px';
            } else if (file.type.startsWith('video/')) {
                previewElement = document.createElement('video');
                previewElement.src = fileUrl;
                previewElement.controls = true;
                previewElement.style.maxWidth = '100%';
                previewElement.style.maxHeight = '150px';
                previewElement.style.borderRadius = '5px';
                previewElement.style.marginBottom = '5px';
            } else if (file.type.startsWith('audio/')) {
                previewElement = document.createElement('audio');
                previewElement.src = fileUrl;
                previewElement.controls = true;
                previewElement.style.maxWidth = '100%'; // Audio players are typically horizontal
                previewElement.style.marginBottom = '5px';
            } else {
                // For other file types, you can show an icon or just the filename
                const iconSpan = document.createElement('span');
                let fileIconClass = 'bi-file-earmark-fill'; // Default generic file icon
                if (file.type === 'application/pdf') fileIconClass = 'bi-file-earmark-pdf-fill';
                else if (file.type.includes('wordprocessingml')) fileIconClass = 'bi-file-earmark-word-fill';
                else if (file.type.includes('spreadsheetml')) fileIconClass = 'bi-file-earmark-excel-fill';
                else if (file.type.includes('zip') || file.type.includes('rar') || file.type.includes('7z')) fileIconClass = 'bi-file-earmark-zip-fill';
                
                iconSpan.innerHTML = `<i class="bi ${fileIconClass} me-2"></i>`;
                iconSpan.className = 'me-2'; // Add some margin
                
                previewElement = document.createElement('div'); // A div to hold icon + name
                previewElement.style.display = 'flex';
                previewElement.style.alignItems = 'center';
                previewElement.appendChild(iconSpan);
                previewElement.appendChild(fileNameSpan.cloneNode(true)); // Use a clone here for display
                fileNameSpan.textContent = ''; // Clear text from main filename span if it's in previewElement
            }

            // Create a container for the file name and remove button if a preview element is present
            const infoContainer = document.createElement('div');
            infoContainer.className = 'd-flex align-items-center w-100'; // Flex for name and close btn
            infoContainer.appendChild(fileNameSpan);
            infoContainer.appendChild(removeBtn);
            
            if (previewElement) {
                attachmentPreview.appendChild(previewElement); // Add the actual preview (image, video, audio)
            }
            attachmentPreview.appendChild(infoContainer); // Add the name and remove button
            
            attachmentPreview.style.display = 'flex'; // Show the preview container
            attachmentPreview.style.flexDirection = 'column'; // Stack elements vertically
            attachmentPreview.style.alignItems = 'flex-start'; // Align content to start
            attachmentPreview.style.padding = '10px';
            attachmentPreview.style.border = '1px solid #dee2e6';
            attachmentPreview.style.borderRadius = '8px';
            attachmentPreview.style.backgroundColor = '#e9ecef';
            attachmentPreview.style.color = '#495057';
            attachmentPreview.style.marginBottom = '10px'; // Add space below preview
            
        } else {
            clearAttachmentPreview();
        }
    }

    function clearAttachmentPreview() {
        if (attachmentPreview) {
            // Revoke any created object URLs to free up memory
            const currentPreviewElement = attachmentPreview.querySelector('img, video, audio');
            if (currentPreviewElement && currentPreviewElement.src.startsWith('blob:')) {
                URL.revokeObjectURL(currentPreviewElement.src);
                console.log('Revoked Blob URL:', currentPreviewElement.src);
            }

            attachmentPreview.innerHTML = '';
            attachmentPreview.style.display = 'none'; // Hide the preview container
            selectedFile = null; // Clear the selected file in JS
            attachmentInput.value = ''; // Clear the file input itself (important for re-selecting same file)
            console.log('Attachment preview cleared.');
        }
    }

// ... (rest of your chat.js code) ...


    // --- Initial Load and Polling for real-time updates ---
    fetchMessages();
    setInterval(fetchMessages, 3000); // Poll for new messages every 3 seconds

    setTimeout(scrollToBottom, 100); // Scroll to bottom initially after a short delay
});