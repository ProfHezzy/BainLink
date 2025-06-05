document.addEventListener('DOMContentLoaded', function() {
    // Initialize Masonry layout for posts
    const postsFeed = document.getElementById('postsFeed');
    if (postsFeed) {
        const msnry = new Masonry(postsFeed, {
            itemSelector: '.post-card',
            columnWidth: '.post-card',
            percentPosition: true,
            transitionDuration: '0.2s'
        });
        
        // Refresh layout after images load
        imagesLoaded(postsFeed).on('progress', function() {
            msnry.layout();
        });
    }

    // Infinite scroll
    let loading = false;
    let page = 1;
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    window.addEventListener('scroll', function() {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500 && !loading) {
            loadMorePosts();
        }
    });
    
    function loadMorePosts() {
        if (loading) return;
        
        loading = true;
        loadingSpinner.classList.remove('d-none');
        page++;
        
        fetch(`/?page=${page}`)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newPosts = doc.getElementById('postsFeed').innerHTML;
                
                if (newPosts.trim() !== '') {
                    postsFeed.insertAdjacentHTML('beforeend', newPosts);
                    
                    // Initialize any new post interactions
                    initPostInteractions();
                    
                    // Refresh Masonry layout
                    if (msnry) {
                        msnry.reloadItems();
                        msnry.layout();
                    }
                } else {
                    // No more posts to load
                    window.removeEventListener('scroll', loadMorePosts);
                }
            })
            .catch(error => console.error('Error loading more posts:', error))
            .finally(() => {
                loading = false;
                loadingSpinner.classList.add('d-none');
            });
    }
    
    // Post creation modal functionality
    const postForm = document.getElementById('postForm');
    const mediaPreview = document.getElementById('mediaPreview');
    const previewContainer = document.getElementById('previewContainer');
    const fileName = document.getElementById('fileName');
    const removeMedia = document.getElementById('removeMedia');
    const addPollBtn = document.getElementById('addPollBtn');
    const pollContainer = document.getElementById('pollContainer');
    const addPollOption = document.getElementById('addPollOption');
    const addLinkBtn = document.getElementById('addLinkBtn');
    const linkPreviewContainer = document.getElementById('linkPreviewContainer');
    const linkPreview = document.getElementById('linkPreview');
    const postSubmitBtn = document.getElementById('postSubmitBtn');
    
    // Handle media uploads
    ['imageUpload', 'videoUpload', 'documentUpload'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    fileName.textContent = file.name;
                    
                    // Hide other media containers
                    pollContainer.classList.add('d-none');
                    linkPreviewContainer.classList.add('d-none');
                    
                    // Show preview based on file type
                    previewContainer.innerHTML = '';
                    if (file.type.startsWith('image/')) {
                        const img = document.createElement('img');
                        img.src = URL.createObjectURL(file);
                        img.className = 'img-fluid rounded';
                        previewContainer.appendChild(img);
                    } else if (file.type.startsWith('video/')) {
                        const video = document.createElement('video');
                        video.src = URL.createObjectURL(file);
                        video.controls = true;
                        video.className = 'img-fluid rounded';
                        previewContainer.appendChild(video);
                    } else {
                        const icon = document.createElement('i');
                        icon.className = 'bi bi-file-earmark-text-fill display-4 text-muted';
                        previewContainer.appendChild(icon);
                        const name = document.createElement('div');
                        name.textContent = file.name;
                        name.className = 'small mt-2';
                        previewContainer.appendChild(name);
                    }
                    
                    mediaPreview.classList.remove('d-none');
                }
            });
        }
    });
    
    // Remove media
    if (removeMedia) {
        removeMedia.addEventListener('click', function() {
            mediaPreview.classList.add('d-none');
            previewContainer.innerHTML = '';
            ['imageUpload', 'videoUpload', 'documentUpload'].forEach(id => {
                document.getElementById(id).value = '';
            });
        });
    }
    
    // Poll functionality
    if (addPollBtn) {
        addPollBtn.addEventListener('click', function() {
            pollContainer.classList.toggle('d-none');
            mediaPreview.classList.add('d-none');
            linkPreviewContainer.classList.add('d-none');
            
            // Clear media inputs when showing poll
            if (!pollContainer.classList.contains('d-none')) {
                ['imageUpload', 'videoUpload', 'documentUpload'].forEach(id => {
                    document.getElementById(id).value = '';
                });
            }
        });
    }
    
    if (addPollOption) {
        addPollOption.addEventListener('click', function() {
            const optionCount = document.querySelectorAll('[name^="poll_option"]').length;
            if (optionCount < 5) {
                const newOption = document.createElement('input');
                newOption.type = 'text';
                newOption.className = 'form-control mb-2';
                newOption.name = `poll_option${optionCount + 1}`;
                newOption.placeholder = `Option ${optionCount + 1}`;
                document.getElementById('pollOptions').appendChild(newOption);
            } else {
                alert('Maximum of 5 options allowed');
            }
        });
    }
    
    // Link preview functionality
    if (addLinkBtn) {
        addLinkBtn.addEventListener('click', function() {
            linkPreviewContainer.classList.toggle('d-none');
            mediaPreview.classList.add('d-none');
            pollContainer.classList.add('d-none');
            
            // Clear media inputs when showing link
            if (!linkPreviewContainer.classList.contains('d-none')) {
                ['imageUpload', 'videoUpload', 'documentUpload'].forEach(id => {
                    document.getElementById(id).value = '';
                });
            }
        });
    }
    
    // Handle link preview (simplified - in real app you'd call an API)
    const linkUrlInput = document.querySelector('[name="link_url"]');
    if (linkUrlInput) {
        linkUrlInput.addEventListener('blur', function() {
            const url = this.value;
            if (url) {
                // In a real app, you'd call your backend to fetch link metadata
                linkPreview.innerHTML = `
                    <div class="card mt-2">
                        <div class="row g-0">
                            <div class="col-md-4">
                                <img src="https://via.placeholder.com/200x150" class="img-fluid rounded-start" alt="Link preview">
                            </div>
                            <div class="col-md-8">
                                <div class="card-body">
                                    <h6 class="card-title">Example Link Title</h6>
                                    <p class="card-text small text-muted">This is an example link preview. In a real app, this would show metadata from the URL.</p>
                                    <p class="card-text"><small class="text-muted">example.com</small></p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        });
    }
    
    // Form submission with AJAX
    if (postForm) {
        postForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            postSubmitBtn.disabled = true;
            postSubmitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Posting...';
            
            const formData = new FormData(postForm);
            
            fetch(postForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Add new post to feed
                    const newPost = document.createElement('div');
                    newPost.className = 'post-card fade-in';
                    newPost.innerHTML = data.post_html;
                    postsFeed.prepend(newPost);
                    
                    // Reset form
                    postForm.reset();
                    mediaPreview.classList.add('d-none');
                    pollContainer.classList.add('d-none');
                    linkPreviewContainer.classList.add('d-none');
                    previewContainer.innerHTML = '';
                    linkPreview.innerHTML = '';
                    
                    // Close modal
                    bootstrap.Modal.getInstance(document.getElementById('createPostModal')).hide();
                    
                    // Update post count in stats
                    const postCountElement = document.querySelector('.stat-value:nth-child(2)');
                    if (postCountElement) {
                        postCountElement.textContent = parseInt(postCountElement.textContent) + 1;
                    }
                    
                    // Refresh Masonry layout
                    if (msnry) {
                        msnry.reloadItems();
                        msnry.layout();
                    }
                } else {
                    alert(data.error || 'Error creating post');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error creating post');
            })
            .finally(() => {
                postSubmitBtn.disabled = false;
                postSubmitBtn.textContent = 'Post';
            });
        });
    }
    
    // Initialize post interactions (like, comment, etc.)
    function initPostInteractions() {
        // Like buttons
        document.querySelectorAll('.like-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const postId = this.dataset.postId;
                const likeCount = this.querySelector('.like-count');
                
                fetch(`/posts/${postId}/like/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.classList.toggle('active');
                        likeCount.textContent = data.like_count;
                        
                        // Update like count in stats if it's the user's post
                        if (this.closest('.post-card').querySelector('[data-post-author]').dataset.postAuthor === '{{ user.username }}') {
                            const likeStat = document.querySelector('.stat-value:nth-child(3)');
                            if (likeStat) {
                                likeStat.textContent = parseInt(likeStat.textContent) + (data.action === 'liked' ? 1 : -1);
                            }
                        }
                    }
                });
            });
        });
        
        // Connection buttons
        document.querySelectorAll('.connect-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const userId = this.dataset.userId;
                const username = this.dataset.username;
                
                fetch(`/users/${username}/connect/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (data.action === 'requested') {
                            this.innerHTML = '<i class="bi bi-hourglass"></i>';
                            this.classList.remove('btn-outline-primary');
                            this.classList.add('btn-secondary');
                        } else if (data.action === 'connected') {
                            this.innerHTML = '<i class="bi bi-check-circle"></i>';
                            this.classList.remove('btn-outline-primary');
                            this.classList.add('btn-success');
                            this.disabled = true;
                            
                            // Update connection count in stats
                            const connectionStat = document.querySelector('.stat-value:first-child');
                            if (connectionStat) {
                                connectionStat.textContent = parseInt(connectionStat.textContent) + 1;
                            }
                        }
                    }
                });
            });
        });
    }
    
    // Initialize interactions on page load
    initPostInteractions();
    
    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});