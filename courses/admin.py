from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
	list_display = ('student_id', 'first_name', 'last_name', 'email', 'is_active', 'created_at')
	search_fields = ('first_name', 'last_name', 'email', 'student_id')
	list_filter = ('is_active',)
