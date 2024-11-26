from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from .forms import UserRegistrationForm, SurveyForm, QuestionForm, OptionFormSet
from .models import Survey, Question, Option, Response, Answer, UserProfile
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.contrib import messages
from django.forms import modelformset_factory



# Register a user and assign roles
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        role = request.POST.get('role', 'taker')  # Default role: Survey Taker
        print(role)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(username=username, email=email)
                user_profile = user.userprofile
                user_profile.add_role(role)
                messages.success(request, f"Role '{role}' added to your account!")
                return redirect('login')
            except User.DoesNotExist:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                UserProfile.objects.create(user=user, roles=role)
                messages.success(request, "Registration successful! Please log in.")
                return redirect('login')
        else:
            print(request.POST)
            messages.error(request, "Please correct the errors.")
    else:
        form = UserRegistrationForm()
    return render(request, 'survey/register.html', {'form': form})


# User login view
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
            messages.error(request, 'Invalid username or password.')
    return render(request, 'survey/login.html')


# Home view to redirect users based on roles
@login_required
def home(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        if 'Survey Creator' in profile.roles:
            return redirect('creator_dashboard')
        elif 'Survey Taker' in profile.roles:
            return redirect('taker_dashboard')
        else:
            messages.error(request, "No valid role found. Please contact support.")
    except UserProfile.DoesNotExist:
        messages.error(request, "Profile not found. Please contact support.")
    return redirect('login')


# Creator dashboard
@login_required
def creator_dashboard(request):
    """
    Display the creator's dashboard with all surveys created by them.
    """
    surveys = Survey.objects.filter(creator=request.user)
    for survey in surveys:
        if survey.is_closed:
            survey.status = "Closed"
        elif survey.is_published:
            survey.status = "Published"
        else:
            survey.status = "Draft"
    return render(request, 'survey/creator_dashboard.html', {
        'surveys': surveys,
        'role': 'Survey Creator'
    })



# Taker dashboard
@login_required
def taker_dashboard(request):
    surveys = Survey.objects.filter(is_published=True)
    return render(request, 'survey/taker_dashboard.html', {'surveys': surveys, 'role': 'Survey Taker'})


# Create a new survey

@login_required
def create_survey(request):
    """
    Create a survey with title and description only.
    """
    if request.method == 'POST':
        survey_form = SurveyForm(request.POST)
        if survey_form.is_valid():
            # Save the survey and redirect to the question creation page
            survey = survey_form.save(commit=False)
            survey.creator = request.user
            survey.save()
            messages.success(request, "Survey created successfully! Now add questions.")
            return redirect('add_questions', survey_id=survey.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        survey_form = SurveyForm()

    return render(request, 'survey/create_survey.html', {
        'survey_form': survey_form,
    })

@login_required
def add_questions(request, survey_id):
    """
    Add questions to an existing survey, with dynamic options.
    """
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)

    QuestionFormSet = modelformset_factory(
        Question,
        fields=['question_text', 'question_type'],
        extra=5,  # Ensure at least 5 questions initially
        can_delete=True,
    )

    if request.method == 'POST':
        question_formset = QuestionFormSet(request.POST, queryset=survey.questions.all())
        if question_formset.is_valid():
            # Save questions
            questions = question_formset.save(commit=False)
            for question in questions:
                question.survey = survey
                question.save()
            question_formset.save_m2m()
            messages.success(request, "Questions added successfully!")
            return redirect('creator_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        question_formset = QuestionFormSet(queryset=survey.questions.all())

    return render(request, 'survey/add_questions.html', {
        'survey': survey,
        'question_formset': question_formset,
    })



# Edit a survey
@login_required
def edit_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    questions = survey.questions.filter(deleted_at__isnull=True)  # Exclude soft-deleted questions
    return render(request, 'survey/edit_survey.html', {'survey': survey, 'questions': questions})


# Add or edit a question in a survey
@login_required
def edit_question(request, survey_id, question_id=None):
    """
    Handles adding or editing a question within a survey.
    Allows dynamic management of options using formsets.
    """
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    question = None

    # Fetch question if editing
    if question_id:
        question = get_object_or_404(Question, id=question_id, survey=survey)

    if request.method == 'POST':
        # Bind the form and formset with POST data
        question_form = QuestionForm(request.POST, instance=question)
        option_formset = OptionFormSet(request.POST, instance=question)

        if question_form.is_valid() and option_formset.is_valid():
            # Save the question
            question = question_form.save(commit=False)
            question.survey = survey
            question.save()

            # Save the options
            option_formset.instance = question
            option_formset.save()

            messages.success(request, "Question and options saved successfully!")
            return redirect('edit_survey', survey_id=survey.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Initialize the form and formset for GET requests
        question_form = QuestionForm(instance=question)
        option_formset = OptionFormSet(instance=question)

    return render(request, 'survey/edit_question.html', {
        'survey': survey,
        'question_form': question_form,
        'option_formset': option_formset,
    })


# Delete (soft delete) a question
@login_required
def delete_question(request, survey_id, question_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    question = get_object_or_404(Question, id=question_id, survey=survey)
    if request.method == 'POST':
        question.delete()  # Soft delete
        messages.success(request, "Question deleted successfully.")
        return redirect('edit_survey', survey_id=survey.id)
    return render(request, 'survey/confirm_delete.html', {'question': question})


# Publish a survey
@login_required
def publish_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    survey.is_published = True
    survey.is_closed = False
    survey.save()
    messages.success(request, "Survey published successfully!")
    return redirect('creator_dashboard')


# Close a survey
@login_required
def close_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    survey.is_published = False
    survey.is_closed = True
    survey.save()
    messages.success(request, "Survey closed successfully.")
    return redirect('creator_dashboard')

from django.db.models import Count

from django.db.models import Count, Q

@login_required
def republish_survey(request, survey_id):
    """
    Reopen a closed survey by republishing it with aggregated statistics for "Wisdom of the Crowd."
    """
    # Fetch the survey
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user, is_closed=True)

    # Update survey status to republished
    survey.is_published = True
    survey.is_closed = False
    survey.save()

    # Calculate aggregated statistics for each question
    questions = survey.questions.filter(deleted_at__isnull=True)
    statistics = {}
    for question in questions:
        options = question.options.filter(deleted_at__isnull=True).annotate(
            vote_count=Count('answer__response', distinct=True)  # Count the number of responses per option
        )
        statistics[question.question_text] = [
            (option.option_text, option.vote_count) for option in options
        ]

    return render(request, 'survey/republish_survey.html', {
        'survey': survey,
        'statistics': statistics,
    })



# View survey results

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

@login_required
def survey_list(request):
    survey = Survey.objects.filter(is_published=True)
    return render(request, 'survey/survey_list.html', {'surveys':survey})

# Submit survey response
@login_required
def submit_response(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, is_published=True)
    if request.method == 'POST':
        answers = {}
        for question in survey.questions.filter(deleted_at__isnull=True):
            selected_options = request.POST.getlist(str(question.id))
            answers[question.id] = selected_options
        response = Response.objects.create(survey=survey, user=request.user.userprofile)
        for question_id, option_ids in answers.items():
            question = Question.objects.get(id=question_id)
            options = Option.objects.filter(id__in=option_ids)
            answer = Answer.objects.create(response=response, question=question)
            print(f"Answer id is {answer.id}")
            answer.selected_options.set(options)
        messages.success(request, "Survey response submitted successfully!")
        return redirect('taker_dashboard')
    return redirect('take_survey', survey_id=survey_id)

@login_required
def republish_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    if not survey.is_published:
        survey.is_published = True
        survey.is_closed = False
        survey.save()

    questions = survey.questions.filter(deleted_at__isnull=True)
    statistics = {}
    for question in questions:
        options = question.options.annotate(vote_count=Count('response'))
        statistics[question.question_text] = [
            (option.option_text, option.vote_count) for option in options
        ]

    return render(request, 'survey/republish_survey.html', {
        'survey': survey,
        'statistics': statistics,
    })


# View survey results
@login_required
def view_results(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, creator=request.user)
    questions = survey.questions.filter(deleted_at__isnull=True)
    statistics = {}

    for question in questions:
        total_responses = Response.objects.filter(survey=survey).count()
        options = question.options.annotate(vote_count=Count('response'))
        statistics[question.question_text] = [
            (option.option_text, option.vote_count, (option.vote_count / total_responses) * 100 if total_responses else 0)
            for option in options
        ]

    return render(request, 'survey/results.html', {'survey': survey, 'statistics': statistics})


# Logout user
@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')