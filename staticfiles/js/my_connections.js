document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabs = document.querySelectorAll('.connections-tabs .tab');
    const sections = document.querySelectorAll('.connections-section');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            // Show corresponding section
            const target = this.getAttribute('data-target');
            sections.forEach(section => {
                section.style.display = section.id === target ? 'block' : 'none';
            });
        });
    });

    // Initially show the 'Connections' tab and section
    const connectionsTab = document.querySelector('.connections-tabs .tab[data-target="connections"]');
    const connectionsSection = document.getElementById('connections');
    if (connectionsTab && connectionsSection) {
        connectionsTab.classList.add('active');
        connectionsSection.style.display = 'block';
    }

    // Handle connection actions within each connection list item
    document.querySelectorAll('.connection-list-item').forEach(item => {
        const viewBtn = item.querySelector('.btn-outline-primary[data-profile-url]');
        const chatBtn = item.querySelector('.btn-primary.btn-chat[data-chat-url]');
        const connectBtn = item.querySelector('.btn-primary[onclick*="send_connection_request"]'); // Select Connect button

        if (viewBtn) {
            viewBtn.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent triggering the link on the list item
                window.location.href = this.getAttribute('data-profile-url');
            });
        }

        if (chatBtn) {
            chatBtn.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent triggering the link on the list item
                window.location.href = this.getAttribute('data-chat-url');
            });
        }

        if (connectBtn) {
            connectBtn.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent triggering the link on the list item
                // The connect button already has an onclick handler, so no need to add another one here
            });
        }
    });
});