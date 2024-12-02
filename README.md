# Django Survey Project
A project in which we utilize Django to create a survey creation and taking application. Utilizing Postgresql as our database and Bootstrap as our frontend framework. 

## Installation
First download the project folder and navigate into it through the command prompt:

```bash
cd final project (1)/final project/survey
```

Use the package installer pip to get django and crispy_forms like so:

```bash
pip install django
pip install django-crispy-forms
```

## Usage
In order to properly use this application, you need to have a DBMS installed. Go and install PostgreSQL. When installed and working, make sure to make your Server password 'Pineapple110!' or else you will have to manually change the password in the settings file. 

Once that is installed connect the application by creating a database called project_TDS.

If you are using a different password, go to line 83 in the settings.py file and change 'Pineapple110!' to whatever password you set.

Run these commands to make sure your database is set up for the application:

```bash
python manage.py makemigrations survey
python manage.py migrate --run-syncdb
```
### Authors
Jake Castellano, Shunottara Ingle, Nayanpreet Chhabra, Prasanna Bidkar
