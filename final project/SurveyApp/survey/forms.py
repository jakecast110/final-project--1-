from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile, Survey, Question, Option


# User Registration Form with role selection
class UserRegistrationForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('Survey Creator', 'creator'),
        ('Survey Taker', 'taker'),
    ]

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        label="Password",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Re-enter Password'}),
        label="Re-enter Password",
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label="Role",
        widget=forms.Select,
        required=True,
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Check if passwords match
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match")

        # Add password constraints
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit.")
        if not any(char.isalpha() for char in password):
            raise ValidationError("Password must contain at least one letter.")
        if not any(char in '!@#$%^&*()-_+=' for char in password):
            raise ValidationError(
                "Password must contain at least one special character (!@#$%^&*()-_+=)."
            )

        return cleaned_data


# Survey Form for creating or editing surveys
class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter survey title'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter survey description'}),
        }


# Question Form for creating or editing questions
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type']
        widgets = {
            'question_text': forms.TextInput(attrs={'placeholder': 'Enter question text'}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
        }


# Inline formset for managing options of a question
OptionFormSet = forms.inlineformset_factory(
    Question,
    Option,
    fields=('option_text',),
    extra=3,  # Adjust the number of empty forms to display
    can_delete=True,
    widgets={
        'option_text': forms.TextInput(attrs={'placeholder': 'Enter option text'}),
    }
)
