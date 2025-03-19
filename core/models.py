from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime

User = get_user_model()


# User profile
class Profile(models.Model):
    # The user of the current operation
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_user = models.IntegerField()
    # personal profile
    bio = models.TextField(blank=True)
    # avatar
    profileimg = models.ImageField(upload_to='profile_images', default='blank-profile-picture.png')
    # geography
    location = models.CharField(max_length=100, blank=True)


# Posts
class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # user name
    user = models.CharField(max_length=100)
    # Posting terkait untuk pictures
    image = models.ImageField(upload_to='post_images')
    # caption
    caption = models.TextField()
    created_at = models.DateTimeField(default=datetime.now)
    # number of likes
    no_of_likes = models.IntegerField(default=0)


class LikePost(models.Model):
    # Article id
    post_id = models.CharField(max_length=500)
    # user ID
    username = models.CharField(max_length=100)


class FollowersCount(models.Model):
    # follower
    follower = models.CharField(max_length=100)
    # user
    user = models.CharField(max_length=100)


class Comment(models.Model):
    # Posts to which the comment belongs
    post_id = models.CharField(max_length=500)
    # Commenter's username
    username = models.CharField(max_length=100)
    # Comments
    comment = models.TextField()
    # Comment time
    created_at = models.DateTimeField(default=datetime.now)
