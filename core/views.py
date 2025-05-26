from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, PostForm, SubjectForm, PostSearchForm, ProfileForm, UserEditForm
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Profile, User, Post, Subject, Challenge, Submission, Connection, ConnectionRequest, Notification
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.db.models import Q
from django.http import JsonResponse

from django.utils.http import url_has_allowed_host_and_scheme
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')

    # GET or invalid POST
    context = {
        'next': request.GET.get('next', '')
    }
    return render(request, 'registration/login.html', context)


@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    
    is_connected = False
    connection_request_sent = False
    
    if request.user.is_authenticated and request.user != profile_user:
        is_connected = (
            request.user.profile.connections.filter(user=profile_user).exists() or
            profile_user.profile.connections.filter(user=request.user).exists()
        )
        connection_request_sent = ConnectionRequest.objects.filter(
            sender=request.user,
            receiver=profile_user,
            status='pending'
        ).exists()
    
    context = {
        'profile_user': profile_user,
        'is_connected': is_connected,
        'connection_request_sent': connection_request_sent,
        'unread_notifications': request.user.received_notifications.filter(is_read=False) if request.user.is_authenticated else []
    }
    
    return render(request, 'profile.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user.profile
            post.save()
            messages.success(request, 'Your post has been created successfully!')
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Post'
    }
    return render(request, 'posts/create_post.html', context)


from django.shortcuts import get_object_or_404
from django.http import Http404

@login_required
def send_connection_request(request, username):
    receiver = get_object_or_404(User, username=username)
    
    # Validate request
    if request.user == receiver:
        messages.error(request, "You cannot connect with yourself")
        return redirect('profile', username=username)
    
    # Check if connection already exists
    if Connection.objects.filter(
        Q(creator=request.user.profile, friend=receiver.profile) |
        Q(creator=receiver.profile, friend=request.user.profile)
    ).exists():
        messages.warning(request, "You are already connected")
        return redirect('profile', username=username)
    
    # Create connection request
    connection_request, created = ConnectionRequest.objects.get_or_create(
        sender=request.user,
        receiver=receiver,
        defaults={'status': 'pending'}
    )
    
    if created:
        messages.success(request, "Connection request sent!")
    else:
        messages.info(request, "Request already exists")
    
    return redirect('profile', username=username)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Notification, ConnectionRequest

@login_required
def all_notifications(request):
    notifications = request.user.received_notifications.all().order_by('-created_at')
    
    # Mark all as read when visiting notifications page
    if request.GET.get('mark_read'):
        notifications.update(is_read=True)
    
    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    unread_count = request.user.received_notifications.filter(is_read=False).count()
    
    return render(request, 'notifications/all_notifications.html', {
        'notifications': page_obj,
        'page_obj': page_obj,
        'unread_count': unread_count,
        'is_paginated': paginator.num_pages > 1
    })

@login_required
def view_notification(request, notification_id):
    notification = get_object_or_404(
        Notification, 
        id=notification_id,
        recipient=request.user
    )
    
    # Mark as read when viewed
    notification.is_read = True
    notification.save()
    
    if notification.notification_type == 'connection_request':
        connection_request = get_object_or_404(
            ConnectionRequest,
            id=notification.related_object_id,
            receiver=request.user
        )
        return render(request, 'notifications/connection_request.html', {
            'connection_request': connection_request,
            'notification': notification
        })
    
    return redirect(notification.link or 'all_notifications')

@login_required
def accept_connection_request(request, request_id):
    connection_request = get_object_or_404(
        ConnectionRequest,
        id=request_id,
        receiver=request.user,
        status='pending'
    )
    
    # Create the connection
    Connection.objects.create(
        creator=connection_request.sender.profile,
        friend=request.user.profile,
        accepted=True
    )
    
    # Update request status
    connection_request.status = 'accepted'
    connection_request.save()
    
    # Create acceptance notification
    Notification.objects.create(
        recipient=connection_request.sender,
        sender=request.user,
        message=f"{request.user.username} accepted your connection request",
        notification_type='connection_accepted'
    )
    
    messages.success(request, "Connection request accepted!")
    return redirect('all_notifications')

@login_required
def reject_connection_request(request, request_id):
    connection_request = get_object_or_404(
        ConnectionRequest,
        id=request_id,
        receiver=request.user,
        status='pending'
    )
    
    connection_request.status = 'rejected'
    connection_request.save()
    
    messages.info(request, "Connection request declined")
    return redirect('all_notifications')


from django.views.decorators.http import require_POST
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
def home_view(request):
    posts = Post.objects.all().select_related('author__user').order_by('-created_at')
    
    # Suggested connections excluding current user, valid usernames and profiles
    suggested_users = User.objects.exclude(
        Q(id=request.user.id) | 
        Q(username__isnull=True) |
        Q(username__exact='') |
        Q(profile__isnull=True)
    ).order_by('?')[:5]
    
    user_statuses = {}
    for user in suggested_users:
        is_connected = (
            request.user.profile.connections.filter(user__id=user.id).exists() or
            user.profile.connections.filter(user__id=request.user.id).exists()
        )
        connection_request_sent = ConnectionRequest.objects.filter(
            sender=request.user,
            receiver=user,
            status='pending'
        ).exists()
        user_statuses[user.username] = {
            'is_connected': is_connected,
            'connection_request_sent': connection_request_sent,
        }
    
    context = {
        'posts': posts,
        'suggested_users': suggested_users,
        'user_statuses': user_statuses,
        'current_user': request.user,
        'unread_notification_count': request.user.received_notifications.filter(is_read=False).count()
    }
    
    return render(request, 'home.html', context)




