from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User, Profile, Subject, Post, Challenge, Opportunity

# Custom forms to handle the role field
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role')  # Include role field

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Role', {'fields': ('role',)}),  # Add role field to admin
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )

# Profile Admin (inline with User)
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

# Extend CustomUserAdmin with ProfileInline
class CompleteUserAdmin(CustomUserAdmin):
    inlines = (ProfileInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# Other Model Admins
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}  # Add slug field to your model if needed

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'subject', 'created_at')
    list_filter = ('subject', 'created_at')
    search_fields = ('title', 'content')

class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'start_date', 'end_date', 'is_active')
    list_filter = ('subject', 'difficulty', 'is_active')

class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'opportunity_type', 'deadline', 'is_active')
    list_filter = ('opportunity_type', 'subject', 'is_active')

# Register your models here
admin.site.register(User, CompleteUserAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Challenge, ChallengeAdmin)
admin.site.register(Opportunity, OpportunityAdmin)

# Customize Admin Site
admin.site.site_header = "BrainProject Administration"
admin.site.site_title = "BrainProject Admin Portal"
admin.site.index_title = "Welcome to BrainProject Admin"