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
    # 获取当前活跃用户的基本信息
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    # 获取当前用户关注的用户列表
    user_following = FollowersCount.objects.filter(follower=request.user.username)
    
    # 打印调试信息
    print(f"当前用户: {request.user.username}")
    print(f"关注的用户: {[users.user for users in user_following]}")
    
    user_following_list = [users.user for users in user_following]
    
    # 获取关注用户的帖子
    post_list = []
    for username in user_following_list:
        user_posts = Post.objects.filter(user=username).order_by('-created_at')
        
        # 为每个帖子添加用户资料信息
        for post in user_posts:
            try:
                post_user = User.objects.get(username=post.user)
                post.user_profile = Profile.objects.get(user=post_user)
                # 获取帖子的评论
                post.comments = Comment.objects.filter(post_id=post.id).order_by('-created_at')
                # 为每条评论添加用户头像
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
    
    # 如果没有关注任何人，显示提示信息
    if not post_list:
        messages.info(request, 'You are not following anyone yet. Follow some users to see their posts!')
    
    # 获取推荐用户列表
    all_users = User.objects.all()
    user_following_all = [User.objects.get(username=user.user) for user in user_following]
    
    # 排除已关注的人和当前用户
    new_suggestions_list = [x for x in all_users if x not in user_following_all]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in new_suggestions_list if x not in current_user]
    
    # 随机打乱推荐用户列表
    random.shuffle(final_suggestions_list)
    
    # 获取推荐用户的个人信息
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


# 登录
def signin(request):
    # 如果是post请求
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        print(f"username:{username}")
        print(f"password:{password}")
        # 校验
        user = auth.authenticate(username=username, password=password)
        print(f"user:{user}")
        # 如果用户存在
        if user is not None:
            # messages.info(request, '登录成功')
            # return redirect('signin')
            auth.login(request, user)
            return redirect('/')
        # 如果用户不存在
        else:
            messages.info(request, '登录失败')
            return redirect('signin')
    # 如果不是post请求
    else:
        return render(request, 'signin.html')


# 注册
def signup(request):
    # 如果是post请求
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password1']
        password2 = request.POST['password2']
        # 如果密码相等
        if password == password2:
            # 如果邮箱已存在
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email Taken")
                return redirect('signup')
            # 如果用户名已经存在
            elif User.objects.filter(username=username).exists():
                messages.info(request, "Username Taken")
                return redirect('signup')
            # 如果都不存在
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # 登录
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)
                # 设置默认的个人信息
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                # 跳转到设置个人信息界面
                return redirect('settings')
        # 如果密码不等，提示
        else:
            messages.info(request, 'Password Not Matching')
            return redirect('signup')
    # 如果请求不是post，保持在注册界面
    else:
        return render(request, 'signup.html')


@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        try:
            # 更新用户信息
            if 'username' in request.POST:
                request.user.username = request.POST['username']
                request.user.save()
            
            if 'email' in request.POST:
                request.user.email = request.POST['email']
                request.user.save()

            # 更新个人资料
            if 'bio' in request.POST:
                user_profile.bio = request.POST['bio']
            
            if 'location' in request.POST:
                user_profile.location = request.POST['location']

            # 处理头像上传
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


@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    username_profile_list = []  # 初始化空列表

    if request.method == 'POST':
        username = request.POST['username']
        # 模糊查询 忽略大小写 icontains
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        # 搜索到的人的基本信息列表
        username_profile_list = []
        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)

        username_profile_list = list(chain(*username_profile_list))

    return render(request, 'search.html',
                  {'user_profile': user_profile, 'username_profile_list': username_profile_list})


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


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')


@login_required(login_url='signin')
def profile(request, pk):
    # 用户对象
    user_object = User.objects.get(username=pk)
    # 用户基本信息
    user_profile = Profile.objects.get(user=user_object)
    # 用户帖子
    user_posts = Post.objects.filter(user=pk)
    # 用户帖子数
    user_post_length = len(user_posts)

    # 当前用户
    follower = request.user.username
    # 查询的用户
    user = pk
    # 如果有查到的，说明已经关注过，只能进行取消关注操作
    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    # 反之同理
    else:
        button_text = 'Follow'

    # 查询查询的用户的关注者，跟随者
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


@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        try:
            # 操作者，当前用户
            follower = request.POST['follower']
            # 查看的人
            user = request.POST['user']
            
            print(f"当前用户: {request.user.username}")
            print(f"表单follower: {follower}")
            print(f"表单user: {user}")

            # 使用当前登录用户名，而不是表单中的follower值
            follower = request.user.username
            
            # 删除一条数据
            if FollowersCount.objects.filter(follower=follower, user=user).first():
                delete_follower = FollowersCount.objects.get(follower=follower, user=user)
                delete_follower.delete()
                print(f"取消关注: {follower} 不再关注 {user}")
                return redirect('/profile/' + user)
            # 新增一条数据
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


@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    # 被这个用户喜欢 +1
    if not like_filter:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes = post.no_of_likes + 1
        post.save()
        return redirect('/')
    # 没有被这个用户喜欢 -1
    else:
        like_filter.delete()
        post.no_of_likes = post.no_of_likes - 1
        post.save()
        return redirect('/')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # 生成重置密码的token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # 构建重置密码的URL
            reset_url = request.build_absolute_uri(
                reverse('reset_password_confirm', args=[uid, token])
            )
            # 发送邮件
            send_mail(
                'Social Book - 重置密码',
                f'您好，\n\n请点击以下链接重置密码：\n{reset_url}\n\n如果这不是您的操作，请忽略此邮件。\n\n祝您使用愉快！\n\nSocial Book团队',
                'Social Book <1305905369@qq.com>',  # 使用你的邮箱
                [email],
                fail_silently=False,
            )
            messages.success(request, '重置密码链接已发送到您的邮箱')
            return redirect('signin')
        except User.DoesNotExist:
            messages.error(request, '该邮箱未注册')
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
                messages.success(request, '密码已成功重置，请使用新密码登录')
                return redirect('signin')
            else:
                messages.error(request, '两次输入的密码不一致')
    else:
        messages.error(request, '重置密码链接无效或已过期')
        return redirect('forgot_password')
    
    return render(request, 'reset_password.html')

@login_required(login_url='signin')
def add_comment(request):
    if request.method == 'POST':
        username = request.user.username
        post_id = request.POST['post_id']
        comment_text = request.POST['comment_text']
        
        if comment_text.strip():  # 确保评论不为空
            new_comment = Comment.objects.create(
                post_id=post_id,
                username=username,
                comment=comment_text
            )
            new_comment.save()
            messages.success(request, '评论已发布')
        else:
            messages.info(request, '评论不能为空')
            
        return redirect('/')
    else:
        return redirect('/')
