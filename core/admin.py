from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import (
    User, Profile, Subject, Connection, ConnectionRequest,
    Notification, Post, Comment, Message, Project,
    Experience, Education, Skill, Challenge,
    Opportunity, Badge, UserBadge, Submission
)

# Customize the User admin
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_staff')
    search_fields = ('username', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'phone')}),
        ('Permissions', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

# Profile admin with user link
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'headline', 'education_level', 'points')
    list_filter = ('education_level',)
    search_fields = ('user__username', 'headline', 'bio')
    raw_id_fields = ('user',)

# Notification admin with content object link
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'notification_type', 'read', 'created_at')
    list_filter = ('notification_type', 'read')
    search_fields = ('recipient__username', 'sender__username', 'message')
    date_hierarchy = 'created_at'

# Message admin with conversation view
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'timestamp', 'read')
    list_filter = ('read', 'timestamp')
    search_fields = ('sender__username', 'recipient__username', 'content')
    date_hierarchy = 'timestamp'

# Project admin
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'date')
    search_fields = ('user__username', 'title', 'description')
    list_filter = ('date',)
    date_hierarchy = 'created_at'

# Connection admin
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('creator', 'friend', 'created', 'accepted')
    list_filter = ('accepted', 'created')
    search_fields = ('creator__user__username', 'friend__user__username')

# Post admin with rich content display
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'title', 'content_type', 'created_at')
    list_filter = ('content_type', 'is_featured', 'is_approved')
    search_fields = ('author__user__username', 'title', 'content')
    date_hierarchy = 'created_at'
    readonly_fields = ('like_count',)

    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = 'Likes'

# Inline for skills
'''class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1'''

# Experience admin
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'position', 'company', 'start_date', 'current')
    list_filter = ('current', 'start_date')
    search_fields = ('profile__user__username', 'position', 'company')
    #inlines = [SkillInline]

# Challenge admin
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'difficulty', 'start_date', 'end_date', 'is_active')
    list_filter = ('difficulty', 'is_active', 'subject')
    search_fields = ('title', 'description', 'sponsor__username')
    date_hierarchy = 'start_date'

# Register all models
admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Subject)
admin.site.register(Connection, ConnectionAdmin)
admin.site.register(ConnectionRequest)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment)
admin.site.register(Message, MessageAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Experience, ExperienceAdmin)
admin.site.register(Education)
admin.site.register(Skill)
admin.site.register(Challenge, ChallengeAdmin)
admin.site.register(Opportunity)
admin.site.register(Badge)
admin.site.register(UserBadge)
admin.site.register(Submission)