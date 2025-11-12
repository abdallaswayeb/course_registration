from django.contrib import admin
from .models import Student, Section, Material, Enrollment, GradeRecord, MaterialPrerequisite

# --- الأقسام
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active',)

# --- الطلاب
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id_student', 'name', 'section', 'email', 'is_active', 'created_at')
    search_fields = ('name', 'email', 'id_student')
    list_filter = ('is_active', 'section')

# --- المواد
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'section', 'hours')
    search_fields = ('code', 'name')
    list_filter = ('section',)

# --- أسبقيات المواد
@admin.register(MaterialPrerequisite)
class MaterialPrerequisiteAdmin(admin.ModelAdmin):
    list_display = ('prerequisite', 'material')
    search_fields = ('prerequisite__name', 'material__name')

# --- تنزيل المواد
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'material', 'semester', 'year', 'grade')
    search_fields = ('student__name', 'material__name')
    list_filter = ('semester', 'year')

# --- رصد الدرجات
@admin.register(GradeRecord)
class GradeRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'material', 'semester', 'year', 'grade', 'semester_gpa', 'cumulative_gpa')
    search_fields = ('student__name', 'material__name')
    list_filter = ('semester', 'year')