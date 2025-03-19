from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Profile, Post, LikePost, FollowersCount, Comment
import uuid


# MODEL TESTS
class ProfileModelTest(TestCase):
    """Test Profile Model"""

    def setUp(self):
        """Set up test user and profile"""
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.profile = Profile.objects.create(user=self.user, id_user=self.user.id, bio='Hello!', location='NY')

    def test_profile_creation(self):
        """Test if Profile is created correctly"""
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.bio, 'Hello!')
        self.assertEqual(self.profile.location, 'NY')


class PostModelTest(TestCase):
    """Test Post Model"""

    def setUp(self):
        """Set up test user and post"""
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.post = Post.objects.create(user=self.user.username, caption="Test Post")

    def test_post_creation(self):
        """Test if Post is created correctly"""
        self.assertEqual(self.post.user, 'testuser')
        self.assertEqual(self.post.caption, "Test Post")
        self.assertEqual(self.post.no_of_likes, 0)


class LikePostModelTest(TestCase):
    """Test LikePost Model"""

    def setUp(self):
        """Set up test like"""
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.post = Post.objects.create(user=self.user.username, caption="Test Post")
        self.like = LikePost.objects.create(post_id=self.post.id, username=self.user.username)

    def test_like_post(self):
        """Test if LikePost is created correctly"""
        self.assertEqual(self.like.post_id, str(self.post.id))
        self.assertEqual(self.like.username, 'testuser')


class FollowersCountModelTest(TestCase):
    """Test FollowersCount Model"""

    def setUp(self):
        """Set up test follow relationship"""
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.follow = FollowersCount.objects.create(follower='user1', user='user2')

    def test_followers_count(self):
        """Test if follow relationship is created correctly"""
        self.assertEqual(self.follow.follower, 'user1')
        self.assertEqual(self.follow.user, 'user2')


class CommentModelTest(TestCase):
    """Test Comment Model"""

    def setUp(self):
        """Set up test comment"""
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.post = Post.objects.create(user=self.user.username, caption="Test Post")
        self.comment = Comment.objects.create(post_id=self.post.id, username='testuser', comment="Nice post!")

    def test_comment_creation(self):
        """Test if Comment is created correctly"""
        self.assertEqual(self.comment.post_id, str(self.post.id))
        self.assertEqual(self.comment.username, 'testuser')
        self.assertEqual(self.comment.comment, "Nice post!")


# VIEW TESTS
class UserAuthenticationTests(TestCase):
    """Tests for user signup, login, and logout"""

    def setUp(self):
        """Set up a test user"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')

    def test_signup_view(self):
        """Test user signup"""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'password123',
            'password2': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signin_view(self):
        """Test user login"""
        response = self.client.post(reverse('signin'), {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_logout_view(self):
        """Test user logout"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class PostTests(TestCase):
    """Tests for post creation and liking"""

    def setUp(self):
        """Set up test user and post"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.post = Post.objects.create(user=self.user.username, caption="Test Post")

    def test_upload_post(self):
        """Test creating a new post"""
        response = self.client.post(reverse('upload'), {'caption': 'New test post'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(caption='New test post').exists())

    def test_like_post(self):
        """Test liking a post"""
        response = self.client.get(reverse('like_post') + f"?post_id={self.post.id}")
        self.post.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.post.no_of_likes, 1)


class FollowTests(TestCase):
    """Tests for following and unfollowing users"""

    def setUp(self):
        """Set up test users"""
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.client.login(username='user1', password='password123')

    def test_follow_user(self):
        """Test following another user"""
        response = self.client.post(reverse('follow'), {'follower': 'user1', 'user': 'user2'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FollowersCount.objects.filter(follower='user1', user='user2').exists())

    def test_unfollow_user(self):
        """Test unfollowing a user"""
        FollowersCount.objects.create(follower='user1', user='user2')
        response = self.client.post(reverse('follow'), {'follower': 'user1', 'user': 'user2'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FollowersCount.objects.filter(follower='user1', user='user2').exists())
