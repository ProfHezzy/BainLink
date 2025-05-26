from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    User, Profile, Subject, Post, Challenge, 
    Opportunity, Comment, Submission
)
from .models import User
from django.core.validators import URLValidator

# Authentication Forms
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your email address'
    }))
    role = forms.ChoiceField(choices=User.USER_ROLES, widget=forms.Select(attrs={
        'class': 'form-select'
    }))

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use.")
        return email

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role')

# Profile Forms
class ProfileForm(forms.ModelForm):
    skills = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Comma-separated list (e.g., Python, Debate, Machine Learning)'
        })
    )
    
    class Meta:
        model = Profile
        fields = [
            'profile_pic', 'bio', 'education_level', 
            'institution', 'graduation_year', 'location',
            'website', 'linkedin', 'github', 'skills', 'achievements'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'education_level': forms.Select(attrs={'class': 'form-select'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'graduation_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1900,
                'max': 2100
            }),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'github': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username'
            }),
            'achievements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List your notable achievements'
            }),
        }

    def clean_graduation_year(self):
        year = self.cleaned_data.get('graduation_year')
        if year and (year < 1900 or year > 2100):
            raise ValidationError("Please enter a valid year between 1900-2100")
        return year

    def clean_linkedin(self):
        linkedin = self.cleaned_data.get('linkedin')
        if linkedin and 'linkedin.com' not in linkedin:
            raise ValidationError("Please enter a valid LinkedIn URL")
        return linkedin

# Content Forms
from django.core.validators import FileExtensionValidator
class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Show all subjects ordered by name, regardless of user
        self.fields['subject'].queryset = Subject.objects.all().order_by('name')

    class Meta:
        model = Post
        fields = ['title', 'content', 'content_type', 'subject', 'video_url', 'document', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a descriptive title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write your content here...'
            }),
            'content_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_subject'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=...'
            }),
        }
        labels = {
            'video_url': 'YouTube/Vimeo URL',
            'document': 'PDF/Document (optional)',
            'image': 'Featured Image (optional)'
        }

    document = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt'
        }),
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'txt']
        )]
    )
    
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    def clean_video_url(self):
        url = self.cleaned_data.get('video_url')
        if url:
            if not any(domain in url for domain in ['youtube.com', 'youtu.be', 'vimeo.com']):
                raise ValidationError("Only YouTube and Vimeo URLs are supported")
        return url
    
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        video_url = cleaned_data.get('video_url')
        
        if content_type == 'video' and not video_url:
            raise ValidationError("Video URL is required for video content type")
        
        return cleaned_data

class ChallengeForm(forms.ModelForm):
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )

    class Meta:
        model = Challenge
        fields = [
            'title', 'description', 'subject', 'difficulty',
            'prize', 'prize_value', 'start_date', 'end_date',
            'max_participants', 'rules'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'prize': forms.TextInput(attrs={'class': 'form-control'}),
            'prize_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'rules': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise ValidationError("End date must be after start date")
        
        if end_date and end_date <= timezone.now():
            raise ValidationError("End date must be in the future")
        
        return cleaned_data

class OpportunityForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )

    class Meta:
        model = Opportunity
        fields = [
            'title', 'description', 'opportunity_type',
            'subject', 'eligibility', 'deadline', 'link'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'opportunity_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'eligibility': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Who can apply?'
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://'
            }),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline <= timezone.now():
            raise ValidationError("Deadline must be in the future")
        return deadline

# Interaction Forms
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Write your comment...'
            })
        }
        labels = {
            'content': ''
        }

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Explain your solution...'
            }),
        }
        labels = {
            'file': 'Supporting File (optional)',
            'content': 'Your Solution'
        }

# Subject Form
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description', 'parent', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Font Awesome icon class (e.g., fa-math)'
            }),
        }

# Search Forms
class PostSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search posts...'
        })
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    content_type = forms.ChoiceField(
        choices=Post.CONTENT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class UserSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search users...'
        })
    )
    role = forms.ChoiceField(
        choices=User.USER_ROLES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    education_level = forms.ChoiceField(
        choices=Profile.EDUCATION_LEVELS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'is_active', 'is_verified']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

class SystemSettingsForm(forms.Form):
    site_name = forms.CharField(max_length=100)
    maintenance_mode = forms.BooleanField(required=False)
    logo = forms.ImageField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['site_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['maintenance_mode'].widget.attrs.update({'class': 'form-check-input'})



from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_pic', 'bio', 'location', 'birth_date']  # Add your actual profile fields