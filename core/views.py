from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from itertools import chain
import random

from .models import Profile, Post, LikePost, FollowersCount, Comment


@login_required(login_url='signin')
def index(request):
    # Get basic information about current active users
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    # Get a list of users that the current user is following
    user_following = FollowersCount.objects.filter(follower=request.user.username)
    
    # Print debug information
    print(f"当前用户: {request.user.username}")
    print(f"关注的用户: {[users.user for users in user_following]}")
    
    user_following_list = [users.user for users in user_following]
    
    # Get posts from followed users
    post_list = []
    for username in user_following_list:
        user_posts = Post.objects.filter(user=username).order_by('-created_at')
        
        # Add user profile information to each post
        for post in user_posts:
            try:
                post_user = User.objects.get(username=post.user)
                post.user_profile = Profile.objects.get(user=post_user)
                # Get comments on posts
                post.comments = Comment.objects.filter(post_id=post.id).order_by('-created_at')
                # Add user avatars to each comment
                for comment in post.comments:
                    try:
                        comment_user = User.objects.get(username=comment.username)
                        comment.user_profile = Profile.objects.get(user=comment_user)
                    except:
                        pass
                post.comment_count = len(post.comments)
            except:
                pass
        
        post_list.extend(user_posts)
        print(f"用户 {username} 的帖子数量: {len(user_posts)}")
    
    # Display an alert message if you are not following anyone
    if not post_list:
        messages.info(request, 'You are not following anyone yet. Follow some users to see their posts!')
    
    # Get a list of recommended users
    all_users = User.objects.all()
    user_following_all = [User.objects.get(username=user.user) for user in user_following]
    
    # Excluding Followed People and Current Users
    new_suggestions_list = [x for x in all_users if x not in user_following_all]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in new_suggestions_list if x not in current_user]
    
    # Randomly disrupting the list of recommended users
    random.shuffle(final_suggestions_list)
    
    # Obtaining Personal Information of Referral Users
    suggestions_username_profile_list = []
    for users in final_suggestions_list:
        suggestions_username_profile_list.append(Profile.objects.filter(user=users).first())
    
    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'post_list': post_list,
        'suggestions_username_profile_list': suggestions_username_profile_list
    }
    return render(request, 'index.html', context)


# Login
def signin(request):
    # post request
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        print(f"username:{username}")
        print(f"password:{password}")
        # calibration
        user = auth.authenticate(username=username, password=password)
        print(f"user:{user}")
        # If the user exists
        if user is not None:
            # messages.info(request, '登录成功')
            # return redirect('signin')
            auth.login(request, user)
            return redirect('/')
        # If the user does not exist
        else:
            messages.info(request, '登录失败')
            return redirect('signin')
    # If not a post request
    else:
        return render(request, 'signin.html')


# Register
def signup(request):
    # post request
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password1']
        password2 = request.POST['password2']
        # If the passwords are equal
        if password == password2:
            # If the mailbox already exists
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email Taken")
                return redirect('signup')
            # If the username already exists
            elif User.objects.filter(username=username).exists():
                messages.info(request, "Username Taken")
                return redirect('signup')
            # If none of it exists.
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # sign in
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)
                # Setting the default personal information
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                # Jump to the screen of setting personal information
                return redirect('settings')
        # If the passwords are not equal
        else:
            messages.info(request, 'Password Not Matching')
            return redirect('signup')
    # not post request
    else:
        return render(request, 'signup.html')


# User information
@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        try:
            # Updating user information
            if 'username' in request.POST:
                request.user.username = request.POST['username']
                request.user.save()
            
            if 'email' in request.POST:
                request.user.email = request.POST['email']
                request.user.save()

            # Update personal data
            if 'bio' in request.POST:
                user_profile.bio = request.POST['bio']
            
            if 'location' in request.POST:
                user_profile.location = request.POST['location']

            # Processing avatar uploads
            if 'profileimg' in request.FILES:
                user_profile.profileimg = request.FILES['profileimg']

            user_profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('settings')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            return redirect('settings')
            
    return render(request, 'settings.html', {
        'user_profile': user_profile,
        'user': request.user
    })


