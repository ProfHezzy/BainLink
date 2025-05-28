from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

# Import all forms
from .forms import (
    CustomUserCreationForm, PostForm, SubjectForm, PostSearchForm,
    ProfileForm, UserEditForm, MessageForm, ProjectForm, ChallengeForm,
    SubmissionForm, SystemSettingsForm # Added ChallengeForm, SubmissionForm, SystemSettingsForm from forms.py
)

# Import all models
from .models import (
    Profile, User, Post, Subject, Challenge, Submission,
    Connection, ConnectionRequest, Notification, Message, Project,
    Skill # Skill model is now separate and used by Profile
    # Assuming Experience and Education models exist based on about_view
)

# Get the custom User model
User = get_user_model()

# --- Authentication Views ---

def login_view(request):
    """
    Handles user login. Redirects authenticated users to 'home'.
    Authenticates user credentials and redirects to 'next' URL if provided and safe,
    otherwise to 'home'. Displays error message for invalid credentials.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next') # Check both POST and GET for 'next'

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    # GET request or invalid POST
    context = {
        'next': request.GET.get('next', '')
    }
    return render(request, 'registration/login.html', context)

def register_view(request):
    """
    Handles new user registration. Redirects authenticated users to 'posts'.
    Creates a new user, logs them in, and redirects to 'posts' on success.
    """
    if request.user.is_authenticated:
        return redirect('posts_list') # Redirect to posts_list, consistent with other views

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Django's UserCreationForm handles password hashing correctly.
            # No need to call authenticate again unless there's a specific post-save step that modifies password.
            login(request, user) # Log in the newly created user
            messages.success(request, f'Account created for {user.username} successfully!')
            return redirect('posts_list') # Redirect to posts_list
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@require_POST
def logout_view(request):
    """
    Logs out the current user.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# --- Profile Management Views ---

@login_required
def profile_view(request, username):
    """
    Displays a user's profile, their posts, and connection status.
    """
    # Use user__username for querying Profile through its OneToOneField with User
    profile = get_object_or_404(Profile.objects.select_related('user'), user__username=username)
    posts = Post.objects.filter(author=profile).select_related('subject').order_by('-created_at')

    is_connected = False
    connection_request_sent = False
    # Check connection status only if viewing another user's profile
    if request.user.profile != profile:
        is_connected = request.user.profile.is_connected_with(profile)
        # Check for pending request sent FROM current user TO this profile's user
        connection_request_sent = ConnectionRequest.objects.filter(
            sender=request.user,            # ConnectionRequest.sender is User
            receiver=profile.user,          # ConnectionRequest.receiver is User
            status='pending'
        ).exists()

    context = {
        'profile_user': profile, # Renamed from profile_user to profile for clarity
        'posts': posts,
        'is_connected': is_connected,
        'connection_request_sent': connection_request_sent,
        'unread_notifications_count': request.user.received_notifications.filter(read=False).count()
    }
    return render(request, 'profile.html', context)

@login_required
def edit_profile(request, username):
    """
    Allows the logged-in user to edit their own profile.
    """
    # Ensure only the profile owner can edit
    if request.user.username != username:
        messages.error(request, "You are not authorized to edit this profile.")
        return redirect('profile_view', username=username)

    profile = request.user.profile # Get the logged-in user's profile

    if request.method == 'POST':
        # Pass instance and files (for profile_pic, cover_photo)
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile_view', username=username)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        'title': f'Edit {profile.user.username}\'s Profile'
    }
    return render(request, 'profile/edit_profile.html', context) # Adjusted template path for consistency

@login_required
def about_view(request, username):
    """
    Displays the 'About' section of a user's profile, including skills, experiences, and education.
    """
    # Use user__username for querying Profile through its OneToOneField with User
    profile = get_object_or_404(Profile.objects.select_related('user').prefetch_related('skills', 'subjects'), user__username=username)

    context = {
        'profile_user': profile.user, # Keep profile_user as the User object for template consistency
        'profile': profile, # Pass the profile object directly
        'skills': profile.skills.all(), # Access skills via ManyToManyField
        'experiences': profile.experience_set.all(), # Assuming Experience model exists
        'educations': profile.education_set.all() # Assuming Education model exists
    }
    return render(request, 'profile/about.html', context)

