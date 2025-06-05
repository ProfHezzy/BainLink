document.addEventListener('DOMContentLoaded', function() {
    // Initialize tab functionality
    const profileTabs = new bootstrap.Tab(document.getElementById('posts-tab'));
    
    // Load more posts functionality
    const loadMoreBtn = document.getElementById('loadMorePosts');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function() {
            const page = this.dataset.page;
            const username = '{{ profile_user.username }}';
            const loadingText = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
            
            this.innerHTML = loadingText;
            this.disabled = true;
            
            fetch(`/profile/${username}/?page=${page}`)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newPosts = doc.getElementById('postsContainer').innerHTML;
                    const newLoadMoreBtn = doc.getElementById('loadMorePosts');
                    
                    document.getElementById('postsContainer').insertAdjacentHTML('beforeend', newPosts);
                    
                    if (newLoadMoreBtn) {
                        this.dataset.page = parseInt(page) + 1;
                        this.innerHTML = 'Load More Posts';
                        this.disabled = false;
                    } else {
                        this.remove();
                    }
                })
                .catch(error => {
                    console.error('Error loading more posts:', error);
                    this.innerHTML = 'Error loading posts';
                });
        });
    }
    
    // Edit cover photo modal
    const editCoverBtn = document.getElementById('editCoverBtn');
    if (editCoverBtn) {
        editCoverBtn.addEventListener('click', function() {
            const editCoverModal = new bootstrap.Modal(document.getElementById('editCoverModal'));
            editCoverModal.show();
        });
    }
    
    // Edit profile picture modal
    const editProfilePicBtn = document.getElementById('editProfilePicBtn');
    if (editProfilePicBtn) {
        editProfilePicBtn.addEventListener('click', function() {
            const editProfilePicModal = new bootstrap.Modal(document.getElementById('editProfilePicModal'));
            editProfilePicModal.show();
        });
    }
    
    // Share profile functionality
    const shareProfileBtn = document.getElementById('shareProfileBtn');
    if (shareProfileBtn) {
        shareProfileBtn.addEventListener('click', function() {
            const profileUrl = window.location.href;
            
            if (navigator.share) {
                navigator.share({
                    title: 'Check out {{ profile_user.username }}\'s profile',
                    url: profileUrl
                }).catch(err => {
                    console.log('Error sharing:', err);
                    copyToClipboard(profileUrl);
                });
            } else {
                copyToClipboard(profileUrl);
            }
        });
    }
    
    // Helper function to copy to clipboard
    function copyToClipboard(text) {
        const tempInput = document.createElement('input');
        tempInput.value = text;
        document.body.appendChild(tempInput);
        tempInput.select();
        document.execCommand('copy');
        document.body.removeChild(tempInput);
        
        // Show toast notification
        const toast = new bootstrap.Toast(document.getElementById('shareToast'));
        toast.show();
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Handle form submissions with AJAX
    document.querySelectorAll('.ajax-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const form = this;
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            submitBtn.disabled = true;
            
            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        location.reload();
                    }
                } else {
                    alert(data.error || 'An error occurred');
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred');
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        });
    });
});