"""
URL configuration for course_registration project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path
from course_registration import views

urlpatterns = [
    path('', views.root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashbord/', views.admin_dashbord, name='admin_dashbord'),
    path('materials/', views.materials_page, name='materials_page'),
    path('students/', views.students_page, name='students_page'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('sections/', views.sections_page, name='sections_page'),
    path('reports/', views.reports_page, name='reports_page'),
    path('students/add/', views.add_student, name='add_student'),
    path('sections/add/', views.add_section, name='add_section'),
    path('materials/add/', views.add_material_page, name='add_material_page'),
    path('sections/<int:id>/edit/', views.edit_section, name='edit_section'),
    path('materials/<int:material_id>/', views.material_detail, name='material_detail'),
    path('grades_entry/', views.grades_entry, name='grades_entry'),
    path('add_grade_entry/', views.add_grade_entry, name='add_grade_entry'),
    path('procedures/', views.procedures_page, name='procedures_page'),
    path('materials_download/', views.materials_download_page, name='materials_download_page'),
    path('students/materials_download/', views.student_material_download, name='student_material_download'),
    path('students/edit_student_downloads/', views.edit_student_downloads, name='edit_student_downloads'),
    path('procedures/material_prerequisites/', views.manage_material_prerequisites, name='manage_material_prerequisites'),
    path('procedures/timetable/', views.timetable_page, name='timetable_page'),
    path('procedures/timetable/save/', views.save_lecture, name='save_lecture'),

]
