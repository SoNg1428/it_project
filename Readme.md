# Social media



## Overview

The project implemented a social media system, a social media platform designed to enable users to create, share and interact with various types of content such as posts, images and videos. Key features include user-generated posts, friend networks, comments and likes.

The system uses Django as the back-end and Bootstrap as the front-end.

## Project Setup

### Prerequisites

Social media system uses a number of open source projects to work properly:

- [Python 3.8+] Python environment
- [Django] Python based web framework
- [Bootstrap] JavaScript based web framework
- [MySQL] Database
- [Redis] In-memory data store
- [GitLab] Open-source Git-based DevOps platform

### Installation

1. Install Dependencies:
```
pip install -r requirements.txt
```

2. Configure the Database:

Create a MySQL database [socialmedia] and configure the database connection in settings.py:
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'socialmedia',
        'USER': 'your_db_username',
        'PASSWORD': 'your_db_password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

3. Configure the Redis:

Make sure you download the Redis and configure the database connection in settings.py:
```
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            # "PASSWORD": ,
            "DECODE_RESPONSES": True
        }
    },
}
```

4. Run Migrations:
```
python manage.py makemigrations
python manage.py migrate
```

5. Run the Development Server:
```
python manage.py runserver
```


## Usage Guide

### User Functions

- **User Registration and Login：** Users can create an account, login and logout. If a user forgets password, can set a new one via email.
- **Personal Page:** Users can edit and update their personal information.
- **User Homepage:** Users can post, view, like and comment.
- **Friends System:** Users can search and follow users.


## Development Guidelines

### Collaboration and Communication

- **Version Control:** All code is committed to the GitHub repository.
- **Team Communication:** Use Microsoft Teams for discussions.