// chat_history.js
document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchInput = document.querySelector('.chat-search-input');
    const chatCards = document.querySelectorAll('.chat-card');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            chatCards.forEach(card => {
                const userName = card.querySelector('.chat-user-name').textContent.toLowerCase();
                const preview = card.querySelector('.chat-preview').textContent.toLowerCase();
                
                if (userName.includes(searchTerm) || preview.includes(searchTerm)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
    
    // Click handler for chat cards
    chatCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // If clicking on a link inside the card, don't prevent default
            if (e.target.tagName === 'A') return;
            
            // Otherwise navigate to chat
            window.location.href = this.getAttribute('data-chat-url');
        });
    });
});