def superuser_check(user):
    return user.is_authenticated and user.role in ['super_super', 'super']

@user_passes_test(superuser_check, login_url='login')
def system_dashboard(request):
    # System statistics
    total_users = User.objects.count()
    new_users = User.objects.filter(date_joined__gte=timezone.now()-timezone.timedelta(days=7)).count()
    total_posts = Post.objects.count()
    active_challenges = Challenge.objects.filter(is_active=True).count()
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_posts = Post.objects.order_by('-created_at')[:5]
    
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
    users = User.objects.all().order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # User search
    search_query = request.GET.get('q')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__institution__icontains=search_query)
        )
        paginator = Paginator(users, 25)
        page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query or '',
    }
    return render(request, 'admin/user_management.html', context)

@user_passes_test(superuser_check, login_url='login')
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} updated successfully")
            return redirect('user_management')
    else:
        form = UserEditForm(instance=user)
    
    return render(request, 'admin/edit_user.html', {'form': form, 'user': user})

@login_required
def edit_profile(request, username):
    # Only allow the logged-in user to edit their own profile
    if request.user.username != username:
        return redirect('profile', username=username)

    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=username)
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})



@user_passes_test(superuser_check, login_url='login')
def content_review(request):
    # Unapproved posts
    unapproved_posts = Post.objects.filter(is_approved=False).order_by('-created_at')
    
    # Reported content (if you have a reporting system)
    # reported_content = ReportedContent.objects.filter(resolved=False)
    
    # Challenge submissions needing review
    pending_submissions = Submission.objects.filter(
        challenge__is_active=True,
        is_winner=False
    ).order_by('-submitted_at')
    
    context = {
        'unapproved_posts': unapproved_posts,
        # 'reported_content': reported_content,
        'pending_submissions': pending_submissions,
    }
    return render(request, 'admin/content_review.html', context)

@user_passes_test(superuser_check, login_url='login')
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_approved = True
    post.save()
    messages.success(request, f"Post '{post.title}' has been approved")
    return redirect('content_review')


from django.conf import settings
from .forms import SystemSettingsForm

@user_passes_test(lambda u: u.role == 'super_super', login_url='login')
def system_settings(request):
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST)
        if form.is_valid():
            # In a real implementation, you would save these to your settings model
            messages.success(request, "System settings updated successfully")
            return redirect('system_settings')
    else:
        initial = {
            'site_name': getattr(settings, 'SITE_NAME', 'BrainLink'),
            'maintenance_mode': getattr(settings, 'MAINTENANCE_MODE', False),
        }
        form = SystemSettingsForm(initial=initial)
    
    return render(request, 'admin/system_settings.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('posts')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, f'Account created for {username}!')
            return redirect('posts')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def posts_view(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'posts/list.html', {'posts': posts})


@login_required
def posts_list_view(request):
    posts = Post.objects.all().order_by('-created_at')
    subjects = Subject.objects.all()
    selected_subject = None
    
    subject_filter = request.GET.get('subject')
    if subject_filter:
        try:
            selected_subject = Subject.objects.get(id=subject_filter)
            posts = posts.filter(subject=selected_subject)
        except Subject.DoesNotExist:
            pass
    
    context = {
        'posts': posts,
        'subjects': subjects,
        'selected_subject': selected_subject  # Now passing the object directly
    }
    return render(request, 'posts/list.html', context)


@login_required
def create_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user.profile
            post.save()
            messages.success(request, 'Your post has been created successfully!')
            return redirect('post_detail', pk=post.id)
    else:
        form = PostForm(user=request.user)
    
    return render(request, 'posts/create.html', {
        'form': form,
        'subjects': Subject.objects.all()
    })

@login_required
def post_detail_view(request, pk):
    post = get_object_or_404(Post, id=pk)
    
    # Mark as viewed (optional)
    if request.user != post.author.user:
        post.views = post.views + 1 if hasattr(post, 'views') else 1
        post.save()
    
    return render(request, 'posts/detail.html', {
        'post': post,
        'related_posts': Post.objects.filter(subject=post.subject)
            .exclude(id=pk)
            .order_by('-created_at')[:3]
    })

@login_required
def challenge_detail_view(request, pk):
    challenge = get_object_or_404(Challenge, id=pk)
    user_submission = None
    
    if request.method == 'POST' and challenge.is_active:
        # Handle submission logic here
        pass
    
    # Check if user already submitted
    if request.user.is_authenticated:
        user_submission = Submission.objects.filter(
            challenge=challenge,
            user=request.user.profile
        ).first()
    
    return render(request, 'challenges/detail.html', {
        'challenge': challenge,
        'user_submission': user_submission,
        'time_remaining': challenge.end_date - timezone.now(),
        'submissions': Submission.objects.filter(challenge=challenge)
                                      .order_by('-score')[:10]
    })