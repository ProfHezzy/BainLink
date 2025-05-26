from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q


# 1. First define User model
class User(AbstractUser):
    USER_ROLES = [
        ('super_super', 'Super Super User'),
        ('super', 'Super User'),
        ('admin', 'Admin'),
        ('mentor', 'Mentor'),
        ('student', 'Student'),
        ('recruiter', 'Recruiter'),
        ('sponsor', 'Sponsor'),
    ]
    role = models.CharField(max_length=20, choices=USER_ROLES, default='student')
    is_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)


    def get_unread_notification_count(self):
        return self.received_notifications.filter(is_read=False).count()
    
    def save(self, *args, **kwargs):
        if self.is_superuser and not self.role.startswith('super'):
            self.role = 'super_super' if self.is_staff else 'super'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def can_connect_with(self, other_user):
        """Check if connection is possible"""
        return (self != other_user and 
                not Connection.objects.filter(
                    Q(creator=self.profile, friend=other_user.profile) |
                    Q(creator=other_user.profile, friend=self.profile)
                ).exists())

# 2. Define Subject model
class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, 
                             null=True, blank=True, related_name='children')
    icon = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

from django.core.validators import MinValueValidator, MaxValueValidator

class Profile(models.Model):
    EDUCATION_LEVELS = [
        ('high_school', 'High School'),
        ('undergrad', 'Undergraduate'), 
        ('masters', 'Master\'s'),
        ('phd', 'PhD'),
        ('professional', 'Professional'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profiles/%Y/%m/%d/', blank=True)
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVELS, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    graduation_year = models.PositiveIntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)]
    )
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True) 
    github = models.URLField(blank=True)
    points = models.PositiveIntegerField(default=0)
    last_active = models.DateTimeField(auto_now=True)
    skills = models.TextField(blank=True)
    subjects = models.ManyToManyField('Subject', blank=True)
    achievements = models.TextField(blank=True)
    connections = models.ManyToManyField(
        'self',
        through='Connection',
        symmetrical=False,
        related_name='connected_to',
        blank=True
    )

    class Meta:
        ordering = ['-points']
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def is_connected_with(self, other_profile):
        """Check connection status with another profile"""
        return Connection.objects.filter(
            models.Q(creator=self, friend=other_profile) |
            models.Q(creator=other_profile, friend=self),
            accepted=True
        ).exists()

class Connection(models.Model):
    creator = models.ForeignKey(
        Profile,
        related_name='created_connections',
        on_delete=models.CASCADE
    )
    friend = models.ForeignKey(
        Profile, 
        related_name='friend_connections',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('creator', 'friend')
        ordering = ['-created']

    def __str__(self):
        return f"{self.creator} -> {self.friend} ({'accepted' if self.accepted else 'pending'})"

class ConnectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]
    
    sender = models.ForeignKey(
        User,
        related_name='sent_connection_requests',
        on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User,
        related_name='received_connection_requests', 
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        super().save(*args, **kwargs)
        
        if is_new and self.status == 'pending':
            self.create_notification()
    
    def create_notification(self):
        """Create notification for the connection request"""
        from .models import Notification
        
        Notification.objects.create(
            recipient=self.receiver,
            sender=self.sender,
            message=f"{self.sender.username} wants to connect with you",
            notification_type='connection_request',
            related_object_id=self.id
        )

class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        related_name='received_notifications',
        on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        User,
        related_name='sent_notifications',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=50, default='general')
    related_object_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recipient.username}"

# Post model with content types
class Post(models.Model):
    CONTENT_TYPES = [
        ('article', 'Article'),
        ('question', 'Question'),
        ('solution', 'Solution'),
        ('debate', 'Debate'),
        ('project', 'Project'),
    ]
    
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='article')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)  # For moderation
    
    # Media fields
    video_url = models.URLField(blank=True)  # Embedded videos (YouTube/Vimeo)
    document = models.FileField(upload_to='posts/documents/%Y/%m/%d/', blank=True)
    image = models.ImageField(upload_to='posts/images/%Y/%m/%d/', blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author.user.username}"

# Challenge/Competition model
class Challenge(models.Model):
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='intermediate')
    prize = models.CharField(max_length=200)
    prize_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    sponsor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rules = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def save(self, *args, **kwargs):
        if self.end_date <= timezone.now():
            self.is_active = False
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} (Prize: {self.prize})"

# Scholarship/Opportunity model
class Opportunity(models.Model):
    OPPORTUNITY_TYPES = [
        ('scholarship', 'Scholarship'),
        ('internship', 'Internship'),
        ('competition', 'Competition'),
        ('job', 'Job'),
        ('conference', 'Conference'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPES)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    eligibility = models.TextField(blank=True)
    deadline = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    link = models.URLField()
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Opportunities"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_opportunity_type_display()}: {self.title}"

# Badge/Achievement model
class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)  # Font awesome class
    points_required = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.name

# User's Badge model
class UserBadge(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
    
    def __str__(self):
        return f"{self.user.user.username} - {self.badge.name}"

# Like/Engagement model
class Like(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
    
    def __str__(self):
        return f"{self.user.user.username} likes {self.post.title}"

# Comment model
class Comment(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.user.username} on {self.post.title}"


# Submission model for challenges
class Submission(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField()
    file = models.FileField(upload_to='submissions/%Y/%m/%d/', blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_winner = models.BooleanField(default=False)
    score = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ('challenge', 'user')
    
    def __str__(self):
        return f"{self.user.user.username}'s submission for {self.challenge.title}"



