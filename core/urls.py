# urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# Import all necessary views.
# Consolidated some views from the previous version.
from .views import (
    login_view, register_view, home_view,
    profile_view, edit_profile, projects_view, add_project, edit_project, delete_project,
    posts_list_view, create_post_view, post_detail_view, # 'create_post' is now 'create_post_view'
    challenge_detail_view, logout_view, send_connection_request, remove_connection, chat_view, # Added remove_connection
    accept_connection_request, reject_connection_request, connections_view
    , message_list_view, message_detail_view, delete_message, # Renamed message_list and message_detail
    all_notifications, view_notification,
    system_dashboard, user_management, edit_user, content_review, approve_post, system_settings, # Added edit_user, approve_post
    get_messages, send_message_api, chat_list_history, like_post, unlike_post, add_comment, view_all_comments
)

urlpatterns = [
    # Root URL redirects to login
    path('', lambda request: redirect('login/')), # Using 'login/' ensures the trailing slash is handled consistently
    path('admin/', admin.site.urls),

    # Authentication URLs
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),

    # Core Application URLs
    path('home/', home_view, name='home'),

    # Profile URLs
    path('profile/<str:username>/', profile_view, name='profile_view'), # Renamed for consistency with views.py
    path('edit-profile/<str:username>/', edit_profile, name='edit_profile'),

    # Post URLs
    path('posts/', posts_list_view, name='posts_list_view'), # Renamed for clarity and consistency
    path('posts/create/', create_post_view, name='create_post_view'), # Changed to 'create_post_view'
    path('posts/<int:pk>/', post_detail_view, name='post_detail_view'), # Renamed for clarity

    # Challenge URLs
    path('challenges/<int:pk>/', challenge_detail_view, name='challenge_detail_view'), # Renamed for clarity

    # Connection URLs
    path('connect/<str:username>/', send_connection_request, name='send_connection_request'),
    path('disconnect/<str:username>/', remove_connection, name='remove_connection'), # Added route for removing connection
    path('connections/', connections_view, name='connections_view'), # Renamed for clarity
    path('connect/accept/<int:request_id>/', accept_connection_request, name='accept_connection_request'),
    path('reject-connection/<int:request_id>/', reject_connection_request, name='reject_connection_request'),

    # Messaging URLs
    path('messages/', login_required(message_list_view), name='message_list_view'), # Renamed for consistency
    path('messages/<int:message_id>/', login_required(message_detail_view), name='message_detail_view'), # Renamed for consistency
    path('messages/<int:message_id>/delete/', login_required(delete_message), name='delete_message'),
    path('message/<str:username>/', chat_view, name='chat_view'),
    path('messages/', chat_list_history, name='chat_list_history'),

    # Post Action URLs
    path('like/<int:post_id>/', like_post, name='like_post'),
    path('unlike/<int:post_id>/', unlike_post, name='unlike_post'),
    path('comment/<int:post_id>/', add_comment, name='add_comment'),
    path('comments/<int:post_id>/all/', view_all_comments, name='view_all_comments'),


    # Add/Confirm this API URL for fetching messages
    path('api/messages/<str:recipient_username>/', get_messages, name='api_get_messages'),
    path('api/messages/<str:recipient_username>/send/', send_message_api, name='api_send_message'),

    # Project URLs
    path('projects/<str:username>/', login_required(projects_view), name='projects_view'), # Renamed for consistency
    path('projects/add/', login_required(add_project), name='add_project'),
    path('projects/<int:project_id>/edit/', login_required(edit_project), name='edit_project'),
    path('projects/<int:project_id>/delete/', login_required(delete_project), name='delete_project'),

    # Notification URLs
    path('notifications/', all_notifications, name='all_notifications'),
    path('notifications/<int:notification_id>/', view_notification, name='view_notification'), # Path changed for consistency

    # System (superuser) routes
    path('system/', include([
        path('', system_dashboard, name='system_dashboard'),
        path('users/', user_management, name='user_management'),
        path('users/<int:user_id>/edit/', edit_user, name='edit_user'), # Added edit_user route
        path('content/', content_review, name='content_review'),
        path('content/posts/<int:post_id>/approve/', approve_post, name='approve_post'), # Added approve_post route
        path('settings/', system_settings, name='system_settings'),
    ])),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)