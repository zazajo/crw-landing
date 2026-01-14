# crownie/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Choose a username'
    }))
    display_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Display name'
    }))
    
    # ADD REFERRAL FIELD
    referral_code_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Friend\'s referral code (optional)'
        }),
        label="Referral Code",
        help_text="Get 10 bonus points when you use a referral code"
    )
    
    class Meta:
        model = User
        fields = ('username', 'display_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        # Get initial data for referral code
        initial = kwargs.get('initial', {})
        referral_code = initial.pop('referral_code', None)
        if referral_code:
            initial['referral_code_input'] = referral_code
        kwargs['initial'] = initial
        
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
        
        # Set referral code from initial if provided
        if referral_code:
            self.fields['referral_code_input'].initial = referral_code

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

class QuestForm(forms.Form):
    """Form for creating/editing quests"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter quest title'
        })
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe the quest...',
            'rows': 4
        })
    )
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control select-control'
        })
    )
    
    QUEST_TYPE_CHOICES = [
        ('discord', 'Discord Activity'),
        ('social', 'Social Media'),
        ('referral', 'Referral'),
        ('daily', 'Daily Task'),
        ('special', 'Special Event'),
        ('other', 'Other'),
    ]
    quest_type = forms.ChoiceField(
        choices=QUEST_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control select-control'
        })
    )
    
    # Requirements
    required_discord_messages = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )
    
    required_discord_voice_minutes = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )
    
    required_referrals = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )
    
    required_daily_login_streak = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )
    
    # Social requirements
    required_twitter_follow = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    required_twitter_like = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    required_twitter_retweet = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    # Rewards
    reputation_reward = forms.IntegerField(
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 1000
        })
    )
    
    token_reward = forms.FloatField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0,
            'step': '0.000001'
        })
    )
    
    badge_reward = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Badge name (optional)'
        })
    )
    
    xp_reward = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )
    
    # Settings
    is_daily = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    is_recurring = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    recurrence_days = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )
    
    max_completions = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )
    
    requirements = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'JSON requirements (optional)',
            'rows': 3
        })
    )
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        if instance:
            # Populate form from Quest instance
            self.fields['title'].initial = instance.title
            self.fields['description'].initial = instance.description
            self.fields['difficulty'].initial = instance.difficulty
            self.fields['quest_type'].initial = instance.quest_type
            
            # Requirements
            self.fields['required_discord_messages'].initial = instance.required_discord_messages
            self.fields['required_discord_voice_minutes'].initial = instance.required_discord_voice_minutes
            self.fields['required_referrals'].initial = instance.required_referrals
            self.fields['required_daily_login_streak'].initial = instance.required_daily_login_streak
            
            # Social requirements
            self.fields['required_twitter_follow'].initial = instance.required_twitter_follow
            self.fields['required_twitter_like'].initial = instance.required_twitter_like
            self.fields['required_twitter_retweet'].initial = instance.required_twitter_retweet
            
            # Rewards
            self.fields['reputation_reward'].initial = instance.reputation_reward
            self.fields['token_reward'].initial = instance.token_reward
            self.fields['badge_reward'].initial = instance.badge_reward
            self.fields['xp_reward'].initial = instance.xp_reward
            
            # Settings
            self.fields['is_daily'].initial = instance.is_daily
            self.fields['is_recurring'].initial = instance.is_recurring
            self.fields['is_active'].initial = instance.is_active
            self.fields['recurrence_days'].initial = instance.recurrence_days
            self.fields['max_completions'].initial = instance.max_completions
            
            # Requirements JSON
            try:
                self.fields['requirements'].initial = json.loads(instance.requirements)
            except:
                self.fields['requirements'].initial = '{}'