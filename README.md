## About
Epróba is Django web app for managing scouts worksheets from website.

## Running app in local environment. 
You can run this app in any system with python installed. 
### Linux
First make sure you have installed python in min. version 3.7 or recommend 3.12
1. Clone repository to your disk using `git clone git@github.com:eproba/web.git`  
2. Navigate to repo directory: `cd eproba`  
3. Create virtual environment using python venv `venv eproba` and activate it (`source eproba/bin/activate`)  
4. Install dependencies: `pip3 install -r requirements.txt`  
5. Create migrations: `python manage.py makemigrations`  
6. Make migrations: `python manage.py migrate`  
7. Copy static files to your static directory: `python manage.py collectstatic`  
8. Run the standard tests. These should all pass: `python manage.py test`  
9. Create admin account: `python eproba/manage.py createsuperuser`  
10. Start server: `python eproba/manage.py runserver`  

### Windows
First make sure you have installed [git](https://git-scm.com/downloads) and [python](https://www.python.org/downloads/) in min. version 3.7 or recommend 3.12.  
If you are using Windows 10 or Windows 11, you can download python from the [Microsoft store](https://www.microsoft.com/store/productId/9P7QFQMJRFP7).
1. Clone repository to your disk using `git clone git@github.com:eproba/web.git`  
2. Navigate to repo directory: `cd eproba`  
3. Create virtual environment using python venv (available from python 3.3) `venv eproba` and activate it (`eproba/bin/activate.bat`)  
4. Install dependencies: `pip3 install -r requirements.txt`  
5. Create migrations: `python manage.py makemigrations`  
6. Make migrations: `python manage.py migrate`  
7. Copy static files to your static directory: `python manage.py collectstatic`  
8. Run the standard tests. These should all pass: `python manage.py test`  
9. Create admin account: `python eproba/manage.py createsuperuser`  
10. Start server: `python eproba/manage.py runserver`
