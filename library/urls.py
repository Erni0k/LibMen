from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'library'

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.LogoutPostView.as_view(), name='logout'),
]
