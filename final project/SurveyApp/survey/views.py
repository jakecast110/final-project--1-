from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from .forms import UserRegistrationForm, SurveyForm, QuestionForm, OptionFormSet
from .models import Survey, Question, Option, Response, UserProfile

from django.contrib.auth.models import User
from .models import UserProfile

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        role = request.POST.get('role', 'taker')  # Default to 'taker'

        if form.is_valid():
            # Check if the user already exists
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(username=username, email=email)
                # Add the new role to the existing UserProfile
                user_profile = user.userprofile
                user_profile.add_role(role)
                messages.success(request, f"Role '{role}' added successfully to your account!")
                return redirect('login')
            except User.DoesNotExist:
                # If the user does not exist, create a new user and profile
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()

                # Create a new UserProfile with the selected role
                UserProfile.objects.create(user=user, roles=role)
                messages.success(request, "Registration successful! You can now log in.")
                return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()
    return render(request, 'survey/register.html', {'form': form})

# User login view with improved error feedback
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    return render(request, 'survey/login.html')

# Home view with UserProfile handling
@login_required
def home(request):
    try:
        # Retrieve the UserProfile
        profile = UserProfile.objects.get(user=request.user)

        # Ensure roles exist and are valid
        if not profile.roles:
            messages.error(request, "TEST 1. No valid role found. Please contact support.")
            return redirect('login')

        if 'Creator' in profile.roles.split(' '):
            return redirect('creator_dashboard')
        elif 'Taker' in profile.roles.split(' '):
            return redirect('taker_dashboard')
        else:
            messages.error(request, f"{profile.roles.split(' ')}. No valid role found. Please contact support.")
            return redirect('login')

    except UserProfile.DoesNotExist:
        messages.error(request, "No profile found. Please contact support.")
        return redirect('login')
    
# Creator dashboard
@login_required
def creator_dashboard(request):
    surveys = Survey.objects.filter(creator=request.user)
    return render(request, 'survey/creator_dashboard.html', {
        'surveys': surveys,
        'role': 'Survey Creator'
    })

# Taker dashboard
@login_required
def taker_dashboard(request):
    surveys = Survey.objects.filter(is_published=True)
    return render(request, 'survey/taker_dashboard.html', {
        'surveys': surveys,
        'role': 'Survey Taker',
    })

# Create a new survey
@login_required
def create_survey(request):
    if request.method == 'POST':
        survey_form = SurveyForm(request.POST)
        if survey_form.is_valid():
            survey = survey_form.save(commit=False)
            survey.creator = request.user
            survey.save()
            messages.success(request, "Survey created successfully!")
            return redirect('edit_survey', survey_id=survey.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        survey_form = SurveyForm()
    return render(request, 'survey/create_survey.html', {'survey_form': survey_form})

# Edit an existing survey
@login_required
def edit_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    question_form = QuestionForm()
    option_formset = OptionFormSet()

    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        option_formset = OptionFormSet(request.POST)

        if question_form.is_valid() and option_formset.is_valid():
            question = question_form.save(commit=False)
            question.survey = survey
            question.save()

            options = option_formset.save(commit=False)
            for option in options:
                option.question = question
                option.survey = survey
                option.save()

            messages.success(request, "Question added successfully!")
            return redirect('edit_survey', survey_id=survey.id)
        else:
            messages.error(request, "Please correct the errors below.")

    return render(request, 'survey/edit_survey.html', {
        'survey': survey,
        'question_form': question_form,
        'option_formset': option_formset,
        'questions': survey.questions.all()
    })

# Publish a survey
@login_required
def publish_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    if not survey.is_published:
        if survey.is_closed:
            survey.is_closed = False
        survey.is_published = True
        survey.save()
        messages.success(request, "Survey published successfully!")
    return redirect('creator_dashboard')

# Close a survey
@login_required
def close_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    if survey.is_published:
        survey.is_published = False
        survey.is_closed = True
        survey.save()
        messages.success(request, "Survey closed successfully.")
    return redirect('creator_dashboard')

# Republish a survey for "Wisdom of the Crowd" feature
@login_required
def republish_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    if not survey.is_published:
        survey.is_published = True
        survey.is_closed = False
        survey.save()

    questions = survey.questions.all()
    statistics = {}
    for question in questions:
        options = question.options.annotate(vote_count=Count('response'))
        statistics[question.question_text] = [
            (option.option_text, option.vote_count) for option in options
        ]

    return render(request, 'survey/republish_survey.html', {
        'survey': survey,
        'statistics': statistics
    })

# List all published surveys for Survey Takers
@login_required
def survey_list(request):
    surveys = Survey.objects.filter(is_published=True)
    return render(request, 'survey/survey_list.html', {'surveys': surveys})

# Take a survey
@login_required
def take_survey(request, survey_id):
    profile = UserProfile.objects.get(user=request.user)
    survey = get_object_or_404(Survey, id=survey_id, is_published=True)
    questions = Question.objects.filter(survey_id=survey_id)
    options = Option.objects.filter(survey_id=survey_id) 
    response = Response.objects.filter(survey_id=survey_id)
    #get list of users in responses of surveys
    users=[]
    for rsp in response:
        users.append(rsp.user_id)
    if request.user.id in users:
        return render(request, 'survey/taken_survey.html')
    return render(request, 'survey/take_survey.html', {'survey': survey, 
                                                       'questions': questions, 
                                                       'options': options, 
                                                       'profile': profile, 
                                                       'response': response,
                                                       'users':users})

# Submit survey response
@login_required
def submit_response(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, is_published=True)
    answers={}
    errors=0
    if request.method == 'POST':
        questions = survey.questions.all()
        for question in questions:
            response = request.POST.get(f'question_{question.id}') #Only grabbing one response for CB
            if response==None:
                errors+=1
            else:
                answers[question.id] = response
        if errors>0:
            messages.error(request, "Please select at least one answer.")
            return redirect('take_survey', survey_id=survey_id)
        Response.objects.create(survey=survey, user=request.user.userprofile, answers=answers)
        messages.success(request, "Survey response submitted successfully!")
        return redirect('taker_dashboard')
    return redirect('take_survey', survey_id=survey_id)

# View results for a survey
@login_required
def view_results(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    questions = survey.questions.all()
    statistics = {}

    for question in questions:
        options = question.options.annotate(vote_count=Count('response'))
        total_responses = sum(option.vote_count for option in options)
        statistics[question.question_text] = [
            (option.option_text, option.vote_count, (option.vote_count / total_responses) * 100 if total_responses else 0)
            for option in options
        ]

    return render(request, 'survey/results.html', {
        'survey': survey,
        'statistics': statistics
    })

# Logout user
@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')