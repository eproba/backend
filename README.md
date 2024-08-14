## About
Scouts exams is Django web app for managing scouts exams from website.

## Running app in local environment. 
You can run this app in any system with python installed. 
### Linux
First make sure you have installed python in min. version 3.7 or recommend 3.9
1. Clone repository to your disk using `git clone git@github.com:Antoni-Czaplicki/scouts_exams.git`  
2. Navigate to repo directory: `cd eproba`  
3. Create virtual environment using python venv (available from python 3.3) `venv scouts_exams` and activate it (`source scouts_exams/bin/activate`)  
4. Install dependencies: `pip3 install -r requirements.txt`  
5. Create migrations: `python3 manage.py makemigrations`  
6. Make migrations: `python3 manage.py migrate`  
7. Copy static files to your static directory: `python3 manage.py collectstatic`  
8. Run the standard tests. These should all pass: `python3 manage.py test`  
9. Create admin account: `python3 scouts_exams/manage.py createsuperuser`  
10. Start server: `python3 scouts_exams/manage.py runserver`  

### Windows
First make sure you have installed [git](https://git-scm.com/downloads) and [python](https://www.python.org/downloads/) in min. version 3.7 or recommend 3.9.  
If you are using Windows 10 or Windows 11, you can download python from the [Microsoft store](https://www.microsoft.com/store/productId/9P7QFQMJRFP7).
1. Clone repository to your disk using `git clone git@github.com:Antoni-Czaplicki/scouts_exams.git`  
2. Navigate to repo directory: `cd scouts_exams`  
3. Create virtual environment using python venv (available from python 3.3) `venv scouts_exams` and activate it (`scouts_exams/bin/activate.bat`)  
4. Install dependencies: `pip3 install -r requirements.txt`  
5. Create migrations: `python3 manage.py makemigrations`  
6. Make migrations: `python3 manage.py migrate`  
7. Copy static files to your static directory: `python3 manage.py collectstatic`  
8. Run the standard tests. These should all pass: `python3 manage.py test`  
9. Create admin account: `python3 scouts_exams/manage.py createsuperuser`  
10. Start server: `python3 scouts_exams/manage.py runserver`
