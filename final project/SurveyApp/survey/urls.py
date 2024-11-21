from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # User registration and authentication URLs
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='survey/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Home URL
    path('', views.home, name='home'),

    # Dashboard URLs
    path('creator_dashboard/', views.creator_dashboard, name='creator_dashboard'),
    path('taker_dashboard/', views.taker_dashboard, name='taker_dashboard'),

    # Survey Creator URLs
    path('survey/create/', views.create_survey, name='create_survey'),
    path('survey/<int:survey_id>/add_questions/', views.add_questions, name='add_questions'),
    path('survey/<int:survey_id>/edit/', views.edit_survey, name='edit_survey'),
    path('survey/<int:survey_id>/publish/', views.publish_survey, name='publish_survey'),
    path('survey/<int:survey_id>/close/', views.close_survey, name='close_survey'),
    path('survey/<int:survey_id>/republish/', views.republish_survey, name='republish_survey'),

    # Question Management URLs
    path('survey/<int:survey_id>/question/create/', views.edit_question, name='create_question'),
    path('survey/<int:survey_id>/question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('survey/<int:survey_id>/question/<int:question_id>/delete/', views.delete_question, name='delete_question'),

    # Survey Results and Statistics URL
    path('survey/<int:survey_id>/results/', views.view_results, name='view_results'),

    # Survey Taker URLs
    path('survey/list/', views.survey_list, name='survey_list'),
    path('survey/<int:survey_id>/take/', views.take_survey, name='take_survey'),
    path('survey/<int:survey_id>/submit/', views.submit_response, name='submit_response'),
]
