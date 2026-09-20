"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from boards.views import board_dashboard
from accounts.views import staff_access_create, staff_access_delete, staff_user_create, staff_users
from .views import create_form_invitation, dashboard, harmony_list, organization_overview, people_list, public_form, shared_profile

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('organization/', organization_overview, name='organization'),
    path('people/', people_list, name='people'),
    path('family-harmony/', harmony_list, name='family_harmony'),
    path('family-harmony/form/<str:token>/', public_form, name='public_form'),
    path('family-harmony/form-invitation/new/', create_form_invitation, name='create_form_invitation'),
    path('family-harmony/share/<str:token>/', shared_profile, name='shared_profile'),
    path('boards/<str:code>/', board_dashboard, name='board_dashboard'),
    path('staff-admin/users/', staff_users, name='staff_users'),
    path('staff-admin/users/new/', staff_user_create, name='staff_user_create'),
    path('staff-admin/users/<int:user_id>/access/new/', staff_access_create, name='staff_access_create'),
    path('staff-admin/access/<int:access_id>/remove/', staff_access_delete, name='staff_access_delete'),
    path('admin/', admin.site.urls),
]