# Search other users
@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    username_profile_list = []  # Initialising an empty list

    if request.method == 'POST':
        username = request.POST['username']
        # Fuzzy Queries Ignore Case  icontains
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        # List of basic information of people searched
        username_profile_list = []
        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)

        username_profile_list = list(chain(*username_profile_list))

    return render(request, 'search.html',
                  {'user_profile': user_profile, 'username_profile_list': username_profile_list})


# Upload image
@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect('/')
    else:
        return redirect('/')


# Log out
@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')


# User profile
@login_required(login_url='signin')
def profile(request, pk):
    # user object
    user_object = User.objects.get(username=pk)
    # Basic user information
    user_profile = Profile.objects.get(user=user_object)
    # User Posts
    user_posts = Post.objects.filter(user=pk)
    # Number of user posts
    user_post_length = len(user_posts)

    # current user
    follower = request.user.username
    # Queried Users
    user = pk
    # If there are found, it means that it has been followed, and can only be unfollowed operation
    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    # Querying the followers of a query's users, followers
    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
    }
    return render(request, 'profile.html', context)


# Follow other users
@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        try:
            # Operator, current user
            follower = request.POST['follower']
            # People who view
            user = request.POST['user']
            
            print(f"当前用户: {request.user.username}")
            print(f"表单follower: {follower}")
            print(f"表单user: {user}")

            # Use the current login username instead of the follower value in the form
            follower = request.user.username
            
            # Deleting a piece of data
            if FollowersCount.objects.filter(follower=follower, user=user).first():
                delete_follower = FollowersCount.objects.get(follower=follower, user=user)
                delete_follower.delete()
                print(f"取消关注: {follower} 不再关注 {user}")
                return redirect('/profile/' + user)
            # Add a new piece of data
            else:
                new_follower = FollowersCount.objects.create(follower=follower, user=user)
                new_follower.save()
                print(f"新增关注: {follower} 现在关注 {user}")
                return redirect('/profile/' + user)
        except Exception as e:
            print(f"关注操作出错: {str(e)}")
            messages.error(request, f"关注操作出错: {str(e)}")
            return redirect('/')
    else:
        return redirect('/')


# Liking posts
@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    # Liked by this user +1
    if not like_filter:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes = post.no_of_likes + 1
        post.save()
        return redirect('/')
    # Not liked by this user -1
    else:
        like_filter.delete()
        post.no_of_likes = post.no_of_likes - 1
        post.save()
        return redirect('/')


# comment
@login_required(login_url='signin')
def add_comment(request):
    if request.method == 'POST':
        username = request.user.username
        post_id = request.POST['post_id']
        comment_text = request.POST['comment_text']
        
        if comment_text.strip():  # Make sure comments are not empty
            new_comment = Comment.objects.create(
                post_id=post_id,
                username=username,
                comment=comment_text
            )
            new_comment.save()
            messages.success(request, 'Comments have been posted')
        else:
            messages.info(request, 'Comments cannot be empty')
            
        return redirect('/')
    else:
        return redirect('/')


# Retrieve password
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate token to reset password
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # Build the URL to reset your password
            reset_url = request.build_absolute_uri(
                reverse('reset_password_confirm', args=[uid, token])
            )
            # Send Mail
            send_mail(
                'Social Book - Reset Password',
                f'Hello，\n\nPlease click the following link to reset your password：\n{reset_url}\n\nIf this is not your operation, please ignore this email. \n\nHave fun with it! \n\nSocial Book Team',
                'Social Book <1305905369@qq.com>',  # Your email
                [email],
                fail_silently=False,
            )
            messages.success(request, 'The link has been sent to your email')
            return redirect('signin')
        except User.DoesNotExist:
            messages.error(request, 'This email is not registered')
    return render(request, 'forgot_password.html')


def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            if new_password1 == new_password2:
                user.set_password(new_password1)
                user.save()
                messages.success(request, 'Password has been successfully reset, please use the new password to login!')
                return redirect('signin')
            else:
                messages.error(request, 'Inconsistent passwords entered twice')
    else:
        messages.error(request, 'Reset password link is invalid or expired')
        return redirect('forgot_password')

    return render(request, 'reset_password.html')