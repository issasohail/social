from django.urls import path
from . import views
urlpatterns=[
    path('',views.team_list,name='team_list'),
    path('new/',views.team_create,name='team_create'),
    path('<int:pk>/',views.team_detail,name='team_detail'),
    path('<int:pk>/edit/',views.team_edit,name='team_edit'),
    path('export/<str:export_format>/',views.team_export,name='team_export'),
    path('terms/',views.term_list,name='team_terms'),
    path('settings/',views.team_settings,name='team_settings'),
]