@login_required
def projects_view(request, username):
    """
    Displays a user's projects and allows the owner to add new projects.
    """
    user = get_object_or_404(User, username=username)
    projects = Project.objects.filter(user=user).order_by('-date')
    is_owner = request.user == user

    form = None
    if is_owner:
        if request.method == 'POST':
            form = ProjectForm(request.POST, request.FILES)
            if form.is_valid():
                project = form.save(commit=False)
                project.user = request.user
                project.save()
                messages.success(request, 'Project added successfully!')
                return redirect('projects_view', username=username)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
        else:
            form = ProjectForm()

    return render(request, 'profile/projects.html', {
        'projects': projects,
        'form': form, # form is None if not owner
        'profile_user': user,
        'is_owner': is_owner
    })

# Add/Edit/Delete Project views could be combined into one (e.g., using a project_id optional parameter)
# For now, keeping separate as per original, but consolidating duplicate ProjectForm
@login_required
def add_project(request):
    """
    Allows the logged-in user to add a new project.
    """
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            messages.success(request, 'Project added successfully!')
            return redirect('projects_view', username=request.user.username)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        form = ProjectForm()

    return render(request, 'profile/add_project.html', { # Adjusted template path
        'form': form,
        'title': 'Add New Project'
    })

@login_required
def edit_project(request, project_id):
    """
    Allows the logged-in user to edit an existing project.
    """
    project = get_object_or_404(Project, id=project_id, user=request.user) # Ensures user owns the project

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('projects_view', username=request.user.username)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        form = ProjectForm(instance=project)

    return render(request, 'profile/add_project.html', { # Using same template for add/edit
        'form': form,
        'title': 'Edit Project',
        'project': project
    })

@login_required
def delete_project(request, project_id):
    """
    Allows the logged-in user to delete their project.
    """
    project = get_object_or_404(Project, id=project_id, user=request.user) # Ensures user owns the project

    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully!')
        return redirect('projects_view', username=request.user.username)

    return render(request, 'confirm_delete.html', {
        'object': project, # Pass object for generic confirm_delete template
        'message': f"Are you sure you want to delete the project '{project.title}'?"
    })

# --- Content Management Views (Posts, Challenges) ---

@login_required
def posts_list_view(request):
    """
    Displays a list of all posts, with optional subject filtering.
    """
    posts = Post.objects.all().select_related('author__user', 'subject').order_by('-created_at')
    subjects = Subject.objects.all().order_by('name')
    selected_subject = None

    subject_filter_id = request.GET.get('subject')
    if subject_filter_id:
        try:
            selected_subject = Subject.objects.get(id=subject_filter_id)
            posts = posts.filter(subject=selected_subject)
        except Subject.DoesNotExist:
            messages.error(request, "Selected subject does not exist.")
            pass # Keep all posts if subject filter is invalid

    context = {
        'posts': posts,
        'subjects': subjects,
        'selected_subject': selected_subject
    }
    return render(request, 'posts/list.html', context)

