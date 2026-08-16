from django.urls import path
from django.contrib import admin
from . import admin_views

urlpatterns = [
    path('estudiantes/', admin.site.admin_view(admin_views.StudentListAdminView.as_view()), name='admin_student_list'),
    path('estudiantes/<str:username>/', admin.site.admin_view(admin_views.StudentDetailAdminView.as_view()), name='admin_student_detail'),
]
