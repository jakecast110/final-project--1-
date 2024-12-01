from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from enum import Enum


# Enumerations for Roles
class RoleChoices(Enum):
    CREATOR = "creator"
    TAKER = "taker"

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]


# Abstract Base Class for Soft Deletes
class SoftDeletableModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        """Soft delete the object."""
        self.deleted_at = now()
        self.save()

    class Meta:
        abstract = True


# User Profile to Allow Multiple Roles
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roles = models.CharField(max_length=50, choices=RoleChoices.choices(), default=RoleChoices.TAKER.value)

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


# Survey Model to Define a Survey's Basic Details
class Survey(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


# Question Model for Storing Each Question of a Survey
class Question(SoftDeletableModel):
    MULTIPLE_CHOICE = 'MC'
    CHECKBOX = 'CB'

    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (CHECKBOX, 'Checkbox'),
    ]

    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    question_text = models.CharField(max_length=255, null=True)
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['survey', 'question_text'], name='unique_question_per_survey'),
        ]

    def __str__(self):
        return self.question_text


# Option Model to Store the Options for Each Question
class Option(SoftDeletableModel):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    option_text = models.CharField(max_length=255, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='options')

    class Meta:
        ordering = ['id']  # Orders options by their creation order
        constraints = [
            models.UniqueConstraint(fields=['question', 'option_text'], name='unique_option_per_question'),
        ]

    def __str__(self):
        return self.option_text


# Response Model to Store the Responses of Survey Takers
class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.user.user.username} to {self.survey.title}"


# Answer Model for Normalized Response Storage
class Answer(models.Model):
    response = models.ForeignKey(Response, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(Option, blank=True)  # For multiple-choice or checkbox answers

    def save(self, *args, **kwargs):
        # Ensure selected options belong to the same question
        if self.selected_options.exists():
            for option in self.selected_options.all():
                if option.question != self.question:
                    raise ValidationError("All selected options must belong to the same question.")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Answer to {self.question.question_text} by {self.response.user.user.username}"