@login_required
def create_post_view(request):
    """
    Allows a user to create a new post.
    """
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user) # Pass user for PostForm's init
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user.profile # Post.author is ForeignKey to Profile
            post.save()
            messages.success(request, 'Your post has been created successfully!')
            return redirect('post_detail_view', pk=post.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        form = PostForm(user=request.user) # Pass user for PostForm's init

    return render(request, 'posts/create.html', {
        'form': form,
        'title': 'Create New Post',
        'subjects': Subject.objects.all().order_by('name') # Ensure subjects are available for the form
    })

@login_required
def post_detail_view(request, pk):
    """
    Displays the details of a single post and increments its view count.
    """
    post = get_object_or_404(Post.objects.select_related('author__user', 'subject'), id=pk)

    # Increment views only if it's not the author viewing
    if request.user != post.author.user:
        # Assuming Post model has a 'views' PositiveIntegerField with default=0
        post.views = (post.views or 0) + 1
        post.save()

    related_posts = Post.objects.filter(subject=post.subject)\
                                .exclude(id=pk)\
                                .select_related('author__user', 'subject')\
                                .order_by('-created_at')[:3]

    return render(request, 'posts/detail.html', {
        'post': post,
        'related_posts': related_posts
    })

@login_required
def challenge_detail_view(request, pk):
    """
    Displays the details of a challenge, including submissions and time remaining.
    Allows users to submit solutions (submission handling logic is a placeholder).
    """
    challenge = get_object_or_404(Challenge.objects.select_related('subject'), id=pk)
    user_submission = None
    submission_form = None

    if request.user.is_authenticated:
        user_submission = Submission.objects.filter(
            challenge=challenge,
            user=request.user.profile # Submission.user is ForeignKey to Profile
        ).first()

    if request.method == 'POST' and challenge.is_active:
        if not user_submission: # Only allow new submission if none exists
            submission_form = SubmissionForm(request.POST, request.FILES)
            if submission_form.is_valid():
                submission = submission_form.save(commit=False)
                submission.challenge = challenge
                submission.user = request.user.profile # Submission.user is ForeignKey to Profile
                submission.save()
                messages.success(request, "Your submission has been recorded!")
                return redirect('challenge_detail_view', pk=challenge.id)
            else:
                for field, errors in submission_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
        else:
            messages.info(request, "You have already submitted for this challenge.")
    
    if not user_submission and challenge.is_active:
        submission_form = SubmissionForm() # Initialize form for new submission if allowed

    time_remaining = challenge.end_date - timezone.now() if challenge.end_date else None
    
    submissions = Submission.objects.filter(challenge=challenge)\
                                     .select_related('user__user')\
                                     .order_by('-score', 'submitted_at') # Order by score, then by submission time

    context = {
        'challenge': challenge,
        'user_submission': user_submission,
        'time_remaining': time_remaining,
        'submissions': submissions,
        'submission_form': submission_form,
        'can_submit': request.user.is_authenticated and not user_submission and challenge.is_active
    }
    return render(request, 'challenges/detail.html', context)

# --- Connection Management Views ---

@login_required
def connections_view(request):
    """
    Displays a user's confirmed connections, pending requests, and suggested connections.
    """
    user = request.user
    # Get all confirmed connections for the profile
    connections = user.profile.get_connections().select_related('user') # Select related 'user' for profiles
    
    # Get pending received connection requests for the User object
    pending_requests = ConnectionRequest.objects.filter(receiver=user, status='pending').select_related('sender')
    
    # Suggested connections: users not connected with, not self, and not having a pending request
    # Exclude current user, users already connected with, and users who sent a pending request
    # Use user.id for filtering users, and req.sender.id for pending requests (assuming sender is User FK)
    connected_user_ids = [p.user.id for p in connections]
    pending_sender_ids = [req.sender.id for req in pending_requests]

    suggested = User.objects.exclude(
        id__in=connected_user_ids + pending_sender_ids + [user.id]
    ).filter(
        # Ensure only users with a profile are suggested
        profile__isnull=False
    ).order_by('?')[:10].select_related('profile')
    
    return render(request, 'connections/connections.html', {
        'connections': connections,
        'pending_requests': pending_requests,
        'suggested_connections': suggested
    })

@login_required
def send_connection_request(request, username):
    """
    Sends a connection request from the current user to another user.
    """
    receiver_user = get_object_or_404(User, username=username)
    
    if request.user == receiver_user:
        messages.error(request, "You cannot send a connection request to yourself.")
        return redirect('profile_view', username=username)
    
    # Check if they are already connected (symmetrical check)
    if request.user.profile.is_connected_with(receiver_user.profile):
        messages.warning(request, f"You are already connected with {receiver_user.username}.")
        return redirect('profile_view', username=username)
    
    # Check if a pending request already exists (either way)
    if ConnectionRequest.objects.filter(
        (Q(sender=request.user, receiver=receiver_user) | Q(sender=receiver_user, receiver=request.user)),
        status='pending'
    ).exists():
        messages.info(request, "A connection request is already pending.")
        return redirect('profile_view', username=username)
    
    # Create the connection request (sender and receiver are User objects)
    connection_request = ConnectionRequest.objects.create(
        sender=request.user,
        receiver=receiver_user,
        status='pending'
    )
    
    # Create notification for the receiver
    Notification.objects.create(
        recipient=receiver_user, # Notification recipient is User object
        sender=request.user,    # Notification sender is User object
        message=f"{request.user.username} sent you a connection request.",
        notification_type='connection_request',
        content_type=ContentType.objects.get_for_model(connection_request),
        object_id=connection_request.id
    )
    messages.success(request, "Connection request sent successfully!")
    
    return redirect('profile_view', username=username)

@login_required
@require_POST # Ensure this is a POST request for security
def remove_connection(request, username):
    """
    Removes an existing connection between the current user and another.
    """
    user_to_remove = get_object_or_404(User, username=username)
    
    # Remove connection symmetrically
    # Find the Connection object where both profiles are involved and it's accepted
    connection_to_delete = Connection.objects.filter(
        (Q(creator=request.user.profile, friend=user_to_remove.profile) |
         Q(creator=user_to_remove.profile, friend=request.user.profile)),
        accepted=True
    ).first()

    if connection_to_delete:
        connection_to_delete.delete()
        messages.success(request, f'Removed connection with {user_to_remove.username}.')
        # Optionally, create a notification for the removed user
        Notification.objects.create(
            recipient=user_to_remove,
            sender=request.user,
            message=f"{request.user.username} has removed you from their connections.",
            notification_type='connection_removed'
        )
    else:
        messages.warning(request, f"You are not connected with {user_to_remove.username}.")

    return redirect('connections_view')


@login_required
@require_POST # Ensure this is a POST request for security
def accept_connection_request(request, request_id):
    """
    Accepts a pending connection request.
    """
    connection_request = get_object_or_404(
        ConnectionRequest,
        id=request_id,
        receiver=request.user, # Receiver is User object
        status='pending'
    )
    
    # Create the symmetrical connection in the Connection model (using Profile objects)
    Connection.objects.create(
        creator=connection_request.sender.profile, # Sender is User, get its Profile
        friend=request.user.profile,               # Requesting user is receiver, get its Profile
        accepted=True
    )
    
    # Update request status
    connection_request.status = 'accepted'
    connection_request.save()
    
    # Create acceptance notification for the sender
    Notification.objects.create(
        recipient=connection_request.sender, # Notification recipient is User object
        sender=request.user,                 # Notification sender is User object
        message=f"{request.user.username} accepted your connection request.",
        notification_type='connection_accepted',
        content_type=ContentType.objects.get_for_model(connection_request),
        object_id=connection_request.id
    )
    
    messages.success(request, "Connection request accepted!")
    return redirect('all_notifications') # Redirect to notifications list

@login_required
@require_POST # Ensure this is a POST request for security
def reject_connection_request(request, request_id):
    """
    Rejects a pending connection request.
    """
    connection_request = get_object_or_404(
        ConnectionRequest,
        id=request_id,
        receiver=request.user, # Receiver is User object
        status='pending'
    )
    
    connection_request.status = 'rejected'
    connection_request.save()
    
    # Optionally, create a rejection notification for the sender
    Notification.objects.create(
        recipient=connection_request.sender,
        sender=request.user,
        message=f"{request.user.username} declined your connection request.",
        notification_type='connection_rejected',
        content_type=ContentType.objects.get_for_model(connection_request),
        object_id=connection_request.id
    )

    messages.info(request, "Connection request declined.")
    return redirect('all_notifications') # Redirect to notifications list

# --- Messaging Views ---

'''@login_required
def send_message(request, username):
    """
    Allows a user to send a direct message to another user.
    """
    recipient_user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient_user
            message.save()
            messages.success(request, 'Message sent successfully!')
            
            # Create a notification for the recipient
            Notification.objects.create(
            recipient=recipient_user,
            sender=request.user, # The sender of the notification is the current user
            message=f"{request.user.username} sent you a message.",
            notification_type='new_message',
            # Correct way to link a related object using Generic Foreign Key:
            content_type=ContentType.objects.get_for_model(message), # Get the ContentType for the Message model
            object_id=message.id # Pass the ID of the specific message object
        )
            return redirect('profile_view', username=username) # Redirect back to the profile
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        form = MessageForm()

    return render(request, 'messages/send_message.html', {
        'form': form,
        'recipient': recipient_user
    })'''


@login_required
def chat_view(request, username): # Or a different name, if you want to keep send_message separate
    """
    Displays the chat interface for a given user.
    """
    profile_user = get_object_or_404(User, username=username)

    context = {
        'profile_user': profile_user,  # The recipient user for the chat
        # You might not need 'form' here, as the chat is primarily AJAX-driven
    }
    return render(request, 'messages/chat.html', context)


# core/views.py

from django.http import JsonResponse
from datetime import datetime
import json
from django.views.decorators.csrf import csrf_exempt # Use carefully, for API endpoints

# Assuming I have a Message model and Notification model correctly defined
# from .models import Message, Notification
# from django.contrib.contenttypes.models import ContentType # For notifications

import logging # Import logging for debug messages
logger = logging.getLogger(__name__)

# ... (other imports) ...

@login_required
def get_messages(request, recipient_username):
    logger.debug(f"get_messages called by: {request.user.username} for recipient_username: {recipient_username}")
    try:
        recipient = User.objects.get(username=recipient_username)
        logger.debug(f"Resolved recipient User object: {recipient.username}")
    except User.DoesNotExist:
        logger.warning(f"Recipient {recipient_username} not found.")
        return JsonResponse({'error': 'Recipient not found'}, status=404)

    # Base queryset for messages between current user and recipient
    messages_qs = Message.objects.filter(
        Q(sender=request.user, recipient=recipient) | Q(sender=recipient, recipient=request.user)
    ).order_by('timestamp') # Order by timestamp applies to the full set

    # Log the full base queryset before 'since' filter
    logger.debug(f"Base messages_qs count (before 'since' filter): {messages_qs.count()}")
    # Log first few messages for debugging, showing sender/recipient/content
    for msg in messages_qs[:5]: 
        logger.debug(f"  Base Message (ID:{msg.id}): Sender={msg.sender.username}, Recipient={msg.recipient.username}, Content='{msg.content[:20] if msg.content else ''}...'{' (File: ' + msg.file_name + ')' if msg.file else ''}")

    since_timestamp_str = request.GET.get('since')
    if since_timestamp_str:
        logger.debug(f"Received 'since' parameter: {since_timestamp_str}")
        try:
            since_dt = datetime.fromisoformat(since_timestamp_str.replace('Z', '+00:00'))
            logger.debug(f"Parsed 'since' datetime: {since_dt}")
            # --- CHANGE THIS LINE ---
            messages_qs = messages_qs.filter(timestamp__gte=since_dt) # Changed from gt to gte
            logger.debug(f"Applied timestamp filter. Messages count AFTER 'since' filter: {messages_qs.count()}")

        except ValueError as e:
            logger.error(f"ValueError parsing 'since' timestamp '{since_timestamp_str}': {e}")
                # If the timestamp is malformed, the filter is not applied.
                # The frontend `createMessageElement` ID check helps prevent visual duplicates.
    else:
        logger.debug("No 'since' timestamp provided, fetching initial messages.")

    message_data = []
    for msg in messages_qs: # Loop through the filtered messages
        msg_dict = {
            'id': msg.id,
            'sender_username': msg.sender.username,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(), # Essential for JS date parsing
            # Include file details in the response if a file is attached
            'file_url': msg.file_url, # Uses the @property
            'file_name': msg.file_name,
            'file_type': msg.file_type,
            'is_image': msg.is_image, # Uses the @property
            'is_video': msg.is_video, # Uses the @property
            'is_audio': msg.is_audio, # Uses the @property
            'is_document': msg.is_document, # Uses the @property
        }
        message_data.append(msg_dict)

    logger.debug(f"Returning {len(message_data)} messages in final JSON response.")
    return JsonResponse(message_data, safe=False)


import logging
logger = logging.getLogger(__name__)

@login_required
# @csrf_exempt # Consider removing this in production and relying on CSRF token
def send_message_api(request, recipient_username):
    if request.method == 'POST':
        logger.debug(f"send_message_api called. User: {request.user.username}, Recipient: {recipient_username}")
        content = request.POST.get('content', '').strip()
        uploaded_file = request.FILES.get('file')

        logger.debug(f"Content: '{content}', Uploaded File: {uploaded_file}")

        if not content and not uploaded_file:
            logger.warning("Attempted to send message with no content and no file.")
            return JsonResponse({'error': 'Message content or a file is required'}, status=400)

        try:
            recipient = User.objects.get(username=recipient_username)
            logger.debug(f"Recipient resolved: {recipient.username}")
        except User.DoesNotExist:
            logger.error(f"Recipient '{recipient_username}' not found for message sending.")
            return JsonResponse({'error': 'Recipient not found'}, status=404)

        message_fields = {
            'sender': request.user,
            'recipient': recipient,
            'content': content,
        }

        if uploaded_file:
            message_fields['file'] = uploaded_file
            message_fields['file_name'] = uploaded_file.name
            message_fields['file_type'] = uploaded_file.content_type
            logger.debug(f"File details added: Name={uploaded_file.name}, Type={uploaded_file.content_type}")

        try:
            new_message = Message.objects.create(**message_fields)
            logger.info(f"Message ID {new_message.id} created successfully.")
        except Exception as e:
            logger.exception(f"Error creating message in DB: {e}") # Use exception for full traceback
            return JsonResponse({'error': 'Failed to save message'}, status=500)

        response_data = {
            'id': new_message.id,
            'sender_username': new_message.sender.username,
            'content': new_message.content,
            'timestamp': new_message.timestamp.isoformat(),
        }

        if new_message.file:
            response_data['file_url'] = new_message.file_url
            response_data['file_name'] = new_message.file_name
            response_data['file_type'] = new_message.file_type
            response_data['is_image'] = new_message.is_image
            response_data['is_video'] = new_message.is_video
            response_data['is_audio'] = new_message.is_audio
            response_data['is_document'] = new_message.is_document
            logger.debug(f"Response data includes file URL: {new_message.file_url}")

        logger.debug(f"Sending JSON response for message ID: {new_message.id}")
        return JsonResponse(response_data, status=201)
    else:
        logger.warning(f"Invalid request method for send_message_api: {request.method}")
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def message_list_view(request):
    """
    Displays a list of all messages (sent and received) for the current user.
    Marks associated message notifications as read.
    """
    # Mark all unread message notifications as read when the message list is viewed
    unread_message_notifs = Notification.objects.filter(
        recipient=request.user,
        notification_type='message',
        read=False
    )
    unread_message_notifs.update(read=True)

    # Fetch all messages sent to or from the current user
    messages_query = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-timestamp').select_related('sender', 'recipient') # Optimize queries

    # Group messages by conversation partner for display
    # This might require more advanced logic for a proper conversation view,
    # but for a simple list, displaying distinct partners is a start.
    conversations = {}
    for msg in messages_query:
        partner = msg.sender if msg.recipient == request.user else msg.recipient
        if partner.id not in conversations:
            conversations[partner.id] = {
                'partner': partner,
                'last_message': msg,
                'unread_count': 0 # Could add complex logic here if needed
            }
        # A more sophisticated approach would involve `distinct_on` and `Max` annotations for actual last message/unread count per convo.
        # For this simple list, we'll just show the last overall message.

    context = {
        'messages': messages_query, # Raw list of all messages
        'conversations': conversations.values(), # Dictionary of last message per partner
    }
    return render(request, 'messages/message_list.html', context)


@login_required
def message_detail_view(request, message_id):
    """
    Displays a single message and marks it as read.
    Ensures the message belongs to the current user (as sender or recipient).
    """
    message = get_object_or_404(
        Message.objects.select_related('sender', 'recipient'),
        # Combine all conditions using Q objects
        Q(id=message_id) & (Q(sender=request.user) | Q(recipient=request.user))
    )

    # Mark the message as read if the current user is the recipient
    if message.recipient == request.user:
        message.read = True
        message.save()
        # Also mark any related notifications as read
        Notification.objects.filter(
            content_type=ContentType.objects.get_for_model(message),
            object_id=message.id,
            recipient=request.user,
            read=False
        ).update(read=True)

    return render(request, 'messages/message_detail.html', {'message': message})

@login_required
@require_POST
def delete_message(request, message_id):
    """
    Deletes a message. Only the recipient can delete it.
    """
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    message.delete()
    messages.success(request, 'Message deleted successfully!')
    return redirect('message_list_view')

# --- Notification Views ---

@login_required
def all_notifications(request):
    """
    Displays all notifications for the current user and marks them as read.
    Supports pagination.
    """
    notifications = request.user.received_notifications.all().order_by('-created_at')

    # Mark all visible notifications as read when the page loads
    notifications.filter(read=False).update(read=True)

    paginator = Paginator(notifications, 15) # 15 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Unread count will now be 0 after updating all on the page.
    # If you want to show total unread from the past, you'd calculate before the update.
    # For simplicity, this implies current page mark as read.
    unread_count = request.user.received_notifications.filter(read=False).count() 
    
    return render(request, 'notifications/all_notifications.html', {
        'notifications': page_obj,
        'page_obj': page_obj,
        'unread_count': unread_count, # This will typically be 0 after marking current page as read
        'is_paginated': paginator.num_pages > 1
    })



@login_required
def view_notification(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user # Only recipient can view/mark as read
    )

    # Mark as read
    if not notification.read:
        notification.read = True
        notification.save()

    # Redirect based on notification type
    # This is the section where the error is likely happening
    if notification.notification_type == 'connection_request':
        # Assuming you want to redirect to the sender's profile
        if notification.sender: # Or check notification.content_object is a User/Profile
            return redirect(reverse('profile_view', args=[notification.sender.username]))
        else:
            return redirect(reverse('connections_view')) # Or to connections list
    elif notification.notification_type == 'new_message':
        # Assuming content_object is the Message instance
        if notification.content_object and hasattr(notification.content_object, 'id'):
            return redirect(reverse('message_detail_view', args=[notification.content_object.id]))
        else:
            return redirect(reverse('message_list_view'))
    elif notification.notification_type == 'post_mention' or notification.notification_type == 'post_comment':
        # Assuming content_object is the Post instance
        if notification.content_object and hasattr(notification.content_object, 'id'):
            return redirect(reverse('post_detail_view', args=[notification.content_object.id]))
        else:
            return redirect(reverse('posts_list_view'))
    # Add more conditions for other notification types as needed

    # Default fallback if type is unknown or content object missing
    messages.info(request, "Notification viewed.")
    return redirect('home') # Fallback to home if no specific redirect

# --- Home & Dashboard Views ---

@login_required
def home_view(request):
    """
    Displays the main home feed with recent posts and suggested connections.
    """
    posts = Post.objects.all().select_related('author__user', 'subject').order_by('-created_at')

    # Suggested connections: exclude current user, and users they are already connected with
    # or have a pending request from/to.

    # Get IDs of users already connected with (using Profile.is_connected_with which checks both ways)
    connected_profiles = request.user.profile.get_connections()
    connected_user_ids = [p.user.id for p in connected_profiles]

    # Get IDs of users involved in pending requests with current user (sender or receiver)
    pending_request_user_ids = ConnectionRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='pending'
    ).values_list('sender__id', 'receiver__id')

    # Flatten the list of IDs
    pending_user_ids = [id for sublist in pending_request_user_ids for id in sublist]

    # Combine all excluded IDs and ensure uniqueness
    excluded_user_ids = list(set(connected_user_ids + pending_user_ids + [request.user.id]))

    suggested_users = User.objects.exclude(
        id__in=excluded_user_ids
    ).filter(
        profile__isnull=False # Only suggest users who have a profile
    ).order_by('?')[:5].select_related('profile') # Get 5 random suggestions

    user_statuses = {}
    for user_obj in suggested_users: # Renamed 'user' to 'user_obj' to avoid conflict with 'user = request.user'
        user_statuses[user_obj.username] = {
            'is_connected': request.user.profile.is_connected_with(user_obj.profile),
            'connection_request_sent': ConnectionRequest.objects.filter(
                sender=request.user, receiver=user_obj, status='pending'
            ).exists() # REMOVED THE TRAILING COMMA HERE!
        }

    context = {
        'posts': posts,
        'suggested_users': suggested_users,
        'user_statuses': user_statuses,
        'current_user': request.user,
        'unread_notification_count': request.user.received_notifications.filter(read=False).count()
    }
    return render(request, 'home.html', context)

