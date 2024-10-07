# Django Application Integration with exsited-python SDK
## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setup Django Project](#setup-django-sdk)
  - [1. Clone the Project](#1-clone-the-project)
  - [2. Set Up Virtual Environment](#2-set-up--virtual-environment)
  - [3. Install necessary dependencies](#3-install-necessary-dependencies)

- [Steps to Integrate the SDK](#steps-to-integrate-the-sdk)
  - [1. Create a Dependency Directory](#1-create-a-dependency-directory)
  - [2. Navigate to the Dependency Directory](#2-navigate-to-the-dependency-directory)
  - [3. Clone the SDK Repository](#3-clone-the-sdk-repository)
  - [4. Install SDK Dependencies](#4-install-sdk-dependencies)
  - [5. Set exsited-python as a Source Root](#5-set-exsited-python-as-a-source-root)
  - [6. Update SDK Credentials](#6-update-sdk-credentials)
  - [7. Update Database Credentials](#7-update-database-credentials)
  - [8. Run the Django Application](#8-run-the-django-application)
- [Conclusion](#conclusion)


## Overview

This guide outlines the steps required to integrate the "exsited-python SDK" into your Django project. By following this guide, you'll install necessary "dependencies," set up a "virtual environment," configure "database credentials," and run the "project."

## Prerequisites

Ensure the following are installed on your system:
- Python 3.12.3
- Git
- MySQl
- Django 5.0.6
- django-mysqlclient


##  Setup Django SDK

### 1. Clone the Project

```bash
git clone https://github.com/exsited/django_sdk_project.git

# navigate into the directory
cd django_sdk_project/djangoSDK

```
### 2. Set up  virtual environment

```bash
# Install "virtualenv" if not already installed
pip install virtualenv

# Create a "virtual environment"
python -m venv venv

# Activate the "virtual environment" (Windows)
venv\Scripts\activate

# For Linux/Mac, use: 
source venv/bin/activate

# Upgrade "pip"
python -m pip install --upgrade pip
```
### 3. Install necessary dependencies

```bash
pip install Django==5.0.6
pip install mysqlclient
pip install djangorestframework
```



## Steps to Integrate the SDK
### 1. Create a Dependency Directory

First, create a directory within your Django project to store the SDK and its dependencies:

```bash
mkdir dependencies
```

### 2. Navigate to the Dependency Directory

Change your working directory to the newly created dependencies directory:

```bash
cd dependencies
```

### 3. Clone the SDK Repository

Clone the exsited-python SDK repository from "GitHub" into your dependencies directory:

```bash
git clone https://github.com/exsited/exsited-python.git
```


### 4. Install SDK Dependencies

Navigate to the exsited-python directory and  install the necessary dependencies:

```bash
cd exsited-python

# Install "setuptools"
pip install setuptools

# Install the SDK as a "dependency"
pip install -e .

# Install additional "dependencies"
pip install peewee
pip install mysql-connector-python
```


### 5. Set exsited-python as a Source Root

Configure your "Django project to recognize the "exsited-python" directory as a source root, so you can import and use the SDK. This step may vary depending on your IDE. If needed, adjust your PYTHONPATH or configure your IDE to include the exsited-python directory.

### 6. Update SDK Credentials

Go to the file located at `dependencies/exsited-python/tests/common/common_data.py` and update the following credentials with your details:

```python
clientId	= "[YOUR_CLIENT_ID]"
clientSecret    = "[YOUR_CLIENT_SECRET]"
redirectUri	= "[YOUR_REDIRECT_URI]"
ExsitedUrl	= "[YOUR_EXSITED_SERVER_URL]"
```

### 7. Update Database Credentials

Next, go to `djangoSDK/service/utils.py` and update the database credentials:

```python
def connect_to_db():
    return MySQLdb.connect(
        host="[YOUR_HOST]",          # Your Database host
        user="[YOUR_USERNAME]",      # Your Database username
        passwd="[YOUR_PASSWORD]",    # Your Database password
        db="[YOUR_DATABASE_NAME]"    # Your Database name
    )
```

### 8. Run the Django Application

Finally, navigate to the "djangoSDK" directory and run the Django development server:

```bash
python manage.py runserver
```

## Conclusion

By following these steps, you should be able to successfully integrate the exsited-python SDK into your Django project. If you encounter any issues, ensure your environment is set up correctly, and all dependencies are properly installed.
