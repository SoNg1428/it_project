from django.urls import path
from . import views
from django.views.decorators.cache import cache_page

urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup'),
    path('signin', views.signin, name='signin'),
    path('settings', views.settings, name='settings'),
    path('search', views.search, name='search'),
    path('upload', views.upload, name='upload'),
    path('logout', views.logout, name='logout'),
    # path('profile/<str:pk>', views.profile, name='profile'),
    path('profile/<str:pk>', cache_page(60 * 15)(views.profile), name='profile'),
    path('follow', views.follow, name='follow'),
    path('like-post', views.like_post, name='like-post'),
    path('add-comment', views.add_comment, name='add-comment'),
    path('forgot-password', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:uidb64>/<str:token>', views.reset_password_confirm, name='reset_password_confirm'),
]