# --- Admin/Superuser Views ---

def superuser_check(user):
    """
    Helper function to check if a user has 'super_super' or 'super' role.
    """
    return user.is_authenticated and user.role in ['super_super', 'super']

@user_passes_test(superuser_check, login_url='login')
def system_dashboard(request):
    """
    Displays an administrative dashboard with system statistics and recent activity.
    """
    total_users = User.objects.count()
    # Assume 'date_joined' field exists on User model
    new_users = User.objects.filter(date_joined__gte=timezone.now()-timezone.timedelta(days=7)).count()
    total_posts = Post.objects.count()
    active_challenges = Challenge.objects.filter(end_date__gt=timezone.now()).count() # Assumed logic for 'is_active'

    recent_users = User.objects.order_by('-date_joined')[:5].select_related('profile')
    recent_posts = Post.objects.order_by('-created_at')[:5].select_related('author__user', 'subject')

    context = {
        'total_users': total_users,
        'new_users': new_users,
        'total_posts': total_posts,
        'active_challenges': active_challenges,
        'recent_users': recent_users,
        'recent_posts': recent_posts,
    }
    return render(request, 'admin/system_dashboard.html', context)

@user_passes_test(superuser_check, login_url='login')
def user_management(request):
    """
    Allows superusers to view and search all users.
    """
    users_query = User.objects.all().order_by('-date_joined').select_related('profile')

    search_query = request.GET.get('q')
    if search_query:
        users_query = users_query.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__institution__icontains=search_query) |
            Q(profile__location__icontains=search_query)
        ).distinct() # Use distinct to avoid duplicate users if filtering on multiple related fields

    # Pagination
    paginator = Paginator(users_query, 25) # 25 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query or '',
        'total_users_found': users_query.count(), # Show total count of filtered users
    }
    return render(request, 'admin/user_management.html', context)

