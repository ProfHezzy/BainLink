from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    login_view, register_view, posts_view, posts_list_view, 
    create_post_view, post_detail_view, challenge_detail_view, 
    home_view, profile_view, logout_view, 
    system_dashboard, user_management, content_review, system_settings, edit_profile, create_post, send_connection_request,
    all_notifications, view_notification, accept_connection_request, reject_connection_request
)
from django.shortcuts import redirect


urlpatterns = [
    path('', lambda request: redirect('login')),  # redirect root URL to 'home' view
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('home/', home_view, name='home'),
    path('register/', register_view, name='register'),
    path('profile/<str:username>/', profile_view, name='profile'),
    path('posts/', posts_list_view, name='posts'),
    path('posts/create/', create_post, name='create_post'),
    path('posts/<int:pk>/', post_detail_view, name='post_detail'),
    path('challenges/<int:pk>/', challenge_detail_view, name='challenge_detail'),
    path('edit-profile/<str:username>/', edit_profile, name='edit_profile'),
    path('connect/<str:username>/', send_connection_request, name='send_connection_request'),
    path('notifications/', all_notifications, name='all_notifications'),
    path('notification/<int:notification_id>/', view_notification, name='view_notification'),
    path('accept-connection/<int:request_id>/', accept_connection_request, name='accept_connection_request'),
    path('accept-connection/<int:request_id>/', accept_connection_request, name='accept_connection_request'),
    path('reject-connection/<int:request_id>/', reject_connection_request, name='reject_connection_request'),

    # System (superuser) routes
    path('system/', include([
        path('', system_dashboard, name='system_dashboard'),
        path('users/', user_management, name='user_management'),
        path('content/', content_review, name='content_review'),
        path('settings/', system_settings, name='system_settings'),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
