document.addEventListener('DOMContentLoaded', function() {
    console.log("Home.js loaded!"); // Confirm JS is running

    // Event delegation for Like button clicks
    document.addEventListener('click', function(e) {
        const likeButton = e.target.closest('.like-button');
        if (likeButton) {
            const postId = likeButton.getAttribute('data-post-id');
            const isLiked = likeButton.classList.contains('active');
            const url = isLiked ? `/unlike/${postId}/` : `/like/${postId}/`;

            console.log("Like button clicked for post ID: ", postId); // Debug log

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        likeButton.classList.toggle('active');
                        const icon = likeButton.querySelector('i');
                        icon.classList.toggle('bi-hand-thumbs-up');
                        icon.classList.toggle('bi-hand-thumbs-up-fill');
                        // Optional: Update like count display if you have one
                    } else {
                        console.error('Failed to like/unlike post:', data.error);
                    }
                })
                .catch(err => {
                    console.error('Fetch error: ', err);
                });
        }
    });

    // Event delegation for Comment toggle button
    document.addEventListener('click', function(e) {
        const commentToggle = e.target.closest('.comment-toggle');
        if (commentToggle) {
            const postId = commentToggle.getAttribute('data-post-id');
            const commentsSection = document.getElementById(`comments-${postId}`);
            if (commentsSection) {
                commentsSection.style.display = commentsSection.style.display === 'none' ? 'block' : 'none';
            }
        }
    });

    // Event delegation for Share button
    document.addEventListener('click', function(e) {
        const shareButton = e.target.closest('.share-button');
        if (shareButton) {
            const postId = shareButton.getAttribute('data-post-id');
            const postUrl = window.location.origin + `/post/${postId}/`;
            navigator.clipboard.writeText(postUrl)
                .then(() => alert('Link copied to clipboard!'))
                .catch(err => console.error('Failed to copy link: ', err));
        }
    });

    // Event delegation for Comment submit button
    document.addEventListener('click', function(e) {
        const commentSubmit = e.target.closest('.comment-submit');
        if (commentSubmit) {
            const postId = commentSubmit.getAttribute('data-post-id');
            const commentInput = document.querySelector(`.comment-input[data-post-id="${postId}"]`);
            const commentText = commentInput.value.trim();
            const commentList = document.querySelector(`#comments-${postId} .comment-list`);

            if (commentText) {
                fetch(`/comment/${postId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ text: commentText }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.comment_html) {
                        commentList.innerHTML = data.comment_html + commentList.innerHTML;
                        commentInput.value = '';
                    } else {
                        console.error('Failed to post comment:', data.error);
                    }
                });
            }
        }
    });

    // Helper: Get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = cookie.substring(name.length + 1);
                    break;
                }
            }
        }
        return cookieValue;
    }
});