@user_passes_test(superuser_check, login_url='login')
def edit_user(request, user_id):
    """
    Allows superusers to edit user details (e.g., role, active status).
    """
    user_to_edit = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user_to_edit.username}' updated successfully.")
            return redirect('user_management')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        form = UserEditForm(instance=user_to_edit)
    
    return render(request, 'admin/edit_user.html', {
        'form': form,
        'user': user_to_edit,
        'title': f"Edit User: {user_to_edit.username}"
    })

@user_passes_test(superuser_check, login_url='login')
def content_review(request):
    """
    Provides a dashboard for superusers to review unapproved posts and pending challenge submissions.
    """
    unapproved_posts = Post.objects.filter(is_approved=False).order_by('-created_at').select_related('author__user', 'subject')
    
    # Assuming 'is_winner' signifies a final state for submissions that are reviewed.
    # Adjust logic based on your exact submission review workflow (e.g., 'status' field on Submission)
    pending_submissions = Submission.objects.filter(
        challenge__end_date__gt=timezone.now(), # Still active challenges
        # Consider adding a 'status' field to Submission (e.g., 'pending', 'reviewed')
        # For now, using is_winner as a proxy for 'not yet marked as winner'
        is_winner=False
    ).order_by('-submitted_at').select_related('challenge', 'user__user')
    
    context = {
        'unapproved_posts': unapproved_posts,
        'pending_submissions': pending_submissions,
    }
    return render(request, 'admin/content_review.html', context)

