from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.urls import reverse

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
        return self != other_user and not self.profile.is_connected_with(other_user.profile)


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
    
# Redefined Skill Model first, as Profile will now depend on it
class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="A specific skill (e.g., 'Python', 'Public Speaking').")

    class Meta:
        ordering = ['name']
        verbose_name = "Skill"
        verbose_name_plural = "Skills"

    def __str__(self):
        return self.name

# Redefined Profile Model
class Profile(models.Model):
    EDUCATION_LEVELS = [
        ('high_school', 'High School'),
        ('undergrad', 'Undergraduate'),
        ('masters', 'Master\'s'),
        ('phd', 'PhD'),
        ('professional', 'Professional'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile')
    profile_pic = models.ImageField(upload_to='profiles/%Y/%m/%d/', blank=True, null=True) # Added null=True for consistency
    cover_photo = models.ImageField(upload_to='cover_photos/', blank=True, null=True)
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
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

    # --- IMPORTANT CHANGE HERE: skills is now a ManyToManyField to the Skill model ---
    skills = models.ManyToManyField(
        'Skill',
        blank=True,
        related_name='profiles_with_skill', # Defines the reverse relation from Skill to Profile
        help_text="Select or add relevant skills."
    )
    # ----------------------------------------------------------------------------------

    subjects = models.ManyToManyField('Subject', blank=True, related_name='profiles_studying') # Added related_name for clarity
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
        verbose_name = "User Profile" # Added for clarity in admin
        verbose_name_plural = "User Profiles" # Added for clarity in admin

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_absolute_url(self):
        return reverse('profile_detail', kwargs={'username': self.user.username}) # Changed 'profile' to 'profile_detail' for common convention

    def get_connection_count(self):
        # This counts accepted connections for the profile
        # Note: if Connection model's 'accepted' field is used for established connections
        return Connection.objects.filter(
            Q(creator=self, accepted=True) | Q(friend=self, accepted=True)
        ).distinct().count() # Use distinct to avoid double counting if connection creation is not strictly ordered

    def get_post_count(self):
        return self.posts.count()

    def get_follower_count(self):
        # This definition of 'follower' implies non-symmetrical connections.
        # If 'Connection' is purely symmetrical, this method might be misleading.
        # Assuming 'friend' in Connection means "who accepted the request" if symmetrical means A connected to B, and B connected to A.
        # If 'Connection' is used to represent followers, this logic would be correct.
        return Connection.objects.filter(friend=self, accepted=True).count()

    

    def get_connections(self):
        # Returns all established connections (both where current profile is creator or friend)
        return Profile.objects.filter(
            Q(created_connections__friend=self, created_connections__accepted=True) |
            Q(friend_connections__creator=self, friend_connections__accepted=True)
        ).distinct()
    

    def get_pending_requests(self):
        # This will now refer to ConnectionRequest model directly, as it handles pending state
        return self.user.received_connection_requests.filter(status='pending')

    def is_connected_with(self, other_profile):
        """
        Checks if the current profile is connected with another profile.
        Assumes 'Connection' model implies an accepted, established connection.
        """
        return Connection.objects.filter(
            (Q(creator=self, friend=other_profile) | Q(creator=other_profile, friend=self)),
            accepted=True
        ).exists()

    def get_skills_display(self):
        """Returns a comma-separated string of the profile's skills."""
        return ", ".join([skill.name for skill in self.skills.all()])
    
    def get_suggested_connects(self, limit=10):
        """Returns a queryset of suggested User objects for this profile."""
        connected_user_ids = self.connections.values_list('user_id', flat=True)
        pending_sent_request_receiver_ids = self.user.sent_connection_requests.filter(status='pending').values_list('receiver_id', flat=True)
        pending_received_request_sender_ids = self.user.received_connection_requests.filter(status='pending').values_list('sender_id', flat=True)

        exclude_ids = list(connected_user_ids) + list(pending_sent_request_receiver_ids) + list(pending_received_request_sender_ids) + [self.user.id]

        suggested_users = User.objects.exclude(id__in=exclude_ids).filter(profile__isnull=False).order_by('?')[:limit]
        return suggested_users.select_related('profile')
    

class Connection(models.Model):
    creator = models.ForeignKey(Profile, related_name='created_connections', on_delete=models.CASCADE)
    friend = models.ForeignKey(Profile, related_name='friend_connections', on_delete=models.CASCADE)
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
    
    sender = models.ForeignKey(User, related_name='sent_connection_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_connection_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
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
        Notification.objects.create(
            recipient=self.receiver,
            sender=self.sender,
            message=f"{self.sender.username} wants to connect with you",
            notification_type='connection_request',
            related_object_id=self.id
        )


from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('connection_request', 'Connection Request'),
        ('connection_accepted', 'Connection Accepted'),
        ('message', 'Message'),
        ('post_like', 'Post Like'),
        ('post_comment', 'Post Comment'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.recipient.username}"
    
    def mark_as_read(self):
        self.read = True
        self.save()

    @property
    def link(self):
        # Depending on notification_type, return different URLs
        if self.notification_type == 'connection_request':
            # Example: link to the sender's profile
            return reverse('profile', kwargs={'username': self.sender.username})
        elif self.notification_type == 'connection_accepted':
            # Example: link to some connection list or sender profile
            return reverse('profile', kwargs={'username': self.sender.username})
        # Add more types as needed

        # Default fallback
        return '#'

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
    is_approved = models.BooleanField(default=False)
    video_url = models.URLField(blank=True)
    document = models.FileField(upload_to='posts/documents/%Y/%m/%d/', blank=True)
    image = models.ImageField(upload_to='posts/images/%Y/%m/%d/', blank=True)
    likes = models.ManyToManyField(Profile, related_name='liked_posts', blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author.user.username}"
    
    def get_like_count(self):
        return self.likes.count()
    
    def get_comment_count(self):
        return self.comments.count()
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})

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
    

# Your Message model
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    
    # Content can be blank/null if a message is only an attachment
    content = models.TextField(blank=True, null=True) 
    
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    # Fields for attachments
    file = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_type = models.CharField(max_length=50, null=True, blank=True) # e.g., 'image/jpeg', 'application/pdf'

    class Meta:
        ordering = ['timestamp'] # Keep messages ordered by time

    def __str__(self):
        # Provide a more descriptive string representation
        if self.content and self.file_name:
            return f"From {self.sender.username} to {self.recipient.username}: '{self.content[:30]}...' with {self.file_name}"
        elif self.content:
            return f"From {self.sender.username} to {self.recipient.username}: '{self.content[:50]}...'"
        elif self.file_name:
            return f"From {self.sender.username} to {self.recipient.username}: Attachment ({self.file_name})"
        else:
            return f"Empty message from {self.sender.username} to {self.recipient.username}"


    # Override save method to create notification for new messages
    def save(self, *args, **kwargs):
        is_new = not self.pk # Check if this is a new message being created
        super().save(*args, **kwargs) # Save the message first to get its ID
        if is_new:
            self.create_notification()

    # Helper method to create a notification
    def create_notification(self):
        notification_message = f"New message from {self.sender.username}"
        if self.file_name:
            # Shorten content for notification if both content and file exist
            display_content = self.content[:20] + '...' if self.content else ''
            inner = f': "{display_content}"' if display_content else ''
            notification_message += f"{inner} (with attachment: {self.file_name})"
        elif not self.content: # If only a file, and no explicit content
             notification_message = f"New file from {self.sender.username} ({self.file_name})"

        Notification.objects.create(
            recipient=self.recipient,
            sender=self.sender,
            notification_type='message', # Or 'new_message_with_attachment' for more specificity
            message=notification_message,
            
            # Use GenericForeignKey fields to link to the Message object
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.id
        )

    # Mark message and related notification as read
    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.save(update_fields=['read']) # Use update_fields for efficiency

            # Mark related notification(s) as read
            Notification.objects.filter(
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.id,
                recipient=self.recipient,
                read=False # Only mark unread notifications
            ).update(read=True)

    # --- Helper Properties for Frontend (accessed via API response) ---
    @property
    def file_url(self):
        """Returns the URL of the attached file."""
        if self.file:
            return self.file.url
        return None

    @property
    def is_image(self):
        """Checks if the attached file is an image."""
        return self.file_type and self.file_type.startswith('image/')

    @property
    def is_video(self):
        """Checks if the attached file is a video."""
        return self.file_type and self.file_type.startswith('video/')

    @property
    def is_audio(self):
        """Checks if the attached file is an audio file."""
        return self.file_type and self.file_type.startswith('audio/')

    @property
    def is_document(self):
        """Checks if the attached file is a common document type (PDF, Word, Excel, Text, Zip, Rar)."""
        if not self.file_type:
            return False
        doc_types = [
            'application/pdf',
            'application/msword', # .doc
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', # .docx
            'application/vnd.ms-excel', # .xls
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', # .xlsx
            'text/plain',
            'application/zip',
            'application/x-rar-compressed', # Common MIME type for .rar
            'application/vnd.rar', # Another common MIME type for .rar
            'application/x-7z-compressed', # .7z
        ]
        return self.file_type in doc_types

        
class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='project_images/', blank=True, null=True)
    link = models.URLField(blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'pk': self.pk})

class Experience(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='experiences')
    position = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.position} at {self.company}"

class Education(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.degree} from {self.institution}"


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

class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    points_required = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
    
    def __str__(self):
        return f"{self.user.user.username} - {self.badge.name}"

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