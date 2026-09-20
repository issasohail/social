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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from boards.views import board_dashboard
from accounts.views import staff_access_create, staff_access_delete, staff_user_create, staff_users
from settings_app.views import settings_page
from .views import (create_form_invitation, create_profile_share, dashboard, harmony_create, harmony_delete,
                   harmony_detail, harmony_edit, harmony_export, harmony_inline_update, harmony_list, health,
                   inline_update_person, jamatkhanas, local_councils, organization_overview, people_list,
                   person_create, person_delete, person_detail, person_edit, person_export, create_person_share,
                   public_form, regional_councils, shared_person, shared_profile)

urlpatterns = [
    path('health/', health, name='health'),
    path('', dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('organization/', organization_overview, name='organization'),
    path('organization/regional-councils/', regional_councils, name='regional_councils'),
    path('organization/local-councils/', local_councils, name='local_councils'),
    path('organization/jamatkhanas/', jamatkhanas, name='jamatkhanas'),
    path('settings/regional-councils/', regional_councils, name='settings_regional_councils'),
    path('settings/local-councils/', local_councils, name='settings_local_councils'),
    path('settings/jamatkhanas/', jamatkhanas, name='settings_jamatkhanas'),
    path('people/', people_list, name='people'),
    path('people/new/', person_create, name='person_create'),
    path('people/<int:person_id>/', person_detail, name='person_detail'),
    path('people/<int:person_id>/edit/', person_edit, name='person_edit'),
    path('people/<int:person_id>/delete/', person_delete, name='person_delete'),
    path('people/<int:person_id>/export/<str:export_format>/', person_export, name='person_export'),
    path('people/<int:person_id>/share/', create_person_share, name='create_person_share'),
    path('people/share/<str:token>/', shared_person, name='shared_person'),
    path('people/inline-update/', inline_update_person, name='inline_update_person'),
    path('family-harmony/', harmony_list, name='family_harmony'),
    path('family-harmony/new/', harmony_create, name='harmony_create'),
    path('family-harmony/<int:profile_id>/', harmony_detail, name='harmony_detail'),
    path('family-harmony/<int:profile_id>/edit/', harmony_edit, name='harmony_edit'),
    path('family-harmony/<int:profile_id>/delete/', harmony_delete, name='harmony_delete'),
    path('family-harmony/<int:profile_id>/export/<str:export_format>/', harmony_export, name='harmony_export'),
    path('family-harmony/inline-update/', harmony_inline_update, name='harmony_inline_update'),
    path('family-harmony/<int:profile_id>/share/', create_profile_share, name='create_profile_share'),
    path('family-harmony/form/<str:token>/', public_form, name='public_form'),
    path('family-harmony/form-invitation/new/', create_form_invitation, name='create_form_invitation'),
    path('family-harmony/share/<str:token>/', shared_profile, name='shared_profile'),
    path('boards/<str:code>/', board_dashboard, name='board_dashboard'),
    path('staff-admin/users/', staff_users, name='staff_users'),
    path('staff-admin/users/new/', staff_user_create, name='staff_user_create'),
    path('staff-admin/users/<int:user_id>/access/new/', staff_access_create, name='staff_access_create'),
    path('staff-admin/access/<int:access_id>/remove/', staff_access_delete, name='staff_access_delete'),
    path('settings/', settings_page, name='settings'),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