@user_passes_test(superuser_check, login_url='login')
@require_POST
def approve_post(request, post_id):
    """
    Approves a post, making it visible to other users.
    """
    post = get_object_or_404(Post, id=post_id)
    post.is_approved = True
    post.save()
    messages.success(request, f"Post '{post.title}' has been approved.")
    return redirect('content_review')

@user_passes_test(lambda u: u.role == 'super_super', login_url='login')
def system_settings(request):
    """
    Allows 'super_super' users to configure system-wide settings.
    (Note: In a real app, these settings would typically be stored in a dedicated model
    or a Django settings library rather than directly modifying settings.py from runtime).
    """
    # Placeholder for reading/writing settings from/to a database model
    # For now, we'll use a dummy 'settings_obj'
    class DummySettings:
        def __init__(self):
            self.site_name = getattr(request.session, 'site_name', 'BrainLink')
            self.maintenance_mode = getattr(request.session, 'maintenance_mode', False)
            self.logo = None # Placeholder, saving files would need storage logic
    
    settings_obj = DummySettings() # Replace with your actual SiteSettings model instance

    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, request.FILES)
        if form.is_valid():
            # In a real implementation, you would save these to your SiteSettings model instance
            settings_obj.site_name = form.cleaned_data['site_name']
            settings_obj.maintenance_mode = form.cleaned_data['maintenance_mode']
            if form.cleaned_data['logo']:
                # Handle file upload and saving here
                messages.info(request, "Logo upload functionality needs to be implemented (saving file).")
            
            # Update session for demonstration (replace with model save)
            request.session['site_name'] = settings_obj.site_name
            request.session['maintenance_mode'] = settings_obj.maintenance_mode

            messages.success(request, "System settings updated successfully (session-based).")
            return redirect('system_settings')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        initial = {
            'site_name': settings_obj.site_name,
            'maintenance_mode': settings_obj.maintenance_mode,
            # 'logo': settings_obj.logo # If you had a stored logo, pass it here
        }
        form = SystemSettingsForm(initial=initial)
    
    return render(request, 'admin/system_settings.html', {'form': form})