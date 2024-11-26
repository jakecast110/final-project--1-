from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


# User Profile to allow multiple roles for a user
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('creator', 'Survey Creator'),
        ('taker', 'Survey Taker'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roles = models.CharField(max_length=50, default='taker')  # Stores roles as a comma-separated string

    def add_role(self, role):
        """Add a new role to the user if it doesn't already exist."""
        role_list = self.roles.split(',')
        if role not in role_list:
            role_list.append(role)
            self.roles = ','.join(role_list)
            self.save()

    def has_role(self, role):
        """Check if the user has a specific role."""
        return role in self.roles.split(',')

    def __str__(self):
        return f"{self.user.username} - Roles: {self.roles}"


# Survey model to define a survey's basic details
class Survey(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


# Question model for storing each question of a survey
class Question(models.Model):
    MULTIPLE_CHOICE = 'MC'
    CHECKBOX = 'CB'

    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (CHECKBOX, 'Checkbox')
    ]

    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    question_text = models.CharField(max_length=255, null=True)
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES, null=True)
    updated_at = models.DateTimeField(auto_now=True)  # Tracks when the question was last updated
    deleted_at = models.DateTimeField(null=True, blank=True)  # Soft delete

    def delete(self, *args, **kwargs):
        """Soft delete the question."""
        self.deleted_at = now()
        self.save()

    def __str__(self):
        return self.question_text


# Option model to store the options for each question
class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    option_text = models.CharField(max_length=255, null=True)
    updated_at = models.DateTimeField(auto_now=True)  # Tracks when the option was last updated
    deleted_at = models.DateTimeField(null=True, blank=True)  # Soft delete
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)

    def delete(self, *args, **kwargs):
        """Soft delete the option."""
        self.deleted_at = now()
        self.save()

    def __str__(self):
        return self.option_text

    class Meta:
        ordering = ['id']  # Orders options by their creation order


# Response model to store the responses of survey takers
class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.user} to {self.survey.title}"


# Answer model for normalized response storage
class Answer(models.Model):
    response = models.ForeignKey(Response, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(Option, blank=True)  # For multiple-choice or checkbox answers

    def save(self, *args, **kwargs):
        # Ensure selected options belong to the same question

        if not self.pk:  # Check if the instance has not been saved yet
            super().save(*args, **kwargs)
            return

        if self.selected_options.exists() and not all(option.question == self.question for option in self.selected_options.all()):
            raise ValueError("All selected options must belong to the same question.")
    
    # Save again to ensure any other changes are persisted
        super().save(*args, **kwargs)
        return

    def __str__(self):
        return f"Answer to {self.question}"
